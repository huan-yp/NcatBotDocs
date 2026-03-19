"""
common/01_hello_world — 跨平台最小可运行插件

演示功能:
  - NcatBotPlugin 基类继承
  - manifest.toml 插件清单
  - on_load / on_close 生命周期
  - @registrar.on_command() 跨平台命令装饰器
  - Replyable Trait 跨平台回复

本示例不依赖任何平台，可在 QQ / Bilibili / GitHub 上运行。
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event import Replyable
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("HelloWorld")


class HelloWorldPlugin(NcatBotPlugin):
    name = "hello_world_common"
    version = "1.0.0"
    author = "NcatBot"
    description = "跨平台最小可运行插件 — 纯 Trait 编程"

    async def on_load(self):
        LOG.info("HelloWorld 插件已加载！")

    async def on_close(self):
        LOG.info("HelloWorld 插件已卸载。")

    @registrar.on_command("hello", ignore_case=True)
    async def on_hello(self, event):
        """任何平台收到 'hello' 命令时回复（跨平台）"""
        if isinstance(event, Replyable):
            await event.reply(text="Hello, World! 👋")

    @registrar.on_command("hi", ignore_case=True)
    async def on_hi(self, event):
        """用 event.reply() 快速回复（跨平台）"""
        if isinstance(event, Replyable):
            await event.reply(text="你好呀！这是跨平台 hello world 🎉")
