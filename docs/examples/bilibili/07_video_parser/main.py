"""
bilibili/07_video_parser — QQ 群内自动解析 B 站视频链接

演示功能:
  - api.bilibili.parse_bili_id(): 从文本解析 B 站视频 ID
  - api.bilibili.get_video_info(): 获取视频详细信息
  - registrar.qq.on_group_command(): QQ 群命令
  - registrar.qq.on_group_message(): QQ 群消息监听
  - MessageArray.filter(Json): 从 QQ 小程序卡片中提取 B 站链接

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
  在 QQ 群中发送 "b站视频 BV1wa411Q7N6"    → 返回视频信息
  在 QQ 群中分享 B 站视频链接/小程序卡片     → 自动解析并展示视频信息
"""

import json as _json
from datetime import datetime

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types.qq import Json
from ncatbot.utils import get_log

LOG = get_log("BiliVideoParser")


class BiliVideoParserPlugin(NcatBotPlugin):
    name = "video_parser_bilibili"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 群内自动解析 B 站视频链接"

    async def on_load(self):
        LOG.info("B站视频解析插件已加载")

    # ==================== 辅助方法 ====================

    def _format_video_info(self, info) -> str:
        """将 VideoInfo 格式化为展示文本"""
        pubdate = datetime.fromtimestamp(info.pubdate).strftime("%Y-%m-%d %H:%M:%S")
        desc = (info.desc[:100] + "...") if len(info.desc) > 100 else info.desc
        lines = [
            "📺 B站视频信息:",
            f"  标题: {info.title}",
            f"  BV号: {info.bvid}  av号: av{info.aid}",
            f"  分区: {info.tname}",
            f"  发布: {pubdate}",
            f"  UP主: {info.owner.name} (UID: {info.owner.mid})",
            f"  时长: {info.duration_text}  分P: {info.videos}",
            f"  ▶ {info.stat.view}  💬 {info.stat.danmaku}  📝 {info.stat.reply}",
            f"  ❤ {info.stat.like}  🪙 {info.stat.coin}  ⭐ {info.stat.favorite}",
            f"  简介: {desc}",
            f"  链接: {info.url}",
        ]
        return "\n".join(lines)

    # ==================== QQ 群命令：主动查询 ====================

    @registrar.qq.on_group_command("b站视频", ignore_case=True)
    async def qq_video_info(self, event, video_id: str = ""):
        """查询 B 站视频信息

        支持多种输入格式：
          b站视频 BV1wa411Q7N6
          b站视频 av258296202
          b站视频 https://www.bilibili.com/video/BV1wa411Q7N6
          b站视频 https://b23.tv/xxxxxx
        """
        if not video_id:
            await event.reply(text="用法: b站视频 <BV号/av号/链接>")
            return

        try:
            # 使用 parse_bili_id 统一处理各种格式
            parsed = await self.api.bilibili.parse_bili_id(video_id)
            if not parsed:
                await event.reply(text="❌ 无法从输入中解析出 B 站视频 ID")
                return

            info = await self.api.bilibili.get_video_info(parsed.video_id)
            if not info:
                await event.reply(text="❌ 未找到视频信息")
                return

            await event.reply(text=self._format_video_info(info))
        except Exception as e:
            await event.reply(text=f"❌ 查询视频信息失败: {e}")

    # ==================== 自动解析群消息中的 B 站链接 ====================

    @registrar.qq.on_group_message()
    async def on_group_auto_parse(self, event: GroupMessageEvent):
        """监听群消息，自动检测 B 站链接并展示视频信息

        处理两种场景：
          1. 直接发送的文字消息（含 BV号/av号/b23 短链）
          2. QQ 小程序卡片（JSON 消息段，B 站链接在 meta.detail_1.qqdocurl）
        """
        # 收集候选文本：raw_message + JSON 小程序卡片 qqdocurl
        candidates: list[str] = [event.raw_message]
        for seg in event.message.filter(Json):
            try:
                obj = _json.loads(seg.data)
                qqdocurl = (
                    obj.get("meta", {})
                    .get("detail_1", {})
                    .get("qqdocurl", "")
                )
                if qqdocurl:
                    candidates.append(qqdocurl)
            except Exception:
                pass

        # 逐个候选尝试解析
        for candidate in candidates:
            parsed = await self.api.bilibili.parse_bili_id(candidate)
            if parsed:
                break
        else:
            return  # 均未匹配，忽略

        try:
            info = await self.api.bilibili.get_video_info(parsed.video_id)
            if info:
                await event.reply(text=self._format_video_info(info))
        except Exception as e:
            LOG.warning("自动解析B站视频失败 %s: %s", parsed.video_id, e)
