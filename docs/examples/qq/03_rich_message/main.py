"""
qq/03_rich_message — QQ 富文本消息发送演示

演示功能:
  - MessageArray 链式构造     图文 → text + image
  - 各类常用消息段              At, Reply, Face, Image, Video, File, Record
  - event.reply()             快速回复
  - Sugar 发送接口             send_group_text, send_group_image, ...
  - 底层 API                  post_group_msg / post_group_array_msg

三种发送路径:
  1. event.reply()             — 最简单，自动定位到当前会话
  2. Sugar 方法                 — 指定 group_id 的便捷封装
  3. 底层 API                  — 最灵活，完全控制消息结构

边界:
  本示例不承担合并转发教学职责，转发消息在 04 单独讲。

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from pathlib import Path

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import MessageArray
from ncatbot.types.qq import Face
from ncatbot.utils import get_log

LOG = get_log("RichMessage")

# 资源目录，用于存放示例图片、文件等
PLUGIN_DIR = Path(__file__).parent
RESOURCE_DIR = PLUGIN_DIR / "resources"


class RichMessagePlugin(NcatBotPlugin):
    name = "rich_message_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 富文本消息发送演示"

    # ================================================================
    # 1. MessageArray 链式构造 — 图文混排
    # ================================================================
    # MessageArray 是 NcatBot 的消息构造器，支持链式调用添加多种消息段。
    # 最终通过 post_group_array_msg 或 event.reply 发送。

    @registrar.qq.on_group_command("图文")
    async def on_rich_text(self, event: GroupMessageEvent):
        """MessageArray 链式构造 — 图文混排消息"""
        msg = MessageArray()
        msg.add_text("这是一条图文消息 📸\n")
        msg.add_text("下面附带一张图片：\n")
        msg.add_image("https://via.placeholder.com/200x200.png?text=NcatBot")

        # 使用 event.reply 发送 MessageArray
        await event.reply(msg)

    # ================================================================
    # 2. MessageArray — Reply / Face / Record 消息段
    # ================================================================
    # add_reply: 引用回复指定消息
    # add_segment: 添加任意消息段，如 Face（QQ 表情）
    # Record 语音段通过 send_group_record Sugar 发送（见下方）

    @registrar.qq.on_group_command("回复")
    async def on_reply(self, event: GroupMessageEvent):
        """MessageArray — Reply 消息段（引用回复）"""
        msg = MessageArray()
        msg.add_reply(event.message_id)         # 引用原消息
        msg.add_text("已收到你的消息！这是引用回复 ↩️")
        await event.reply(msg)

    @registrar.qq.on_group_command("表情段")
    async def on_face(self, event: GroupMessageEvent):
        """MessageArray — Face 消息段（QQ 表情）"""
        msg = MessageArray()
        msg.add_text("发送一个 QQ 表情：")
        msg.add_segment(Face(id="178"))         # 178 = 喝彩 表情
        msg.add_text(" ")
        msg.add_segment(Face(id="66"))          # 66 = 爱心 表情
        await event.reply(msg)

    # ================================================================
    # 3. send_group_image — Sugar 发送图片
    # ================================================================
    # Sugar 方法是对底层 API 的便捷封装，一行代码即可发送单类型消息。

    @registrar.qq.on_group_command("图片")
    async def on_image(self, event: GroupMessageEvent):
        """Sugar — send_group_image 发送图片"""
        await self.api.qq.send_group_image(
            event.group_id,
            "https://via.placeholder.com/300x200.png?text=Hello",
        )

    # ================================================================
    # 4. send_group_record — Sugar 发送语音
    # ================================================================

    @registrar.qq.on_group_command("语音")
    async def on_record(self, event: GroupMessageEvent):
        """Sugar — send_group_record 发送语音"""
        record_path = RESOURCE_DIR / "sample.mp3"
        if record_path.exists():
            await self.api.qq.send_group_record(event.group_id, str(record_path))
        else:
            await event.reply(text="请将 sample.mp3 放入 resources/ 目录后重试")

    # ================================================================
    # 5. send_group_video — Sugar 发送视频
    # ================================================================

    @registrar.qq.on_group_command("视频")
    async def on_video(self, event: GroupMessageEvent):
        """Sugar — send_group_video 发送视频"""
        # 传入本地路径或 URL
        video_path = RESOURCE_DIR / "sample.mp4"
        if video_path.exists():
            await self.api.qq.send_group_video(event.group_id, str(video_path))
        else:
            # 没有本地文件时，提示用户
            await event.reply(text="请将 sample.mp4 放入 resources/ 目录后重试")

    # ================================================================
    # 6. send_group_file — Sugar 发送文件
    # ================================================================

    @registrar.qq.on_group_command("文件")
    async def on_file(self, event: GroupMessageEvent):
        """Sugar — send_group_file 发送文件"""
        file_path = RESOURCE_DIR / "sample.pdf"
        if file_path.exists():
            await self.api.qq.send_group_file(
                event.group_id, str(file_path), name="示例文档.pdf"
            )
        else:
            await event.reply(text="请将 sample.pdf 放入 resources/ 目录后重试")

    # ================================================================
    # 7. At 消息段 — MessageArray 构造
    # ================================================================
    # At 段用于在群聊中 @某人。通过 add_at 添加。

    @registrar.qq.on_group_command("at我")
    async def on_at_me(self, event: GroupMessageEvent):
        """MessageArray — At 消息段"""
        msg = MessageArray()
        msg.add_at(event.user_id)
        msg.add_text(" 你好！我 @ 了你 👋")
        await event.reply(msg)

    # ================================================================
    # 8. send_group_sticker — Sugar 发送表情贴纸
    # ================================================================

    @registrar.qq.on_group_command("表情")
    async def on_sticker(self, event: GroupMessageEvent):
        """Sugar — send_group_sticker 发送表情贴纸"""
        sticker_path = RESOURCE_DIR / "sticker.png"
        if sticker_path.exists():
            await self.api.qq.send_group_sticker(event.group_id, str(sticker_path))
        else:
            await event.reply(text="请将 sticker.png 放入 resources/ 目录后重试")

    # ================================================================
    # 9. send_poke — Sugar 戳一戳
    # ================================================================

    @registrar.qq.on_group_command("戳我")
    async def on_poke(self, event: GroupMessageEvent):
        """Sugar — send_poke 戳一戳"""
        await self.api.qq.send_poke(event.group_id, event.user_id)

    # ================================================================
    # 10. 语法糖大全 — 一次展示多种 Sugar 方法
    # ================================================================

    @registrar.qq.on_group_command("语法糖")
    async def on_sugar_demo(self, event: GroupMessageEvent):
        """展示多种 Sugar 方法"""
        gid = event.group_id

        # 1) 纯文本
        await self.api.qq.send_group_text(gid, "① send_group_text — 纯文本消息")

        # 2) 图片（URL）
        await self.api.qq.send_group_image(
            gid, "https://via.placeholder.com/100x100.png?text=Sugar"
        )

        # 3) 戳一戳
        await self.api.qq.send_poke(gid, event.user_id)

        await self.api.qq.send_group_text(
            gid,
            "以上是 send_group_text / send_group_image / send_poke 的效果。\n"
            "其他 Sugar 方法: send_group_file, send_group_record, "
            "send_group_video, send_group_sticker",
        )

    # ================================================================
    # 11. 底层 API — post_group_msg vs post_group_array_msg
    # ================================================================
    # post_group_msg:      发送纯文本消息（text 参数）
    # post_group_array_msg: 发送 MessageArray 构造的富文本消息
    #
    # 多数场景下 Sugar 方法和 event.reply 已足够。
    # 底层 API 适用于需要完全控制消息内容的场景。

    @registrar.qq.on_group_command("底层")
    async def on_low_level(self, event: GroupMessageEvent):
        """底层 API — post_group_msg 与 post_group_array_msg 对比"""
        gid = event.group_id

        # 方式 A: post_group_msg — 发送纯文本
        await self.api.qq.post_group_msg(gid, text="[底层 A] post_group_msg 纯文本消息")

        # 方式 B: post_group_array_msg — 发送 MessageArray
        msg = MessageArray()
        msg.add_text("[底层 B] post_group_array_msg\n")
        msg.add_text("支持任意消息段组合：文本 + 图片 + At + ...\n")
        msg.add_at(event.user_id)
        await self.api.qq.post_group_array_msg(gid, msg)

        # 总结
        await self.api.qq.post_group_msg(
            gid,
            text="对比：\n"
            "• post_group_msg — 只能发纯文本（text 参数）\n"
            "• post_group_array_msg — 发送 MessageArray，支持富文本",
        )
