from typing import TypedDict


class DbConfig(TypedDict):
    user: str
    password: str
    db: str
    host: str


class RabbitMQConfig(TypedDict):
    url: str
    queue: str


class ResendConfig(TypedDict):
    api_key: str
    from_email: str


class Config(TypedDict):
    resend: ResendConfig
    infobig_key: str
    db: DbConfig
    rabbitmq: RabbitMQConfig
    default_email_destination: str


class TestMessage(TypedDict):
    title: str
