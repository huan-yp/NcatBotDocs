# GitHub ↔ QQ 双向桥接机器人

> ⚠️ 本示例依赖开发中的 GitHub Adapter，API 可能变动。

## 功能概览

```
GitHub                          QQ 群
  │                               │
  │  Issue 创建/关闭/评论          │
  │  PR 打开/合并                  │
  │  Push 提交                     │
  │ ─────────────────────────────→ │  自动转发通知
  │                               │
  │                               │  引用(reply)通知消息
  │  ← Issue Comment ──────────── │  自动回复到 GitHub
  │                               │
  │                               │  issue <number>
  │  ← 查询 Issue ─────────────── │  查看 Issue 详情
  │                               │
  │                               │  issue-reply <number> <内容>
  │  ← Issue Comment ──────────── │  直接评论 Issue
```

## QQ 群命令

| 命令 | 说明 |
|------|------|
| `issue <编号>` | 查看 Issue 详情 |
| `issue-reply <编号> <内容>` | 直接评论某个 Issue |
| `gh-status` | 查看桥接状态（平台/群号/仓库/映射数） |
| 引用通知消息并回复 | 自动作为 GitHub Issue Comment 发送 |

## 配置

### 1. 适配器配置 (config.yaml)

同时启用 NapCat 和 GitHub 适配器：

```yaml
adapters:
  - type: napcat
    platform: qq
    enabled: true
    config:
      # ... NapCat 配置

  - type: github
    platform: github
    enabled: true
    config:
      token: "github_pat_xxx"
      repos: ["owner/repo"]
      mode: webhook
      webhook_host: "127.0.0.1"
      webhook_port: 8741
      webhook_path: "/webhook"
      webhook_secret: "<your-secret>"
```

### 2. 插件配置

在插件的配置文件中设置（通过 ConfigMixin 读取）：

```yaml
target_qq_group: 123456789      # 转发目标 QQ 群号
target_repo: "owner/repo"       # 监听的 GitHub 仓库
```

### 3. Webhook 转发（本地开发）

使用 smee.io 将 GitHub Webhook 转发到本地：

```bash
# 1. 访问 https://smee.io/new 获取频道 URL
# 2. 安装 gosmee 并启动转发
gosmee client <smee-url> http://127.0.0.1:8741/webhook
```

## 核心机制

**消息映射追踪**：当 GitHub 事件转发到 QQ 群时，记录 QQ 消息 ID → GitHub Issue 的映射。
用户在 QQ 群中引用(reply)某条通知消息时，插件通过映射找到对应的 Issue，
将回复内容自动作为 GitHub Issue Comment 发送，实现双向桥接。

映射默认保留 24 小时后自动清理。

## 涉及的框架特性

- `registrar.github.*` / `registrar.qq.*` 平台子注册器
- `self.api.qq.*` / `self.api.github.*` 多平台 API
- `ConfigMixin` 配置管理
- `HasSender` Trait 跨平台获取发送者
- `MessageArray.filter()` 消息段过滤
