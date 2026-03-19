"""
qq/05_notice_and_request — QQ 通知与请求事件处理

演示功能:
  - registrar.qq.on_group_increase(): 群成员增加 → 自动欢迎
  - registrar.qq.on_group_decrease(): 群成员减少 → 记录
  - registrar.qq.on_poke(): 戳一戳 → 回戳
  - registrar.qq.on_friend_request(): 好友请求 → 自动通过
  - registrar.qq.on_group_request(): 群请求 → 记录
  - registrar.on("notice.group_recall"): 消息撤回 → 记录

使用方式: 将本文件夹复制到 plugins/ 目录即可，事件自动触发。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import (
    GroupIncreaseEvent,
    NoticeEvent,
    FriendRequestEvent,
    GroupRequestEvent,
)
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import MessageArray
from ncatbot.utils import get_log

LOG = get_log("NoticeAndRequest")


class NoticeAndRequestPlugin(NcatBotPlugin):
    name = "notice_and_request_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 通知与请求事件处理演示"

    async def on_load(self):
        LOG.info("NoticeAndRequest 插件已加载")

    # ==================== 通知事件 ====================

    @registrar.qq.on_group_increase()
    async def on_group_increase(self, event: GroupIncreaseEvent):
        """群成员增加 → 发送欢迎消息"""
        msg = MessageArray()
        msg.add_at(event.user_id)
        msg.add_text(" 欢迎加入本群！请仔细阅读群规 📜")
        await self.api.qq.post_group_array_msg(event.group_id, msg)
        LOG.info("欢迎新成员 %s 加入群 %s", event.user_id, event.group_id)

    @registrar.qq.on_group_decrease()
    async def on_group_decrease(self, event: NoticeEvent):
        """群成员减少 → 记录日志"""
        sub_type = getattr(event, "sub_type", "unknown")
        LOG.info(
            "成员 %s 离开了群 %s (类型: %s)", event.user_id, event.group_id, sub_type
        )
        if event.group_id:
            await self.api.qq.post_group_msg(
                event.group_id, text=f"成员 {event.user_id} 已离开群聊 👋"
            )

    @registrar.on("notice.group_recall", platform="qq")
    async def on_group_recall(self, event: NoticeEvent):
        """消息撤回 → 记录撤回信息"""
        operator_id = getattr(event.data, "operator_id", None)
        message_id = getattr(event.data, "message_id", None)
        LOG.info(
            "群 %s 中用户 %s 的消息 %s 被 %s 撤回",
            event.group_id,
            event.user_id,
            message_id,
            operator_id,
        )
        if event.group_id:
            await self.api.qq.post_group_msg(
                event.group_id,
                text=f"有人撤回了一条消息 👀 (操作者: {operator_id})",
            )

    @registrar.qq.on_poke()
    async def on_poke(self, event: NoticeEvent):
        """戳一戳 → 回戳"""
        target_id = getattr(event.data, "target_id", None)
        if str(target_id) == str(event.self_id) and event.group_id and event.user_id:
            await self.api.qq.send_poke(event.group_id, event.user_id)
            LOG.info("被 %s 戳了，已回戳", event.user_id)

    # ==================== 请求事件 ====================

    @registrar.qq.on_friend_request()
    async def on_friend_request(self, event: FriendRequestEvent):
        """好友添加请求 → 自动通过"""
        await event.approve()
        LOG.info("自动通过好友请求: %s (验证信息: %s)", event.user_id, event.comment)

    @registrar.qq.on_group_request()
    async def on_group_request(self, event: GroupRequestEvent):
        """群邀请/申请 → 记录日志"""
        LOG.info(
            "群请求: 用户 %s, 类型: %s, 验证: %s",
            event.user_id,
            event.sub_type,
            event.comment,
        )
