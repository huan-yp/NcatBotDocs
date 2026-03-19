"""
github/02_issue_bot — GitHub Issue 自动回复机器人

⚠️ 开发中 — GitHub Adapter 尚在开发阶段，本示例为骨架代码。

演示功能:
  - registrar.github.on_issue(): 新 Issue 自动回复
  - registrar.github.on_comment(): Issue/PR 评论处理
  - event.reply(): 自动回复 Issue
  - GitHubIssueEvent / GitHubIssueCommentEvent 事件类型

使用方式: 配置 GitHub Webhook 后，将本文件夹复制到 plugins/ 目录。
新建 Issue 时 Bot 自动回复欢迎消息。
"""

from ncatbot.core import registrar
from ncatbot.event.github import GitHubIssueEvent, GitHubIssueCommentEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("GitHubIssueBot")


class GitHubIssueBotPlugin(NcatBotPlugin):
    name = "issue_bot_github"
    version = "1.0.0"
    author = "NcatBot"
    description = "GitHub Issue 自动回复机器人（开发中）"

    async def on_load(self):
        LOG.info("GitHub IssueBot 插件已加载")

    @registrar.github.on_issue()
    async def on_new_issue(self, event: GitHubIssueEvent):
        """新 Issue 自动回复"""
        action = getattr(event.data, "action", "")
        if action != "opened":
            return

        LOG.info("[GitHub] 新 Issue 已创建")
        await event.reply(
            "感谢你的反馈！我们会尽快处理这个 Issue。\n"
            "请确保你已经：\n"
            "1. 搜索过已有的 Issue\n"
            "2. 提供了足够的复现信息\n"
            "\n— Bot 自动回复"
        )

    @registrar.github.on_comment()
    async def on_comment(self, event: GitHubIssueCommentEvent):
        """Issue/PR 评论处理"""
        LOG.info("[GitHub] 新评论: 用户=%s", event.user_id)
