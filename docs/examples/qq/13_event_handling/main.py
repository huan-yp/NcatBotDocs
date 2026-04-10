"""
qq/13_event_handling — QQ 事件处理示例

演示功能:
  - @registrar.on_command() 装饰器方式处理命令
  - 事件流后台消费（监听私聊）
  - wait_event 等待用户确认
"""

import asyncio

from ncatbot.core import registrar, from_event
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("EventHandlingQQ")


class EventHandlingPlugin(NcatBotPlugin):
    name = "event_handling_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 事件处理示例"

    async def on_load(self):
        LOG.info("EventHandling 插件已加载")
        self._listener_task = asyncio.create_task(self._listen_private())

    async def on_close(self):
        if hasattr(self, "_listener_task") and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        LOG.info("EventHandling 插件已卸载")

    async def _listen_private(self):
        """后台监听私聊消息并记录日志"""
        try:
            async with self.events("message.private") as stream:
                async for event in stream:
                    LOG.info("收到私聊消息: %s", event.data.raw_message)
        except asyncio.CancelledError:
            pass

    @registrar.on_command("ping")
    async def on_ping(self, event):
        """ping → pong"""
        await event.reply(text="pong 🏓")

    @registrar.on_command("状态")
    async def on_status(self, event):
        """查看插件状态"""
        await event.reply(text="✅ EventHandling 插件运行正常")

    @registrar.on_command("确认测试")
    async def on_confirm_test(self, event):
        """确认测试：要求用户在 15 秒内回复「确认」"""
        await event.reply(text="请在 15 秒内回复「确认」")
        try:
            reply_event = await self.wait_session_event(
                event, timeout=15.0
            )
            text = reply_event.data.raw_message.strip()
            if text == "确认":
                await event.reply(text="✅ 操作已确认！")
            else:
                await event.reply(text=f"❌ 收到非确认回复: {text}")
        except asyncio.TimeoutError:
            await event.reply(text="⏰ 确认超时，操作已取消")
