---
title: 事件参考
createTime: 2026/03/19 17:26:45
permalink: /reference/kmerqln8/
---

> 事件体系完整参考。按 **通用层 → QQ 平台 → Bilibili 平台** 组织。
>
> NcatBot 事件系统采用 **数据模型 + 实体** 双层设计，插件只需操作事件实体即可。

---

## Quick Reference

### 事件架构

```bash
ncatbot.event                     # 通用层导出
├── ncatbot.event.common          #   BaseEvent, Mixin traits, create_entity 工厂
├── ncatbot.event.qq              # QQ 事件实体
├── ncatbot.event.bilibili        # Bilibili 事件实体
├── ncatbot.event.github          # GitHub 事件实体（实验性）
└── ncatbot.event.lark            # Lark (飞书) 事件实体
```

### Mixin Trait 速查

| Trait | 能力 | 方法/属性 |
|-------|------|-----------|
| `Replyable` | 可回复 | `async reply(...)` |
| `Deletable` | 可撤回 | `async delete()` |
| `HasSender` | 有发送者 | `user_id`, `sender` |
| `GroupScoped` | 群/频道相关 | `group_id` |
| `Kickable` | 可踢人 | `async kick(...)` |
| `Bannable` | 可禁言 | `async ban(duration=...)` |
| `Approvable` | 可审批 | `async approve(...)`, `async reject(...)` |
| `HasAttachments` | 有可下载附件 | `async get_attachments() -> AttachmentList` |

### QQ 事件速查

```python
from ncatbot.event.qq import GroupMessageEvent, PrivateMessageEvent, NoticeEvent, RequestEvent
```

| 事件类 | Trait 组合 | 关键属性 |
|--------|-----------|----------|
| `MessageEvent` | Replyable, Deletable, HasSender | `message_id`, `message`, `raw_message` |
| `GroupMessageEvent` | + GroupScoped, Kickable, Bannable | `group_id`, `group_name?`, `anonymous` |
| `PrivateMessageEvent` | *(同 MessageEvent)* | — |
| `NoticeEvent` | HasSender, GroupScoped | `notice_type`, `group_id?` |
| `GroupIncreaseEvent` | + Kickable | `sub_type`, `operator_id` |
| `RequestEvent` | HasSender, Approvable | `request_type`, `flag` |
| `MetaEvent` | — | `meta_event_type` |

### Bilibili 事件速查

```python
from ncatbot.event.bilibili import DanmuMsgEvent, BiliPrivateMessageEvent, BiliCommentEvent
```

| 事件类 | Trait 组合 | 关键属性 |
|--------|-----------|----------|
| `DanmuMsgEvent` | Replyable, HasSender, Bannable, GroupScoped | `user_id`, `sender`, `group_id`(=room_id) |
| `SuperChatEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `GiftEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `GuardBuyEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `InteractEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `LikeEvent` | HasSender, GroupScoped | `user_id`, `sender` |
| `BiliPrivateMessageEvent` | Replyable, HasSender | `user_id`, `sender` |
| `BiliCommentEvent` | Replyable, HasSender, Deletable | `user_id`, `sender` |

### GitHub 事件速查

```python
from ncatbot.event.github import GitHubIssueEvent, GitHubPREvent, GitHubPushEvent
```

> **实验性**：GitHub 适配器处于活跃开发中。

| 事件类 | Trait 组合 | 关键属性 |
|--------|-----------|----------|
| `GitHubIssueEvent` | HasSender, Replyable | `issue_number`, `issue_title`, `action`, `repo` |
| `GitHubIssueCommentEvent` | HasSender, Replyable, Deletable | `comment_body`, `issue_number`, `repo` |
| `GitHubPREvent` | HasSender, Replyable | `pr_number`, `pr_title`, `action`, `merged`, `repo` |
| `GitHubPRReviewCommentEvent` | HasSender, Replyable, Deletable | `comment_body`, `pr_number`, `path`, `repo` |
| `GitHubPushEvent` | HasSender | `ref`, `before`, `after`, `commits`, `repo` |
| `GitHubStarEvent` | HasSender | `repo`, `starred_at` |
| `GitHubForkEvent` | HasSender | `repo`, `forkee_full_name` |
| `GitHubReleaseEvent` | HasSender | `release_tag`, `release_name`, `repo` |

### Lark 事件速查

```python
from ncatbot.event.lark import LarkGroupMessageEvent, LarkPrivateMessageEvent
```

| 事件类 | Trait 组合 | 关键属性 |
|--------|-----------|----------|
| `LarkGroupMessageEvent` | Replyable, HasSender | `chat_id`, `group_id`, `content`, `sender` |
| `LarkPrivateMessageEvent` | Replyable, HasSender | `chat_id`, `content`, `user_id`, `sender` |
| `LarkMessageReadEvent` | — | `message_id_list`, `reader_open_id`, `read_time` |
| `LarkMessageRecalledEvent` | — | `message_id`, `chat_id`, `recall_time`, `recall_type` |

---

## 本目录索引

| 文件 | 层级 | 说明 |
|------|------|------|
| [1_common.md](<1. 通用事件.md>) | 通用 | BaseEvent 基类、Mixin Traits、工厂函数 |
| [2_qq_events.md](<2. QQ 事件.md>) | QQ | QQ 事件实体完整参考 |
| [3_bilibili_events.md](<3. Bilibili 事件.md>) | Bilibili | Bilibili 事件实体完整参考 |
| [4_github_events.md](<4. GitHub 事件.md>) | GitHub | GitHub 事件实体完整参考（实验性） |
| [5_lark_events.md](<5. Lark 事件.md>) | Lark | Lark (飞书) 事件实体完整参考 |

---

## 交叉引用

| 如果你在找… | 去这里 |
|------------|--------|
| 消息段类型 | [types/](<../3. 数据类型/>) |
| Bot API 方法 | [api/](<../1. Bot API/>) |
| 事件注册方式 | [guide/plugin/4a.event-registration.md](<../../guide/3. 插件开发/4. 事件注册.md>) |
