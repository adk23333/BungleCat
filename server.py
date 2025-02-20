from asyncio import AbstractEventLoop

from tortoise.contrib.sanic import register_tortoise

from config import load_config, load_env_config
from custom_type import ApiType, App, Context
from http_client import (
    close_http_session,
    create_http_session,
    create_reverse_ws_connections,
)
from log import logger
from reviewer import create_reviewers
from route import group
from utils import CustomErrorHandler, close_tieba_client, init_tieba_client

env_config = load_env_config("BC_")

app = App(
    "BungleCat",
    ctx=Context,
    config=env_config,
    error_handler=CustomErrorHandler(),
)
register_tortoise(
    app,
    db_url=env_config.DB_URL,
    modules={"models": ["models"]},
    generate_schemas=True,
)
app.blueprint(group)


@app.before_server_start
async def before_server_start(_app: App, loop: AbstractEventLoop):
    _app.ctx.config = load_config()
    logger.info("Server config loaded.")

    await init_tieba_client(_app)

    if (
        ApiType.HTTP_CALLBACK in _app.config.API_TYPE
        or ApiType.REVERSE_WS in _app.config.API_TYPE
    ):
        await create_http_session(_app)

    if ApiType.REVERSE_WS in _app.config.API_TYPE:
        ws_tasks = await create_reverse_ws_connections(_app)
        _app.ctx.tasks.extend(ws_tasks)

    if (
        ApiType.HTTP_CALLBACK in _app.config.API_TYPE
        or ApiType.REVERSE_WS in _app.config.API_TYPE
        or ApiType.WS in _app.config.API_TYPE
    ):
        review_task = create_reviewers(_app)
        _app.ctx.tasks.append(review_task)


@app.before_server_stop
async def before_server_stop(_app: App, loop):
    await close_tieba_client(_app)
    await close_http_session(_app)


if __name__ == "__main__":
    app.run(
        host=app.config.HOST,
        port=app.config.PORT,
        dev=app.config.DEV,
        workers=app.config.WORKERS,
    )
