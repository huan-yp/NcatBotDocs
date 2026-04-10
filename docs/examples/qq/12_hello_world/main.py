"""
qq/12_hello_world — QQ 平台 Hello World

演示功能:
  - NcatBotPlugin 基类继承
  - @registrar.on_command() 命令装饰器
  - event.reply() 回复消息
"""

from ncatbot.core import registrar
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("HelloWorldQQ")


class HelloWorldQQPlugin(NcatBotPlugin):
    name = "hello_world_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 平台 Hello World 示例"

    async def on_load(self):
        LOG.info("HelloWorldQQ 插件已加载！")

    async def on_close(self):
        LOG.info("HelloWorldQQ 插件已卸载。")

    @registrar.on_command("hello", ignore_case=True)
    async def on_hello(self, event):
        """收到 'hello' 回复"""
        await event.reply(text="Hello, World! 👋")

    @registrar.on_command("hi", ignore_case=True)
    async def on_hi(self, event):
        """收到 'hi' 回复"""
        await event.reply(text="你好呀！🎉")
