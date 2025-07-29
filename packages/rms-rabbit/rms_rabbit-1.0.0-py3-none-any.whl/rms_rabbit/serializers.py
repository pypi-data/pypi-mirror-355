""" Модуль сериализации для библиотеки. """

import json
import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import orjson

logger = logging.getLogger(__name__)

MessageType = TypeVar("MessageType")


class AbstractSerializer(ABC, Generic[MessageType]):
    """ Класс абстракции сериализатора. Базовый класс. """
    content_type: str

    @abstractmethod
    def serialize(self, data: dict) -> bytes:
        """
            Абстрактный метод сериализации.

            Arguments:
                - data: Данные для сериализации.

            Returning:
                Сериализованные данные.
        """
        raise NotImplementedError()

    @abstractmethod
    def deserialize(self, msg: bytes) -> MessageType:
        """
            Абстрактный метод десериализации.

            Arguments:
                - msg: Сериализованные данные, которые нужно десериализовать.

            Returning:
                Десериализованное сообщение.
        """
        raise NotImplementedError()


class JSONSerializer(AbstractSerializer[dict]):
    """ Класс сериализатора json. """
    content_type = "application/json"

    def serialize(self, data: dict) -> bytes:
        try:
            return orjson.dumps(data)
        except Exception:
            logger.error("Message serialization error", exc_info=True)
            raise

    def deserialize(self, msg: bytes) -> dict:
        try:
            return orjson.loads(msg)
        except json.JSONDecodeError:
            logger.error("Error deserializing message body", exc_info=True)
            raise


__all__ = [
    "AbstractSerializer",
    "JSONSerializer",
]
