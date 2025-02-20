import json as sys_json
from asyncio import Task
from enum import StrEnum, auto
from types import SimpleNamespace
from typing import Any, List, Literal, Optional, Set, Union

from aiohttp import ClientSession, ClientWebSocketResponse
from aiotieba import Client
from pydantic import BaseModel
from sanic import Config as SanicConfig
from sanic import Request as SanicRequest
from sanic import Sanic, SanicException, Websocket, json
from sanic.log import error_logger

from exceptions import AioTiebaException


class ApiType(StrEnum):
    WS = auto()
    HTTP = auto()
    REVERSE_WS = "reverse-ws"
    HTTP_CALLBACK = "http-callback"


class Config(BaseModel):
    bduss: str = ""
    token: str = ""
    fnames: List[str] = []
    http_callback_url: Optional[List[str]] = None
    reverse_ws_url: Optional[List[str]] = None


class EnvConfig(SanicConfig):
    HOST: str
    PORT: int
    WORKERS: int
    DEV: bool
    API_TYPE: Set[ApiType]
    DB_URL: str


class Context:
    config: Config = Config()
    bot: Optional[Client] = None
    bot_id: int = 0
    bot_uid: int = 0
    bot_show_name: str = ""
    tasks: list[Task] = []
    ws_connections: list[Union[Websocket, ClientWebSocketResponse]] = []
    http_session: Optional[ClientSession] = None


App = Sanic[EnvConfig, Context]


class Request(SanicRequest[App, SimpleNamespace]):
    app: App

class Result(BaseModel):
    status: Literal["ok", "failed"] = "ok"
    code: int = 200
    retcode: int = 0
    msg: Optional[str] = None
    description: Optional[str] = None
    data: Any = None

    def to_http(self):
        result = self.model_dump(exclude={"code"}, exclude_none=True)
        return json(sys_json.dumps(result), self.code)

    def to_ws(self):
        result = self.model_dump(exclude={"code"}, exclude_none=True)
        return sys_json.dumps(result)
    
    @classmethod
    def from_exception(cls, app: App, url: str, exception: Exception):
        quiet = getattr(exception, "quiet", False)
        noisy = getattr(app.config, "NOISY_EXCEPTIONS", False)
        if quiet is False or noisy is True:
            error_logger.exception(
                "Exception occurred while handling uri: %s", url
            )

        if isinstance(exception, SanicException):
            result = cls(
                status="failed",
                code=exception.status_code,
                retcode=exception.status_code,
                msg=exception.__class__.__name__,
                description=exception.message,
            )
        elif isinstance(exception, AioTiebaException):
            result = cls(
                status="failed",
                code=exception.status_code,
                retcode=exception.retcode,
                msg=exception.__class__.__name__,
                description=exception.message,
            )
        else:
            result = cls(
                status="failed",
                code=500,
                retcode=500,
                msg=exception.__class__.__name__,
                description=str(exception),
            )
        return result
