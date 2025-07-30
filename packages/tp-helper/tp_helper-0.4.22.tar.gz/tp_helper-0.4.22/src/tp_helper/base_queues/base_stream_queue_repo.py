from typing import Type, TypeVar, Generic
from pydantic import BaseModel
from redis.asyncio import Redis

SchemaType = TypeVar("SchemaType", bound=BaseModel)


class BaseStreamQueueRepo(Generic[SchemaType]):
    """
    Репозиторий для работы с Redis Stream (XADD/XREADGROUP) с использованием Consumer Group.

    Поддерживает:
    - Добавление сообщений в поток
    - Получение сообщений через группу
    - Подтверждение обработки (XACK)
    - Авто-клейм сообщений (XAUTOCLAIM) при сбоях
    """

    def __init__(
        self,
        redis_client: Redis,
        schema: Type[SchemaType],
        queue_name: str,
        group_name: str,
        consumer_name: str,
    ):
        self.redis_client = redis_client
        self.schema = schema
        self.queue_name = queue_name
        self.group_name = group_name
        self.consumer_name = consumer_name

    async def setup(self, create_stream: bool = True) -> None:
        """
        Создаёт группу потребителей, если она ещё не существует.
        """
        try:
            await self.redis_client.xgroup_create(
                name=self.queue_name,
                groupname=self.group_name,
                id="0",
                mkstream=create_stream,
            )
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise

    async def add(self, schema: SchemaType) -> None:
        """
        Добавляет элемент в поток.

        :param schema: Объект Pydantic-схемы
        """
        data = schema.model_dump()
        await self.redis_client.xadd(self.queue_name, fields=data)

    async def pop(
        self, block: int = 0, count: int = 100
    ) -> list[tuple[str, SchemaType]]:
        """
        Получает сообщение из потока через XREADGROUP.

        :param block: Время блокировки в мс (0 — бесконечно)
        :param count: Сколько сообщений брать из потока.
        :return: Кортеж (message_id, объект схемы) или None
        """
        result = await self.redis_client.xreadgroup(
            groupname=self.group_name,
            consumername=self.consumer_name,
            streams={self.queue_name: ">"},
            count=count,
            block=block,
        )
        if not result:
            return []
        _, messages = result[0]
        return [(msg_id, self.schema(**data)) for msg_id, data in messages]

    async def pop_one(self, block: int = 0) -> tuple[str, SchemaType] | None:
        """
        Получает одно сообщение из потока через XREADGROUP.

        :param block: Время блокировки в мс (0 — бесконечно)
        :return: Кортеж (message_id, объект схемы) или None, если нет сообщений
        """
        result = await self.redis_client.xreadgroup(
            groupname=self.group_name,
            consumername=self.consumer_name,
            streams={self.queue_name: ">"},
            count=1,
            block=block,
        )
        if not result:
            return None

        _, messages = result[0]
        msg_id, data = messages[0]
        return msg_id, self.schema(**data)

    async def ack(self, message_id: str) -> None:
        """
        Подтверждает обработку сообщения.

        :param message_id: Идентификатор сообщения
        """
        await self.redis_client.xack(self.queue_name, self.group_name, message_id)

    async def claim_reassign(
        self, min_idle_time: int = 60000, count: int = 100
    ) -> list[tuple[str, SchemaType]]:
        """
        Переназначает до `count` зависших сообщений текущему consumer'у,
        используя Redis-команду XAUTOCLAIM.

        Возвращает сообщения, которые не были подтверждены и находились в Pending Entries List
        дольше указанного времени (`min_idle_time`), начиная с ID "0-0".

        Пример:
        [
            ("message_id", TestSchema(task_id="abc123", payload="example")),
            ("1718547500414-0", TestSchema(task_id="abc123", payload="example")),
            ("1718547500420-0", TestSchema(task_id="def456", payload="data"))
        ]
        """
        _, messages = await self.redis_client.xautoclaim(
            name=self.queue_name,
            groupname=self.group_name,
            consumername=self.consumer_name,
            min_idle_time=min_idle_time,
            start_id="0-0",
            count=count
        )
        if not messages:
            return []
        return [(msg_id, self.schema(**data)) for msg_id, data in messages if data]
