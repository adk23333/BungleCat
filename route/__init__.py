import json as sys_json
from typing import Any, Optional

from aiohttp import WSMessage
from aiotieba import Client
from sanic import Blueprint, Websocket
from sanic.log import logger
from sanic_ext.extensions.openapi import openapi

from config import load_env_config
from custom_type import ApiType, App, Request, Result
from exceptions import AioTiebaException, InvalidParameter
from utils import get_aiotieba_methods, inject_bot, union_ws_send

env_config = load_env_config("BC_")
index = Blueprint("index")
aiotieba_bp = Blueprint("aiotieba", url_prefix="/aiotieba")
group = Blueprint.group(
    index,
    aiotieba_bp,
)


async def call_aiotieba(
    _name: str, bot: Client, _args=(), _kwargs: Optional[dict[str, Any]] = None
):
    bot.del_bawu()
    method = getattr(bot, _name)
    if _args or _kwargs:
        result = await method(*_args, **_kwargs)
    else:
        result = await method()
    if getattr(result, "err", None) is not None:
        if isinstance(result.err, TypeError):
            raise InvalidParameter(str(result.err))
        else:
            raise AioTiebaException(result.err)
    return Result(data=result.__dict__)


funcs = get_aiotieba_methods(Client)


if ApiType.HTTP in env_config.API_TYPE:
    for func_name, func in funcs.items():

        @openapi.description(func.__doc__)
        @inject_bot()
        async def http_call(request: Request, bot: Client):
            data: dict[str, Any] = request.json
            name = request.name.split(".")[2]
            result = await call_aiotieba(
                name, bot, *data.get("args", []), **data.get("kwargs", {})
            )
            return result.to_http()

        aiotieba_bp.add_route(
            http_call,
            f"/{func_name}",
            ["POST"],
            name=func_name,
            unquote=True,
        )


async def _websocket_call(app: App, ws: Websocket, bot: Client, url="unknown"):
    app.ctx.ws_connections.append(ws)
    try:
        async for msg in ws:
            try:
                if isinstance(msg, WSMessage):
                    msg = str(msg.data)

                logger.debug("Websocket receive: %s", msg)

                data: dict = sys_json.loads(msg)
                action = data.get("action", None)
                if action:
                    action = action.split(".")
                else:
                    raise InvalidParameter("JSON format error")
                if action[0] == "get_server_status":
                    result = await _get_server_status(app)

                elif action[0] == "aiotieba":
                    if action[1] in funcs.keys():
                        result = await call_aiotieba(
                            action[1], bot, data.get("args", ()), data.get("kwargs", {})
                        )
                    else:
                        result = Result(status="failed", msg=f"unknown action {action}")

                else:
                    result = Result(status="failed", msg=f"unknown action {action}")
            except sys_json.JSONDecodeError:
                result = Result(
                    status="failed",
                    retcode=500,
                    msg="invalid json",
                    description="msg must be json",
                )

            except Exception as e:
                result = Result.from_exception(app, url, e)

            data = result.to_ws()
            await union_ws_send(ws, data)
    except Exception as e:
        logger.debug(e)
    finally:
        await ws.close()

    app.ctx.ws_connections.remove(ws)


@inject_bot()
async def websocket_call(request: Request, ws: Websocket, bot: Client):
    await _websocket_call(request.app, ws, bot, request.url)


if ApiType.WS in env_config.API_TYPE:
    index.add_websocket_route(
        websocket_call,
        "/ws",
    )


async def _get_server_status(app: App):
    status = app.m.workers
    return Result(data=status)


async def get_server_status(request: Request):
    result = await _get_server_status(request)
    return result.to_http()


index.add_route(
    get_server_status,
    "get_server_status",
    ["POST"],
    name="status",
    unquote=True,
)
