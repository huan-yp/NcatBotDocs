"""
common/09_plugin_management — 插件管理与生命周期演示

演示功能:
  - 通过 self._plugin_loader 动态查询/重载插件
  - on_load / on_close 生命周期回调
  - self.data 状态持久化（重载计数、时间戳）
  - @registrar.on_command() 跨平台命令

本示例不依赖任何平台，可在 QQ / Bilibili / GitHub 上运行。
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

import time

from ncatbot.core import registrar
from ncatbot.event import Replyable
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("PluginManagement")


class PluginManagementPlugin(NcatBotPlugin):
    name = "plugin_management_demo"
    version = "1.0.0"
    author = "NcatBot"
    description = "插件管理示例 — 动态加载/卸载、生命周期回调与状态持久化"

    async def on_load(self):
        # 持久化数据初始化
        self.data.setdefault("reload_count", 0)
        self.data["reload_count"] += 1
        self.data["last_load_time"] = time.time()

        LOG.info(
            "PluginManagement 已加载（第 %d 次）",
            self.data["reload_count"],
        )

    async def on_close(self):
        LOG.info("PluginManagement 正在卸载，累计加载 %d 次", self.data["reload_count"])

    # ------------------------------------------------------------------
    # 插件列表
    # ------------------------------------------------------------------

    @registrar.on_command("插件列表")
    async def on_list_plugins(self, event):
        """列出所有已加载插件及索引中的插件"""
        loader = self._plugin_loader

        loaded = loader.list_plugins()
        indexed = loader.list_indexed()

        lines = ["📦 插件列表:"]
        lines.append(f"  已加载: {len(loaded)} 个")
        lines.append(f"  已索引: {len(indexed)} 个")
        lines.append("")

        for name in sorted(indexed.keys()):
            manifest = indexed[name]
            status = "✅ 已加载" if name in loaded else "⬚ 未加载"
            lines.append(f"  {status} {name} v{manifest.version}")

        if isinstance(event, Replyable):
            await event.reply(text="\n".join(lines))

    # ------------------------------------------------------------------
    # 重载插件
    # ------------------------------------------------------------------

    @registrar.on_command("重载插件")
    async def on_reload_plugin(self, event, name: str):
        """重载指定插件（卸载 → 重索引 → 加载）"""
        loader = self._plugin_loader

        # 检查插件是否已索引
        indexed = loader.list_indexed()
        if name not in indexed:
            if isinstance(event, Replyable):
                await event.reply(text=f"❌ 未找到插件 [{name}]，请检查插件名")
            return

        if isinstance(event, Replyable):
            await event.reply(text=f"🔄 正在重载插件 [{name}]...")

        success = await loader.reload_plugin(name)
        if isinstance(event, Replyable):
            if success:
                await event.reply(text=f"✅ 插件 [{name}] 重载成功")
            else:
                await event.reply(text=f"❌ 插件 [{name}] 重载失败，请查看日志")

    # ------------------------------------------------------------------
    # 当前插件状态
    # ------------------------------------------------------------------

    @registrar.on_command("插件状态")
    async def on_plugin_status(self, event):
        """显示当前插件自身的运行状态"""
        reload_count = self.data.get("reload_count", 0)
        last_load = self.data.get("last_load_time", 0)
        uptime = time.time() - last_load if last_load else 0

        # 格式化运行时长
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        lines = [
            "📊 插件状态:",
            f"  名称: {self.name}",
            f"  版本: {self.version}",
            f"  累计加载次数: {reload_count}",
            f"  本次运行时长: {uptime_str}",
        ]

        if isinstance(event, Replyable):
            await event.reply(text="\n".join(lines))
