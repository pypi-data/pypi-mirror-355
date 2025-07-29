""" Модуль реализации коннекторов для библиотеки работы с очередями. """

import logging
from typing import Optional

from aio_pika import RobustChannel, RobustConnection, connect_robust

from rms_rabbit.datatypes import RabbitConfig
from rms_rabbit.serializers import AbstractSerializer, JSONSerializer

logger = logging.getLogger(__name__)


class Connector:
    """ Класс подлючения для консьюмеров и паблишеров. """

    def __init__(self, config: RabbitConfig, serializer: Optional[AbstractSerializer] = None):
        self.exchange = config.exchange
        self.connection_settings = config.connection_settings

        self.timeout = config.connection_settings.timeout
        self._channel: Optional[RobustChannel] = None
        self._connection: Optional[RobustConnection] = None

        self._serializer = serializer or JSONSerializer()

    async def connect(self) -> None:
        """ Метод создания нового подключения Rabbit. """

        if self._connection is None:
            logger.info(
                "Подключение к RabbitMQ по %s...",
                self.connection_settings.connection_parameters.human_dsn,
            )
            self._connection = await connect_robust(   # type: ignore
                host=self.connection_settings.connection_parameters.host,
                port=self.connection_settings.connection_parameters.port,
                virtualhost=self.connection_settings.connection_parameters.virtualhost,
                login=self.connection_settings.connection_parameters.login,
                password=self.connection_settings.connection_parameters.password,
                timeout=self.connection_settings.timeout,
                reconnect_interval=self.connection_settings.reconnect_interval,
                fail_fast=self.connection_settings.fail_fast,
            )

        if self._channel is None:
            self._channel = await self._connection.channel(  # type: ignore
                channel_number=self.connection_settings.channel.channel_number,
                publisher_confirms=self.connection_settings.channel.publisher_confirms,
                on_return_raises=self.connection_settings.channel.on_return_raises,
            )

    async def close(self) -> None:
        """ Метод закрытия подключения к Rabbit. """
        logger.debug("Закрытие подключения к RabbitMQ...")

        if self._channel is not None:
            await self._channel.close()
            self._channel = None

        if self._connection is not None:
            await self._connection.close()
            self._connection = None


__all__ = [
    "Connector",
]
