from nonebot import get_driver, get_plugin_config, require, logger
from pydantic import BaseModel


class Config(BaseModel):
    pass


# 配置加载
plugin_config: Config = get_plugin_config(Config)
global_config = get_driver().config
SUPERUSER: set[str] = get_driver().config.superusers


require("nonebot_plugin_localstore")
# pylint: disable=wrong-import-position
import nonebot_plugin_localstore as store  # noqa: E402

DATA_DIR = store.get_plugin_data_dir()
CACHE_DIR = store.get_plugin_cache_dir()

logger.info(f"data folder ->  {DATA_DIR}")
