from typing import Any
from dynaconf import Dynaconf
from justserver.logging import logger



def log_settings(settings: Any, masked_values: list[str] | None = None) -> None:
    for key, value in settings.to_dict().items():
        if masked_values is not None and key.lower() in masked_values:
            value = '***'
        full_key = get_setting_env_name(settings, key)
        logger.info(f'{full_key}={value}')


def get_setting_env_name(settings: Dynaconf, key: str) -> str:
    return f'{settings.ENVVAR_PREFIX_FOR_DYNACONF}_{key.upper()}'


