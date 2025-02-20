from asyncio import Task

from aiohttp import ClientSession
from sanic.log import logger

from custom_type import App
from route import _websocket_call


async def create_http_session(app: App):
    app.ctx.http_session = ClientSession(loop=app.loop)
    for url in app.ctx.config.http_callback_url:
        logger.info("loaded http callback url: %s", url)


async def close_http_session(app: App):
    if app.ctx.http_session:
        await app.ctx.http_session.close()


async def create_reverse_ws_connections(app: App):
    tasks: list[Task] = []
    for url in app.ctx.config.reverse_ws_url or ():
        ws = await app.ctx.http_session.ws_connect(url)

        task = app.add_task(_websocket_call(app, ws, app.ctx.bot, url))
        logger.info("reverse-ws %s was connected.", url)
        tasks.append(task)
    return tasks
