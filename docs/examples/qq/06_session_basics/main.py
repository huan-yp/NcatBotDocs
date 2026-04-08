"""
qq/06_session_basics — QQ 会话等待与过滤基础

演示功能:
  - wait_session_reply    等待同会话文本回复，返回 SessionResult
  - wait_session_event    等待同会话事件（带 extra_predicate）
  - SessionResult         ok / text / timed_out / cancelled / cancel_word
  - from_event            自动推导同会话条件
  - has_keyword           消息包含关键词谓词
  - msg_in                消息精确匹配谓词
  - msg_matches           正则匹配谓词
  - 谓词组合              & (AND)  | (OR)  ~ (NOT)

只做提及:
  - wait_event     底层等待 API（需手动构造谓词，不自动绑定 session）
  - events()       持续事件流工具（async for 消费多条事件）

边界:
  本示例只讲"等待和过滤"，不讲多步对话 UI 和菜单流程。

前置知识: qq/01_event_registration, qq/02_command_binding
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import from_event, has_keyword, msg_in, msg_matches, registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.plugin.mixin import SessionResult
from ncatbot.utils import get_log

LOG = get_log("SessionBasics")


class SessionBasicsPlugin(NcatBotPlugin):
    name = "session_basics_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 会话等待与过滤基础"

    # ================================================================
    # 1. wait_session_reply — 等待文本回复
    # ================================================================

    @registrar.qq.on_group_command("等待回复")
    async def on_wait_reply(self, event: GroupMessageEvent):
        """最基础的会话等待：等用户回复一条文本"""
        await self.api.qq.send_group_text(
            event.group_id, "请在 30 秒内回复任意内容（发送「取消」或「退出」可中止）"
        )

        result: SessionResult = await self.wait_session_reply(
            event,
            timeout=30,
            cancel_words=["取消", "退出"],
        )

        # ---- SessionResult 字段演示 ----
        if result.ok:
            await self.api.qq.send_group_text(
                event.group_id,
                f"✅ 收到回复: {result.text}",
            )
        elif result.timed_out:
            await self.api.qq.send_group_text(
                event.group_id, "⏰ 等待超时，未收到回复"
            )
        elif result.cancelled:
            await self.api.qq.send_group_text(
                event.group_id,
                f"🚫 已取消（触发词: {result.cancel_word}）",
            )

    # ================================================================
    # 2. wait_session_event + extra_predicate — 等待确认
    # ================================================================

    @registrar.qq.on_group_command("等待确认")
    async def on_wait_confirm(self, event: GroupMessageEvent):
        """使用 extra_predicate 限制只接受「确认」或「是」"""
        await self.api.qq.send_group_text(
            event.group_id, '请回复「确认」或「是」以继续（发送「取消」中止）'
        )

        try:
            # extra_predicate 与 from_event 自动 AND 组合
            confirmed_event = await self.wait_session_event(
                event,
                timeout=30,
                extra_predicate=msg_in("确认", "是"),
                cancel_words=["取消"],
            )
            await self.api.qq.send_group_text(
                event.group_id, "✅ 已确认，继续执行后续操作"
            )
        except TimeoutError:
            await self.api.qq.send_group_text(
                event.group_id, "⏰ 等待超时"
            )

    # ================================================================
    # 3. has_keyword / msg_matches — 消息谓词演示
    # ================================================================

    @registrar.qq.on_group_command("关键词测试")
    async def on_predicate_demo(self, event: GroupMessageEvent):
        """演示 has_keyword 和 msg_matches 谓词"""
        await self.api.qq.send_group_text(
            event.group_id,
            "请回复包含「天气」或「温度」的消息，或回复 4 位数字验证码"
        )

        # has_keyword: 消息中包含任意关键词即匹配
        # msg_matches: 正则匹配整条消息
        pred = has_keyword("天气", "温度") | msg_matches(r"^\d{4}$")

        try:
            matched = await self.wait_session_event(
                event,
                timeout=30,
                extra_predicate=pred,
                cancel_words=["取消"],
            )
            text = matched.data.raw_message.strip()
            await self.api.qq.send_group_text(
                event.group_id, f"✅ 匹配成功: {text}"
            )
        except TimeoutError:
            await self.api.qq.send_group_text(
                event.group_id, "⏰ 等待超时，未收到匹配消息"
            )

    # ================================================================
    # 4. 谓词组合运算 — & | ~
    # ================================================================

    @registrar.qq.on_group_command("谓词组合")
    async def on_combinator_demo(self, event: GroupMessageEvent):
        """演示谓词的 AND / OR / NOT 组合"""
        await self.api.qq.send_group_text(
            event.group_id,
            "请回复消息。匹配规则：\n"
            "  包含「订单」且不包含「退款」\n"
            "  或精确回复「帮助」",
        )

        # & = AND,  | = OR,  ~ = NOT
        order_not_refund = has_keyword("订单") & ~has_keyword("退款")
        help_exact = msg_in("帮助")
        combined = order_not_refund | help_exact

        try:
            matched = await self.wait_session_event(
                event,
                timeout=30,
                extra_predicate=combined,
                cancel_words=["取消"],
            )
            text = matched.data.raw_message.strip()
            await self.api.qq.send_group_text(
                event.group_id, f"✅ 谓词匹配成功: {text}"
            )
        except TimeoutError:
            await self.api.qq.send_group_text(
                event.group_id, "⏰ 等待超时"
            )

    # ================================================================
    # 5. from_event — 自动推导同会话条件
    # ================================================================

    @registrar.qq.on_group_command("下一条")
    async def on_next_event(self, event: GroupMessageEvent):
        """展示 from_event 的自动推导：同用户、同群、同消息类型"""
        await self.api.qq.send_group_text(
            event.group_id, "等待你在本群的下一条消息（30 秒超时）"
        )

        # from_event(event) 自动绑定：
        #   同 user_id  +  同 group_id  +  同消息类型（群消息）
        # wait_session_event 内部已自动调用 from_event，此处显式展示
        pred = from_event(event)
        LOG.info("from_event 推导的谓词: %s", pred)

        try:
            next_evt = await self.wait_session_event(event, timeout=30)
            text = next_evt.data.raw_message.strip()
            await self.api.qq.send_group_text(
                event.group_id, f"📩 收到下一条消息: {text}"
            )
        except TimeoutError:
            await self.api.qq.send_group_text(
                event.group_id, "⏰ 等待超时"
            )

    # ================================================================
    # 提及但不展开
    # ================================================================
    # 底层 API:
    #   await self.wait_event(predicate, timeout)
    #     — 不绑定 session，需手动构造完整谓词
    #
    # 持续事件流:
    #   async for evt in self.events(predicate, timeout_each):
    #     — 循环消费多条事件，适合收集型场景
    #
    # 这两个工具在 07_dialog_and_menu 中详细展开。
