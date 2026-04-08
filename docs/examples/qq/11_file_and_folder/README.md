# 11_file_and_folder

> 分类：qq

## 这个示例教什么

NcatBot 中如何上传文件到群、管理群文件夹、下载文件，以及如何将用户发来的附件一键转存到指定文件夹。文件 API 分为**文件传输**（`self.api.qq.file`）和**文件查询**（`self.api.qq.query`）两大分组，本示例完整串联两者的使用方式。

## 你将学到

- `upload_group_file` — 上传本地文件到群文件（支持路径字符串和 Attachment 对象）
- `create_group_file_folder` — 创建群文件夹
- `get_group_root_files` — 获取群根目录文件列表
- `get_group_files_by_folder` — 获取指定文件夹中的文件
- `get_group_file_url` — 获取文件下载链接
- `download_file` — 通过 URL 下载文件到本地
- `send_group_file` — 发送文件消息（消息层面的语法糖）
- `get_or_create_group_folder` — 查找/创建文件夹语法糖
- **转存串联场景** — 接收附件 → 创建文件夹 → 上传到指定目录

## 前置知识

- [03_rich_message](../03_rich_message/) — 消息段与富文本构造
- [08_receive_attachment](../08_receive_attachment/) — 消息附件接收与处理

## 目录结构

~~~text
11_file_and_folder/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
├── resources/       # 示例资源目录
│   └── .gitkeep
└── README.md
~~~

## 完整代码

~~~python
"""
qq/11_file_and_folder — QQ 文件上传与群文件夹管理演示

演示功能:
  - upload_group_file          上传文件到群（本地路径 / Attachment）
  - upload_private_file        上传私聊文件（注释提及）
  - create_group_file_folder   创建群文件夹
  - get_group_root_files       获取群根目录文件列表
  - get_group_files_by_folder  获取指定文件夹中的文件
  - get_group_file_url         获取文件下载链接
  - download_file              下载文件到本地
  - send_group_file            发送文件消息（sugar）
  - upload_attachment          Attachment 一步上传语法糖
  - get_or_create_group_folder 查找/创建文件夹语法糖

提及但不展开:
  - delete_group_file          删除群文件
  - delete_group_folder        删除群文件夹
  - get_group_file_system_info 获取群文件系统信息

边界:
  本示例聚焦文件上传与群文件夹管理，
  消息附件接收见 qq/08_receive_attachment。

前置知识: qq/03_rich_message, qq/08_receive_attachment
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from pathlib import Path

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("FileAndFolder")

# 插件所在目录，用于定位 resources/
PLUGIN_DIR = Path(__file__).parent


class FileAndFolderPlugin(NcatBotPlugin):
    name = "file_and_folder_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 文件上传与群文件夹管理演示"

    # ================================================================
    # 1. 上传文件 — upload_group_file（本地路径）
    # ================================================================
    # 将本地文件上传到群文件。
    # file 参数接受本地路径字符串。

    @registrar.qq.on_group_command("上传文件")
    async def on_upload_file(self, event: GroupMessageEvent):
        """上传本地文件到群文件 — '上传文件'"""
        # 这里用 resources/ 下的示例文件演示
        test_file = PLUGIN_DIR / "resources" / "example.txt"
        if not test_file.exists():
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("这是一个测试文件\n由 NcatBot 示例插件创建", encoding="utf-8")

        try:
            await self.api.qq.file.upload_group_file(
                event.group_id,
                file=str(test_file),  # 本地路径字符串
                name="示例文件.txt",   # 上传后的文件名
            )
            await event.reply("✅ 文件已上传到群文件")
        except Exception as e:
            await event.reply(f"❌ 上传失败: {e}")

    # ================================================================
    # 2. 创建文件夹 — create_group_file_folder
    # ================================================================
    # 在群文件根目录创建新文件夹。
    # parent_id 为空表示根目录；可指定已有文件夹 ID 创建子文件夹。

    @registrar.qq.on_group_command("创建文件夹")
    async def on_create_folder(self, event: GroupMessageEvent, name: str = ""):
        """创建群文件夹 — '创建文件夹 名称'"""
        if not name:
            await event.reply("❌ 请指定文件夹名称，如：创建文件夹 资料库")
            return

        try:
            result = await self.api.qq.file.create_group_file_folder(
                event.group_id,
                name=name,
                parent_id="",  # 空字符串 = 根目录
            )
            LOG.info("创建文件夹结果: %s", result)
            await event.reply(f"✅ 文件夹「{name}」已创建")
        except Exception as e:
            await event.reply(f"❌ 创建失败: {e}")

    # ================================================================
    # 3. 查看文件 — get_group_root_files
    # ================================================================
    # 列出群文件根目录下的所有文件和文件夹。

    @registrar.qq.on_group_command("查看文件")
    async def on_list_root_files(self, event: GroupMessageEvent):
        """查看群根目录文件列表 — '查看文件'"""
        try:
            file_list = await self.api.qq.query.get_group_root_files(event.group_id)

            lines = ["📁 群文件根目录："]

            # 文件夹列表
            for folder in file_list.folders or []:
                lines.append(
                    f"  📂 {folder.folder_name}"
                    f"  (ID: {folder.folder_id})"
                )

            # 文件列表
            for f in file_list.files or []:
                lines.append(
                    f"  📄 {f.file_name}"
                    f"  (ID: {f.file_id}, 大小: {f.file_size} bytes)"
                )

            if len(lines) == 1:
                lines.append("  (空)")

            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 获取文件列表失败: {e}")

    # ================================================================
    # 4. 查看文件夹 — get_group_files_by_folder
    # ================================================================
    # 获取指定文件夹中的文件和子文件夹。
    # folder_id 从「查看文件」返回的列表中获取。

    @registrar.qq.on_group_command("查看文件夹")
    async def on_list_folder(self, event: GroupMessageEvent, folder_id: str = ""):
        """查看指定文件夹内容 — '查看文件夹 文件夹ID'"""
        if not folder_id:
            await event.reply("❌ 请指定文件夹 ID，如：查看文件夹 abc123")
            return

        try:
            file_list = await self.api.qq.query.get_group_files_by_folder(
                event.group_id, folder_id
            )

            lines = [f"📂 文件夹 {folder_id} 内容："]

            for folder in file_list.folders or []:
                lines.append(
                    f"  📂 {folder.folder_name}"
                    f"  (ID: {folder.folder_id})"
                )

            for f in file_list.files or []:
                lines.append(
                    f"  📄 {f.file_name}"
                    f"  (ID: {f.file_id}, 大小: {f.file_size} bytes)"
                )

            if len(lines) == 1:
                lines.append("  (空)")

            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 获取文件夹内容失败: {e}")

    # ================================================================
    # 5. 文件链接 — get_group_file_url
    # ================================================================
    # 根据 file_id 获取文件的下载链接。

    @registrar.qq.on_group_command("文件链接")
    async def on_get_file_url(self, event: GroupMessageEvent, file_id: str = ""):
        """获取文件下载链接 — '文件链接 文件ID'"""
        if not file_id:
            await event.reply("❌ 请指定文件 ID，如：文件链接 abc123")
            return

        try:
            url = await self.api.qq.query.get_group_file_url(
                event.group_id, file_id
            )
            await event.reply(f"🔗 文件下载链接：\n{url}")
        except Exception as e:
            await event.reply(f"❌ 获取链接失败: {e}")

    # ================================================================
    # 6. 下载文件 — download_file
    # ================================================================
    # 通过 URL 下载文件到 Bot 本地。

    @registrar.qq.on_group_command("下载文件")
    async def on_download_file(self, event: GroupMessageEvent, url: str = ""):
        """下载文件到本地 — '下载文件 URL'"""
        if not url:
            await event.reply("❌ 请指定文件 URL，如：下载文件 https://...")
            return

        try:
            result = await self.api.qq.file.download_file(url=url)
            await event.reply(f"✅ 文件已下载\n  本地路径: {result.file}")
        except Exception as e:
            await event.reply(f"❌ 下载失败: {e}")

    # ================================================================
    # 7. 发文件 — send_group_file（sugar）
    # ================================================================
    # send_group_file 是消息层面的文件发送语法糖，
    # 将文件作为消息段发出（不同于 upload_group_file 传到群文件）。

    @registrar.qq.on_group_command("发文件")
    async def on_send_file(self, event: GroupMessageEvent):
        """通过消息发送文件 — '发文件'"""
        test_file = PLUGIN_DIR / "resources" / "example.txt"
        if not test_file.exists():
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("这是一个测试文件", encoding="utf-8")

        try:
            # send_group_file — 将文件作为消息发送（文件消息段）
            # 与 upload_group_file 的区别：
            #   send_group_file → 发送文件消息到聊天窗口
            #   upload_group_file → 上传到群文件管理系统
            await self.api.qq.send_group_file(
                event.group_id,
                file=str(test_file),
                name="示例文件.txt",
            )
        except Exception as e:
            await event.reply(f"❌ 发送失败: {e}")

    # ================================================================
    # 8. 转存 — 串联场景：接收附件 → 下载 → 创建文件夹 → 上传
    # ================================================================
    # 这是一个完整的实战场景：
    #   1. 用户回复一条含附件的消息，发送「转存」
    #   2. Bot 获取附件 → 下载到本地
    #   3. 使用 get_or_create_group_folder 查找/创建目标文件夹
    #   4. 将下载的文件上传到该文件夹
    #
    # Attachment 可直接传给 upload_group_file，无需手动下载：
    #   await self.api.qq.file.upload_group_file(gid, att, folder_id=fid)
    # 但这里演示完整手动流程以便理解。

    @registrar.qq.on_group_command("转存")
    async def on_save_attachment(self, event: GroupMessageEvent):
        """接收附件 → 下载 → 创建文件夹 → 上传到群文件"""
        # Step 1: 获取消息中的附件
        attachments = event.message.get_attachments()
        if not attachments:
            await event.reply(
                "❌ 消息中没有附件\n"
                "💡 请在包含文件/图片的消息上回复「转存」"
            )
            return

        att = attachments[0]
        await event.reply(f"⏳ 正在转存「{att.name}」...")

        try:
            # Step 2: 使用 get_or_create_group_folder 查找/创建文件夹
            # 如果「Bot转存」文件夹不存在会自动创建
            folder_id = await self.api.qq.file.get_or_create_group_folder(
                event.group_id, "Bot转存"
            )

            # Step 3: 直接将 Attachment 传给 upload_group_file
            # upload_group_file 的 file 参数支持 Attachment 对象，
            # 内部自动下载到临时目录再上传，上传完成后清理临时文件。
            await self.api.qq.file.upload_group_file(
                event.group_id,
                file=att,           # 直接传 Attachment 对象
                name=att.name,      # 使用原文件名
                folder_id=folder_id,
            )

            await event.reply(
                f"✅ 转存成功\n"
                f"  文件: {att.name}\n"
                f"  文件夹: Bot转存"
            )
        except Exception as e:
            await event.reply(f"❌ 转存失败: {e}")

    # ================================================================
    # 补充说明（不在命令中演示）
    # ================================================================
    #
    # upload_private_file — 私聊文件上传
    #   用法与 upload_group_file 类似，目标换成 user_id：
    #     await self.api.qq.file.upload_private_file(user_id, file, name="")
    #   file 同样支持本地路径字符串和 Attachment 对象。
    #
    # upload_attachment — 一步上传语法糖
    #   更高层的封装，自动处理下载 → 上传 → 清理的全部流程：
    #     await self.api.qq.file.upload_attachment(
    #         group_id, att, target_type="group", folder="Bot转存"
    #     )
    #   当 folder 参数指定文件夹名时，会自动调用
    #   get_or_create_group_folder 查找/创建文件夹。
    #
    # delete_group_file(group_id, file_id) — 删除群文件
    # delete_group_folder(group_id, folder_id) — 删除群文件夹
    # get_group_file_system_info(group_id) — 获取群文件系统信息
    #   （文件数量上限、已用空间等）
~~~

## 关键代码讲解

### 文件 API 分类速查

| 分组 | API | 说明 |
|------|-----|------|
| **文件传输** `self.api.qq.file` | `upload_group_file(group_id, file, name, folder_id)` | 上传文件到群文件系统 |
| | `upload_private_file(user_id, file, name)` | 上传私聊文件 |
| | `create_group_file_folder(group_id, name, parent_id)` | 创建群文件夹 |
| | `delete_group_file(group_id, file_id)` | 删除群文件 |
| | `delete_group_folder(group_id, folder_id)` | 删除群文件夹 |
| | `download_file(url, file, headers)` | 下载文件到本地 |
| **文件查询** `self.api.qq.query` | `get_group_root_files(group_id)` | 获取群根目录文件 |
| | `get_group_files_by_folder(group_id, folder_id)` | 获取指定文件夹内容 |
| | `get_group_file_url(group_id, file_id)` | 获取文件下载链接 |
| | `get_group_file_system_info(group_id)` | 获取群文件系统信息 |
| **语法糖** `self.api.qq.file` | `get_or_create_group_folder(group_id, name)` | 查找/创建文件夹 |
| | `upload_attachment(target_id, att, folder=...)` | 一步上传 Attachment |
| **消息发送** `self.api.qq` | `send_group_file(group_id, file, name)` | 发送文件消息到聊天窗口 |

> **`upload_group_file` vs `send_group_file`：**
> - `upload_group_file` 将文件上传到群文件管理系统（「群文件」页面可见）
> - `send_group_file` 将文件作为消息段发送到聊天窗口

### `upload_group_file` — file 参数的两种用法

~~~python
# 用法 1：本地路径字符串
await self.api.qq.file.upload_group_file(
    group_id, file=str(path), name="文件名.txt"
)

# 用法 2：直接传 Attachment 对象（自动下载 → 上传 → 清理临时文件）
att = event.message.get_attachments()[0]
await self.api.qq.file.upload_group_file(
    group_id, file=att, name=att.name, folder_id=folder_id
)
~~~

### 转存串联流程

~~~text
用户发送「转存」（回复含附件的消息）
    │
    ▼
get_attachments() ─── 提取附件
    │
    ▼
get_or_create_group_folder() ─── 查找/创建「Bot转存」文件夹
    │
    ▼
upload_group_file(file=att) ─── 直接传 Attachment，自动完成下载→上传→清理
    │
    ▼
回复「✅ 转存成功」
~~~

### 路径定位 — `Path(__file__).parent`

~~~python
PLUGIN_DIR = Path(__file__).parent
test_file = PLUGIN_DIR / "resources" / "example.txt"
~~~

使用 `Path(__file__).parent` 定位插件目录，确保无论 Bot 从哪个工作目录启动，都能正确找到 `resources/` 下的资源文件。

## 运行方式

1. 将 `11_file_and_folder/` 文件夹复制到 `plugins/` 目录
2. 启动 Bot
3. 在群中发送命令测试：

| 命令 | 效果 |
|------|------|
| `上传文件` | 上传示例文件到群文件 |
| `创建文件夹 资料库` | 在群文件根目录创建文件夹 |
| `查看文件` | 列出群根目录下的文件和文件夹 |
| `查看文件夹 <ID>` | 查看指定文件夹内容 |
| `文件链接 <文件ID>` | 获取文件的下载链接 |
| `下载文件 <URL>` | 下载文件到 Bot 本地 |
| `发文件` | 通过消息发送文件（消息段方式） |
| `转存` | 回复含附件的消息，一键转存到「Bot转存」文件夹 |

## 延伸阅读

- [03_rich_message](../03_rich_message/) — 消息段构造与发送
- [08_receive_attachment](../08_receive_attachment/) — 消息附件接收与处理
- [10_info_query](../10_info_query/) — 更多 QQ 查询 API
