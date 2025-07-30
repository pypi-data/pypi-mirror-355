from nonebot import require, logger
from nonebot.plugin import PluginMetadata
from .config import Config
from .db_action import init_database
from .commands import sunset_reminder_command  # NOQA: F401
from .reminder import (notify, get_cloud_image,  # NOQA: F401
                       noon_job, night_job)  # NOQA: F401

require("nonebot_plugin_localstore")
require("nonebot_plugin_apscheduler")


__plugin_meta__ = PluginMetadata(
    name="nonebot_plugin_sunset_reminder",
    description="a plugin to inform flame cloud infos.",
    usage="a plugin to inform flame cloud infos.",
    type="application",  # library
    homepage="https://github.com/HTony03/nonebot-plugin-sunset-reminder",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={"author": "HTony03 <HTony03@foxmail.com>"},
)
VERSION = '0.1.0'
logger.info(f" initalizing {VERSION}.")

BASEURL = 'https://sunsetbot.top/static/media/map'

init_database()
