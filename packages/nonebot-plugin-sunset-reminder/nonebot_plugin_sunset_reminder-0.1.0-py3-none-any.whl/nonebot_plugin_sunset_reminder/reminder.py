import datetime
import aiohttp
from nonebot import require, logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot import get_bot

require('nonebot_plugin_apscheduler')
# pylint: disable=wrong-import-position
from nonebot_plugin_apscheduler import scheduler  # NOQA: E402

from .db_action import load_data
from .config import CACHE_DIR, SUPERUSER
from .data import set_data


async def notify(id_: int, type_: str, message: Message) -> None:
    try:
        bot = get_bot()
    # pylint: disable=broad-exception-caught
    except Exception as exc:
        raise RuntimeError("No bot available to send messages.") from exc
    if type_ == 'private':
        await bot.send_private_msg(user_id=id_, message=message)
    elif type_ == 'group':
        await bot.send_group_msg(group_id=id_, message=message)


async def get_cloud_image(type_: str, date: datetime.date) -> str | None:
    """Get image."""
    from . import BASEURL
    async with aiohttp.ClientSession() as session:
        if type_ == 'rise':
            nextdate: str = (date + datetime.timedelta(days=1)).strftime("%Y%m%d")
        elif type_ == 'set':
            nextdate: str = date.strftime("%Y%m%d")
        else:
            raise ValueError("Invalid type. Use 'rise' or 'set'.")

        for j in [0, -1]:
            for i in range(24, -1, -1):
                dates = (date + datetime.timedelta(days=j)).strftime("%Y%m%d")
                url = f'{BASEURL}/%E4%B8%AD%E4%B8%9C_{nextdate}_{type_}_{dates}{i:02d}z.jpg'
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    logger.info(f"Image found at {dates}{i:02d}z.jpg")
                    with open(f'{CACHE_DIR}/{nextdate}_{type_}.jpg', 'wb') as f:
                        f.write(await resp.read())
                    return f'{CACHE_DIR}/{nextdate}_{type_}.jpg'
        logger.warning(f'date {nextdate} {type_} image not found.')
        return None


@scheduler.scheduled_job('cron', hour=12, minute=0)
async def noon_job() -> None:
    data = load_data()
    set_data('remind_dict', data)
    current_date = datetime.date.today()

    image = await get_cloud_image('set', current_date)
    if not isinstance(image, str):
        logger.error(f"Failed to get image for {current_date}.")
        for id_ in SUPERUSER:
            try:
                await notify(int(id_), 'private',
                             Message(f"Failed to get image for {current_date}."))
            except RuntimeError as e:
                logger.opt(exception=True).error(
                    f"Failed to notify superuser {id_}: {e}")
        return

    for d in data:
        for (id_, type_), activate in d.items():
            if activate:
                try:
                    await notify(id_, type_,
                                 Message(MessageSegment.image(f'file:///{image}')))
                except RuntimeError as e:
                    logger.opt(exception=True).error(
                        f"Failed to send reminder to {type_} {id_}: {e}")
                    return


@scheduler.scheduled_job('cron', hour=19, minute=0)
async def night_job() -> None:
    data = load_data()
    set_data('remind_dict', data)
    current_date = datetime.date.today()

    image = await get_cloud_image('rise', current_date)
    if not isinstance(image, str):
        logger.error(f"Failed to get image for {current_date}.")
        for id_ in SUPERUSER:
            try:
                await notify(int(id_), 'private',
                             Message(f"Failed to get image for {current_date}."))
            except RuntimeError as e:
                logger.opt(exception=True).error(
                    f"Failed to notify superuser {id_}: {e}")
        return

    for d in data:
        for (id_, type_), activate in d.items():
            if activate:
                try:
                    await notify(id_, type_,
                                 Message(MessageSegment.image(f'file:///{image}')))
                except RuntimeError as e:
                    logger.opt(exception=True).error(
                        f"Failed to send reminder to {type_} {id_}: {e}")
                    return
