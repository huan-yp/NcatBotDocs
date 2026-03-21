"""
qq/01_hello_world — QQ 平台最小可运行插件

演示功能:
  - NcatBotPlugin 基类继承
  - manifest.toml 插件清单
  - on_load / on_close 生命周期
  - @registrar.qq.on_group_command() QQ 专用命令装饰器
  - event.reply() 回复消息
  - 命令参数自动绑定 vs 手动解析对比

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
群里发送 "hello" 即可收到回复。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import MessageArray
from ncatbot.utils import get_log

LOG = get_log("HelloWorld")


class HelloWorldPlugin(NcatBotPlugin):
    name = "hello_world_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 平台最小可运行插件"

    async def on_load(self):
        LOG.info("HelloWorld 插件已加载！")

    async def on_close(self):
        LOG.info("HelloWorld 插件已卸载。")

    @registrar.qq.on_group_command("hello", ignore_case=True)
    async def on_hello(self, event: GroupMessageEvent):
        """收到群消息 'hello' 时回复"""
        await self.api.qq.post_group_msg(event.group_id, text="Hello, World! 👋")

    @registrar.qq.on_group_command("hi", ignore_case=True)
    async def on_hi(self, event: GroupMessageEvent):
        """用 event.reply() 快速回复"""
        await event.reply(text="你好呀！这是通过 event.reply() 发送的快速回复 🎉")

    @registrar.qq.on_private_command("hello", ignore_case=True)
    async def on_private_hello(self, event: PrivateMessageEvent):
        """收到私聊消息 'hello' 时回复"""
        await event.reply(text="你好！这是来自 HelloWorld 插件的私聊回复 👋")

    # ---- echo: 自动参数绑定（推荐） ----
    # 实现含参数命令时，建议使用自动参数绑定，框架自动提取并转换参数，
    # 无需手动解析消息。上方 hello / hi 是无参数命令的示例。

    @registrar.qq.on_group_command("echo")
    async def on_echo(self, event: GroupMessageEvent, content: str):
        """'echo 你好' → content='你好'（自动参数绑定）
        'echo "hello world"' → content='hello world'（引号包裹视为整体）
        """
        await event.reply(f"🔊 {content}")

    # ---- echo-manual: 手动解析参数（不推荐） ----
    # 同样的功能也可以通过手动解析消息文本实现，但代码更繁琐，
    # 且不支持自动引号处理、类型转换、缺失提示等特性。

    @registrar.qq.on_group_command("echo-manual")
    async def on_echo_manual(self, event: GroupMessageEvent):
        """手动解析版本的 echo（不推荐，仅作对比）"""
        parts = event.raw_message.split(maxsplit=1)
        content = parts[1] if len(parts) > 1 else ""
        if not content:
            await event.reply("用法: echo-manual <内容>")
            return
        await event.reply(f"🔊 {content}")
