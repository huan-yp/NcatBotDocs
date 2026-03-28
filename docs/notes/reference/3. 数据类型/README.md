---
title: 类型参考
createTime: 2026/03/19 17:26:45
permalink: /reference/yi156fkl/
---

> NcatBot 类型系统完整参考。按 **通用层 → QQ 平台 → Bilibili 平台** 组织。

---

## Quick Reference

### 类型架构

```bash
ncatbot.types                    # 通用层导出（平台无关）
├── ncatbot.types.common         #   MessageSegment, MessageArray, PlainText, At, Image ...
├── ncatbot.types.qq             # QQ 平台: Face, Forward, Music, 枚举, Sender ...
├── ncatbot.types.napcat         # QQ 响应: NapCatModel, GroupInfo, SendMessageResult ...
├── ncatbot.types.bilibili       # Bilibili 平台: BiliSender, 枚举, 事件数据模型 ...
├── ncatbot.types.github         # GitHub 平台: GitHubSender, 枚举, Repo, Commit ...
└── ncatbot.types.lark           # Lark 平台: LarkSender, 枚举, 事件数据模型 ...
```

### 消息段速查

**通用段**（所有平台共享）— `from ncatbot.types import ...`

| 类 | `_type` | 关键字段 |
|----|---------|----------|
| `PlainText` | `"text"` | `text: str` |
| `At` | `"at"` | `user_id: str`（`"all"` = @全体） |
| `Reply` | `"reply"` | `id: str` |
| `Image` | `"image"` | `file`, `url?`, `file_id?` |
| `Record` | `"record"` | `file`, `url?` |
| `Video` | `"video"` | `file`, `url?` |
| `File` | `"file"` | `file`, `url?` |

**QQ 专属段** — `from ncatbot.types.qq import ...`

| 类 | `_type` | 关键字段 |
|----|---------|----------|
| `Face` | `"face"` | `id: str` |
| `Share` | `"share"` | `url`, `title` |
| `Location` | `"location"` | `lat`, `lon` |
| `Music` | `"music"` | `type`, `id?`, `url?` |
| `Json` | `"json"` | `data: str` |
| `Markdown` | `"markdown"` | `content: str` |
| `Forward` | `"forward"` | `id?`, `content?` |
| `QQImage` | `"image"` | `sub_type`, `type?` |

### MessageArray 方法速查

| 方法 | 说明 |
|------|------|
| `MessageArray()` / `.from_list()` / `.from_any()` | 构造 |
| `.add_text()` / `.add_at()` / `.add_image()` / `.add_video()` / `.add_reply()` | 链式添加 |
| `.filter(cls)` / `.filter_text()` / `.filter_at()` / `.filter_image()` | 查询过滤 |
| `.text` | 拼接所有纯文本 |
| `.to_list()` | 序列化为 OB11 dict 列表 |

---

## 本目录索引

| 文件 | 层级 | 说明 |
|------|------|------|
| [1_common_segments.md](<1. 通用消息段.md>) | 通用 | 跨平台消息段基类与 7 种通用段 |
| [2_message_array.md](<2. 消息数组.md>) | 通用 | MessageArray 容器完整方法详解 |
| [3_qq_segments.md](<3. QQ 消息段.md>) | QQ | QQ 专属消息段（Face, Forward, Music 等） |
| [4_qq_responses.md](<4. QQ 响应.md>) | QQ | Bot API 响应类型（NapCat 协议） |
| [5_bilibili_types.md](<5. Bilibili 类型.md>) | Bilibili | Bilibili 平台类型（Sender, 枚举, 事件数据） |
| [6_github_types.md](<6. GitHub 类型.md>) | GitHub | GitHub 平台类型（Repo, Commit, Release, 枚举, 事件数据） |
| [7_lark_types.md](<7. Lark 类型.md>) | Lark | Lark (飞书) 平台类型（LarkSender, 枚举, 事件数据） |

---

## 交叉引用

| 如果你在找… | 去这里 |
|------------|--------|
| 消息发送教程 | [guide/send_message/](<../../guide/4. 消息发送/>) |
| 事件类型参考 | [events/](<../2. 事件类型/>) |
| Bot API 方法签名 | [api/](<../1. Bot API/>) |
