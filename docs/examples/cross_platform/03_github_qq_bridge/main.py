"""
cross_platform/03_github_qq_bridge — GitHub ↔ QQ 双向桥接机器人

演示功能:
  - GitHub → QQ: Issue/PR/Push/Comment 事件自动转发到 QQ 群
  - QQ → GitHub: 引用(reply)通知消息 → 自动作为 GitHub Issue Comment 发送
  - QQ 群命令: issue / issue-reply / gh-status
  - 消息 ID ↔ GitHub Issue 映射追踪 (支持 reply 反向关联)
  - ConfigMixin 配置管理 (群号/仓库名从配置读取)

交互流程:
  GitHub → QQ:
    1. 新 Issue 创建/关闭/重新打开 → 自动转发到 QQ 群
    2. Issue 收到新评论 → 自动转发到 QQ 群
    3. Push / PR 事件 → 简要通知到 QQ 群

  QQ → GitHub:
    1. 在 QQ 群中引用某条 Issue 通知消息 → 回复内容自动作为 GitHub Issue Comment
    2. QQ 群命令 "issue <number>" → 查看 Issue 详情
    3. QQ 群命令 "issue-reply <number> <内容>" → 直接评论某个 Issue

配置要求 (config.yaml):
  adapters 中需同时启用 napcat 和 github 适配器。
  插件配置 (通过 ConfigMixin 读取):
    target_qq_group: 123456789    # 转发目标 QQ 群号
    target_repo: "owner/repo"     # 监听的 GitHub 仓库

使用方式: 将本文件夹复制到 plugins/ 目录，配置好双适配器和插件配置后启动 Bot。

⚠️ GitHub Adapter 尚在开发阶段，API 可能变动。

参考文档:
  - docs/guide/multi_platform/README.md
  - docs/guide/api_usage/github/
"""

import time
from typing import Dict, Optional

from ncatbot.core import registrar
from ncatbot.event import HasSender
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.event.github import (
    GitHubIssueEvent,
    GitHubIssueCommentEvent,
    GitHubPushEvent,
    GitHubPREvent,
)
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types.common.segment import Reply, PlainText
from ncatbot.utils import get_log

LOG = get_log("GH-QQ-Bridge")

# 映射过期时间 (秒)
_MAP_TTL = 3600 * 24  # 24 小时


class GitHubQQBridgePlugin(NcatBotPlugin):
    name = "github_qq_bridge"
    version = "1.0.0"
    author = "NcatBot"
    description = "GitHub ↔ QQ 双向桥接机器人"

    async def on_load(self):
        # 从 ConfigMixin 读取配置
        self._target_group = self.get_config("target_qq_group", 0)
        self._target_repo = self.get_config("target_repo", "")

        if not self._target_group or not self._target_repo:
            LOG.warning(
                "请配置 target_qq_group 和 target_repo，当前值: group=%s, repo=%s",
                self._target_group,
                self._target_repo,
            )

        # 消息 ID → GitHub Issue 映射，用于 QQ reply 反向关联
        self._msg_issue_map: Dict[str, dict] = {}
        self._msg_timestamps: Dict[str, float] = {}

        LOG.info(
            "GitHubQQBridge 已加载 — 桥接群: %s, 仓库: %s",
            self._target_group,
            self._target_repo,
        )

    async def on_close(self):
        LOG.info("GitHubQQBridge 已卸载")

    # ==================== 内部工具 ====================

    def _cleanup_old_mappings(self):
        """清理超过 TTL 的旧映射"""
        now = time.monotonic()
        expired = [k for k, ts in self._msg_timestamps.items() if now - ts > _MAP_TTL]
        for k in expired:
            self._msg_issue_map.pop(k, None)
            self._msg_timestamps.pop(k, None)

    def _record_mapping(self, msg_id: str, repo: str, issue_number: int, kind: str):
        """记录 QQ 消息 → GitHub Issue 映射"""
        self._cleanup_old_mappings()
        self._msg_issue_map[msg_id] = {
            "repo": repo,
            "issue_number": issue_number,
            "type": kind,
        }
        self._msg_timestamps[msg_id] = time.monotonic()

    @staticmethod
    def _extract_reply_msg_id(event: GroupMessageEvent) -> Optional[str]:
        """从 QQ 群消息中提取被引用的消息 ID"""
        replies = event.message.filter(Reply)
        return replies[0].id if replies else None

    @staticmethod
    def _extract_text_content(event: GroupMessageEvent) -> str:
        """提取 QQ 消息的纯文本内容 (排除 reply/at 段)"""
        texts = event.message.filter(PlainText)
        return "".join(t.text for t in texts).strip()

    # ==================== GitHub → QQ 转发 ====================

    @registrar.github.on_issue()
    async def on_github_issue(self, event: GitHubIssueEvent):
        """GitHub Issue 事件 → 转发到 QQ 群"""
        action = event.action
        if action not in ("opened", "closed", "reopened", "edited"):
            return

        action_text = {
            "opened": "🆕 新建",
            "closed": "✅ 关闭",
            "reopened": "🔄 重新打开",
            "edited": "✏️ 编辑",
        }.get(action, action)

        sender_name = ""
        if isinstance(event, HasSender):
            sender = event.sender
            sender_name = getattr(sender, "nickname", "") or str(event.user_id)

        body_preview = ""
        if action == "opened":
            raw_body = getattr(event._data, "issue_body", "") or ""
            if raw_body:
                body_preview = f"\n---\n{raw_body[:300]}"
                if len(raw_body) > 300:
                    body_preview += "..."

        text = (
            f"📋 GitHub Issue {action_text}\n"
            f"仓库: {event.repo}\n"
            f"#{event.issue_number} {event.issue_title}\n"
            f"操作者: {sender_name}"
            f"{body_preview}\n"
            f"💬 引用本消息可直接回复到 GitHub"
        )

        try:
            result = await self.api.qq.send_group_text(self._target_group, text)
            if result and result.message_id:
                self._record_mapping(
                    result.message_id, event.repo, event.issue_number, "issue"
                )
            LOG.info(
                "[GH→QQ] Issue #%d %s by %s",
                event.issue_number,
                action,
                sender_name,
            )
        except Exception as e:
            LOG.error("[GH→QQ] 转发 Issue 失败: %s", e)

    @registrar.github.on_comment()
    async def on_github_comment(self, event: GitHubIssueCommentEvent):
        """GitHub Issue/PR 评论 → 转发到 QQ 群"""
        sender_name = ""
        if isinstance(event, HasSender):
            sender = event.sender
            sender_name = getattr(sender, "nickname", "") or str(event.user_id)

        body = event.comment_body or ""
        body_preview = body[:400]
        if len(body) > 400:
            body_preview += "..."

        text = (
            f"💬 GitHub 评论\n"
            f"仓库: {event.repo}\n"
            f"Issue #{event.issue_number}\n"
            f"评论者: {sender_name}\n"
            f"---\n{body_preview}\n"
            f"💬 引用本消息可直接回复到 GitHub"
        )

        try:
            result = await self.api.qq.send_group_text(self._target_group, text)
            if result and result.message_id:
                self._record_mapping(
                    result.message_id, event.repo, event.issue_number, "comment"
                )
            LOG.info("[GH→QQ] Comment on #%d by %s", event.issue_number, sender_name)
        except Exception as e:
            LOG.error("[GH→QQ] 转发评论失败: %s", e)

    @registrar.github.on_push()
    async def on_github_push(self, event: GitHubPushEvent):
        """GitHub Push 事件 → 简要通知到 QQ 群"""
        commits = event._data.commits or []
        if not commits:
            return

        pusher = event._data.pusher_name or "unknown"
        ref = event._data.ref.replace("refs/heads/", "")
        commit_lines = []
        for c in commits[:5]:
            short_sha = c.id[:7] if c.id else "?"
            msg = (c.message or "").split("\n")[0][:60]
            commit_lines.append(f"  {short_sha} {msg}")
        if len(commits) > 5:
            commit_lines.append(f"  ... 共 {len(commits)} 个提交")

        text = (
            f"🚀 GitHub Push\n"
            f"仓库: {event._data.repo.full_name}\n"
            f"分支: {ref}\n"
            f"推送者: {pusher}\n" + "\n".join(commit_lines)
        )

        try:
            await self.api.qq.send_group_text(self._target_group, text)
            LOG.info("[GH→QQ] Push %d commits to %s", len(commits), ref)
        except Exception as e:
            LOG.error("[GH→QQ] 转发 Push 失败: %s", e)

    @registrar.github.on_pr()
    async def on_github_pr(self, event: GitHubPREvent):
        """GitHub PR 事件 → 简要通知到 QQ 群"""
        action = getattr(event._data, "action", "")
        if not action:
            return

        action_text = {
            "opened": "🆕 新建",
            "closed": "✅ 关闭",
            "reopened": "🔄 重新打开",
            "synchronize": "🔄 更新",
        }.get(str(action), str(action))

        sender_name = ""
        if isinstance(event, HasSender):
            sender = event.sender
            sender_name = getattr(sender, "nickname", "") or str(event.user_id)

        merged = getattr(event._data, "merged", False)
        if merged:
            action_text = "🎉 合并"

        text = (
            f"🔀 GitHub PR {action_text}\n"
            f"仓库: {event._data.repo.full_name}\n"
            f"#{event._data.pr_number} {event._data.pr_title}\n"
            f"操作者: {sender_name}\n"
            f"{event._data.head_ref} → {event._data.base_ref}"
        )

        try:
            await self.api.qq.send_group_text(self._target_group, text)
            LOG.info("[GH→QQ] PR #%d %s", event._data.pr_number, action_text)
        except Exception as e:
            LOG.error("[GH→QQ] 转发 PR 失败: %s", e)

    # ==================== QQ → GitHub (reply 引用回复) ====================

    @registrar.qq.on_group_message()
    async def on_qq_reply_to_github(self, event: GroupMessageEvent):
        """QQ 群消息如果引用了 GitHub 通知消息，则转发到 GitHub Issue Comment"""
        if str(event.group_id) != str(self._target_group):
            return

        reply_msg_id = self._extract_reply_msg_id(event)
        if not reply_msg_id:
            return

        mapping = self._msg_issue_map.get(reply_msg_id)
        if not mapping:
            return

        text = self._extract_text_content(event)
        if not text.strip():
            return

        repo = mapping["repo"]
        issue_number = mapping["issue_number"]

        qq_sender = ""
        if hasattr(event, "sender"):
            qq_sender = getattr(event.sender, "nickname", "") or str(event.user_id)

        comment_body = f"**[QQ Bridge]** {qq_sender} 回复:\n\n{text}"

        try:
            await self.api.github.create_issue_comment(
                repo=repo,
                issue_number=issue_number,
                body=comment_body,
            )
            await event.reply(text=f"✅ 已回复到 GitHub {repo}#{issue_number}")
            LOG.info("[QQ→GH] %s 回复 Issue #%d", qq_sender, issue_number)
        except Exception as e:
            await event.reply(text=f"❌ 回复失败: {e}")
            LOG.error("[QQ→GH] 回复 Issue 失败: %s", e)

    # ==================== QQ 群命令 ====================

    @registrar.qq.on_group_command("issue")
    async def qq_issue_detail(self, event: GroupMessageEvent):
        """QQ 群命令: issue <number> — 查看 Issue 详情"""
        text = event.message.text or ""
        number_str = ""
        for p in text.strip().split():
            if p.isdigit():
                number_str = p
                break

        if not number_str:
            await event.reply(text="用法: issue <Issue编号>\n例如: issue 42")
            return

        issue_number = int(number_str)
        try:
            issue = await self.api.github.get_issue(
                repo=self._target_repo,
                issue_number=issue_number,
            )
            title = issue.get("title", "无标题")
            state = issue.get("state", "unknown")
            body = issue.get("body", "") or ""
            user = issue.get("user", {}).get("login", "unknown")
            labels = ", ".join(lb.get("name", "") for lb in issue.get("labels", []))

            body_preview = body[:500]
            if len(body) > 500:
                body_preview += "..."

            state_emoji = "🟢" if state == "open" else "🔴"
            reply_text = (
                f"{state_emoji} Issue #{issue_number}: {title}\n"
                f"状态: {state} | 创建者: {user}\n"
            )
            if labels:
                reply_text += f"标签: {labels}\n"
            if body_preview:
                reply_text += f"---\n{body_preview}"

            result = await event.reply(text=reply_text)
            if result and hasattr(result, "message_id") and result.message_id:
                self._record_mapping(
                    result.message_id, self._target_repo, issue_number, "issue"
                )
        except Exception as e:
            await event.reply(text=f"❌ 获取 Issue 失败: {e}")

    @registrar.qq.on_group_command("issue-reply")
    async def qq_issue_reply(self, event: GroupMessageEvent):
        """QQ 群命令: issue-reply <number> <内容> — 直接评论 Issue"""
        text = event.message.text or ""
        content = text.strip()
        for prefix in ("issue-reply", "issue_reply"):
            if content.startswith(prefix):
                content = content[len(prefix) :].strip()
                break

        parts = content.split(maxsplit=1)
        if len(parts) < 2 or not parts[0].isdigit():
            await event.reply(text="用法: issue-reply <Issue编号> <回复内容>")
            return

        issue_number = int(parts[0])
        reply_content = parts[1].strip()

        qq_sender = ""
        if hasattr(event, "sender"):
            qq_sender = getattr(event.sender, "nickname", "") or str(event.user_id)

        comment_body = f"**[QQ Bridge]** {qq_sender} 回复:\n\n{reply_content}"

        try:
            await self.api.github.create_issue_comment(
                repo=self._target_repo,
                issue_number=issue_number,
                body=comment_body,
            )
            await event.reply(
                text=f"✅ 已评论到 GitHub {self._target_repo}#{issue_number}"
            )
            LOG.info("[QQ→GH] %s 评论 Issue #%d", qq_sender, issue_number)
        except Exception as e:
            await event.reply(text=f"❌ 评论失败: {e}")

    @registrar.qq.on_group_command("gh-status")
    async def qq_gh_status(self, event: GroupMessageEvent):
        """QQ 群命令: gh-status — 查看桥接状态"""
        try:
            platforms = self.api.platforms
            lines = ["📊 跨平台状态:"]
            for name in platforms:
                lines.append(f"  ✅ {name}")
            lines.append(f"\n📍 桥接群: {self._target_group}")
            lines.append(f"📦 监听仓库: {self._target_repo}")
            lines.append(f"📋 活跃映射数: {len(self._msg_issue_map)}")
            await event.reply(text="\n".join(lines))
        except Exception as e:
            await event.reply(text=f"❌ 获取状态失败: {e}")
