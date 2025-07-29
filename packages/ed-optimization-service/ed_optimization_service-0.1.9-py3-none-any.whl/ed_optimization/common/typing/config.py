from typing import TypedDict


class DbConfig(TypedDict):
    user: str
    password: str
    db: str
    host: str


class RabbitMQConfig(TypedDict):
    url: str
    queue: str


class Config(TypedDict):
    db: DbConfig
    rabbitmq: RabbitMQConfig
    core_api: str
    google_maps_api: str


class TestMessage(TypedDict):
    title: str
