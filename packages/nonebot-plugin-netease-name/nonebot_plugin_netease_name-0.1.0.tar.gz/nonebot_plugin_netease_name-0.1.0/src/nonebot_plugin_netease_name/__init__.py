from nonebot.plugin import PluginMetadata, on_command, require

require("nonebot_plugin_localstore")
from .lib.main import get_random_nickname, init_random

__plugin_meta__ = PluginMetadata(
    name="网易版MC昵称生成器", # type: ignore
    description="使用词典生成随机昵称",
    usage="使用/name 或/网易昵称",
    type="application",
    homepage="https://github.com/LiteSuggarDEV/nonebot_plugin_netease_name",
)

init_random()

name = on_command("name", aliases={"网易昵称"}, priority=10)


@name.handle()
async def _():
    await name.finish("给你整了个名：" + get_random_nickname())
