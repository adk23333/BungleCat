import json as sys_json
from typing import Any, Optional

from aiotieba import Client
from sanic import Blueprint, Request, Websocket
from sanic_ext.extensions.openapi import openapi

from exceptions import InvalidParameter, AioTiebaException
from route.model import Result
from utils import get_unhidden_methods, inject_bot, CustomErrorHandler

index = Blueprint("index")
aiotieba_bp = Blueprint("aiotieba", url_prefix="/aiotieba")
group = Blueprint.group(
    index,
    aiotieba_bp,
)


async def call_aiotieba(
        _name: str,
        bot: Client,
        _args=(),
        _kwargs: Optional[dict[str, Any]] = None
):
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


funcs = get_unhidden_methods(Client)
funcs.pop("init_websocket")
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


async def _get_server_status(request: Request):
    status = request.app.m.workers
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


@inject_bot()
async def websocket_call(request: Request, ws: Websocket, bot: Client):
    async for msg in ws:
        try:
            data: dict = sys_json.loads(msg)
            action = data.get("action", "").split(".")
            if action[0] == "get_server_status":
                result = await _get_server_status(request)

            elif action[0] == "aiotieba":
                if action[1] in funcs.keys():
                    result = await call_aiotieba(
                        action[1], bot, data.get("args", ()), data.get("kwargs", {})
                    )
                else:
                    result = Result(status="failed", msg=f"unknown action {action}")

            else:
                result = Result(status="failed", msg=f"unknown action {action}")
        except Exception as e:
            handler = CustomErrorHandler()
            result = handler._default(request, e)
        await ws.send(result.to_ws())


index.add_websocket_route(
    websocket_call,
    "/ws",
)
