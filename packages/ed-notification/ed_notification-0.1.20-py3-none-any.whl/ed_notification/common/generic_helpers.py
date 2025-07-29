import os
from uuid import UUID, uuid4

from dotenv import load_dotenv

from ed_notification.common.typing.config import Config


def get_new_id() -> UUID:
    return uuid4()


def get_config() -> Config:
    load_dotenv()

    return {
        "resend": {
            "api_key": _get_env_variable("RESEND_API_KEY"),
            "from_email": _get_env_variable("RESEND_FROM_EMAIL"),
        },
        "db": {
            "db": _get_env_variable("POSTGRES_DB"),
            "user": _get_env_variable("POSTGRES_USER"),
            "password": _get_env_variable("POSTGRES_PASSWORD"),
            "host": _get_env_variable("POSTGRES_HOST"),
        },
        "infobig_key": _get_env_variable("INFOBIG_KEY"),
        "rabbitmq": {
            "url": _get_env_variable("RABBITMQ_URL"),
            "queue": _get_env_variable("RABBITMQ_QUEUE"),
        },
        "default_email_destination": _get_env_variable("DEFAULT_EMAIL_DESTINATION"),
    }


def _get_env_variable(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Environment variable '{name}' is not set.")

    if not isinstance(value, str):
        raise TypeError(f"Environment variable '{name}' must be a string.")

    value = value.strip()
    if not value:
        raise ValueError(f"Environment variable '{name}' cannot be empty.")

    return value
