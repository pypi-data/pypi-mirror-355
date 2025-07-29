""" Модуль реализации базового хендлера для библиотеки. """

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

from aio_pika.abc import HeadersType

from rms_rabbit.datatypes import QueueRoute

logger = logging.getLogger(__name__)

MessageType = TypeVar("MessageType")


class GenericRmsRabbitHandler(Generic[MessageType], ABC):
    """ Класс-джинерик обработчика кролика для сервисов. """
    def __init__(self, route: QueueRoute) -> None:
        self.route = route
        self.requeue: bool = route.requeue
        self.reject_on_redelivered: bool = route.reject_on_redelivered

    @property
    def requested_topics(self) -> List[str]:
        """ Свойство для получения топиков. """
        return self.route.topics

    @property
    def features(self) -> Dict[str, Any]:
        """ Свойство для получения фич. """
        return self.route.features

    @property
    def queue_name(self) -> str:
        """ Свойство для получения названия очереди. """
        return self.route.queue_name

    async def on_message(self, data: MessageType, topic: str, headers: HeadersType) -> None:
        """
            Метод обработки поступившего сообщения.

            Arguments:
                - data: Данные сообщения;
                - topic: Топик, в который было отправлено сообщение;
                - headers: Заголовки сообщения.
        """
        logger.debug("Обработка %s", topic)

        await self.process_message(data, topic, headers)

    @abstractmethod
    async def process_message(
        self,
        attached_data: MessageType,
        topic: str,
        headers: HeadersType
    ) -> None:
        """
            Абстрактный метод обработки сообщения.

            Arguments:
                - attached_data: Данные сообщения;
                - topic: Топик, в который было отправлено сообщение;
                - headers: Заголовки сообщения.
        """
        raise NotImplementedError(f"Определите process_message в {self.__class__.__name__}.")


__all__ = [
    "GenericRmsRabbitHandler",
]
