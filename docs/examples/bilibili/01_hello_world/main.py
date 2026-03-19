"""
bilibili/01_hello_world — Bilibili 平台最小可运行插件

演示功能:
  - registrar.bilibili.on_danmu(): 弹幕消息处理
  - registrar.bilibili.on_private_message(): 私信消息处理
  - event.reply() 自动回复（弹幕回弹幕、私信回私信）

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
  在直播间发弹幕 "hello" → 收到弹幕回复
  发私信给 Bot          → 收到私信自动回复
"""

from ncatbot.core import registrar
from ncatbot.event.bilibili import DanmuMsgEvent, BiliPrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("BiliHelloWorld")


class BiliHelloWorldPlugin(NcatBotPlugin):
    name = "hello_world_bilibili"
    version = "1.0.0"
    author = "NcatBot"
    description = "Bilibili 平台最小可运行插件"

    async def on_load(self):
        LOG.info("Bilibili HelloWorld 插件已加载！")

    @registrar.bilibili.on_danmu()
    async def on_danmu_hello(self, event: DanmuMsgEvent):
        """收到弹幕时回复"""
        text = event.data.message.text if hasattr(event.data, "message") else ""
        if "hello" in text.lower():
            await event.reply("Hello! 欢迎来到直播间 👋")
            LOG.info("回复弹幕 hello: 房间=%s 用户=%s", event.group_id, event.user_id)

    @registrar.bilibili.on_private_message()
    async def on_pm_hello(self, event: BiliPrivateMessageEvent):
        """收到私信时自动回复"""
        await event.reply("你好！我是 Bot，收到了你的私信 📩")
        LOG.info("回复私信: 用户=%s", event.user_id)
