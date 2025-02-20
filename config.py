import os
from pathlib import Path

import tomli_w
import tomllib
from dotenv import load_dotenv

from custom_type import ApiType, Config, EnvConfig


def load_env_config(env_prefix: str = "SANIC_"):
    load_dotenv(".env")
    API_TYPE = os.environ.get(f"{env_prefix}API_TYPE", "http,ws").split(",")
    API_TYPE = {ApiType(api_type) for api_type in API_TYPE}
    new_config = {
        "HOST": os.environ.get(f"{env_prefix}HOST", "127.0.0.1"),
        "PORT": int(os.environ.get(f"{env_prefix}PORT", 8000)),
        "DEV": bool(os.environ.get(f"{env_prefix}DEV", True)),
        "WORKERS": int(os.environ.get(f"{env_prefix}WORKERS", 1)),
        "API_TYPE": API_TYPE,
        "DB_URL": os.environ.get(f"{env_prefix}DB_URL", "sqlite://db.sqlite3"),
    }
    config = EnvConfig()
    config.update_config(new_config)
    return config


def load_config():
    path = Path("config.toml")
    if not path.exists():
        with open(path, "wb") as fp:
            config = Config()
            tomli_w.dump(config.model_dump(), fp)
    else:
        with open(path, "rb") as fp:
            config = tomllib.load(fp)
            config = Config(**config)
    return config
