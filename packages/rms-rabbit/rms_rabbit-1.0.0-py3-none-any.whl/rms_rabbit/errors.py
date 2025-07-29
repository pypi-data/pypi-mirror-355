""" Модуль реализации ошибок для библиотеки. """

class ConsumerError(Exception):
    """ Класс ошибки при проблемах с консьюмером. """


class PublisherError(ConnectionError):
    """ Класс ошибки при проблемах с публикацие сообщения"""


__all__ = [
    "ConsumerError",
    "PublisherError",
]
