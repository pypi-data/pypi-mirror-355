import os
import uuid

from dotenv import load_dotenv

from ed_webhook.common.typing.config import Config


def get_new_id() -> uuid.UUID:
    return uuid.uuid4()


def get_config() -> Config:
    load_dotenv()

    return {
        "db": {
            "db": _get_env_variable("POSTGRES_DB"),
            "user": _get_env_variable("POSTGRES_USER"),
            "password": _get_env_variable("POSTGRES_PASSWORD"),
            "host": _get_env_variable("POSTGRES_HOST"),
        }
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
