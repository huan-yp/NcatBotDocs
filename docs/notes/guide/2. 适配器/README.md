---
title: 适配器登录与使用指南
createTime: 2026/03/19 17:26:45
permalink: /guide/vagz7643/
---

> 各内置适配器的认证、配置与使用流程 — 从零开始接入每个平台。

---

## 适配器一览

| 适配器 | 平台 | 认证方式 | 协议 | 适用场景 |
|--------|------|---------|------|---------|
| [NapCat](1_napcat_qq.md) | QQ | WebUI 扫码 / 快速登录 | OneBot v11 (WebSocket) | QQ 群聊/私聊 Bot |
| [Bilibili](2_bilibili.md) | Bilibili | 终端扫码 | bilibili-api-python | 直播弹幕 / 私信 / 视频评论 |
| [GitHub](3_github.md) | GitHub | Personal Access Token | Webhook / REST Polling | Issue/PR/Push 事件处理 |
| [Mock](4_mock.md) | 测试 | 无需认证 | 内存模拟 | 插件集成测试 |

## 配置入口

所有适配器均通过 `config.yaml` 的 `adapters` 列表配置：

```yaml
adapters:
  - type: napcat          # 适配器名称
    platform: qq          # 平台标识
    enabled: true
    config:               # 适配器专属配置
      ws_uri: ws://localhost:3001
      ws_token: napcat_ws
```

多个适配器可同时运行：

```yaml
adapters:
  - type: napcat
    platform: qq
    enabled: true
    config:
      ws_uri: ws://localhost:3001
  - type: bilibili
    platform: bilibili
    enabled: true
    config:
      live_rooms: [12345]
  - type: github
    platform: github
    enabled: true
    config:
      token: "ghp_xxxx"
      repos: ["owner/repo"]
```

## 本目录索引

| 文档 | 说明 | 难度 |
|------|------|------|
| [1_napcat_qq.md](1_napcat_qq.md) | NapCat/QQ — Setup/Connect 两种模式、WebUI 登录、诊断 | ⭐ |
| [2_bilibili.md](2_bilibili.md) | Bilibili — 扫码登录、凭据持久化、多数据源配置 | ⭐ |
| [3_github.md](3_github.md) | GitHub — Token 认证、Webhook/Polling 双模式、内网穿透 | ⭐⭐ |
| [4_mock.md](4_mock.md) | Mock — 测试用内存适配器 | ⭐ |

---

## 交叉引用

- 跨平台编程模式（Trait / Platform Filter）→ [multi_platform/](../multi_platform/)
- 适配器接口参考（BaseAdapter / AdapterRegistry）→ [reference/adapter/](../../reference/adapter/)
- 消息发送（按平台）→ [send_message/](../send_message/)
- Bot API（按平台）→ [api_usage/](../api_usage/)
