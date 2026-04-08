"""
qq/05_notice_and_request — QQ 通知与请求事件处理演示

演示功能:
  - @registrar.qq.on_group_increase()       群成员增加 → 欢迎消息
  - @registrar.qq.on_group_decrease()       群成员减少 → 记录日志
  - @registrar.qq.on_group_recall()         消息撤回 → 记录日志
  - @registrar.qq.on_poke()                 戳一戳 → 回戳
  - @registrar.qq.on_group_msg_emoji_like() 表情回应 → 记录日志
  - @registrar.qq.on_friend_request()       好友请求 → 自动同意
  - @registrar.qq.on_group_request()        群请求 → 记录日志
  - @registrar.qq.on_notice()               通用兜底 → 记录日志

本示例聚焦最常用的 Notice/Request 细分处理器。
不展开的事件类型在代码末尾注释中提及。

前置知识: qq/01_event_registration（on_notice / on_request 的注册方式）
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import (
    FriendRequestEvent,
    GroupDecreaseEvent,
    GroupIncreaseEvent,
    GroupMsgEmojiLikeEvent,
    GroupRecallEvent,
    GroupRequestEvent,
    NoticeEvent,
    PokeNotifyEvent,
)
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("NoticeAndRequest")


class NoticeAndRequestPlugin(NcatBotPlugin):
    name = "notice_and_request_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 通知与请求事件处理演示"

    # ================================================================
    # 1. on_group_increase — 群成员增加
    # ================================================================

    @registrar.qq.on_group_increase()
    async def on_member_join(self, event: GroupIncreaseEvent):
        """新成员入群时发送欢迎消息"""
        LOG.info(
            "群 %s 新成员加入: user=%s, operator=%s, sub_type=%s",
            event.group_id, event.user_id, event.operator_id, event.sub_type,
        )
        await self.api.qq.send_group_text(
            event.group_id, f"欢迎新成员 {event.user_id} 加入本群！"
        )

    # ================================================================
    # 2. on_group_decrease — 群成员减少
    # ================================================================

    @registrar.qq.on_group_decrease()
    async def on_member_leave(self, event: GroupDecreaseEvent):
        """成员退群或被踢时记录日志"""
        # sub_type: "leave"（主动退群）| "kick"（被踢）| "kick_me"（Bot 被踢）
        LOG.info(
            "群 %s 成员减少: user=%s, operator=%s, sub_type=%s",
            event.group_id, event.user_id, event.operator_id, event.sub_type,
        )

    # ================================================================
    # 3. on_group_recall — 群消息撤回
    # ================================================================

    @registrar.qq.on_group_recall()
    async def on_recall(self, event: GroupRecallEvent):
        """消息被撤回时记录日志"""
        LOG.info(
            "群 %s 消息撤回: message_id=%s, user=%s, operator=%s",
            event.group_id, event.message_id, event.user_id, event.operator_id,
        )

    # ================================================================
    # 4. on_poke — 戳一戳
    # ================================================================

    @registrar.qq.on_poke()
    async def on_poke(self, event: PokeNotifyEvent):
        """被戳时回戳对方"""
        LOG.info(
            "戳一戳: user=%s → target=%s (group=%s)",
            event.user_id, event.target_id, event.group_id,
        )
        # 只在 Bot 被戳时回戳
        if event.target_id == event.self_id and event.group_id:
            await self.api.qq.send_poke(event.group_id, event.user_id)

    # ================================================================
    # 5. on_group_msg_emoji_like — 群消息表情回应
    # ================================================================

    @registrar.qq.on_group_msg_emoji_like()
    async def on_emoji_like(self, event: GroupMsgEmojiLikeEvent):
        """收到表情回应时记录日志"""
        LOG.info(
            "群 %s 表情回应: message_id=%s, user=%s, likes=%s",
            event.group_id, event.message_id, event.user_id, event.likes,
        )

    # ================================================================
    # 6. on_friend_request — 好友请求
    # ================================================================

    @registrar.qq.on_friend_request()
    async def on_friend_request(self, event: FriendRequestEvent):
        """收到好友请求时自动同意（示例用，生产环境请按需过滤）"""
        LOG.info(
            "好友请求: user=%s, comment=%s",
            event.user_id, event.comment,
        )
        await event.approve()

    # ================================================================
    # 7. on_group_request — 群请求（加群 / 邀请）
    # ================================================================

    @registrar.qq.on_group_request()
    async def on_group_request(self, event: GroupRequestEvent):
        """收到加群申请或邀请时记录日志（不自动通过）"""
        # sub_type: "add"（主动申请）| "invite"（被邀请）
        LOG.info(
            "群 %s 请求: user=%s, sub_type=%s, comment=%s",
            event.group_id, event.user_id, event.sub_type, event.comment,
        )
        # 如需自动通过，可调用: await event.approve()
        # 如需拒绝，可调用:     await event.reject(reason="理由")

    # ================================================================
    # 8. on_notice — 通用兜底
    # ================================================================

    @registrar.qq.on_notice()
    async def on_any_notice(self, event: NoticeEvent):
        """兜底：捕获所有未被上面细分处理器匹配的通知事件"""
        LOG.info(
            "未处理的通知事件: notice_type=%s, group=%s, user=%s",
            event.notice_type, event.group_id, event.user_id,
        )

    # ================================================================
    # 提及但不展开的事件类型
    # ================================================================
    # - @registrar.qq.on_group_admin()   管理员变动（设置/取消管理员）
    # - @registrar.qq.on_group_ban()     群禁言（禁言/解除禁言）
    # - @registrar.qq.on_friend_add()    好友已添加（添加成功后的通知）
    # - @registrar.qq.on_message_sent()  Bot 自身发出的消息
    # 这些事件的用法与上面的模式完全一致：装饰器 + 对应 Event 类型注解。
