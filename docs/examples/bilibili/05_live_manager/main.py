"""
bilibili/05_live_manager — Bilibili 直播间管理

演示功能:
  - registrar.bilibili.on_danmu(): 弹幕命令解析
  - self.api.bilibili.ban_user(): 禁言用户
  - self.api.bilibili.set_room_silent(): 全局静音
  - self.api.bilibili.get_room_info(): 查询房间信息
  - 简易弹幕命令系统

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
在直播间弹幕中发送:
  "!禁言 <uid>"  → 禁言指定用户
  "!静音"        → 开启全局静音
  "!解除静音"    → 关闭全局静音
  "!房间信息"    → 查询当前房间信息

参考文档: docs/guide/api_usage/bilibili/1_live_room.md
"""

from ncatbot.core import registrar
from ncatbot.event.bilibili import DanmuMsgEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("BiliLiveManager")


class BiliLiveManagerPlugin(NcatBotPlugin):
    name = "live_manager_bilibili"
    version = "1.0.0"
    author = "NcatBot"
    description = "Bilibili 直播间管理"

    async def on_load(self):
        LOG.info("BiliLiveManager 插件已加载")

    @registrar.bilibili.on_danmu()
    async def on_danmu_command(self, event: DanmuMsgEvent):
        """弹幕命令路由"""
        text = event.data.message.text if hasattr(event.data, "message") else ""
        if not text.startswith("!"):
            return

        room_id = event.group_id
        cmd = text[1:].strip()

        if cmd.startswith("禁言"):
            await self._handle_ban(room_id, cmd)
        elif cmd == "静音":
            await self._handle_silent(room_id, True)
        elif cmd == "解除静音":
            await self._handle_silent(room_id, False)
        elif cmd == "房间信息":
            await self._handle_room_info(room_id)

    async def _handle_ban(self, room_id, cmd: str):
        """禁言用户"""
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].isdigit():
            await self.api.bilibili.send_danmu(
                room_id=room_id, text="用法: !禁言 <uid>"
            )
            return

        target_uid = int(parts[1])
        try:
            await self.api.bilibili.ban_user(
                room_id=room_id, user_id=target_uid, hour=1
            )
            await self.api.bilibili.send_danmu(
                room_id=room_id, text=f"已禁言用户 {target_uid}"
            )
            LOG.info("禁言用户 %s (房间=%s)", target_uid, room_id)
        except Exception as e:
            LOG.error("禁言失败: %s", e)

    async def _handle_silent(self, room_id, enable: bool):
        """全局静音开关"""
        try:
            await self.api.bilibili.set_room_silent(room_id=room_id, enable=enable)
            state = "开启" if enable else "关闭"
            await self.api.bilibili.send_danmu(
                room_id=room_id, text=f"已{state}全局静音"
            )
            LOG.info("%s全局静音 (房间=%s)", state, room_id)
        except Exception as e:
            LOG.error("设置静音失败: %s", e)

    async def _handle_room_info(self, room_id):
        """查询房间信息"""
        try:
            info = await self.api.bilibili.get_room_info(room_id=room_id)
            title = info.get("title", "未知") if info else "获取失败"
            await self.api.bilibili.send_danmu(room_id=room_id, text=f"房间: {title}")
        except Exception as e:
            LOG.error("查询房间信息失败: %s", e)
