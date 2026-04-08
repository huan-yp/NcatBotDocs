# 09_group_admin

> 分类：qq

## 这个示例教什么

NcatBot 中如何使用 QQ 群管理 API 构建一个**群管小助手**。通过 RBAC 权限守卫 + 管理 API 的组合，实现踢人、禁言、全体禁言、设管理员、改名片、设头衔、发公告、设精华等常见群管操作。

## 你将学到

- `set_group_kick` — 踢出群成员
- `set_group_ban` — 禁言 / 解禁（`duration=0` 解禁）
- `set_group_whole_ban` — 全体禁言 / 解除
- `set_group_admin` — 设置 / 取消管理员
- `set_group_card` — 修改群名片
- `set_group_special_title` — 设置专属头衔
- `send_group_notice` — 发送群公告
- `set_essence_msg` — 设为精华消息（需 Reply 参数绑定获取 message_id）
- RBAC 权限守卫 — 管理命令前置权限检查模式

## 前置知识

- [01_event_registration](../01_event_registration/) — 事件注册基础
- [02_command_binding](../02_command_binding/) — 命令参数绑定（At / Reply / Optional）
- [common/04_rbac](../../common/04_rbac/) — RBAC 权限管理系统

## 目录结构

~~~text
09_group_admin/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
└── README.md
~~~

## 完整代码

~~~python
"""
qq/09_group_admin — QQ 群管理小助手

演示功能:
  - set_group_kick           踢人
  - set_group_ban            禁言 / 解禁
  - set_group_whole_ban      全体禁言 / 解除
  - set_group_admin          设置 / 取消管理员
  - set_group_card           修改群名片
  - set_group_special_title  设置专属头衔
  - send_group_notice        发送群公告
  - set_essence_msg          设为精华消息
  - RBAC 权限守卫            管理命令前置权限检查

提及但不展开:
  - set_friend_add_request / set_group_add_request — 已在 05_notice_and_request 演示
  - delete_essence_msg / 删除公告 / 批量踢人 / 群头像 / 群待办等扩展接口
  - RBAC 系统详解 — 见 common/04_rbac

边界:
  本示例聚焦群管理 API 的实际使用，RBAC 仅作权限守卫，不深入讲解。

前置知识: qq/01_event_registration, qq/02_command_binding, common/04_rbac
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from typing import Optional

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import At, Reply
from ncatbot.utils import get_log

LOG = get_log("GroupAdmin")


class GroupAdminPlugin(NcatBotPlugin):
    name = "group_admin_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 群管理小助手"

    # ================================================================
    # 初始化 — 注册 RBAC 权限和角色
    # ================================================================

    async def on_load(self):
        """初始化权限体系：注册权限节点和角色"""
        self.add_permission("group_admin.manage")

        self.add_role("group_admin", exist_ok=True)

        if self.rbac:
            self.rbac.grant("role", "group_admin", "group_admin.manage")

        LOG.info("群管插件已加载，权限体系已初始化")

    # ================================================================
    # 权限检查辅助
    # ================================================================

    def _check_admin(self, user_id: int) -> bool:
        """检查用户是否拥有群管权限"""
        return self.check_permission(str(user_id), "group_admin.manage")

    # ================================================================
    # 1. 踢人 — set_group_kick
    # ================================================================
    # 用户发送: 踢 @某人
    # At 参数绑定自动提取被 @ 用户，调用管理 API 踢出。

    @registrar.qq.on_group_command("踢")
    async def on_kick(self, event: GroupMessageEvent, target: At):
        """踢出群成员 — '踢 @某人'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_kick(event.group_id, target.user_id)
            await event.reply(f"✅ 已将 {target.user_id} 踢出群聊")
        except Exception as e:
            await event.reply(f"❌ 踢人失败: {e}")

    # ================================================================
    # 2. 禁言 — set_group_ban
    # ================================================================
    # 用户发送: 禁言 @某人 60    → 禁言 60 秒
    # 用户发送: 禁言 @某人       → 使用默认 60 秒
    # Optional[int] 默认值实现可选时长。

    @registrar.qq.on_group_command("禁言")
    async def on_ban(self, event: GroupMessageEvent, target: At, duration: int = 60):
        """禁言群成员 — '禁言 @某人 [秒数]'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_ban(
                event.group_id, target.user_id, duration=duration
            )
            await event.reply(f"✅ 已禁言 {target.user_id}，时长 {duration} 秒")
        except Exception as e:
            await event.reply(f"❌ 禁言失败: {e}")

    # ================================================================
    # 3. 解禁 — set_group_ban(duration=0)
    # ================================================================
    # duration=0 即解除禁言。

    @registrar.qq.on_group_command("解禁")
    async def on_unban(self, event: GroupMessageEvent, target: At):
        """解除禁言 — '解禁 @某人'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_ban(
                event.group_id, target.user_id, duration=0
            )
            await event.reply(f"✅ 已解除 {target.user_id} 的禁言")
        except Exception as e:
            await event.reply(f"❌ 解禁失败: {e}")

    # ================================================================
    # 4. 全体禁言 / 解除全体禁言 — set_group_whole_ban
    # ================================================================

    @registrar.qq.on_group_command("全体禁言")
    async def on_whole_ban(self, event: GroupMessageEvent):
        """开启全体禁言 — '全体禁言'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_whole_ban(event.group_id, enable=True)
            await event.reply("✅ 已开启全体禁言")
        except Exception as e:
            await event.reply(f"❌ 全体禁言失败: {e}")

    @registrar.qq.on_group_command("解除全体禁言")
    async def on_whole_unban(self, event: GroupMessageEvent):
        """解除全体禁言 — '解除全体禁言'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_whole_ban(event.group_id, enable=False)
            await event.reply("✅ 已解除全体禁言")
        except Exception as e:
            await event.reply(f"❌ 解除全体禁言失败: {e}")

    # ================================================================
    # 5. 设置/取消管理员 — set_group_admin
    # ================================================================

    @registrar.qq.on_group_command("设管理")
    async def on_set_admin(self, event: GroupMessageEvent, target: At):
        """设置管理员 — '设管理 @某人'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_admin(
                event.group_id, target.user_id, enable=True
            )
            await event.reply(f"✅ 已将 {target.user_id} 设为管理员")
        except Exception as e:
            await event.reply(f"❌ 设置管理员失败: {e}")

    @registrar.qq.on_group_command("取消管理")
    async def on_unset_admin(self, event: GroupMessageEvent, target: At):
        """取消管理员 — '取消管理 @某人'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_admin(
                event.group_id, target.user_id, enable=False
            )
            await event.reply(f"✅ 已取消 {target.user_id} 的管理员")
        except Exception as e:
            await event.reply(f"❌ 取消管理员失败: {e}")

    # ================================================================
    # 6. 修改群名片 — set_group_card
    # ================================================================
    # 用户发送: 改名片 @某人 新名片内容

    @registrar.qq.on_group_command("改名片")
    async def on_set_card(self, event: GroupMessageEvent, target: At, card: str):
        """修改群名片 — '改名片 @某人 新名片'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_card(
                event.group_id, target.user_id, card=card
            )
            await event.reply(f"✅ 已将 {target.user_id} 的名片修改为「{card}」")
        except Exception as e:
            await event.reply(f"❌ 修改名片失败: {e}")

    # ================================================================
    # 7. 设置专属头衔 — set_group_special_title
    # ================================================================
    # 用户发送: 头衔 @某人 称号文本

    @registrar.qq.on_group_command("头衔")
    async def on_set_title(self, event: GroupMessageEvent, target: At, title: str):
        """设置专属头衔 — '头衔 @某人 称号'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_group_special_title(
                event.group_id, target.user_id, special_title=title
            )
            await event.reply(f"✅ 已为 {target.user_id} 设置头衔「{title}」")
        except Exception as e:
            await event.reply(f"❌ 设置头衔失败: {e}")

    # ================================================================
    # 8. 发送群公告 — send_group_notice
    # ================================================================
    # 用户发送: 发公告 公告内容文本

    @registrar.qq.on_group_command("发公告")
    async def on_send_notice(self, event: GroupMessageEvent, content: str):
        """发送群公告 — '发公告 内容'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.send_group_notice(event.group_id, content)
            await event.reply("✅ 群公告已发送")
        except Exception as e:
            await event.reply(f"❌ 发送公告失败: {e}")

    # ================================================================
    # 9. 设为精华消息 — set_essence_msg
    # ================================================================
    # 用户引用一条消息并发送: 设精华
    # Reply 参数绑定自动提取被引用消息的 ID。

    @registrar.qq.on_group_command("设精华")
    async def on_set_essence(self, event: GroupMessageEvent, ref: Reply):
        """设为精华消息 — 引用消息后发送 '设精华'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        try:
            await self.api.qq.manage.set_essence_msg(ref.id)
            await event.reply("✅ 已设为精华消息")
        except Exception as e:
            await event.reply(f"❌ 设为精华失败: {e}")

    # ================================================================
    # 10. 授管理 — 通过 RBAC 授予群管角色
    # ================================================================
    # 用户发送: 授管理 @某人
    # 将目标用户添加到 group_admin 角色，使其拥有群管权限。

    @registrar.qq.on_group_command("授管理")
    async def on_grant_admin(self, event: GroupMessageEvent, target: At):
        """授予群管 RBAC 角色 — '授管理 @某人'"""
        if not self._check_admin(event.user_id):
            await event.reply("🚫 你没有群管权限")
            return

        if not self.rbac:
            await event.reply("❌ RBAC 系统未启用")
            return

        self.rbac.assign_role(str(target.user_id), "group_admin")
        await event.reply(f"✅ 已授予 {target.user_id} 群管权限")

    # ================================================================
    # 提及但不展开的 API
    # ================================================================
    # - set_friend_add_request(flag, approve, remark)
    #   处理好友添加请求。已在 qq/05_notice_and_request 中通过
    #   event.approve() 演示，此处不再重复。
    #
    # - set_group_add_request(flag, sub_type, approve, reason)
    #   处理加群请求/邀请。同样可通过 event.approve() / event.reject()
    #   快捷处理，详见 qq/05_notice_and_request。
    #
    # 更多扩展 API（仅列举，详见 API Reference）：
    # - delete_essence_msg(message_id)      — 删除精华消息
    # - _send_group_notice + delete 参数    — 删除群公告
    # - set_group_portrait(group_id, file)  — 设置群头像
    # - set_group_name(group_id, name)      — 修改群名
    # - 批量踢人、群待办等扩展接口
~~~

## 关键代码讲解

### RBAC 权限守卫模式

每个管理命令前都调用 `_check_admin` 检查权限，这是一个常见的**权限守卫**模式：

~~~python
def _check_admin(self, user_id: int) -> bool:
    return self.check_permission(str(user_id), "group_admin.manage")

@registrar.qq.on_group_command("踢")
async def on_kick(self, event: GroupMessageEvent, target: At):
    if not self._check_admin(event.user_id):
        await event.reply("🚫 你没有群管权限")
        return
    # ... 执行管理操作
~~~

**权限初始化**在 `on_load` 中完成：

~~~python
async def on_load(self):
    self.add_permission("group_admin.manage")       # 注册权限节点
    self.add_role("group_admin", exist_ok=True)      # 注册角色
    if self.rbac:
        self.rbac.grant("role", "group_admin", "group_admin.manage")  # 角色 ← 权限
~~~

**授权用户**通过 `assign_role` 完成：

~~~python
self.rbac.assign_role(str(target.user_id), "group_admin")
~~~

RBAC 系统的完整用法详见 [common/04_rbac](../../common/04_rbac/)。

### 管理 API 速查表

所有管理 API 都在 `self.api.qq.manage` 命名空间下：

| API | 说明 | 关键参数 |
|---|---|---|
| `set_group_kick(group_id, user_id)` | 踢出群成员 | `reject_add_request=False` 拒绝再加群 |
| `set_group_ban(group_id, user_id, duration)` | 禁言 | `duration` 秒，`0` = 解禁 |
| `set_group_whole_ban(group_id, enable)` | 全体禁言 | `enable=True` 开启，`False` 关闭 |
| `set_group_admin(group_id, user_id, enable)` | 设置管理员 | `enable=True` 设置，`False` 取消 |
| `set_group_card(group_id, user_id, card)` | 修改群名片 | `card=""` 清空名片 |
| `set_group_special_title(group_id, user_id, special_title)` | 专属头衔 | 仅群主可设 |
| `send_group_notice(group_id, content)` | 发送群公告 | `image=""` 可附带图片 |
| `set_essence_msg(message_id)` | 设为精华 | 需通过 Reply 绑定获取 message_id |
| `delete_essence_msg(message_id)` | 删除精华 | — |

### 参数绑定技巧回顾

本示例综合运用了 [02_command_binding](../02_command_binding/) 中介绍的绑定方式：

~~~python
# At 绑定 — 从消息中提取 @某人
async def on_kick(self, event, target: At):
    target.user_id  # 被 @ 用户的 ID

# At + Optional[int] 组合 — 可选数字参数
async def on_ban(self, event, target: At, duration: int = 60):
    # duration 可省略，默认 60

# Reply 绑定 — 从引用消息中提取消息 ID
async def on_set_essence(self, event, ref: Reply):
    ref.id  # 被引用消息的 ID
~~~

## 运行方式

1. 将 `09_group_admin/` 文件夹复制到 `plugins/` 目录
2. 启动 Bot
3. 先用「授管理 @某人」给自己授权（或在 `data/rbac.json` 中手动配置）
4. 在群聊中发送以下命令测试：
   - **踢 @某人** — 踢出群成员
   - **禁言 @某人 60** — 禁言 60 秒
   - **解禁 @某人** — 解除禁言
   - **全体禁言** / **解除全体禁言**
   - **设管理 @某人** / **取消管理 @某人**
   - **改名片 @某人 新名片** — 修改群名片
   - **头衔 @某人 称号** — 设置专属头衔
   - **发公告 内容** — 发送群公告
   - **设精华**（引用消息）— 设为精华消息
   - **授管理 @某人** — 授予 RBAC 群管角色

## 延伸阅读

- [common/04_rbac](../../common/04_rbac/) — RBAC 权限管理系统完整教程
- [05_notice_and_request](../05_notice_and_request/) — 好友/群请求处理（`event.approve()`）
- 更多管理 API（删除公告、删除精华、群头像、群名修改、群待办等）详见 API Reference
