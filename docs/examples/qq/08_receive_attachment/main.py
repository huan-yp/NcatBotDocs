"""
qq/08_receive_attachment — QQ 消息接收与附件处理演示

演示功能:
  - event.message.filter(Image)       过滤出图片消息段
  - filter_text / filter_at / filter_image  快捷过滤方法
  - event.message.get_attachments()   获取附件列表
  - Attachment.download(dest)         下载附件到本地
  - Attachment.as_bytes()             获取附件字节数据
  - Attachment.to_segment()           将附件转为可发送消息段
  - ImageAttachment 元信息            width, height
  - event.message.text                获取纯文本
  - event.message.is_at(bot_id)       检查是否 @Bot

边界:
  本示例聚焦消息接收侧的解析与附件处理，
  消息发送侧的富文本构造见 qq/03_rich_message。

前置知识: qq/03_rich_message
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import Image, ImageAttachment
from ncatbot.utils import get_log

LOG = get_log("ReceiveAttachment")


class ReceiveAttachmentPlugin(NcatBotPlugin):
    name = "receive_attachment_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 消息接收与附件处理演示"

    # ================================================================
    # 1. 提取图片 — filter(Image) 过滤图片消息段
    # ================================================================

    @registrar.qq.on_group_command("提取图片")
    async def on_extract_images(self, event: GroupMessageEvent):
        """过滤出消息中的所有图片段，展示信息"""
        images = event.message.filter(Image)

        if not images:
            await event.reply("❌ 消息中没有图片，请在发送「提取图片」时附带图片")
            return

        lines = [f"🖼️ 找到 {len(images)} 张图片："]
        for i, img in enumerate(images, 1):
            lines.append(f"  {i}. URL: {img.url}")

        # 同时检查是否有 ImageAttachment（含 width/height 元信息）
        attachments = event.message.get_attachments()
        for att in attachments:
            if isinstance(att, ImageAttachment):
                lines.append(
                    f"  📐 图片尺寸: {att.width}x{att.height}"
                    f"  大小: {att.size} bytes"
                )

        await event.reply("\n".join(lines))

    # ================================================================
    # 2. 提取文本 — text / filter_text / filter_at
    # ================================================================

    @registrar.qq.on_group_command("提取文本")
    async def on_extract_text(self, event: GroupMessageEvent):
        """展示消息的纯文本、文本段列表和 At 段列表"""

        # event.message.text — 拼接后的纯文本字符串
        plain_text = event.message.text

        # filter_text() — 所有 PlainText 段
        text_segments = event.message.filter_text()

        # filter_at() — 所有 At 段
        at_segments = event.message.filter_at()

        lines = [
            "📝 消息解析结果：",
            f"  纯文本: {plain_text!r}",
            f"  文本段数量: {len(text_segments)}",
        ]
        for i, seg in enumerate(text_segments, 1):
            lines.append(f"    {i}. {seg.text!r}")

        lines.append(f"  At 段数量: {len(at_segments)}")
        for i, at in enumerate(at_segments, 1):
            lines.append(f"    {i}. @{at.qq}")

        await event.reply("\n".join(lines))

    # ================================================================
    # 3. 下载 — Attachment.download(dest) 下载附件
    # ================================================================

    @registrar.qq.on_group_command("下载")
    async def on_download(self, event: GroupMessageEvent):
        """下载消息中的第一个附件到本地"""
        attachments = event.message.get_attachments()

        if not attachments:
            await event.reply("❌ 消息中没有附件，请附带图片或文件后再试")
            return

        att = attachments[0]
        LOG.info(
            "开始下载附件: name=%s, size=%s, content_type=%s",
            att.name, att.size, att.content_type,
        )

        dest = "/tmp/ncatbot_downloads"
        path = await att.download(dest)

        await event.reply(
            f"✅ 附件已下载\n"
            f"  文件名: {att.name}\n"
            f"  类型: {att.content_type}\n"
            f"  大小: {att.size} bytes\n"
            f"  保存路径: {path}"
        )

    # ================================================================
    # 4. 转发附件 — to_segment() + as_bytes()
    # ================================================================

    @registrar.qq.on_group_command("转发附件")
    async def on_forward_attachment(self, event: GroupMessageEvent):
        """获取附件 → 转为消息段 → 原样发回"""
        attachments = event.message.get_attachments()

        if not attachments:
            await event.reply("❌ 消息中没有附件")
            return

        att = attachments[0]

        # as_bytes() — 获取原始字节（可用于二次处理）
        data = await att.as_bytes()
        LOG.info("附件字节大小: %d bytes", len(data))

        # to_segment() — 将附件转为可直接发送的消息段
        segment = att.to_segment()
        await event.reply(segment)

    # ================================================================
    # 5. @检测 — is_at(bot_id)
    # ================================================================

    @registrar.qq.on_group_command("@检测")
    async def on_at_check(self, event: GroupMessageEvent):
        """检测消息是否 @Bot"""
        is_at_me = event.message.is_at(event.self_id)

        at_segments = event.message.filter_at()
        at_list = ", ".join(f"@{at.qq}" for at in at_segments) or "无"

        await event.reply(
            f"🔍 @检测结果：\n"
            f"  是否 @我: {'✅ 是' if is_at_me else '❌ 否'}\n"
            f"  消息中的 @: {at_list}"
        )

    # ================================================================
    # 6. 自动检测图片 — 低优先级通用处理器
    # ================================================================

    @registrar.qq.on_group_message(priority=100)
    async def on_auto_detect_image(self, event: GroupMessageEvent):
        """自动检测消息中的图片，记录日志（不回复，避免刷屏）"""
        images = event.message.filter_image()

        if not images:
            return

        LOG.info(
            "检测到 %d 张图片 (群=%s, 用户=%s)",
            len(images), event.group_id, event.user_id,
        )

        # 如果有 ImageAttachment，记录尺寸元信息
        attachments = event.message.get_attachments()
        for att in attachments:
            if isinstance(att, ImageAttachment):
                LOG.info(
                    "  图片元信息: %s — %dx%d, %s bytes",
                    att.name, att.width, att.height, att.size,
                )
