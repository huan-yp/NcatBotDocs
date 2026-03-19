"""
bilibili/03_private_message — Bilibili 私信操作

演示功能:
  - registrar.bilibili.on_private_message(): 私信事件处理
  - self.api.bilibili.send_private_msg(): 发送文字私信
  - self.api.bilibili.send_private_image(): 发送图片私信
  - self.api.bilibili.get_session_history(): 获取私信历史

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
向 Bot 发送私信即可触发自动回复。

参考文档: docs/guide/api_usage/bilibili/2_private_msg.md
"""

from ncatbot.core import registrar
from ncatbot.event.bilibili import BiliPrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("BiliPrivateMessage")


class BiliPrivateMessagePlugin(NcatBotPlugin):
    name = "private_message_bilibili"
    version = "1.0.0"
    author = "NcatBot"
    description = "Bilibili 私信操作"

    async def on_load(self):
        self.data.setdefault("reply_count", 0)
        LOG.info("BiliPrivateMessage 插件已加载")

    @registrar.bilibili.on_private_message()
    async def on_private_msg(self, event: BiliPrivateMessageEvent):
        """收到私信 → 自动回复 + 查询历史"""
        text = event.data.message.text if hasattr(event.data, "message") else ""
        LOG.info("[私信] 用户=%s: %s", event.user_id, text)

        # 自动回复
        await self.api.bilibili.send_private_msg(
            user_id=event.user_id,
            content=f"收到你的消息：「{text}」\n这是自动回复 🤖",
        )
        self.data["reply_count"] = self.data.get("reply_count", 0) + 1

        # 查看历史记录
        history = await self.api.bilibili.get_session_history(
            user_id=event.user_id, count=5
        )
        LOG.info(
            "[私信] 最近 %d 条历史记录已获取 (用户=%s)",
            len(history) if history else 0,
            event.user_id,
        )
