from types import SimpleNamespace
from typing import Type, Literal

from aiotieba import Client
from pydantic import BaseModel, ConfigDict
from sanic import Sanic, Config, Request as SanicRequest


class BotInfo(BaseModel):
    bduss: str
    token: str = ""


class BotConfig(BaseModel):
    bots: dict[str, BotInfo]


class EnvConfig(BaseModel):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 1
    DEV: bool = False


class Context(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: BotConfig
    bots: dict[str, Client]


App: Type[Sanic[Config, Context]] = Sanic[Config, Context]


class Request(SanicRequest[App, SimpleNamespace]):
    app: App
