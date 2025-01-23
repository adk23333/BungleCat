import os
import tomllib
from pathlib import Path

import tomli_w
from dotenv import load_dotenv
from sanic import Config

from custom_type import BotConfig, EnvConfig


def load_env_config(env_prefix: str = "SANIC_"):
    load_dotenv(".env")
    env = os.environ.get("ENV", "prod")
    load_dotenv(f".env.{env}")
    config = Config()
    new_config = {k.removeprefix(env_prefix): v for k, v in os.environ.items() if k.startswith(env_prefix)}
    new_config = EnvConfig(**new_config)
    config.update_config(new_config.model_dump())
    return config


def get_bot_config():
    path = Path("config.toml")
    if not path.exists():
        with open(path, "wb") as fp:
            config = BotConfig(bots={})
            tomli_w.dump(config.model_dump(), fp)
    else:
        with open(path, "rb") as fp:
            config = tomllib.load(fp)
            config = BotConfig(**config)
    return config
