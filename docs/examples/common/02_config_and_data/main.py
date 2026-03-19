"""
common/02_config_and_data — 配置与数据持久化（跨平台）

演示功能:
  - ConfigMixin: get_config / set_config / update_config (YAML 持久化)
  - DataMixin: self.data 字典 (JSON 持久化)
  - 配置和数据在插件重启后自动恢复
  - @registrar.on_command() 跨平台命令匹配

本示例不依赖任何平台，可在 QQ / Bilibili / GitHub 上运行。
使用方式:
  发送 "设置前缀 !"   → 修改命令前缀配置
  发送 "查看配置"      → 显示当前所有配置
  发送 "统计"          → 显示消息计数统计
  发送 "重置统计"      → 清空统计数据
"""

from ncatbot.core import registrar
from ncatbot.event import HasSender
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("ConfigAndData")


class ConfigAndDataPlugin(NcatBotPlugin):
    name = "config_and_data"
    version = "1.0.0"
    author = "NcatBot"
    description = "配置与数据持久化演示（跨平台）"

    async def on_load(self):
        if not self.get_config("prefix"):
            self.set_config("prefix", "/")
        if not self.get_config("welcome_msg"):
            self.set_config("welcome_msg", "欢迎使用！")
        if not self.get_config("enabled"):
            self.set_config("enabled", True)

        self.data.setdefault("total_messages", 0)
        self.data.setdefault("user_counts", {})

        LOG.info("ConfigAndData 已加载，累计消息: %d", self.data["total_messages"])

    # ---- 消息计数（自动统计） ----

    @registrar.on_message(priority=100)
    async def count_message(self, event):
        """每条消息都计数（高优先级，不影响其他 handler）"""
        self.data["total_messages"] = self.data.get("total_messages", 0) + 1
        if isinstance(event, HasSender):
            uid = str(event.user_id)
            counts = self.data.setdefault("user_counts", {})
            counts[uid] = counts.get(uid, 0) + 1

    # ---- 配置管理命令 ----

    @registrar.on_command("设置前缀")
    async def on_set_prefix(self, event, new_prefix: str):
        """设置命令前缀 — CommandHook 自动提取参数"""
        self.set_config("prefix", new_prefix)
        await event.reply(f"命令前缀已更新为: {new_prefix}")

    @registrar.on_command("查看配置")
    async def on_view_config(self, event):
        """查看当前配置"""
        lines = ["📋 当前配置:"]
        for key, value in self.config.items():
            lines.append(f"  {key}: {value}")
        await event.reply("\n".join(lines))

    # ---- 数据查询命令 ----

    @registrar.on_command("统计")
    async def on_stats(self, event):
        """显示统计信息"""
        total = self.data.get("total_messages", 0)
        user_counts = self.data.get("user_counts", {})
        top_users = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        lines = ["📊 消息统计:", f"  总消息数: {total}"]
        if top_users:
            lines.append("  活跃用户 Top 5:")
            for uid, count in top_users:
                lines.append(f"    {uid}: {count} 条")

        await event.reply("\n".join(lines))

    @registrar.on_command("重置统计")
    async def on_reset_stats(self, event):
        """重置统计数据"""
        self.data["total_messages"] = 0
        self.data["user_counts"] = {}
        await event.reply("统计数据已重置 🗑️")
