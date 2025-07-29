""" Модуль конфигурации библиотеки работы с очередями. """

import os
from pathlib import Path
from typing import Any, Dict, Optional

from pyhocon import ConfigFactory


def config_factory(folder: str, section: Optional[str] = None) -> Dict[str, Any]:
    """
        Метод-фабрика конфигурации.

        Arguments:
            - folder: Папка, из которой читаем конфигурацию;
            - section: Секция файла конфигурации, которую читаем.

        Returning:
            Сформированная конфигурация.
    """
    package_dir = Path(folder)
    env = os.getenv("ENV", "default")
    conf_path = package_dir / f"{env}.conf"
    fallback_conf_path = package_dir / "default.conf"
    factory = ConfigFactory.parse_file(conf_path)
    factory = factory.with_fallback(fallback_conf_path)
    return factory.get_config(section or "config")


__all__ = [
    "config_factory",
]
