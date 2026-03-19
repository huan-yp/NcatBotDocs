"""
qq/08_scheduled_reporter — QQ 定时报告与统计

演示功能:
  - TimeTaskMixin: 每天定时发送报告
  - DataMixin: 持久化统计数据
  - ForwardConstructor: 合并转发消息发送长报告
  - @registrar.qq.on_group_command() 命令匹配

使用方式:
  "开启统计"         → 开始统计当前群的消息活跃度
  "关闭统计"         → 停止统计
  "统计报告"         → 手动触发统计报告
  "今日热词"         → 查看今天出现频率最高的词
"""

import time
from collections import Counter

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types.qq import ForwardConstructor
from ncatbot.utils import get_log

LOG = get_log("ScheduledReporter")


class ScheduledReporterPlugin(NcatBotPlugin):
    name = "scheduled_reporter_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 定时报告与统计"

    async def on_load(self):
        self.data.setdefault("enabled_groups", [])
        self.data.setdefault("daily_stats", {})
        self.add_scheduled_task("daily_report", "22:00")
        LOG.info("ScheduledReporter 已加载，监控群: %s", self.data["enabled_groups"])

    @registrar.qq.on_group_command("开启统计")
    async def on_enable(self, event: GroupMessageEvent):
        gid = str(event.group_id)
        groups = self.data.setdefault("enabled_groups", [])
        if gid not in groups:
            groups.append(gid)
            await event.reply("📊 已开启本群的消息统计")
        else:
            await event.reply("📊 本群统计已开启")

    @registrar.qq.on_group_command("关闭统计")
    async def on_disable(self, event: GroupMessageEvent):
        gid = str(event.group_id)
        groups = self.data.get("enabled_groups", [])
        if gid in groups:
            groups.remove(gid)
            await event.reply("📊 已关闭本群的消息统计")
        else:
            await event.reply("📊 本群统计未开启")

    @registrar.qq.on_group_message(priority=200)
    async def on_count(self, event: GroupMessageEvent):
        """高优先级: 统计每条群消息"""
        gid = str(event.group_id)
        if gid not in self.data.get("enabled_groups", []):
            return

        today = time.strftime("%Y-%m-%d")
        daily = self.data.setdefault("daily_stats", {})
        today_stats = daily.setdefault(today, {})
        group_stats = today_stats.setdefault(
            gid, {"total": 0, "users": {}, "words": {}}
        )

        group_stats["total"] += 1
        uid = str(event.user_id)
        group_stats["users"][uid] = group_stats["users"].get(uid, 0) + 1

        text = event.message.text.strip()
        if len(text) > 1:
            words = group_stats.setdefault("words", {})
            for word in text.split():
                if len(word) >= 2:
                    words[word] = words.get(word, 0) + 1

    @registrar.qq.on_group_command("统计报告")
    async def on_report(self, event: GroupMessageEvent):
        await self._send_report(str(event.group_id))

    @registrar.qq.on_group_command("今日热词")
    async def on_hot_words(self, event: GroupMessageEvent):
        gid = str(event.group_id)
        today = time.strftime("%Y-%m-%d")
        stats = self.data.get("daily_stats", {}).get(today, {}).get(gid, {})
        words = stats.get("words", {})

        if not words:
            await event.reply("今天还没有统计到热词")
            return

        top = Counter(words).most_common(10)
        lines = ["🔥 今日热词 Top 10:"]
        for word, count in top:
            lines.append(f"  {word}: {count} 次")
        await event.reply("\n".join(lines))

    async def _send_report(self, group_id: str):
        today = time.strftime("%Y-%m-%d")
        stats = self.data.get("daily_stats", {}).get(today, {}).get(group_id, {})

        if not stats or stats.get("total", 0) == 0:
            await self.api.qq.post_group_msg(group_id, text="📊 今天还没有统计数据")
            return

        total = stats["total"]
        users = stats.get("users", {})
        words = stats.get("words", {})

        fc = ForwardConstructor(
            user_id=str(getattr(self, "_self_id", "10000")),
            nickname="📊 统计助手",
        )

        fc.attach_text(
            f"📊 {today} 群活跃度报告\n总消息: {total} 条\n活跃人数: {len(users)} 人"
        )

        top_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
        user_lines = ["👑 活跃排行 Top 10:"]
        for rank, (uid, count) in enumerate(top_users, 1):
            user_lines.append(f"  {rank}. {uid}: {count} 条")
        fc.attach_text("\n".join(user_lines))

        if words:
            top_words = Counter(words).most_common(10)
            word_lines = ["🔥 热词 Top 10:"]
            for word, count in top_words:
                word_lines.append(f"  {word}: {count} 次")
            fc.attach_text("\n".join(word_lines))

        forward = fc.build()
        await self.api.qq.post_group_forward_msg(group_id, forward)

    async def daily_report(self):
        """每日 22:00 自动发送报告"""
        for gid in self.data.get("enabled_groups", []):
            try:
                await self._send_report(gid)
            except Exception as e:
                LOG.error("发送群 %s 报告失败: %s", gid, e)
