""" Модуль для описания датаклассов для библиотеки. """

import logging
from abc import ABC
from dataclasses import InitVar, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import marshmallow
from marshmallow_dataclass import class_schema

logger = logging.getLogger(__name__)


@dataclass
class ConnectionParameters:
    """ Универсальный класс параметров подключения. """
    host: str
    port: int
    virtualhost: str
    login: str
    password: str

    @property
    def human_dsn(self) -> str:
        """ Свойство получения человекочитабельного адреса подключения. """
        return f"amqp://{self.host}:{self.port}/{self.virtualhost}"

    @staticmethod
    def from_uri(uri: str) -> "ConnectionParameters":
        """
            Метод обработки адреса подлючения и генерации параметров подключения.
            Адрес указывается в переменных окружения, но необходимо проверять None поля.

            Arguments:
                - uri: Адрес подключения.

            Returning:
                Параметры подключения.
        """
        connection = urlparse(uri)

        input_as_dict = {
            "host": connection.hostname,
            "port": connection.port,
            "virtualhost": connection.path[1:],
            "login": connection.username,
            "password": connection.password,
        }

        return connection_parameters_schema.load(input_as_dict)


connection_parameters_schema: marshmallow.Schema = class_schema(ConnectionParameters)()


@dataclass
class ExchangeBinding:
    """ Класс параметров связывания эксченджей. """
    source: str
    topics: List[str] = field(default_factory=list)
    bind_arguments: Dict[str, Any] = field(default_factory=dict)


class ExchangeTypes(Enum):
    """ Класс типов эксченджей. """
    DIRECT = "direct"
    FANOUT = "fanout"
    TOPIC = "topic"
    HEADERS = "headers"
    DELAY = "x-delayed-message"


class PriorityLevels(Enum):
    """ Класс уровней приоритета. """
    LOW = 0
    HIGH = 1


@dataclass
class ChannelSettings:
    """ Класс настроек канала подключения. """
    channel_number: Optional[int] = None
    publisher_confirms: bool = True
    on_return_raises: bool = False


@dataclass
class ExchangeConfig:
    """ Класс конфигурации эксченджей. """
    name: str
    exchange_type: ExchangeTypes = field(metadata=dict(data_key="type", by_value=True))
    binding: Optional[ExchangeBinding] = None
    arguments: List[Tuple[str, Union[str, int]]] = field(default_factory=list)
    dlx: Optional[str] = None

    def args(self) -> Dict[str, Union[str, int]]:
        """
            Метод получения аргументов эксченджа.

            Returning:
                Объект с параметрами и их значениями эксченджа.
        """
        return {k_arg: v_arg for k_arg, v_arg in self.arguments}

    def __str__(self) -> str:
        return f"{self.name}: {self.exchange_type}"


@dataclass
class ConnectionSettings:
    """ Класс настроек подключения. """
    connection_parameters: ConnectionParameters = None  # type: ignore
    connection_uri: InitVar[str] = None
    timeout: int = 30
    reconnect_interval: int = 5
    fail_fast: str = "1"
    channel: ChannelSettings = field(default_factory=ChannelSettings)

    class Meta:
        """ Класс метаданных подключения. """
        load_only = additional = ("connection_uri",)

    def __post_init__(self, connection_uri: Optional[str] = None) -> None:
        if self.connection_parameters is None and connection_uri is not None:
            self.connection_parameters = ConnectionParameters.from_uri(connection_uri)

        if connection_uri is None and self.connection_parameters is None:
            raise ValueError("Не задан connection_uri или connection_parameters")


@dataclass
class RabbitConfig(ABC):
    """ Базовый класс конфигурации кролика для сервисов. """
    connection_settings: ConnectionSettings
    exchange: ExchangeConfig


@dataclass
class QueueRoute:
    """ Класс настроек роутинга очередей. """
    name: str
    queue_name: str
    requeue: bool = True
    reject_on_redelivered: bool = True
    topics: List[str] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    bind_arguments: Dict[str, Any] = field(default_factory=dict)
    dlq_create: bool = False
    priority: bool = False

    def __post_init__(self) -> None:
        if self.features.get("x-max-priority"):
            self.features.update({"x-max-priority": PriorityLevels.HIGH.value})
            logger.warning("Для использования приоретизации воспользуйтесь флагом \"priority\"")
            return

        if self.priority:
            self.features.update({"x-max-priority": PriorityLevels.HIGH.value})


@dataclass
class ConsumerConfig(RabbitConfig):
    """ Класс конфигурации консьюмеров. """
    route: QueueRoute
    prefetch_count: int = 0


@dataclass
class PublisherConfig(RabbitConfig):
    """ Класс конфигурации паблишеров сообщений. """
    routing_key: str


__all__ = [
    "ConnectionParameters",
    "ExchangeBinding",
    "ExchangeTypes",
    "ChannelSettings",
    "ExchangeConfig",
    "ConnectionSettings",
    "RabbitConfig",
    "QueueRoute",
    "ConsumerConfig",
    "PublisherConfig",
    "PriorityLevels",
]
