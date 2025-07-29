""" Модуль реализации базового функционала паблишера. """

import logging
from typing import Dict, Optional, Union

from aio_pika.abc import AbstractRobustExchange, DateType
from aio_pika.message import DeliveryMode, Message

from rms_rabbit.config import config_factory
from rms_rabbit.connectors import Connector
from rms_rabbit.datatypes import PriorityLevels, PublisherConfig
from rms_rabbit.errors import PublisherError
from rms_rabbit.schemas import publisher_config_schema
from rms_rabbit.serializers import AbstractSerializer

logger = logging.getLogger(__name__)


class Publisher(Connector):
    """ Базовый класс паблишера сообщений. """
    def __init__(self, config: PublisherConfig, serializer: Optional[AbstractSerializer] = None):
        if not isinstance(config, PublisherConfig):
            raise TypeError("Паблишер должен быть проинициализован с PublisherConfig,"
                            f" а не с {type(config)}")

        self._routing_key = config.routing_key
        self.message_exchange: Optional[AbstractRobustExchange] = None
        super().__init__(config=config, serializer=serializer)

    @classmethod
    def from_settings(
        cls,
        folder: str = "settings",
        section: Optional[str] = None,
        serializer: Optional[AbstractSerializer] = None,
    ) -> "Publisher":
        """
            Метод инициализации паблишера через конфигурацию.

            Arguments:
                - folder: Папка, из которой читаем настройки;
                - section: Секция файла настроек, из которой читаем настройки паблишера;
                - serializer: Сериализатор.

            Returning:
                Инициализированный паблишер.
        """
        config = publisher_config_schema.load(config_factory(folder=folder, section=section))
        return cls(config=config, serializer=serializer)

    async def connect(self) -> None:
        """ Метод создания соединения для паблишера. """
        await super().connect()

        if self.message_exchange is None:
            self.message_exchange = await self._make_exchange()

    async def publish(
        self,
        data: dict,
        correlation_id: Optional[str],
        headers: Optional[Dict[str, Union[str, int]]] = None,
        routing_key: Optional[str] = None,
        priority: bool = False,
        expiration: Optional[DateType] = None,
    ) -> None:
        """
            Метод публикации сообщения.

            Arguments:
                - data: Данные сообщения для публикации;
                - correlation_id: Идентификатор корреляции;
                - headers: Заголовки сообшения;
                - routing_key: Ключ адресации;
                - priority: Приоритет сообщения;
                - expiration: Окончание действия сообщения.
        """
        routing_key = routing_key or self._routing_key
        try:
            await self._publish(
                data,
                correlation_id,
                headers if headers is not None else {},
                routing_key,
                priority,
                expiration,
            )
            logger.debug("Публикация в %s", routing_key)
        except Exception:
            logger.error("Невозможно отправить сообщение в брокер сообшений", exc_info=True)
            raise PublisherError(f"Невозможно опубликовать сообщение в {routing_key}")

    async def close(self) -> None:
        """ Метод закрытия соединения паблишера. """
        self.message_exchange = None

        await super().close()

    async def _publish(
        self,
        data: dict,
        correlation_id: Optional[str],
        headers: Dict[str, Union[str, int]],
        routing_key: str,
        priority: bool,
        expiration: Optional[DateType],
    ) -> None:
        """
            Внутренний метод публикации сообщения.

            Arguments:
                - data: Данные сообщения для публикации;
                - correlation_id: Идентификатор корреляции;
                - headers: Заголовки сообшения;
                - routing_key: Ключ адресации;
                - priority: Приоритет сообщения;
                - expiration: Окончание действия сообщения.
        """
        await self.connect()

        message = Message(
            body=self._serializer.serialize(data),
            delivery_mode=DeliveryMode.PERSISTENT,
            correlation_id=correlation_id,
            content_type=self._serializer.content_type,
            expiration=expiration,
        )
        message.priority = PriorityLevels.HIGH.value if priority else PriorityLevels.LOW.value
        message.headers.update(headers)

        # self.message_exchange при необходимости пересоздается в self.connect()
        await self.message_exchange.publish(  # type: ignore
            message=message,
            routing_key=routing_key,
            mandatory=self.connection_settings.channel.publisher_confirms,
        )

    async def _make_exchange(self) -> AbstractRobustExchange:
        if self._connection is None:
            logger.error("[RMS_RABBIT][PUBLISHER] Состояние паблишера: Не подключен")

        if self._channel is None:
            logger.error(
                "[RMS_RABBIT][PUBLISHER] Состояние паблишера: Подключение %r не имеет канала",
                self._connection,
            )

        return await self._channel.declare_exchange(  # type: ignore
            name=self.exchange.name,
            type=self.exchange.exchange_type.value,
            durable=True,
            passive=True,
            timeout=self.timeout,
            arguments=self.exchange.args(),
        )


__all__ = [
    "Publisher",
]
