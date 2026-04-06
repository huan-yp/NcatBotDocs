# 05_notice_and_request

> 分类：qq

## 文件结构

~~~text
05_notice_and_request/
├── main.py
└── manifest.toml
~~~

## main.py

~~~python
"""
qq/05_notice_and_request — QQ 通知与请求事件处理

演示功能:
  - registrar.qq.on_group_increase(): 群成员增加 → 自动欢迎
  - registrar.qq.on_group_decrease(): 群成员减少 → 记录
  - registrar.qq.on_group_recall(): 消息撤回 → 记录
  - registrar.qq.on_group_admin(): 管理员变动 → 记录
  - registrar.qq.on_group_ban(): 禁言 → 记录
  - registrar.qq.on_friend_add(): 好友已添加 → 记录
  - registrar.qq.on_poke(): 戳一戳 → 回戳
  - registrar.qq.on_group_msg_emoji_like(): 群消息表情回应 → 记录
  - registrar.qq.on("notice.group_upload"): 群文件上传 → 记录
  - registrar.qq.on("notice.friend_recall"): 好友撤回 → 记录
  - registrar.qq.on("notice.notify"): 运气王/群荣誉 → 记录
  - registrar.qq.on_friend_request(): 好友请求 → 自动通过
  - registrar.qq.on_group_request(): 群请求 → 记录

使用方式: 将本文件夹复制到 plugins/ 目录即可，事件自动触发。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import (
    GroupIncreaseEvent,
    GroupDecreaseEvent,
    GroupRecallEvent,
    GroupAdminEvent,
    GroupBanEvent,
    GroupUploadEvent,
    FriendAddEvent,
    FriendRecallEvent,
    PokeNotifyEvent,
    LuckyKingNotifyEvent,
    HonorNotifyEvent,
    FriendRequestEvent,
    GroupRequestEvent,
    GroupMsgEmojiLikeEvent,
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
    async def on_group_decrease(self, event: GroupDecreaseEvent):
        """群成员减少 → 记录日志"""
        LOG.info(
            "成员 %s 离开了群 %s (类型: %s)", event.user_id, event.group_id, event.sub_type
        )
        if event.group_id:
            await self.api.qq.post_group_msg(
                event.group_id, text=f"成员 {event.user_id} 已离开群聊 👋"
            )

    @registrar.qq.on_group_recall()
    async def on_group_recall(self, event: GroupRecallEvent):
        """消息撤回 → 记录撤回信息"""
        LOG.info(
            "群 %s 中用户 %s 的消息 %s 被 %s 撤回",
            event.group_id,
            event.user_id,
            event.message_id,
            event.operator_id,
        )
        if event.group_id:
            await self.api.qq.post_group_msg(
                event.group_id,
                text=f"有人撤回了一条消息 👀 (操作者: {event.operator_id})",
            )

    @registrar.qq.on_poke()
    async def on_poke(self, event: PokeNotifyEvent):
        """戳一戳 → 回戳"""
        if str(event.target_id) == str(event.self_id) and event.group_id and event.user_id:
            await self.api.qq.send_poke(event.group_id, event.user_id)
            LOG.info("被 %s 戳了，已回戳", event.user_id)

    @registrar.qq.on_group_msg_emoji_like()
    async def on_group_msg_emoji_like(self, event: GroupMsgEmojiLikeEvent):
        """群消息点赞 → 记录日志"""
        LOG.info(
            "群 %s 中用户 %s 对消息 %s 贴了表情点赞 (表情细节: %s)",
            event.group_id,
            event.user_id,
            event.message_id,
            event.likes,
        )

    @registrar.qq.on_group_admin()
    async def on_group_admin(self, event: GroupAdminEvent):
        """管理员变动 → 记录日志"""
        LOG.info(
            "群 %s 管理员变动: 用户 %s, 类型: %s",
            event.group_id,
            event.user_id,
            event.sub_type,
        )

    @registrar.qq.on_group_ban()
    async def on_group_ban(self, event: GroupBanEvent):
        """禁言事件 → 记录日志"""
        LOG.info(
            "群 %s 禁言事件: 用户 %s 被 %s %s, 时长: %s 秒",
            event.group_id,
            event.user_id,
            event.operator_id,
            event.sub_type,
            event.duration,
        )

    @registrar.qq.on_friend_add()
    async def on_friend_add(self, event: FriendAddEvent):
        """好友已添加 → 记录日志"""
        LOG.info("新好友已添加: %s", event.user_id)

    @registrar.qq.on("notice.group_upload")
    async def on_group_upload(self, event: GroupUploadEvent):
        """群文件上传 → 记录日志"""
        LOG.info(
            "群 %s 用户 %s 上传了文件: %s (大小: %s)",
            event.group_id,
            event.user_id,
            event.file.name,
            event.file.size,
        )

    @registrar.qq.on("notice.friend_recall")
    async def on_friend_recall(self, event: FriendRecallEvent):
        """好友消息撤回 → 记录日志"""
        LOG.info("好友 %s 撤回了消息 %s", event.user_id, event.message_id)

    @registrar.qq.on("notice.notify")
    async def on_lucky_king(self, event: LuckyKingNotifyEvent):
        """运气王 → 记录日志（通过 sub_type 手动过滤）"""
        if event.sub_type != "lucky_king":
            return
        LOG.info(
            "群 %s 运气王: 用户 %s, 运气王: %s",
            event.group_id,
            event.user_id,
            event.target_id,
        )

    @registrar.qq.on("notice.notify")
    async def on_honor(self, event: HonorNotifyEvent):
        """群荣誉变更 → 记录日志（通过 sub_type 手动过滤）"""
        if event.sub_type != "honor":
            return
        LOG.info(
            "群 %s 荣誉变更: 用户 %s, 荣誉类型: %s",
            event.group_id,
            event.user_id,
            event.honor_type,
        )

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
~~~

## manifest.toml

~~~toml
name = "notice_and_request_qq"
version = "1.0.0"
main = "main.py"
entry_class = "NoticeAndRequestPlugin"
author = "NcatBot"
description = "QQ 通知与请求事件处理演示"
~~~

