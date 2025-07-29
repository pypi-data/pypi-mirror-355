""" Модуль реализации базового функционала консьюмера. """

import logging
from typing import Dict, Optional

from aio_pika.abc import AbstractRobustQueue
from aio_pika.message import IncomingMessage

from rms_rabbit.config import config_factory
from rms_rabbit.connectors import Connector
from rms_rabbit.base_handler import GenericRmsRabbitHandler
from rms_rabbit.datatypes import ConsumerConfig
from rms_rabbit.errors import ConsumerError
from rms_rabbit.schemas import consumer_config_schema
from rms_rabbit.serializers import AbstractSerializer

logger = logging.getLogger(__name__)


class Consumer(Connector):
    def __init__(self, config: ConsumerConfig, serializer: Optional[AbstractSerializer] = None):
        if not isinstance(config, ConsumerConfig):
            raise TypeError("Консумер должен быть проинициализован с ConsumerConfig,"
                            f" а не с {type(config)}")

        self._prefetch_count = config.prefetch_count
        self._routing: Dict[str, GenericRmsRabbitHandler] = {}
        self.route = config.route
        super().__init__(config=config, serializer=serializer)

    @classmethod
    def from_settings(
        cls,
        folder: str = "settings",
        section: Optional[str] = None,
        serializer: Optional[AbstractSerializer] = None,
    ) -> "Consumer":
        """
            Метод инициализации консьюмера через конфигурацию.

            Arguments:
                - folder: Папка, из которой читаем настройки;
                - section: Секция файла настроек, из которой читаем настройки консьюмера;
                - serializer: Сериализатор.

            Returning:
                Инициализированный консьюмер.
        """
        config = consumer_config_schema.load(
            config_factory(
                folder=folder,
                section=section,
            )
        )

        return cls(
            config=config,
            serializer=serializer,
        )

    async def connect(self) -> None:
        """ Метод создания соединения для консьюмера. """
        await super().connect()

        await self._channel.set_qos(  # type: ignore
            prefetch_count=self._prefetch_count,
            timeout=self.connection_settings.timeout,
        )

    async def consume_queue(self, queue_handler: GenericRmsRabbitHandler) -> str:
        """
            Метод прослушивания очереди консьюмером.

            Arguments:
                - queue_handler: Обработчик входящих сообщений в очереди.

            Returning:
                Обработанное полученное сообщение.
        """
        await self.connect()

        queue_name = queue_handler.queue_name
        topics = queue_handler.requested_topics
        features = queue_handler.features

        if queue_name in self._channel._queues.keys():  # type: ignore # noqa: WPS437
            raise ConsumerError(f"Очередь \"{queue_name}\" уже прослушивается.")

        for key in topics:
            if queue_handler == self._routing.get(key):
                logger.warning(
                    "Обработчик сообщений в очереди \"%s\" уже обработал ключ \"%s\".",
                    queue_handler,
                    key,
                )
                break

            prefix = key.replace(".#", "").replace(".*", "")
            self._routing[prefix] = queue_handler

            logger.info("Добавляем обработчик для %s топика", prefix)

        logger.info("Прослушиваем очередь \"%s\"", queue_name)

        queue: AbstractRobustQueue = await self._channel.declare_queue(  # type: ignore
            name=queue_name,
            durable=True,
            passive=True,
            timeout=self.timeout,
            arguments=features,
        )

        return await queue.consume(
            callback=self._on_message_received,  # type: ignore
            timeout=self.timeout,
        )

    def _get_handler(self, message: IncomingMessage) -> Optional[GenericRmsRabbitHandler]:
        """
            Внутренний метод получения обработчика сообщений.

            Arguments:
                - message: Входящее сообщение.

            Returning:
                Обработчик сообщения.
        """
        keys = []
        if message.routing_key is not None:
            keys = message.routing_key.split(".")
        handler = None
        while keys and not handler:
            topic = ".".join(keys)
            handler = self._routing.get(topic)
            keys.pop()
        return handler or self._routing.get("*") or self._routing.get("#")

    async def _on_message_received(self, message: IncomingMessage) -> None:
        """
            внутренний метод обработки получения сообщения консьюмером.

            Arguments:
                - message: Входящее сообщение.
        """
        if message.routing_key is None:
            message.routing_key = ""

        handler = self._get_handler(message)

        if not handler:
            logger.debug("Нет роута для сообщения с ключем \"%s\"", message.routing_key)

            await message.nack(requeue=False)
            return

        async with message.process(
            requeue=handler.requeue,
            reject_on_redelivered=handler.reject_on_redelivered,
            ignore_processed=True,
        ):
            try:
                body = self._serializer.deserialize(message.body)
                await handler.on_message(body, message.routing_key, message.headers)
            except Exception as err:
                logger.exception(
                    "Невозможно обработать сообщение \"%s\" в \"%s\" потому что %s.",
                    message.delivery_tag,
                    message.routing_key,
                    err,
                )

                await message.nack(requeue=handler.requeue)
                logger.debug("Сообщение \"%s\" неудовлетворено.", message.delivery_tag)
            else:
                await message.ack()
                logger.debug("Сообщение \"%s\" было удовлетворено.", message.delivery_tag)


__all__ = [
    "Consumer",
]
