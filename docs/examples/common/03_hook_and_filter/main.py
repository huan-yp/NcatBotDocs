"""
common/03_hook_and_filter — Hook 系统与过滤器（跨平台）

演示功能:
  - 自定义 BEFORE_CALL Hook: 关键词屏蔽
  - 自定义 AFTER_CALL Hook: 命令执行日志
  - 自定义 ON_ERROR Hook: 异常自动通知
  - @registrar.on_command() 跨平台命令装饰器
  - add_hooks 批量绑定 Hook

本示例不依赖任何平台。
使用方式:
  发送 "回声 你好"    → 回复 "你好"（经过关键词过滤）
  发送 "回声 违禁词"  → 被 Hook 拦截
  发送 "除零"         → 触发异常，ON_ERROR Hook 自动回复
"""

from ncatbot.core import registrar, Hook, HookAction, HookContext, HookStage, add_hooks
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("HookAndFilter")

BLOCKED_WORDS = ["违禁词", "广告", "spam"]


class KeywordFilterHook(Hook):
    """BEFORE_CALL: 检查消息文本是否包含屏蔽词"""

    stage = HookStage.BEFORE_CALL
    priority = 50

    async def execute(self, ctx: HookContext) -> HookAction:
        message = getattr(ctx.event.data, "message", None)
        if message is None:
            return HookAction.CONTINUE
        text = message.text if hasattr(message, "text") else ""
        for word in BLOCKED_WORDS:
            if word in text:
                LOG.info("消息被屏蔽词过滤: %s", text)
                return HookAction.SKIP
        return HookAction.CONTINUE


class LoggingHook(Hook):
    """AFTER_CALL: 记录命令成功执行的日志"""

    stage = HookStage.AFTER_CALL
    priority = 0

    async def execute(self, ctx: HookContext) -> HookAction:
        handler_name = ctx.handler_entry.func.__name__
        user_id = getattr(ctx.event.data, "user_id", "unknown")
        LOG.info("[日志 Hook] %s 被 %s 成功执行", handler_name, user_id)
        return HookAction.CONTINUE


class ErrorNotifyHook(Hook):
    """ON_ERROR: 异常时自动记录"""

    stage = HookStage.ON_ERROR
    priority = 0

    async def execute(self, ctx: HookContext) -> HookAction:
        error = ctx.error
        LOG.error("[错误 Hook] handler 异常: %s", error)
        return HookAction.CONTINUE


keyword_filter = KeywordFilterHook()
logging_hook = LoggingHook()
error_notify = ErrorNotifyHook()


class HookAndFilterPlugin(NcatBotPlugin):
    name = "hook_and_filter"
    version = "1.0.0"
    author = "NcatBot"
    description = "Hook 系统与过滤器演示（跨平台）"

    async def on_load(self):
        LOG.info("HookAndFilter 插件已加载")

    @add_hooks(keyword_filter, logging_hook, error_notify)
    @registrar.on_command("回声")
    async def on_echo(self, event, content: str):
        """回声命令（经过关键词过滤 + 日志记录 + 错误捕获）"""
        await event.reply(f"🔊 {content}")

    @error_notify
    @registrar.on_command("除零")
    async def on_divide_by_zero(self, event):
        """故意触发异常，演示 ON_ERROR Hook"""
        _ = 1 / 0
