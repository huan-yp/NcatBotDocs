"""
bilibili/02_live_room — Bilibili 直播间全事件处理

演示功能:
  - registrar.bilibili.on_danmu(): 弹幕消息
  - registrar.bilibili.on_superchat(): 醒目留言 (SC)
  - registrar.bilibili.on_gift(): 礼物事件
  - registrar.bilibili.on_guard_buy(): 大航海（舰长/提督/总督）
  - registrar.bilibili.on_interact(): 互动事件（进入/关注/分享）
  - registrar.bilibili.on_like(): 点赞事件
  - HasSender Trait 获取用户信息

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot 连接 Bilibili 直播间。
所有事件自动触发并记录日志。
"""

from ncatbot.core import registrar
from ncatbot.event.bilibili import (
    DanmuMsgEvent,
    SuperChatEvent,
    GiftEvent,
    GuardBuyEvent,
    InteractEvent,
    LikeEvent,
)
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("LiveRoom")


class LiveRoomPlugin(NcatBotPlugin):
    name = "live_room_bilibili"
    version = "1.0.0"
    author = "NcatBot"
    description = "Bilibili 直播间全事件处理"

    async def on_load(self):
        LOG.info("LiveRoom 插件已加载")

    @registrar.bilibili.on_danmu()
    async def on_danmu(self, event: DanmuMsgEvent):
        """弹幕消息"""
        text = event.data.message.text if hasattr(event.data, "message") else ""
        LOG.info(
            "[弹幕] 房间=%s 用户=%s: %s",
            event.group_id,
            event.user_id,
            text,
        )

    @registrar.bilibili.on_superchat()
    async def on_superchat(self, event: SuperChatEvent):
        """醒目留言 (SC)"""
        LOG.info(
            "[SC] 房间=%s 用户=%s",
            event.group_id,
            event.user_id,
        )
        # 感谢 SC
        await self.api.bilibili.send_danmu(
            room_id=event.group_id,
            text="感谢 SC！🎉",
        )

    @registrar.bilibili.on_gift()
    async def on_gift(self, event: GiftEvent):
        """礼物事件"""
        sender = event.sender
        nickname = getattr(sender, "nickname", str(event.user_id))
        LOG.info(
            "[礼物] 房间=%s 用户=%s",
            event.group_id,
            nickname,
        )

    @registrar.bilibili.on_guard_buy()
    async def on_guard_buy(self, event: GuardBuyEvent):
        """大航海事件（舰长/提督/总督）"""
        LOG.info(
            "[大航海] 房间=%s 用户=%s",
            event.group_id,
            event.user_id,
        )
        await self.api.bilibili.send_danmu(
            room_id=event.group_id,
            text="欢迎上船！🚢",
        )

    @registrar.bilibili.on_interact()
    async def on_interact(self, event: InteractEvent):
        """互动事件（进入直播间/关注/分享）"""
        LOG.info(
            "[互动] 房间=%s 用户=%s",
            event.group_id,
            event.user_id,
        )

    @registrar.bilibili.on_like()
    async def on_like(self, event: LikeEvent):
        """点赞事件"""
        LOG.info("[点赞] 房间=%s", event.group_id)
