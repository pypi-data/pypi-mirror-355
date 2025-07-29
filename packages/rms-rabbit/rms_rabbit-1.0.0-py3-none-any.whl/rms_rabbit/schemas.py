""" Модуль, реализующий схемы для библиотеки. """

import marshmallow
from marshmallow_dataclass import class_schema

from rms_rabbit.datatypes import ConnectionSettings, ConsumerConfig, PublisherConfig

connection_settings_schema: marshmallow.Schema = class_schema(ConnectionSettings)()
consumer_config_schema: marshmallow.Schema = class_schema(ConsumerConfig)()
publisher_config_schema: marshmallow.Schema = class_schema(PublisherConfig)()
