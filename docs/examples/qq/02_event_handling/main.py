"""
qq/02_event_handling — QQ 事件处理三模式

演示功能:
  - 模式 A: @registrar.qq.on_group_command() 命令装饰器自动路由
  - 模式 B: self.events() 事件流连续消费
  - 模式 C: self.wait_event() 单次等待（多步确认）
  - Handler 优先级控制

使用方式:
  群里发 "ping"   → 装饰器模式回复 "pong"
  群里发 "确认测试" → 进入 wait_event 模式
"""

import asyncio

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("EventHandling")


class EventHandlingPlugin(NcatBotPlugin):
    name = "event_handling_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 事件处理三模式演示"

    async def on_load(self):
        LOG.info("EventHandling 插件已加载")
        self._stream_task = asyncio.create_task(self._stream_listener())

    async def on_close(self):
        if hasattr(self, "_stream_task"):
            self._stream_task.cancel()

    # ==================== 模式 A: 命令装饰器 ====================

    @registrar.qq.on_group_command("ping", priority=10)
    async def on_ping(self, event: GroupMessageEvent):
        """高优先级：群里发 'ping' 回复 'pong'"""
        await event.reply("pong 🏓")

    @registrar.qq.on_group_command("状态", priority=0)
    async def on_status(self, event: GroupMessageEvent):
        """低优先级：群里发 '状态' 回复插件状态"""
        await event.reply("EventHandling 插件运行中 ✅")

    # ==================== 模式 B: 事件流 ====================

    async def _stream_listener(self):
        """后台事件流: 监听所有私聊消息并记录日志"""
        try:
            async with self.events("message") as stream:
                async for event in stream:
                    if (
                        getattr(event.data, "message_type", None)
                        and event.data.message_type.value == "private"
                    ):
                        LOG.info(
                            "[事件流] 收到私聊消息: %s (来自 %s)",
                            event.data.raw_message,
                            event.data.user_id,
                        )
        except asyncio.CancelledError:
            pass

    # ==================== 模式 C: wait_event ====================

    @registrar.qq.on_group_command("确认测试")
    async def on_confirm_test(self, event: GroupMessageEvent):
        """群里发 '确认测试' → 等待用户在 15 秒内回复 '确认'"""
        await event.reply("请在 15 秒内回复「确认」来完成操作...")

        try:
            await self.wait_event(
                predicate=lambda e: (
                    hasattr(e.data, "user_id")
                    and str(e.data.user_id) == str(event.user_id)
                    and hasattr(e.data, "raw_message")
                    and e.data.raw_message.strip() == "确认"
                ),
                timeout=15.0,
            )
            await self.api.qq.post_group_msg(event.group_id, text="操作已确认 ✅")
        except asyncio.TimeoutError:
            await self.api.qq.post_group_msg(event.group_id, text="操作超时已取消 ⏰")
