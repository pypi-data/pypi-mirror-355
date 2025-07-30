<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-sunset-reminder ✨

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/HTony03/nonebot-plugin-sunset-reminder.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-sunset-reminder">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-sunset-reminder.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=social" alt="python">
<a href="https://wakatime.com/badge/github/HTony03/nonebot-plugin-sunset-reminder"><img src="https://wakatime.com/badge/github/HTony03/nonebot-plugin-sunset-reminder.svg?style=social" alt="wakatime"></a>
</div>

> [!IMPORTANT]
> **收藏项目** ～⭐️

<img width="100%" src="https://starify.komoridevs.icu/api/starify?owner=HTony03&repo=nonebot-plugin-sunset-reminder" alt="starify" />

## 📖 介绍

本插件用于自动提醒日出日落火烧云信息，支持添加、移除提醒，查询最近的火烧云图片。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-sunset-reminder --upgrade

使用 **pypi** 源安装

    nb plugin install nonebot-plugin-sunset-reminder --upgrade -i "https://pypi.org/simple"

使用**清华源**安装

    nb plugin install nonebot-plugin-sunset-reminder --upgrade -i "https://pypi.tuna.tsinghua.edu.cn/simple"

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details open>
<summary>uv</summary>

    uv add nonebot-plugin-sunset-reminder

安装仓库 master 分支

    uv add git+https://github.com/HTony03/nonebot-plugin-sunset-reminder@master

</details>

<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-sunset-reminder

安装仓库 master 分支

    pdm add git+https://github.com/HTony03/nonebot-plugin-sunset-reminder@master

</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-sunset-reminder

安装仓库 master 分支

    poetry add git+https://github.com/HTony03/nonebot-plugin-sunset-reminder@master

</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_sunset_reminder"]

</details>

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的必填配置

**暂无**

## 🎉 使用

### 指令表

|                 指令                 |   权限    | 需要@ |  范围   |      说明       |
|:----------------------------------:|:-------:|:---:|:-----:|:-------------:|
|           /add 或 添加火烧云提醒           | 群管理员/私聊 |  否  | 群聊/私聊 |   添加火烧云自动提醒   |
|         /remove 或 移除火烧云提醒          | 群管理员/私聊 |  否  | 群聊/私聊 |   移除火烧云自动提醒   |
| /latest_sunset_remind 或 最近日落火烧云提醒  |  群员/私聊  |  否  | 群聊/私聊 | 获取最近一次日落火烧云图片 |
| /latest_sunrise_remind 或 最近日出火烧云提醒 |  群员/私聊  |  否  | 群聊/私聊 | 获取最近一次日出火烧云图片 |
|          /search 或 火烧云查询           |  群员/私聊  |  否  | 群聊/私聊 |  查询指定城市火烧云信息  |

#### *search指令详细介绍*

| 参数         | 说明          | 接受的值                            | 示例      |
|:-----------|:------------|:--------------------------------|:--------|
| -c, --city | 城市名称        | str                             | 北京      |
| -d, --day  | 查询的时间，默认为今天 | 'today', 'tomorrow', '今天', '昨天' | today   |
| -t, --type | 查询类型，默认为日出  | 'sunrise', 'sunset', '日出', '日落' | sunrise |
| -h, --help | 帮助信息        | 无                               | 无       |
