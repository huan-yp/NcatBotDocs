"""
common/04_rbac — 权限管理系统（跨平台）

演示功能:
  - RBACMixin: add_permission / add_role / check_permission
  - self.rbac: assign_role / grant / revoke
  - @registrar.on_command() 跨平台命令
  - 权限检查保护命令

本示例不依赖任何平台。
使用方式:
  "管理命令"       → 仅 admin 角色用户可执行
  "查权限"         → 查看自己是否有 admin 权限
  "权限信息"       → 查看 RBAC 系统配置
"""

from ncatbot.core import registrar
from ncatbot.event import HasSender
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("RBAC")


class RBACPlugin(NcatBotPlugin):
    name = "rbac"
    version = "1.0.0"
    author = "NcatBot"
    description = "权限管理系统演示（跨平台）"

    async def on_load(self):
        self.add_permission("rbac.admin")
        self.add_permission("rbac.user")

        self.add_role("rbac_admin", exist_ok=True)
        self.add_role("rbac_user", exist_ok=True)

        if self.rbac:
            self.rbac.grant("role", "rbac_admin", "rbac.admin")
            self.rbac.grant("role", "rbac_admin", "rbac.user")
            self.rbac.grant("role", "rbac_user", "rbac.user")

        LOG.info("RBAC 插件已加载，权限体系已初始化")

    @registrar.on_command("管理命令")
    async def on_admin_cmd(self, event):
        """仅 admin 角色可执行"""
        uid = str(event.user_id) if isinstance(event, HasSender) else "unknown"
        if self.check_permission(uid, "rbac.admin"):
            await event.reply("🔑 管理命令执行成功！你拥有 admin 权限。")
        else:
            await event.reply("🚫 你没有执行此命令的权限（需要 rbac.admin）")

    @registrar.on_command("查权限")
    async def on_check_perm(self, event):
        """查看自己的权限"""
        uid = str(event.user_id) if isinstance(event, HasSender) else "unknown"
        has_admin = self.check_permission(uid, "rbac.admin")
        has_user = self.check_permission(uid, "rbac.user")
        is_admin_role = self.user_has_role(uid, "rbac_admin")
        is_user_role = self.user_has_role(uid, "rbac_user")

        lines = [
            "👤 你的权限状态:",
            f"  角色 rbac_admin: {'✅' if is_admin_role else '❌'}",
            f"  角色 rbac_user: {'✅' if is_user_role else '❌'}",
            f"  权限 rbac.admin: {'✅' if has_admin else '❌'}",
            f"  权限 rbac.user: {'✅' if has_user else '❌'}",
        ]
        await event.reply("\n".join(lines))

    @registrar.on_command("权限信息")
    async def on_rbac_info(self, event):
        """查看 RBAC 系统配置信息"""
        await event.reply(
            "📋 RBAC 配置:\n"
            "  权限: rbac.admin, rbac.user\n"
            "  角色: rbac_admin (拥有 admin+user), rbac_user (拥有 user)\n"
            "  授权需通过平台专用命令（如 QQ 的 @用户 授权）"
        )
