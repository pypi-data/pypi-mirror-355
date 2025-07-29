""" Модуль приложения библиотеки работы с очередиями. """

import logging
from dataclasses import dataclass
from typing import List

from rms_rabbit.consumer import Consumer
from rms_rabbit.base_handler import GenericRmsRabbitHandler
from rms_rabbit.datatypes import QueueRoute

logger = logging.getLogger(__name__)


@dataclass
class QueueConfig:
    """ Класс конфигурации очереди. """
    name: str
    handler: GenericRmsRabbitHandler
    route: QueueRoute


class RmsRabbitApplication:
    """
    Абстракция чтобы обобщить все консьюмеры в одном месте, чтобы разрулить кто что разгребает
    """

    def __init__(self, queues: List[QueueConfig], consumer: Consumer) -> None:
        self.queues = queues
        self.consumer = consumer
        self.consumers: List[GenericRmsRabbitHandler] = []

    async def start(self, consuming: bool = True) -> None:
        """
            Метод запуска приложения.
            Создаем подключение и запускаем консумеров, если задан флаг.

            Arguments:
                - consuming: Флаг, определяющий требование прослушивания.
        """
        await self.consumer.connect()
        if consuming:
            await self.start_consumers()

    async def start_consumers(self) -> None:
        """ Метод запуска консьюмеров. """
        for queue in self.queues:
            if queue.name == queue.route.name:
                consumer = await self.start_consumer(queue)
                self.consumers.append(consumer)

    async def start_consumer(self, queue: QueueConfig) -> GenericRmsRabbitHandler:
        """
            Метод запуска одного консьюмера.

            Arguments:
                - queue: Конфигурация очереди для консьюмера.

            Returning:
                Обработчик очереди.
        """
        await self.consumer.consume_queue(queue.handler)
        return queue.handler

    async def stop(self) -> None:
        """ Метод остановки консьюмера и приложения. """
        await self.consumer.close()


__all__ = [
    "RmsRabbitApplication",
    "QueueConfig",
]
