# 03_rich_message

> 分类：qq

## 这个示例教什么

NcatBot 中**如何发送富文本消息**。QQ 消息不只是纯文本——图片、视频、文件、@某人、表情、戳一戳……NcatBot 提供三种发送路径，从最简单的快速回复到完全控制消息结构的底层 API，让你按需选择。

## 你将学到

- `MessageArray` 链式构造 — `add_text()`, `add_image()`, `add_at()` 组合图文消息
- 各类常用消息段 — Text, Image, At, Video, File, Record, Face
- `event.reply()` — 快速回复当前消息
- Sugar 发送接口 — `send_group_text`, `send_group_image`, `send_group_file`, `send_group_record`, `send_group_video`, `send_group_sticker`, `send_poke`
- 底层 API — `post_group_msg` / `post_group_array_msg` 的定位与区别

## 前置知识

- 了解 NcatBot 的事件注册方式（`@registrar.qq.on_group_command`）
- 建议先完成 [qq/01_event_registration](../01_event_registration/) 和 [qq/02_command_binding](../02_command_binding/)

## 目录结构

~~~text
03_rich_message/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
├── README.md
└── resources/       # 存放示例资源（图片、文件等）
    └── .gitkeep
~~~

## 完整代码

~~~python
"""
qq/03_rich_message — QQ 富文本消息发送演示

演示功能:
  - MessageArray 链式构造     图文 → text + image
  - 各类常用消息段              At, Face, Image, Video, File, Record
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
    # 2. send_group_image — Sugar 发送图片
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
    # 3. send_group_video — Sugar 发送视频
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
    # 4. send_group_file — Sugar 发送文件
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
    # 5. At 消息段 — MessageArray 构造
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
    # 6. send_group_sticker — Sugar 发送表情贴纸
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
    # 7. send_poke — Sugar 戳一戳
    # ================================================================

    @registrar.qq.on_group_command("戳我")
    async def on_poke(self, event: GroupMessageEvent):
        """Sugar — send_poke 戳一戳"""
        await self.api.qq.send_poke(event.group_id, event.user_id)

    # ================================================================
    # 8. 语法糖大全 — 一次展示多种 Sugar 方法
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
    # 9. 底层 API — post_group_msg vs post_group_array_msg
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
~~~

## 关键代码讲解

### 三种发送路径对比

| 路径 | 方法 | 适用场景 | 灵活度 |
|------|------|---------|--------|
| 快速回复 | `event.reply(text=...)` 或 `event.reply(msg)` | 直接回复当前消息 | ⭐ |
| Sugar 方法 | `self.api.qq.send_group_text(gid, ...)` | 发送单类型消息到指定群 | ⭐⭐ |
| 底层 API | `self.api.qq.post_group_msg(gid, text=...)` / `post_group_array_msg(gid, msg)` | 完全控制消息结构 | ⭐⭐⭐ |

**选择建议**：优先用 `event.reply()` → 不够再用 Sugar → 需要完全控制时用底层 API。

### MessageArray 构造富文本

```python
msg = MessageArray()
msg.add_text("文字")           # 文本段
msg.add_image("path_or_url")   # 图片段（本地路径或 URL）
msg.add_at(user_id)            # At 段
msg.add_reply(message_id)      # 引用回复段
msg.add_video("path_or_url")   # 视频段

await event.reply(msg)                          # 通过 reply 发送
await self.api.qq.post_group_array_msg(gid, msg)  # 通过底层 API 发送
```

`MessageArray` 可组合任意消息段，是构造复杂消息的核心工具。

### Sugar 方法速查

| 方法 | 用途 |
|------|------|
| `send_group_text(gid, text)` | 发送纯文本 |
| `send_group_image(gid, path)` | 发送图片 |
| `send_group_file(gid, path, name=...)` | 发送文件 |
| `send_group_record(gid, path)` | 发送语音 |
| `send_group_video(gid, path)` | 发送视频 |
| `send_group_sticker(gid, path)` | 发送表情贴纸 |
| `send_poke(gid, user_id)` | 戳一戳 |

Sugar 方法内部封装了 `MessageArray` 构造和 `post_group_array_msg` 调用，一行代码完成发送。

### 底层 API 区别

```python
# 只能发纯文本
await self.api.qq.post_group_msg(gid, text="纯文本")

# 支持 MessageArray，可发任意富文本
await self.api.qq.post_group_array_msg(gid, msg)
```

- `post_group_msg` — 简单场景，只接受 `text` 参数
- `post_group_array_msg` — 接受 `MessageArray`，支持图文混排、At、视频等

## 运行方式

1. 将 `03_rich_message/` 文件夹复制到项目的 `plugins/` 目录
2. （可选）在 `resources/` 中放入测试文件：`sample.mp4`、`sample.pdf`、`sticker.png`
3. 启动 Bot（`python main.py` 或 `ncatbot run`）
4. 在群聊中发送以下命令测试：
   - `图文` — MessageArray 图文混排
   - `图片` — Sugar 发送图片
   - `视频` — Sugar 发送视频（需 resources/sample.mp4）
   - `文件` — Sugar 发送文件（需 resources/sample.pdf）
   - `at我` — MessageArray At 段
   - `表情` — Sugar 发送表情（需 resources/sticker.png）
   - `戳我` — Sugar 戳一戳
   - `语法糖` — 一次展示多种 Sugar 方法
   - `底层` — post_group_msg vs post_group_array_msg 对比

## 延伸阅读

- [qq/01_event_registration](../01_event_registration/) — 事件注册方式（前置知识）
- [qq/02_command_binding](../02_command_binding/) — 命令参数绑定（前置知识）
- qq/04_forward_message — 合并转发消息的构造与发送（下一篇）
- `MessageArray` 完整 API — `add_text`, `add_image`, `add_at`, `add_reply`, `add_video`, `add_segment` 等
- Sugar 方法参考（Reference）— 所有 `send_group_*` 方法的详细签名与参数
