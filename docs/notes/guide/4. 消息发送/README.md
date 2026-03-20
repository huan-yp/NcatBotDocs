---
title: 发送消息指南
createTime: 2026/03/19 17:26:45
permalink: /guide/newizyxu/
---

> 从快速发送到精细构造，NcatBot 的完整消息发送参考 — 支持多平台。

---

## Quick Reference

### 通用回复（所有平台）

```python
await event.reply(text="收到")  # 自动适配当前平台
```

### QQ 平台

```python
# sugar 方法 — 关键字自动组装
await self.api.qq.post_group_msg(group_id, text="Hello!", at=user_id, image="photo.jpg")

# MessageArray — 精细控制
msg = MessageArray().add_at(user_id).add_text(" 看看这些图 ").add_image("img.png")
await self.api.qq.post_group_array_msg(group_id, msg)
```

### Bilibili 平台

```python
# 弹幕
await self.api.bilibili.send_danmu(room_id, "Hello!")

# 私信
await self.api.bilibili.send_private_msg(user_id, "你好！")

# 评论
await self.api.bilibili.send_comment(resource_id, "video", "好视频！")
```

### GitHub 平台

```python
# Issue 评论（通过事件回复）
await event.reply("感谢你的反馈！")

# Issue 评论（通过 API）
await self.api.github.create_issue_comment("owner/repo", 42, "已处理")

# PR 评论
await self.api.github.create_pr_comment("owner/repo", 10, "LGTM!")
```

---

## 本目录索引

### 通用

| 文档 | 内容 |
|------|------|
| [通用消息概念](<1. 通用/README.md>) | 消息段与 MessageArray 概览 |
| [消息段参考](<1. 通用/1. 消息段.md>) | 所有消息段类型的字段、构造方式和序列化格式 |
| [MessageArray 消息数组](<1. 通用/2. 消息数组.md>) | 容器：创建、链式构造、查询过滤、序列化 |

### QQ 平台

| 文档 | 内容 |
|------|------|
| [QQ 消息发送](<2. QQ/README.md>) | QQ 消息发送方式概览 |
| [便捷接口参考](<2. QQ/1. 语法糖.md>) | event.reply()、所有 sugar 方法完整清单 |
| [合并转发](<2. QQ/2. 合并转发.md>) | ForwardNode / Forward / ForwardConstructor 构造器 |
| [实战示例](<2. QQ/3. 示例.md>) | 常见场景速查：纯文本、图文、回复、转发等 |

### Bilibili 平台

| 文档 | 内容 |
|------|------|
| [Bilibili 消息发送](<3. Bilibili/README.md>) | 弹幕、私信、评论发送概览 |
| [消息发送详解](<3. Bilibili/1. 消息发送.md>) | 弹幕、私信、评论的发送方式与示例 |

### GitHub 平台

| 文档 | 内容 |
|------|------|
| [GitHub 消息发送](<4. GitHub/README.md>) | Issue / PR 评论发送概览 |
| [消息发送详解](<4. GitHub/1. 消息发送.md>) | Issue / PR / Review Comment 发送与示例 |
