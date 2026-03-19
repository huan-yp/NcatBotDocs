"""
cross_platform/02_trait_programming — Trait 跨平台编程

演示功能:
  - Replyable Trait: 统一回复接口，不依赖具体平台
  - HasSender Trait: 统一获取发送者信息
  - GroupScoped Trait: 统一获取群/房间 ID
  - isinstance 分支处理不同平台事件
  - @registrar.on_message() 跨平台消息监听

使用方式: 将本文件夹复制到 plugins/ 目录，配置多平台适配器。
所有平台的消息都会被统一处理和记录。

参考文档: docs/guide/api_usage/common/2_traits.md
"""

from ncatbot.core import registrar
from ncatbot.event import Replyable, HasSender, GroupScoped
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("TraitProgramming")


class TraitProgrammingPlugin(NcatBotPlugin):
    name = "trait_programming"
    version = "1.0.0"
    author = "NcatBot"
    description = "跨平台 Trait 编程演示"

    async def on_load(self):
        self.data.setdefault("platform_counts", {})
        LOG.info("TraitProgramming 插件已加载")

    @registrar.on_message()
    async def on_any_message(self, event):
        """所有平台的消息事件 — Trait 统一处理"""
        platform = event.platform

        # 统计各平台消息数
        counts = self.data.setdefault("platform_counts", {})
        counts[platform] = counts.get(platform, 0) + 1

        # HasSender: 获取发送者信息
        sender_info = ""
        if isinstance(event, HasSender):
            sender = event.sender
            nickname = getattr(sender, "nickname", None)
            sender_info = f" 来自 {nickname or event.user_id}"

        # GroupScoped: 获取群/房间信息
        group_info = ""
        if isinstance(event, GroupScoped):
            group_info = f" (群/房间: {event.group_id})"

        LOG.info("[%s] 收到消息%s%s", platform, sender_info, group_info)

    @registrar.on_command("平台统计")
    async def on_platform_stats(self, event):
        """查看各平台消息统计 — 跨平台命令"""
        counts = self.data.get("platform_counts", {})
        if not counts:
            if isinstance(event, Replyable):
                await event.reply("还没有收到任何平台的消息")
            return

        lines = ["📊 各平台消息统计:"]
        for platform, count in sorted(counts.items()):
            lines.append(f"  {platform}: {count} 条")

        total = sum(counts.values())
        lines.append(f"  总计: {total} 条")

        if isinstance(event, Replyable):
            await event.reply("\n".join(lines))
