from typing import cast, Protocol
from dynaconf import Dynaconf, Validator
from justserver.logging import logger


class Settings(Protocol):
    current_env: str
    max_instances: int
    justniffer_cmd: str
    api_key: str | None
    ENVVAR_PREFIX_FOR_DYNACONF: str
    def to_dict(self) -> dict: ...


MAX_INSTANCES_ATTR = 'max_instances'
API_KEY_ATTR = 'api_key'

MASKED_VALUES = [API_KEY_ATTR]

settings: Settings = cast(Settings, Dynaconf(
    envvar_prefix='JUSTSERVER',
    validators=[
        Validator(MAX_INSTANCES_ATTR, default=10, cast=int),
        Validator('justniffer_cmd', default='nsenter --net=/host/proc/1/ns/net -- justniffer', cast=str),
        Validator(API_KEY_ATTR,  default=None, cast=str),

    ]

))


def log_settings(settings: Settings) -> None:
    for key, value in settings.to_dict().items():
        if key.lower() in MASKED_VALUES:
            value = '***'
        full_key = get_setting_env_name(settings, key)
        logger.info(f'{full_key}={value}')


def get_setting_env_name(settings: Settings, key: str) -> str:
    return f'{settings.ENVVAR_PREFIX_FOR_DYNACONF}_{key.upper()}'


def __init__() -> None:
    log_settings(settings)


__init__()
