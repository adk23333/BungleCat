import inspect
from functools import wraps

from aiotieba import Client
from sanic import Unauthorized, NotFound, HTTPResponse, SanicException
from sanic.handlers import ErrorHandler

from custom_type import Request, App
from exceptions import AioTiebaException
from log import logger
from route import Result


async def init_tieba_client(app: App):
    bots: dict[str, Client] = {}
    bot_infos = app.ctx.config.bots.copy()
    for bot_id, bot_info in bot_infos.items():
        client = await Client(bot_info.bduss).__aenter__()
        user = await client.get_self_info()
        if user:
            bots[bot_id] = client
            logger.info("Bot %s was loaded", bot_id)
        else:
            app.ctx.config.bots.pop(bot_id)
            logger.warning("Bot %s was broken, will not load it", bot_id)
    bots["unsigned"] = await Client().__aenter__()
    return bots


async def close_tieba_client(app: App):
    for bot_id, client in app.ctx.bots.items():
        await client.__aexit__()
        logger.info("Bot %s was closed", bot_id)


def inject_bot():
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            token = request.headers.get("Authorization", "")
            bot_id = request.headers.get("X-Bot-Id")
            if not bot_id:
                client = request.app.ctx.bots.get("unsigned")
                return await func(request, *args, client, **kwargs)

            else:
                bot = request.app.ctx.config.bots.get(bot_id, None)
                if bot:
                    if bot.token == token:
                        client = request.app.ctx.bots.get(bot_id)
                        return await func(request, *args, client, **kwargs)
                    else:
                        raise Unauthorized("The token is invalid")
                else:
                    raise NotFound("The bot does not exist")

        return wrapper

    return decorator


# def json(body: Any, status: int = 200, headers: dict[str, str] | None = None, ):
#     return sanic_json(
#         body,
#         status=status,
#         headers=headers,
#         dumps=lambda x: sys_json.dumps(x, cls=CustomJSONEncoder)
#     )


def get_unhidden_methods(cls: object):
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)
    non_hidden_methods = {name: method for name, method in methods if not name.startswith('_')}
    return non_hidden_methods


class CustomErrorHandler(ErrorHandler):
    def _default(self, request: Request, exception: Exception):
        self.log(request, exception)
        if isinstance(exception, SanicException):
            result = Result(
                status="failed",
                code=exception.status_code,
                retcode=exception.status_code,
                msg=exception.__class__.__name__,
                description=exception.message
            )
        elif isinstance(exception, AioTiebaException):
            result = Result(
                status="failed",
                code=exception.status_code,
                retcode=exception.retcode,
                msg=exception.__class__.__name__,
                description=exception.message
            )
        else:
            result = Result(
                status="failed",
                code=500,
                retcode=500,
                msg=exception.__class__.__name__,
                description=str(exception)
            )
        return result

    def default(self, request: Request, exception: Exception) -> HTTPResponse:
        result = self._default(request, exception)
        return result.to_http()
