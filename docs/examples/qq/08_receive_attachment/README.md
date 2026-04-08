# 08_receive_attachment

> 分类：qq

## 这个示例教什么

NcatBot 中如何在**接收侧**解析富文本消息和处理附件。消息到达时，你可以用 `filter` 按类型提取消息段、用 `get_attachments()` 获取附件列表、下载文件、读取字节、或直接转为消息段转发——这些操作构成了 Bot 处理用户发来的图片、文件等富媒体内容的完整工具链。

## 你将学到

- `event.message.filter(Image)` — 按类型过滤消息段
- `filter_text()` / `filter_at()` / `filter_image()` — 快捷过滤方法
- `event.message.get_attachments()` — 获取附件列表
- `Attachment.download(dest)` — 下载附件到本地路径
- `Attachment.as_bytes()` — 获取附件原始字节数据
- `Attachment.to_segment()` — 将附件转为可发送消息段
- `ImageAttachment` 元信息 — `width`、`height`
- `event.message.text` — 获取拼接后的纯文本
- `event.message.is_at(bot_id)` — 检查消息是否 @Bot

## 前置知识

- [03_rich_message](../03_rich_message/) — 消息发送侧的富文本构造

## 目录结构

~~~text
08_receive_attachment/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
└── README.md
~~~

## 完整代码

~~~python
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
~~~

## 关键代码讲解

### filter vs get_attachments 区别

| | `event.message.filter(Type)` | `event.message.get_attachments()` |
|---|---|---|
| 返回值 | 消息段列表（`List[Image]` 等） | `AttachmentList`（`Attachment` / `ImageAttachment`） |
| 用途 | 按类型过滤出消息中的特定段 | 获取所有可下载的附件对象 |
| 可下载 | ❌ 消息段本身不提供下载方法 | ✅ `download()` / `as_bytes()` |
| 可转发 | ✅ 消息段可直接用于发送 | ✅ `to_segment()` 转为消息段后发送 |
| 元信息 | 部分（如 `img.url`） | 完整（`name`/`size`/`content_type`/`width`/`height`） |
| 典型场景 | 检查消息中有没有图片 | 下载、保存、处理附件文件 |

**简单理解**：`filter` 是在消息链中按类型筛选段，`get_attachments` 是把所有附件提取为可操作对象。

### Attachment 方法速查表

| 方法/属性 | 说明 | 返回值 |
|---|---|---|
| `att.name` | 文件名 | `str` |
| `att.url` | 下载 URL | `str` |
| `att.size` | 文件大小（字节） | `int` |
| `att.content_type` | MIME 类型 | `str` |
| `att.kind` | 附件类别 | `str` |
| `await att.download(dest)` | 下载到指定目录 | `str`（保存路径） |
| `await att.as_bytes()` | 获取原始字节数据 | `bytes` |
| `att.to_segment()` | 转为可发送消息段 | `Image` / 对应段类型 |

**ImageAttachment** 额外属性：

| 属性 | 说明 | 类型 |
|---|---|---|
| `att.width` | 图片宽度（像素） | `int` |
| `att.height` | 图片高度（像素） | `int` |

### 快捷过滤方法

~~~python
# 以下三组写法等价：

# 通用写法
images = event.message.filter(Image)
texts  = event.message.filter(PlainText)
ats    = event.message.filter(At)

# 快捷方法
images = event.message.filter_image()
texts  = event.message.filter_text()
ats    = event.message.filter_at()
~~~

### 纯文本与 @检测

~~~python
# 纯文本 — 将所有 PlainText 段拼接为一个字符串
plain = event.message.text  # "提取图片 这是附加文字"

# @检测 — 检查消息中是否 @了指定用户
is_at_me = event.message.is_at(event.self_id)  # True / False
~~~

## 运行方式

1. 将 `08_receive_attachment/` 文件夹复制到 `plugins/` 目录
2. 启动 Bot
3. 在群聊中发送以下命令测试：
   - **提取图片**（附带图片）— 查看图片段信息和元数据
   - **提取文本**（混合 @和文字）— 查看消息解析结果
   - **下载**（附带图片/文件）— 下载第一个附件
   - **转发附件**（附带图片）— 附件转消息段后转发
   - **@检测**（@Bot 后发送）— 检测 @状态

## 延伸阅读

- [03_rich_message](../03_rich_message/) — 消息发送侧：构造富文本消息
- [05_group_management](../05_group_management/) — 群管理操作
