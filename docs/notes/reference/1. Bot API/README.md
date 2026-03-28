---
title: API 参考
createTime: 2026/03/19 17:26:45
permalink: /reference/8tjs0s36/
---

> Bot API 层完整参考 — NcatBot 5.2 多平台 API 的签名、参数与用法索引。

---

## Quick Reference

```python
from ncatbot.api import BotAPIClient
```

### 架构总览

```text
BotAPIClient                        ← 多平台路由（纯门面，无业务方法）
├── .qq : QQAPIClient               ← QQ 平台 API
│   ├── .messaging : QQMessaging    ← 消息收发 / 表情 / 已读 / 转发 / 历史
│   ├── .manage : QQManage          ← 群管理 / 好友管理 / 个人资料
│   ├── .query : QQQuery            ← 信息查询（40+ 方法）
│   ├── .file : QQFile              ← 文件上传 / 下载 / 文件夹管理
│   ├── post_group_msg()            ← QQMessageSugarMixin 便捷方法
│   └── send_group_text() ...
├── .bilibili : IBiliAPIClient      ← Bilibili 平台 API
│   ├── send_danmu()                ← 弹幕
│   ├── send_private_msg()          ← 私信
│   ├── send_comment()              ← 评论
│   └── ban_user() ...              ← 直播间管理
├── .github : GitHubBotAPI          ← GitHub 平台 API
│   ├── create_issue()              ← Issue 管理
│   ├── create_issue_comment()      ← 评论
│   ├── merge_pr()                  ← PR 管理
│   └── get_repo() ...              ← 信息查询
├── .lark : LarkBotAPI              ← 飞书平台 API
│   ├── send_text()                 ← 发送文本
│   ├── reply_text()                ← 回复文本
│   ├── send_post()                 ← 发送富文本
│   ├── upload_file()               ← 上传文件
│   └── delete_message() ...        ← 撤回消息
├── .ai : IAIAPIClient              ← AI 平台 API
│   ├── chat()                      ← Chat Completion
│   ├── chat_text()                 ← Chat → 直接返回文本
│   ├── embeddings()                ← 文本向量化
│   ├── image_generation()          ← 图像生成
│   └── generate_image()            ← 图像生成 → Image 消息段
├── .misc : MiscAPI                 ← 杂项工具 API
│   ├── download_to_file()          ← 下载到文件
│   ├── download_to_bytes()         ← 下载到内存
│   ├── http_get()                  ← GET 请求
│   └── is_proxy_valid()            ← 代理检查
├── .platform("xxx")                ← 按名称获取平台 API
└── .platforms                      ← 所有已注册平台 Dict[str, IAPIClient]
```

### Trait 协议（跨平台）

| Trait | 核心方法 | 说明 |
|---|---|---|
| `IMessaging` | `send_private_msg`, `send_group_msg`, `delete_msg`, `send_forward_msg` | 消息发送与撤回 |
| `IGroupManage` | `set_group_kick`, `set_group_ban`, `set_group_admin` ... | 群管理 |
| `IQuery` | `get_login_info`, `get_friend_list`, `get_group_list` ... | 信息查询 |
| `IFileTransfer` | `upload_group_file`, `upload_private_file`, `download_file` | 文件上传/下载 |

> 完整方法签名参见各子文档，或查阅 [API 使用指南](<../../guide/5. API 使用/README.md>) 中的速查表。

---

## 本目录索引

### 通用

| 文件 | 说明 |
|------|------|
| [Trait 协议参考](<1. 通用/1. Traits.md>) | IMessaging, IGroupManage, IQuery, IFileTransfer 完整签名 |

### QQ 平台

| 文件 | 说明 |
|------|------|
| [消息 API](<2. QQ/1. 消息 API.md>) | QQMessaging 核心消息方法 + QQMessageSugarMixin 便捷方法 |
| [管理 API](<2. QQ/2. 管理 API.md>) | QQManage 群管理、好友管理与个人资料 |
| [查询与文件 API](<2. QQ/3. 信息支持 API.md>) | QQQuery 信息查询 + QQFile 文件操作 |

### Bilibili 平台

| 文件 | 说明 |
|------|------|
| [Bilibili API](<3. Bilibili/1. API.md>) | IBiliAPIClient 完整方法签名 |

### GitHub 平台

| 文件 | 说明 |
|------|------|
| [GitHub API](<4. GitHub/1. API.md>) | GitHubBotAPI 完整方法签名（Issue / Comment / PR / Query） |

### Lark 平台

| 文件 | 说明 |
|------|------|
| [Lark API](<7. Lark/1. API.md>) | LarkBotAPI 完整方法签名（消息 / 富文本 / 文件上传 / 撤回） |

### AI 平台

| 文件 | 说明 |
|------|------|
| [AI API](<5. AI/1. API.md>) | IAIAPIClient 完整方法签名（Chat / Embeddings / Image Generation） |

### 杂项工具

| 文件 | 说明 |
|------|------|
| [Misc API](<6. Misc/1. API.md>) | MiscAPI 完整方法签名（下载 / HTTP 请求 / 代理检查） |
