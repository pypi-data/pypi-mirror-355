from enum import StrEnum
from typing import TypedDict


class Environment(StrEnum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    TEST = "test"


class RabbitMQConfig(TypedDict):
    url: str
    queues: dict[str, str]


class DbConfig(TypedDict):
    user: str
    password: str
    db: str
    host: str


class ApiConfig(TypedDict):
    auth: str
    notification: str
    optimization: str
    webhook: str


class Config(TypedDict):
    db: DbConfig
    api: ApiConfig
    rabbitmq: RabbitMQConfig
    environment: Environment
    hash_scheme: str
