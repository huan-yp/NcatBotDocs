"""
common/08_dispatch_filter — 分发过滤管理插件

演示功能:
  - DispatchFilterMixin 群级禁用 / 解禁
  - 用户级禁用 / 解禁
  - 命令级精细控制
  - list_filters / clear_filters 查询与批量操作
  - @registrar.on_command() 跨平台命令

本示例不依赖任何平台，可在 QQ / Bilibili / GitHub 上运行。
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event import GroupScoped, Replyable
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("DispatchFilter")


class DispatchFilterPlugin(NcatBotPlugin):
    name = "dispatch_filter_demo"
    version = "1.0.0"
    author = "NcatBot"
    description = "分发过滤示例 — 群级/用户级/命令级禁用与管理命令封装"

    async def on_load(self):
        LOG.info("DispatchFilter 插件已加载")

    # ------------------------------------------------------------------
    # 群级禁用 / 解禁
    # ------------------------------------------------------------------

    @registrar.on_command("禁用插件")
    async def on_block_plugin(self, event, plugin_name: str):
        """在当前群禁用指定插件的全部命令"""
        if not isinstance(event, GroupScoped):
            if isinstance(event, Replyable):
                await event.reply(text="⚠ 此命令仅在群聊中可用")
            return

        rule = self.block_in_group(str(event.group_id), plugin_name)
        if rule:
            await event.reply(text=f"✅ 已在本群禁用插件 [{plugin_name}]")
        else:
            await event.reply(text="❌ 过滤服务不可用，请检查框架配置")

    @registrar.on_command("启用插件")
    async def on_unblock_plugin(self, event, plugin_name: str):
        """在当前群解除对指定插件的禁用"""
        if not isinstance(event, GroupScoped):
            if isinstance(event, Replyable):
                await event.reply(text="⚠ 此命令仅在群聊中可用")
            return

        removed = self.unblock_in_group(str(event.group_id), plugin_name)
        if removed > 0:
            await event.reply(text=f"✅ 已在本群启用插件 [{plugin_name}]（移除 {removed} 条规则）")
        else:
            await event.reply(text=f"ℹ 本群未找到插件 [{plugin_name}] 的禁用规则")

    # ------------------------------------------------------------------
    # 命令级禁用
    # ------------------------------------------------------------------

    @registrar.on_command("禁用命令")
    async def on_block_command(self, event, plugin_name: str, command: str):
        """在当前群禁用指定插件的单条命令"""
        if not isinstance(event, GroupScoped):
            if isinstance(event, Replyable):
                await event.reply(text="⚠ 此命令仅在群聊中可用")
            return

        rule = self.block_in_group(
            str(event.group_id), plugin_name, commands=[command]
        )
        if rule:
            await event.reply(
                text=f"✅ 已在本群禁用 [{plugin_name}] 的命令 [{command}]"
            )
        else:
            await event.reply(text="❌ 过滤服务不可用")

    # ------------------------------------------------------------------
    # 用户级禁用 / 解禁
    # ------------------------------------------------------------------

    @registrar.on_command("屏蔽用户")
    async def on_block_user(self, event, user_id: str, plugin_name: str):
        """对指定用户禁用指定插件"""
        rule = self.block_for_user(user_id, plugin_name)
        if rule:
            if isinstance(event, Replyable):
                await event.reply(
                    text=f"✅ 已对用户 {user_id} 禁用插件 [{plugin_name}]"
                )
        else:
            if isinstance(event, Replyable):
                await event.reply(text="❌ 过滤服务不可用")

    @registrar.on_command("解除屏蔽")
    async def on_unblock_user(self, event, user_id: str, plugin_name: str):
        """解除对指定用户的插件禁用"""
        removed = self.unblock_for_user(user_id, plugin_name)
        if isinstance(event, Replyable):
            if removed > 0:
                await event.reply(
                    text=f"✅ 已解除用户 {user_id} 对插件 [{plugin_name}] 的屏蔽（移除 {removed} 条规则）"
                )
            else:
                await event.reply(
                    text=f"ℹ 未找到用户 {user_id} 对插件 [{plugin_name}] 的屏蔽规则"
                )

    # ------------------------------------------------------------------
    # 查询与批量操作
    # ------------------------------------------------------------------

    @registrar.on_command("过滤列表")
    async def on_list_filters(self, event):
        """列出所有过滤规则"""
        rules = self.list_filters()
        if not rules:
            if isinstance(event, Replyable):
                await event.reply(text="📋 当前没有任何过滤规则")
            return

        lines = ["📋 过滤规则列表:"]
        for i, rule in enumerate(rules, 1):
            cmds = ", ".join(rule.commands) if rule.commands else "全部命令"
            lines.append(
                f"  {i}. [{rule.scope_type}:{rule.scope_id}] "
                f"插件={rule.plugin_name} 命令={cmds}"
            )
        if isinstance(event, Replyable):
            await event.reply(text="\n".join(lines))

    @registrar.on_command("清空过滤")
    async def on_clear_filters(self, event):
        """清除所有过滤规则"""
        removed = self.clear_filters()
        if isinstance(event, Replyable):
            await event.reply(text=f"🗑 已清除 {removed} 条过滤规则")
