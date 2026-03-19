"""
cross_platform/01_multi_adapter — 跨平台双适配器启动

演示功能:
  - BotClient 多适配器同时启动 (QQ + Bilibili)
  - 混合使用 registrar.qq.* 和 registrar.bilibili.* 注册
  - 跨平台状态查询
  - 在 QQ 群中通过命令向 Bilibili 直播间发弹幕

使用方式: 将本文件夹复制到 plugins/ 目录，配置同时启用 napcat + bilibili 适配器。
  QQ 群发 "status"     → 查看多平台状态
  QQ 群发 "弹幕 xxx"   → 向 B 站直播间发弹幕

基于 dev/bilibili_cross_platform.py 改编。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.event.bilibili import DanmuMsgEvent, BiliPrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("MultiAdapter")


class MultiAdapterPlugin(NcatBotPlugin):
    name = "multi_adapter"
    version = "1.0.0"
    author = "NcatBot"
    description = "跨平台双适配器启动演示"

    async def on_load(self):
        LOG.info("MultiAdapter 插件已加载")

    # ==================== QQ 侧命令 ====================

    @registrar.qq.on_group_command("status")
    async def qq_status(self, event: GroupMessageEvent):
        """QQ 群命令: 查看跨平台状态"""
        try:
            platforms = self.api.platforms
            lines = ["📊 跨平台状态:"]
            for name in platforms:
                lines.append(f"  ✅ {name}")
            await event.reply(text="\n".join(lines))
        except Exception as e:
            LOG.error("获取状态失败: %s", e)

    @registrar.qq.on_group_command("弹幕")
    async def qq_send_danmu(self, event: GroupMessageEvent, text: str = ""):
        """QQ 群命令: 向 B 站直播间发弹幕"""
        if not text:
            await event.reply(text="用法: 弹幕 <弹幕内容>")
            return
        try:
            # room_id 需根据实际配置修改
            await self.api.bilibili.send_danmu(room_id=22628755, text=text)
            await event.reply(text=f"✅ 弹幕已发送: {text}")
        except Exception as e:
            await event.reply(text=f"❌ 发送失败: {e}")

    # ==================== Bilibili 侧事件 ====================

    @registrar.bilibili.on_danmu()
    async def on_bili_danmu(self, event: DanmuMsgEvent):
        """Bilibili 弹幕消息 → 记录日志"""
        msg_text = event.data.message.text if hasattr(event.data, "message") else ""
        LOG.info("[bilibili] 弹幕 房间=%s: %s", event.group_id, msg_text)

    @registrar.bilibili.on_private_message()
    async def on_bili_pm(self, event: BiliPrivateMessageEvent):
        """Bilibili 私信 → 自动回复"""
        await event.reply("你好！我是跨平台 Bot，收到了你的 B 站私信 📩")
