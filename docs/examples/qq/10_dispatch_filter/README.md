# 10_dispatch_filter

> 分类：qq

## 文件结构

~~~text
10_dispatch_filter/
├── main.py
└── manifest.toml
~~~

## main.py

~~~python
"""
qq/10_dispatch_filter — 分发过滤（QQ 群管理）

演示功能:
  - DispatchFilterMixin: block_in_group / unblock_in_group 群维度
  - DispatchFilterMixin: block_for_user / unblock_for_user 用户维度
  - DispatchFilterMixin: list_filters / clear_filters 查询与批量操作
  - @registrar.qq.on_group_command() 平台装饰器

框架还提供了内置管理命令作为替代管理方式（需 root 权限）:
  !filter add/remove/list/clear   — 通过聊天管理过滤规则
  !plugins                        — 列出已加载插件
  !indexed                        — 列出已索引但未加载的插件
  !commands                       — 列出已注册的命令

使用方式:
  "禁用插件 <插件名>"             → 在当前群禁用指定插件
  "启用插件 <插件名>"             → 在当前群解除禁用
  "禁用命令 <插件名> <命令>"      → 在当前群禁用某插件的特定命令
  "屏蔽用户 <用户号> <插件名>"    → 对指定用户禁用插件
  "解除屏蔽 <用户号> <插件名>"    → 解除用户级禁用
  "过滤列表"                      → 查看所有过滤规则
  "清空过滤"                      → 清除所有过滤规则
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("DispatchFilter")


class DispatchFilterPlugin(NcatBotPlugin):
    name = "dispatch_filter_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "分发过滤演示 — 按群/用户禁用插件或命令（QQ）"

    async def on_load(self):
        LOG.info("DispatchFilter 插件已加载")

    # ==================== 群维度 ====================

    @registrar.qq.on_group_command("禁用插件")
    async def on_block_plugin(self, event: GroupMessageEvent, target: str):
        """在当前群禁用指定插件的全部命令"""
        group_id = str(event.group_id)
        rule = self.block_in_group(group_id, target)
        if rule:
            await event.reply(
                f"✅ 已在本群禁用 {target}\n"
                f"规则 ID: {rule.rule_id}"
            )
        else:
            await event.reply("⚠️ 分发过滤服务不可用")

    @registrar.qq.on_group_command("启用插件")
    async def on_unblock_plugin(self, event: GroupMessageEvent, target: str):
        """在当前群解除指定插件的禁用"""
        group_id = str(event.group_id)
        count = self.unblock_in_group(group_id, target)
        await event.reply(f"✅ 已在本群启用 {target}（移除 {count} 条规则）")

    @registrar.qq.on_group_command("禁用命令")
    async def on_block_command(
        self, event: GroupMessageEvent, target: str, command: str
    ):
        """在当前群禁用某插件的特定命令"""
        group_id = str(event.group_id)
        rule = self.block_in_group(group_id, target, commands=[command])
        if rule:
            await event.reply(
                f"✅ 已在本群禁用 {target} 的命令 [{command}]\n"
                f"规则 ID: {rule.rule_id}"
            )
        else:
            await event.reply("⚠️ 分发过滤服务不可用")

    # ==================== 用户维度 ====================

    @registrar.qq.on_group_command("屏蔽用户")
    async def on_block_user(
        self, event: GroupMessageEvent, user_id: str, target: str
    ):
        """对指定用户禁用某插件"""
        rule = self.block_for_user(user_id, target)
        if rule:
            await event.reply(
                f"✅ 已对用户 {user_id} 禁用 {target}\n"
                f"规则 ID: {rule.rule_id}"
            )
        else:
            await event.reply("⚠️ 分发过滤服务不可用")

    @registrar.qq.on_group_command("解除屏蔽")
    async def on_unblock_user(
        self, event: GroupMessageEvent, user_id: str, target: str
    ):
        """解除对指定用户的插件禁用"""
        count = self.unblock_for_user(user_id, target)
        await event.reply(f"✅ 已解除用户 {user_id} 对 {target} 的禁用（移除 {count} 条规则）")

    # ==================== 查询与管理 ====================

    @registrar.qq.on_group_command("过滤列表")
    async def on_list_filters(self, event: GroupMessageEvent):
        """列出所有过滤规则"""
        rules = self.list_filters()
        if not rules:
            await event.reply("📋 当前没有过滤规则")
            return

        lines = ["📋 当前过滤规则:"]
        for r in rules:
            cmds = ", ".join(r.commands) if r.commands else "全部"
            lines.append(
                f"  [{r.rule_id}] {r.scope_type}:{r.scope_id} "
                f"→ {r.plugin_name} (命令: {cmds})"
            )
        await event.reply("\n".join(lines))

    @registrar.qq.on_group_command("清空过滤")
    async def on_clear_filters(self, event: GroupMessageEvent):
        """清除所有过滤规则"""
        count = self.clear_filters()
        await event.reply(f"🗑️ 已清除 {count} 条过滤规则")
~~~

## manifest.toml

~~~toml
name = "dispatch_filter_qq"
version = "1.0.0"
main = "main.py"
entry_class = "DispatchFilterPlugin"
author = "NcatBot"
description = "分发过滤演示 — 按群/用户禁用插件或命令（QQ）"
~~~
