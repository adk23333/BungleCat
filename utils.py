import inspect
from dataclasses import asdict, is_dataclass
from datetime import datetime
from functools import wraps
from json import JSONEncoder

import yarl
from aiohttp import ClientWebSocketResponse
from aiotieba import Client
from aiotieba.exception import TiebaValueError
from pydantic import BaseModel
from sanic import HTTPResponse, Unauthorized, Websocket
from sanic.handlers import ErrorHandler

from custom_type import App, Request
from log import logger
from route import Result


async def init_tieba_client(app: App):
    app.ctx.bot = await Client(app.ctx.config.bduss).__aenter__()
    user = await app.ctx.bot.get_self_info()
    app.ctx.bot_id = user.user_id
    app.ctx.bot_show_name = user.show_name
    app.ctx.bot_uid = user.tieba_uid
    if user:
        logger.info("Bot %s was loaded", app.ctx.bot_show_name)
    else:
        logger.warning(
            "Bot %s was broken, Some operations may not be performed.",
            app.ctx.bot_show_name,
        )


async def close_tieba_client(app: App):
    await app.ctx.bot.__aexit__()
    logger.info("Bot %s was closed.", app.ctx.bot_show_name)


def inject_bot():
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.headers.get("Authorization", "")
            if request.app.ctx.config.token == token:
                return await func(request, *args, request.app.ctx.bot, **kwargs)
            else:
                raise Unauthorized("The token is invalid.")

        return wrapper

    return decorator


def get_aiotieba_methods(cls: object):
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)
    non_hidden_methods = {
        name: method for name, method in methods if not name.startswith("_")
    }
    non_hidden_methods.pop("init_websocket")
    return non_hidden_methods


class CustomErrorHandler(ErrorHandler):
    def _default(self, request: Request, exception: Exception):
        return Result.from_exception(request.app, request.url, exception)

    def default(self, request: Request, exception: Exception) -> HTTPResponse:
        result = self._default(request, exception)
        return result.to_http()


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return int(obj.timestamp() * 1000)  # 转换为 13 位时间戳
        elif is_dataclass(obj):
            return asdict(obj)
            # return self.remove_null(asdict(obj))
        # elif isinstance(obj, dict):
        #     return self.remove_null(obj)
        elif isinstance(obj, (TiebaValueError, yarl.URL)):
            return str(obj)
        elif isinstance(obj, BaseModel):
            return obj.model_dump()

        else:
            return super().default(obj)

    @staticmethod
    def remove_null(obj):
        return {k: v for k, v in obj.items() if v is not None}


async def union_ws_send(ws: Websocket | ClientWebSocketResponse, data: str):
    if isinstance(ws, ClientWebSocketResponse):
        ws_send_func = ws.send_str
    elif isinstance(ws, Websocket):
        ws_send_func = ws.send

    return await ws_send_func(data)
