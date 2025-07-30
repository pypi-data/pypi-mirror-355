from typing import Protocol, cast
from dynaconf import Dynaconf, Validator

class Settings(Protocol):
    ENVVAR_PREFIX_FOR_DYNACONF: str
    justniffer_proxy_endpoint: str
    justniffer_proxy_api_key: str
    check_interval: int
    def to_dict(self) -> dict: ...


settings: Settings = cast(Settings, Dynaconf(envvar_prefix='JUSTERNETES', 
                              validators=[
                                  Validator('justniffer_proxy_endpoint', required=True),
                                  Validator('justniffer_proxy_api_key', required=True),
                                  Validator('check_interval', default=60, cast=int)
                              ]))


