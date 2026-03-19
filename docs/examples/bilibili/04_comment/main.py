"""
bilibili/04_comment — Bilibili 评论操作

演示功能:
  - registrar.bilibili.on_comment(): 评论事件处理
  - event.reply(): 回复评论
  - self.api.bilibili.like_comment(): 点赞评论
  - BiliCommentEvent 事件属性

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
当有用户在被监控的视频下评论时自动触发。

参考文档: docs/guide/api_usage/bilibili/3_comment.md
"""

from ncatbot.core import registrar
from ncatbot.event.bilibili import BiliCommentEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("BiliComment")


class BiliCommentPlugin(NcatBotPlugin):
    name = "comment_bilibili"
    version = "1.0.0"
    author = "NcatBot"
    description = "Bilibili 评论操作"

    async def on_load(self):
        self.data.setdefault("comment_count", 0)
        LOG.info("BiliComment 插件已加载")

    @registrar.bilibili.on_comment()
    async def on_comment(self, event: BiliCommentEvent):
        """收到评论 → 自动回复 + 点赞"""
        content = getattr(event.data, "content", "")
        LOG.info("[评论] 用户=%s: %s", event.user_id, content)

        self.data["comment_count"] = self.data.get("comment_count", 0) + 1

        # 自动回复评论
        await event.reply("感谢评论！这是 Bot 自动回复 🤖")

        # 点赞评论
        try:
            await self.api.bilibili.like_comment(
                resource_id=event.data.resource_id,
                resource_type=event.data.resource_type,
                comment_id=int(event.data.comment_id),
            )
            LOG.info("[评论] 已点赞评论 comment_id=%s", event.data.comment_id)
        except Exception as e:
            LOG.warning("[评论] 点赞失败: %s", e)
