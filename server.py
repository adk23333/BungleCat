from config import load_env_config, get_bot_config
from custom_type import Context, App
from log import logger
from route import group
from utils import init_tieba_client, close_tieba_client, CustomErrorHandler

app = App(
    "BungleCat",
    ctx=Context,
    config=load_env_config("OTB_"),
    error_handler=CustomErrorHandler(),
)
app.blueprint(group)


@app.before_server_start
async def before_server_start(_app: App, loop):
    _app.ctx.config = get_bot_config()
    logger.info("Bot config loaded")

    bots = await init_tieba_client(_app)
    _app.ctx.bots = bots
    logger.info("Tieba clients init")


@app.before_server_stop
async def before_server_stop(_app: App, loop):
    await close_tieba_client(_app)
    logger.info("Tieba clients closed")


if __name__ == "__main__":
    app.run(host=app.config.HOST, port=app.config.PORT, dev=app.config.DEV, workers=app.config.WORKERS)
