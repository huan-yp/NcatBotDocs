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

from ncatbot.core import registrar, from_event
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log


class EventHandlingPlugin(NcatBotPlugin):
    name = "event_handling_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 事件处理三模式演示"

    async def on_load(self):
        self.logger.info("EventHandling 插件已加载") # 也可以用 self.logger 记录日志

    async def on_close(self):
        self.logger.info("EventHandling 插件已卸载。")

    # ==================== 模式 C: wait_event ====================
    @registrar.qq.on_group_command("下一条")
    async def on_wait_next(self, event: GroupMessageEvent):
        """收到 '下一条' → 等待用户在同一会话中 30 秒内发送任意消息 → 回复消息内容"""
        """'同一会话' 指的是同一个用户在同一个群里发消息（或同一个用户的私聊消息）"""
        """对其它事件处理无任何干扰"""
        await event.reply("请在 30 秒内发送任意消息，我会回复你的下一条消息内容...")

        try:
            next_event = await self.wait_event(
                predicate=from_event(event),
                timeout=30.0,
            )
            assert isinstance(next_event, GroupMessageEvent)  # 类型断言，方便 IDE 提示
            await event.reply(f"你刚才发的消息是: {next_event.raw_message}")
        except asyncio.TimeoutError:
            await event.reply("等待超时，你没有发送消息 ⏰")

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
