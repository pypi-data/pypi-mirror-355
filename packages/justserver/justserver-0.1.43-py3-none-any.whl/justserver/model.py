
from enum import Enum
from pydantic import BaseModel
from justserver.logging import logger

class Encoder(str, Enum):
    unprintable = 'unprintable'
    hex_encode = 'hex_encode'


class Justniffer(BaseModel):
    model_config = {'extra': 'forbid'}
    interface: str = 'any'
    in_the_middle: bool = True
    filter: str | None = None
    encode: Encoder | None = None
    log_format: str | None = None
    max_tcp_streams: int | None = None
    truncated: bool = False
    newline: bool = False
    uuid: str | None = None

    def __compare__(self, other: 'Justniffer') -> bool:
        logger.info(f'comparing {self} with {other}')
        dict1 = self.model_dump()
        dict2 = other.model_dump()
        to_exclude = 'uuid'
        dict1.pop(to_exclude)
        dict2.pop(to_exclude)
        return dict1 == dict2
    



class BaseResponse(BaseModel):
    message: str


class StartResponse(BaseResponse):
    uuid: str


class StopResponse(BaseResponse):
    message: str


class StopAllResponse(BaseResponse):
    message: str


class JustnifferProcess(BaseModel):
    pid: int
    uuid: str
    justniffer_spec: Justniffer


FuturesDict = dict[str, JustnifferProcess]


class ListResponse(BaseResponse):
    processes: FuturesDict
