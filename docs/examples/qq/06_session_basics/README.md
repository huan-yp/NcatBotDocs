# 06_session_basics

> 分类：qq

## 这个示例教什么

NcatBot 中**如何等待同一会话的用户回复并过滤消息**。通过 `wait_session_reply` 和 `wait_session_event`，你可以在处理一条命令时"暂停"并等待用户的下一条输入，同时用谓词（`has_keyword`、`msg_in`、`msg_matches`）精确过滤期望的消息内容，用 `&` `|` `~` 组合复杂匹配逻辑。

## 你将学到

- `wait_session_reply` — 等待同会话文本回复，返回 `SessionResult`
- `wait_session_event` — 等待同会话事件，支持 `extra_predicate` 附加过滤
- `SessionResult` — `ok` / `text` / `timed_out` / `cancelled` / `cancel_word` 字段
- `cancel_words` — 取消词列表，用户输入取消词时自动中止等待
- `from_event` — 从当前事件自动推导同会话条件（同用户 + 同群 + 同消息类型）
- `has_keyword` — 消息包含关键词
- `msg_in` — 消息精确匹配
- `msg_matches` — 正则匹配
- 谓词组合运算 — `&` (AND), `|` (OR), `~` (NOT)

## 前置知识

- [01_event_registration](../01_event_registration/) — 事件注册基础
- [02_command_binding](../02_command_binding/) — 命令绑定方式

## 目录结构

~~~text
06_session_basics/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
└── README.md
~~~

## 完整代码

~~~python
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
~~~

## 关键代码讲解

### SessionResult 字段说明

`wait_session_reply` 返回 `SessionResult`，通过字段判断用户行为：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ok` | `bool` | `True` = 用户正常回复 |
| `text` | `str \| None` | 回复文本（仅 `ok=True` 时有值） |
| `timed_out` | `bool` | `True` = 等待超时 |
| `cancelled` | `bool` | `True` = 用户输入了取消词 |
| `cancel_word` | `str \| None` | 匹配到的取消词（仅 `cancelled=True` 时有值） |
| `event` | `Event \| None` | 原始事件对象（仅 `ok=True` 时有值） |

典型判断模式：

~~~python
result = await self.wait_session_reply(event, timeout=30, cancel_words=["取消"])
if result.ok:
    print(result.text)      # 用户回复内容
elif result.timed_out:
    print("超时")
elif result.cancelled:
    print(result.cancel_word)  # "取消"
~~~

### wait_session_event vs wait_session_reply

| | `wait_session_event` | `wait_session_reply` |
|---|---|---|
| 返回值 | `Event`（原始事件） | `SessionResult`（封装结果） |
| 超时 | 抛出 `TimeoutError` | `result.timed_out = True` |
| 取消词 | 抛出 `SessionCancelled` | `result.cancelled = True` |
| extra_predicate | ✅ 支持 | ❌ 不支持 |
| 适用场景 | 需要过滤或访问完整事件 | 只需拿到回复文本 |

### 谓词组合运算表

| 运算符 | 含义 | 示例 | 效果 |
|--------|------|------|------|
| `&` | AND | `has_keyword("A") & has_keyword("B")` | 消息同时包含 A 和 B |
| `\|` | OR | `msg_in("是") \| msg_in("确认")` | 消息等于「是」或「确认」 |
| `~` | NOT | `~has_keyword("退款")` | 消息不包含「退款」 |

组合示例：

~~~python
# 包含「订单」且不包含「退款」，或精确等于「帮助」
pred = (has_keyword("订单") & ~has_keyword("退款")) | msg_in("帮助")
~~~

### from_event — 自动推导

`from_event(event)` 根据当前事件自动构建 session 谓词：

- **群消息** → 同 `user_id` + 同 `group_id` + 消息类型为群消息
- **私聊消息** → 同 `user_id` + 消息类型为私聊消息

`wait_session_event` 内部已自动调用 `from_event`，通常不需要手动调用。当你需要在 `from_event` 基础上叠加条件时，使用 `extra_predicate` 参数即可。

## 运行方式

1. 将 `06_session_basics/` 文件夹复制到项目的 `plugins/` 目录
2. 启动 Bot
3. 在群聊中发送以下命令测试：
   - `等待回复` — 体验 `wait_session_reply` 和 `SessionResult`
   - `等待确认` — 体验 `extra_predicate` 过滤
   - `关键词测试` — 体验 `has_keyword`、`msg_matches` 谓词
   - `谓词组合` — 体验 `&` `|` `~` 组合
   - `下一条` — 体验 `from_event` 自动推导

## 延伸阅读

- [07_dialog_and_menu](../07_dialog_and_menu/) — 多步对话 UI 和菜单流程
- `wait_event` — 底层等待 API，不绑定 session
- `events()` — 持续事件流，`async for` 消费多条事件
