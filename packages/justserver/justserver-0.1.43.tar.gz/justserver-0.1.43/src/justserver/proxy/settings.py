from typing import cast, Protocol
from dynaconf import Dynaconf, Validator
from justserver.settings_log import log_settings



class Settings(Protocol):
    pod_namespace: str
    backend_url: list[str] | None 
    ENVVAR_PREFIX_FOR_DYNACONF: str
    def to_dict(self) -> dict: ...

NAMESPACE_ENV = 'pod_namespace'
BACKEND_URLS_ENV = 'backend_url'


def _to_list(value: str | None) -> list[str] | None:
    if value is not None:
        return value.split('|')
    return None

settings: Settings = cast(Settings, Dynaconf(
    envvar_prefix='JUSTSERVER',
    validators=[
        Validator(NAMESPACE_ENV, default='default', cast=str),
        Validator(BACKEND_URLS_ENV, default=None, cast=_to_list),

    ]

))

def __init__() -> None:
    log_settings(settings)


__init__()
