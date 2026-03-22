---
title: Bilibili 平台 API 使用指南
createTime: 2026/03/19 17:26:45
permalink: /guide/9jzb0z71/
---

> Bilibili 平台（B 站适配器）的完整 API 使用教程 — 直播间操作、私信、评论与数据源管理。

---

## Quick Reference

### 访问方式

| 方式 | 类型 | 场景 |
|------|------|------|
| `self.api.bilibili` | `IBiliAPIClient` | 插件中 |
| `bot.api.bilibili` | `IBiliAPIClient` | 非插件模式 |
| `event.reply()` | — | 通用回复（弹幕/评论回复） |

### API 功能分类

| 类别 | 典型方法 | 说明 |
|------|---------|------|
| 直播间操作 | `send_danmu`, `ban_user`, `set_room_silent` | 弹幕、禁言、房间管理 |
| 私信 | `send_private_msg`, `send_private_image` | 私信文字与图片 |
| 评论 | `send_comment`, `reply_comment`, `delete_comment` | 视频/动态评论操作 |
| 数据源管理 | `add_live_room`, `add_comment_watch`, `add_dynamic_watch` | 监听直播间/评论/动态 |
| 动态查询 | `get_user_dynamics`, `get_user_latest_dynamic` | 获取用户动态 |
| 用户查询 | `get_user_info` | 获取用户信息 |
| 视频查询 | `get_video_info`, `parse_bili_id` | 获取视频信息、解析B站链接 |

### 快速示例

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar

class BiliPlugin(NcatBotPlugin):
    name = "bili_demo"
    version = "1.0.0"

    async def on_enable(self):
        # 添加直播间监听
        await self.api.bilibili.add_live_room(12345)

    @registrar.on_message(platform="bilibili")
    async def on_msg(self, event):
        await event.reply(text="收到弹幕！")
```

---

## 认证方式

### 方式 1：扫码登录（推荐）

将 bilibili 适配器的 `sessdata` / `bili_jct` 留空，启动 Bot 时会自动在终端显示二维码：

```yaml
adapters:
  - type: bilibili
    platform: bilibili
    enabled: true
    config:
      sessdata: ""         # 留空即可触发扫码
      bili_jct: ""
      live_rooms: [12345]
```

启动后终端会打印 ASCII 二维码，同时保存 PNG 到临时目录（路径会打印在终端）。使用 Bilibili APP 扫码确认后，凭据自动写入 config.yaml，下次启动不再需要扫码。

凭据过期后再次启动会自动检测并重新触发扫码流程。

### 方式 2：手动填入 Cookie

从浏览器 DevTools → Application → Cookies → bilibili.com 获取以下字段并填入 config.yaml：

```yaml
config:
  sessdata: "从浏览器获取"
  bili_jct: "从浏览器获取"
  buvid3: "可选"
  dedeuserid: "可选"
```

---

## 本目录索引

| 文档 | 内容 |
|------|------|
| [直播间操作](<1. 直播间.md>) | 弹幕发送、用户禁言、全员禁言、房间信息 |
| [私信操作](<2. 私信.md>) | 发送私信文字/图片、获取私信历史 |
| [评论操作](<3. 评论.md>) | 发送/回复/删除/点赞评论 |
| [数据源与查询](<4. 源查询.md>) | 直播间/评论监听管理、用户信息查询 |

---

> **返回**：[Bot API 使用指南](../README.md) · **相关**：[Bilibili 消息发送](<../../4. 消息发送/3. Bilibili/README.md>) · [Bilibili API 参考](<../../../reference/1. Bot API/3. Bilibili/1. API.md>) · **示例**：[examples/bilibili/](../../../../examples/bilibili/01_hello_world/README.md)
