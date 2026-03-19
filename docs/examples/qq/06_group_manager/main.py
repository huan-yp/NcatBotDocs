"""
qq/06_group_manager — QQ 群管理机器人

演示功能:
  - @registrar.qq.on_group_command() + At/int 参数绑定: 踢人/禁言/改名片
  - RBAC 权限控制: 仅管理员可执行管理命令
  - @registrar.qq.on_group_increase(): 新成员入群自动欢迎
  - ConfigMixin: 可配置欢迎语模板

使用方式:
  "踢 @xxx"         → 踢出用户（需管理员权限）
  "禁言 @xxx 60"    → 禁言 60 秒
  "解禁 @xxx"       → 解除禁言
  "全体禁言"        → 开启全体禁言
  "解除全体禁言"    → 关闭全体禁言
  "改名片 @xxx 新名" → 修改群名片
  "设置欢迎语 xxx"   → 修改欢迎消息模板
  "授管理 @xxx"      → 授予管理权限
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent, GroupIncreaseEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import At, MessageArray
from ncatbot.utils import get_log

LOG = get_log("GroupManager")
DEFAULT_WELCOME = "欢迎 {user} 加入本群！请先阅读群规 📜"


class GroupManagerPlugin(NcatBotPlugin):
    name = "group_manager_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 群管理机器人"

    async def on_load(self):
        self.add_permission("group_manager.admin")
        self.add_role("gm_admin", exist_ok=True)
        if self.rbac:
            self.rbac.grant("role", "gm_admin", "group_manager.admin")

        if not self.get_config("welcome_template"):
            self.set_config("welcome_template", DEFAULT_WELCOME)

        LOG.info("GroupManager 已加载")

    def _is_admin(self, user_id) -> bool:
        return self.check_permission(str(user_id), "group_manager.admin")

    # ==================== 管理命令 ====================

    @registrar.qq.on_group_command("踢")
    async def on_kick(self, event: GroupMessageEvent, target: At = None):
        if not self._is_admin(event.user_id):
            await event.reply("🚫 你没有管理权限")
            return
        if target is None:
            await event.reply("请 @一个用户")
            return
        await self.api.qq.manage.set_group_kick(event.group_id, target.user_id)
        await event.reply(f"已踢出用户 {target.user_id}")

    @registrar.qq.on_group_command("禁言")
    async def on_ban(
        self, event: GroupMessageEvent, target: At = None, duration: int = 60
    ):
        if not self._is_admin(event.user_id):
            await event.reply("🚫 你没有管理权限")
            return
        if target is None:
            await event.reply("请 @一个用户，例如: 禁言 @xxx 60")
            return
        await self.api.qq.manage.set_group_ban(event.group_id, target.user_id, duration)
        await event.reply(f"已禁言 {target.user_id}，{duration} 秒")

    @registrar.qq.on_group_command("解禁")
    async def on_unban(self, event: GroupMessageEvent, target: At = None):
        if not self._is_admin(event.user_id):
            await event.reply("🚫 你没有管理权限")
            return
        if target is None:
            await event.reply("请 @一个用户")
            return
        await self.api.qq.manage.set_group_ban(event.group_id, target.user_id, 0)
        await event.reply(f"已解除 {target.user_id} 的禁言")

    @registrar.qq.on_group_command("全体禁言")
    async def on_mute_all(self, event: GroupMessageEvent):
        if not self._is_admin(event.user_id):
            await event.reply("🚫 你没有管理权限")
            return
        await self.api.qq.manage.set_group_whole_ban(event.group_id, True)
        await event.reply("已开启全体禁言 🔇")

    @registrar.qq.on_group_command("解除全体禁言")
    async def on_unmute_all(self, event: GroupMessageEvent):
        if not self._is_admin(event.user_id):
            await event.reply("🚫 你没有管理权限")
            return
        await self.api.qq.manage.set_group_whole_ban(event.group_id, False)
        await event.reply("已解除全体禁言 🔊")

    @registrar.qq.on_group_command("改名片")
    async def on_set_card(
        self, event: GroupMessageEvent, target: At = None, new_card: str = ""
    ):
        if not self._is_admin(event.user_id):
            await event.reply("🚫 你没有管理权限")
            return
        if target is None:
            await event.reply("请 @一个用户，例如: 改名片 @xxx 新名字")
            return
        await self.api.qq.manage.set_group_card(
            event.group_id, target.user_id, new_card
        )
        await event.reply(f"已将 {target.user_id} 的群名片修改为: {new_card}")

    # ==================== 权限管理 ====================

    @registrar.qq.on_group_command("授管理")
    async def on_grant_admin(self, event: GroupMessageEvent, target: At = None):
        if target is None:
            return
        target_uid = str(target.user_id)
        if self.rbac:
            self.rbac.assign_role("user", target_uid, "gm_admin")
            await event.reply(f"已授予 {target_uid} 群管理权限 ✅")

    # ==================== 欢迎消息 ====================

    @registrar.qq.on_group_command("设置欢迎语")
    async def on_set_welcome(self, event: GroupMessageEvent, template: str):
        self.set_config("welcome_template", template)
        await event.reply(f"欢迎语已更新为: {template}")

    @registrar.qq.on_group_increase()
    async def on_member_join(self, event: GroupIncreaseEvent):
        """新成员入群自动欢迎"""
        template = self.get_config("welcome_template", DEFAULT_WELCOME)
        welcome_text = template.replace("{user}", str(event.user_id))

        msg = MessageArray()
        msg.add_at(event.user_id)
        msg.add_text(f" {welcome_text}")
        await self.api.qq.post_group_array_msg(event.group_id, msg)
