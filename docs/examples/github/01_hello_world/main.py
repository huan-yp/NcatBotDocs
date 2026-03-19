"""
github/01_hello_world — GitHub 平台基础事件处理

⚠️ 开发中 — GitHub Adapter 尚在开发阶段，本示例为骨架代码。

演示功能:
  - registrar.github.on_issue(): Issue 事件处理
  - registrar.github.on_pr(): Pull Request 事件处理
  - registrar.github.on_push(): Push 事件处理
  - GitHubIssueEvent / GitHubPREvent / GitHubPushEvent 事件类型

使用方式: 配置 GitHub Webhook 后，将本文件夹复制到 plugins/ 目录。
"""

from ncatbot.core import registrar
from ncatbot.event.github import GitHubIssueEvent, GitHubPREvent, GitHubPushEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("GitHubHelloWorld")


class GitHubHelloWorldPlugin(NcatBotPlugin):
    name = "hello_world_github"
    version = "1.0.0"
    author = "NcatBot"
    description = "GitHub 平台基础事件处理（开发中）"

    async def on_load(self):
        LOG.info("GitHub HelloWorld 插件已加载")

    @registrar.github.on_issue()
    async def on_issue(self, event: GitHubIssueEvent):
        """Issue 事件"""
        action = getattr(event.data, "action", "unknown")
        LOG.info("[GitHub] Issue %s: %s", action, event.data)

    @registrar.github.on_pr()
    async def on_pr(self, event: GitHubPREvent):
        """Pull Request 事件"""
        action = getattr(event.data, "action", "unknown")
        LOG.info("[GitHub] PR %s: %s", action, event.data)

    @registrar.github.on_push()
    async def on_push(self, event: GitHubPushEvent):
        """Push 事件"""
        LOG.info("[GitHub] Push: %s", event.data)
