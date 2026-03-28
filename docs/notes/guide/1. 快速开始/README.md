---
title: Quick Start
createTime: 2026/03/19 17:26:45
permalink: /guide/695ruqzj/
---

> 从零开始，5 分钟运行你的第一个 NcatBot。覆盖三种启动方式：零代码 CLI、非插件模式、插件模式。

---

## 介绍

**NcatBot** 是一个基于 Python 的异步多平台 Bot 框架，以 **QQ 平台**为核心，同时适配 **Bilibili**（直播/私信/评论）和 **GitHub**（Webhook/Polling）等其它主流平台。

### 亮点

- **插件系统** — 配置持久化、权限控制、定时任务、热重载，开箱即用
- **事件驱动** — 装饰器注册 + 谓词 DSL，处理消息、通知、请求
- **跨平台** — 通过 Adapter/Trait 抽象，一套插件适配多个平台
- **CLI 工具** — `ncatbot init` / `run` / `dev` / `plugin` / `adapter`，零代码启动
- **内置 skill** — 强烈推荐使用 AI Agent 进行 NcatBot 插件开发，高效、便捷、功能强大。 
- **Python ≥ 3.12**，原生 async/await，类型标注完备

默认启用 QQ 平台。需要接入 Bilibili 或 GitHub 或其它平台？参见 [适配器指南](<../2. 适配器/>)。

参阅 [最佳实践](<../12. 最佳实践/>) 获取环境安装、生产部署、AI 开发等实用指南。

## Quick Reference

### 最小插件模式（通过 CLI 快速开始）

#### 第 1 步 — 安装 NcatBot

```bash
pip install ncatbot5
```

#### 第 2 步 — 初始化项目

```bash
mkdir my-bot && cd my-bot
ncatbot init
```

按提示交互式输入：

| 提示 | 示例输入 |
|------|---------|
| Bot QQ 号 | `123456789` |
| 管理员 QQ 号 | `987654321` |

完成后自动生成：

```text
my-bot/
├── config.yaml                   # 配置文件
└── plugins/
    └── {你的用户名}_plugin/             # 模板插件目录
        ├── manifest.toml
        └── plugin.py
```

#### 第 3 步 — 启动 Bot

```bash
ncatbot dev     # 开发模式：debug 日志 + 热重载
```

或生产模式：

```bash
ncatbot run
```

按照终端输出的提示，扫描二维码登录。

连接成功后终端输出类似：

```text
[INFO] WebSocket 连接已建立: ws://localhost:3001
[INFO] 插件 {你的用户名}_plugin 已加载
```

在群聊发送 `hello`，Bot 回复 "Hello from plugin!" 即成功。

如果你想最快的定制你的插件，推荐前往 [AI 开发指南](<../12. 最佳实践/3. AI 辅助开发.md>)，使用 AI Agent 进行插件开发，效率更高。

如果你更喜欢古法编程，请继续阅读本文档。

### 最小非插件模式

安装 → 写 config.yaml → 写 main.py → 运行：

```bash
pip install ncatbot5
```

```python
# main.py
from ncatbot.app import BotClient
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent

bot = BotClient()

@registrar.on_group_command("hello", ignore_case=True)
async def on_hello(event: GroupMessageEvent):
    await event.reply(text="Hello, NcatBot!")

if __name__ == "__main__":
    bot.run()
```

---

## 本目录索引

| 文件 | 内容 |
|------|------|
| [1.install-config.md](<1. 安装与配置.md>) | 安装 NcatBot、编写 config.yaml、确认 NapCat 连接 |
| [2.non-plugin-mode.md](<2. 非插件模式.md>) | 非插件模式完整流程 — 直接在 main.py 注册回调，适合快速原型 |
| [3.plugin-mode.md](<3. 插件模式.md>) | 插件模式完整流程 — 创建插件目录 + manifest + 插件类，适合正式项目 |

---

## 交叉引用

- 两种模式的区别 → [使用指南首页](../README.md)
- 插件开发深入 → [插件开发指南](<../3. 插件开发/>)
- CLI 命令详解 → [CLI 指南](<../8. 命令行工具/>)
