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
| [NapCat](<1. NapCat QQ.md>) | QQ | WebUI 扫码 / 快速登录 | OneBot v11 (WebSocket) | QQ 群聊/私聊 Bot |
| [Bilibili](<2. Bilibili.md>) | Bilibili | 终端扫码 | bilibili-api-python | 直播弹幕 / 私信 / 视频评论 |
| [GitHub](<3. GitHub.md>) | GitHub | Personal Access Token | Webhook / REST Polling | Issue/PR/Push 事件处理 |
| [Lark](<6. Lark.md>) | 飞书 | App ID + App Secret | lark-oapi SDK (WebSocket) | 飞书群聊/私聊 Bot |
| [AI](<5. AI.md>) | 多平台 LLM | API Key / 环境变量 | litellm (REST) | Chat / Embeddings / 图像生成 |
| [Mock](<4. Mock 适配器.md>) | 测试 | 无需认证 | 内存模拟 | 插件集成测试 |

## 配置入口

推荐使用 CLI 管理适配器：

```bash
ncatbot adapter                   # 进入副屏交互式管理（启用/禁用/配置一站式完成）
```

副屏中 ↑/↓ 移动光标，空格切换启用/禁用，Enter 进入配置流程，q 保存退出。

`ncatbot init` 的适配器配置也使用相同的副屏交互界面。部分适配器含智能跳过逻辑：

- **NapCat**：选择自动安装时跳过 WS/WebUI 地址输入（启动时自动配置）
- **Bilibili**：选择扫码登录时跳过 sessdata 等凭据手动输入（扫码自动获取）

完整 CLI 命令说明见 [CLI 命令详解](<../8. 命令行工具/1. 命令.md>)。

也可以直接编辑 `config.yaml` 的 `adapters` 列表：

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
  - type: ai
    platform: ai
    enabled: true
    config:
      completion_model: "gpt-4"
```

## 本目录索引

| 文档 | 说明 | 难度 |
|------|------|------|
| [1_napcat_qq.md](<1. NapCat QQ.md>) | NapCat/QQ — Setup/Connect 两种模式、WebUI 登录、诊断 | ⭐ |
| [2_bilibili.md](<2. Bilibili.md>) | Bilibili — 扫码登录、凭据持久化、多数据源配置 | ⭐ |
| [3_github.md](<3. GitHub.md>) | GitHub — Token 认证、Webhook/Polling 双模式、内网穿透 | ⭐⭐ |
| [6_lark.md](<6. Lark.md>) | Lark — 飞书企业应用创建、WebSocket 长连接、群聊/私聊 | ⭐ |
| [5_ai.md](<5. AI.md>) | AI — litellm 统一接口、多提供商、Chat/Embeddings/ImageGen | ⭐ |
| [4_mock.md](<4. Mock 适配器.md>) | Mock — 测试用内存适配器 | ⭐ |

---

## 交叉引用

- 跨平台编程模式（Trait / Platform Filter）→ [multi_platform/](<../10. 多平台开发/>)
- 适配器接口参考（BaseAdapter / AdapterRegistry）→ [reference/adapter/](<../../reference/7. 适配器/>)
- 消息发送（按平台）→ [send_message/](<../4. 消息发送/>)
- Bot API（按平台）→ [api_usage/](<../5. API 使用/>)
