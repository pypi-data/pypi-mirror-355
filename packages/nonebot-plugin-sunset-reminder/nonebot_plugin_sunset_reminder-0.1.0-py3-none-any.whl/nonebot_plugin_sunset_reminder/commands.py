import datetime
import aiohttp
from nonebot import on_command, on_shell_command
from nonebot.exception import ParserExit
from nonebot.params import ShellCommandArgs
from nonebot.rule import Namespace, ArgumentParser
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, PrivateMessageEvent
from nonebot.adapters.onebot.v11.event import MessageEvent, GroupMessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER
from nonebot.adapters.onebot.v11.helpers import Cooldown
from .db_action import add_data, remove_data
from .reminder import get_cloud_image

parser = ArgumentParser(prog='火烧云查询')
parser.add_argument('-c', '--city', action='store', default='北京', type=str, help="查询的城市")
parser.add_argument("-d", "--day", action="store", choices=['today', 'tomorrow', '今天', '昨天'],
                    default='today', type=str, help="查询的时间，默认为今天")
parser.add_argument("-t", "--type", action="store", choices=['rise', 'set', '日落', '日出'],
                    default='rise', type=str, help="查询类型，默认为日出")

search = on_shell_command("search", aliases={'查询火烧云信息', '火烧云查询'}, parser=parser, block=True)


@on_command('latest_sunset_remind', aliases={"最近日落火烧云提醒"}, priority=5).handle(
    parameterless=[Cooldown(15, prompt="调用过快")])
async def sunset_reminder_command(bot: Bot, event: MessageEvent) -> None:
    """日落提醒命令"""
    img = await get_cloud_image("set", datetime.date.today())
    if not isinstance(img, str):
        await bot.send(event, "未找到日落火烧云图片。")
        return
    await bot.send(event, Message(MessageSegment.image(f'file:///{img}')))


@on_command("latest_sunrise_remind", aliases={"最近日出火烧云提醒"}, priority=5).handle(
    parameterless=[Cooldown(15, prompt="调用过快")])
async def sunrise_reminder_command(bot: Bot, event: MessageEvent) -> None:
    """日出提醒命令"""
    if datetime.datetime.now().hour < 8:
        img = await get_cloud_image("rise", datetime.date.today() - datetime.timedelta(days=-1))
    else:
        img = await get_cloud_image("rise", datetime.date.today())
    if not isinstance(img, str):
        await bot.send(event, "未找到日出火烧云图片。")
        return
    await bot.send(event, Message(MessageSegment.image(f'file:///{img}')))


@search.handle(parameterless=[Cooldown(15, prompt="调用过快")])
async def handle_function(args: Namespace = ShellCommandArgs()):
    """处理搜索命令"""
    if not args.city:
        await search.finish("请输入要查询的城市。")

    day = args.day
    type_ = args.type
    event_type = "set" if type_ in ("set", "日落") else "rise"
    day_num = 1 if day in ("today", "今天") else 2
    type_str = f"{event_type}_{day_num}"

    async with aiohttp.ClientSession() as session:
        async with session.get(
                f"https://sunsetbot.top/?intend=select_city&query_city={args.city}"
                f"&event_date=None&event={type_str}&times=None") as response:
            if response.status != 200:
                await search.finish("查询失败，请稍后再试。")
            data = await response.json()
            if not data:
                await search.finish("未找到相关结果。")

    # 这里可以添加实际的查询逻辑
    out = ''
    out += data.get('img_summary', '未找到城市信息。').replace('&ensp;<b>', '').replace('</b>', '') + '\n'
    out += f"鲜艳度: {data.get('tb_aod', '无数据').replace('<br>', '')}\n"
    out += f"火烧云质量: {data.get('tb_quality', '无数据').replace('<br>', '')}\n"
    await search.finish(f"查询结果: \n{out} ")


@search.handle(parameterless=[Cooldown(15, prompt="调用过快")])
async def handle_function_exit(args: ParserExit = ShellCommandArgs()):
    await search.finish(args.message)


@on_command("add", aliases={"添加火烧云提醒"}, permission=GROUP_ADMIN | GROUP_OWNER, priority=5).handle()
async def sunset_reminder_add_group(
        bot: Bot, event: GroupMessageEvent
) -> None:
    add_data(event.group_id, 'group', True)
    await bot.send(event, "已添加火烧云提醒。")


@on_command("add", aliases={"添加火烧云提醒"}, priority=5).handle()
async def sunset_reminder_add(
        bot: Bot, event: PrivateMessageEvent
) -> None:
    """添加火烧云提醒命令"""
    add_data(event.user_id, 'private', True)
    await bot.send(event, "已添加火烧云提醒。")


@on_command("remove", aliases={"移除火烧云提醒"}, permission=GROUP_ADMIN | GROUP_OWNER, priority=5).handle()
async def sunset_reminder_del_group(
        bot: Bot, event: GroupMessageEvent
) -> None:
    remove_data(event.group_id, 'group')
    await bot.send(event, "已移除火烧云提醒。")


@on_command("remove", aliases={"移除火烧云提醒"}, priority=5).handle()
async def sunset_reminder_del(
        bot: Bot, event: PrivateMessageEvent
) -> None:
    remove_data(event.user_id, 'private')
    await bot.send(event, "已移除火烧云提醒。")
