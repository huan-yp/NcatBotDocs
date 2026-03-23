---
title: 使用指南
createTime: 2026/03/19 17:26:45
permalink: /guide/
---

> NcatBot 从入门到进阶的完整指南 — 面向 Bot 开发者的任务导向文档。

---

## Quick Reference

### 两种使用模式

| 模式 | 入口 | 特点 | Mixin / 热重载 |
|------|------|------|---------------|
| 非插件模式 | `main.py` + `registrar` 装饰器 | 快速原型，无需插件目录 | ❌ |
| 插件模式（推荐） | `NcatBotPlugin` 子类 + `manifest.toml` | 配置持久化、RBAC、定时任务等 | ✅ |

从零开始的完整流程见 [quick_start/](<1. 快速开始/>)。

### 核心导入路径

| 导入 | 说明 |
|------|------|
| `from ncatbot.app import BotClient` | 应用入口 |
| `from ncatbot.core import registrar` | 全局事件注册器 |
| `from ncatbot.plugin import NcatBotPlugin` | 插件基类 |
| `from ncatbot.event.qq import GroupMessageEvent` | QQ 群消息事件 |
| `from ncatbot.event.qq import PrivateMessageEvent` | QQ 私聊事件 |
| `from ncatbot.types import MessageArray` | 消息数组 |
| `from ncatbot.utils import get_log` | 日志工具 |

### 最常用操作速查

| 操作 | 调用方式 | 需要插件模式 |
|------|---------|-------------|
| 注册群命令 | `@registrar.on_group_command("cmd")` | ❌ |
| 注册私聊命令 | `@registrar.on_private_command("cmd")` | ❌ |
| 回复消息 | `await event.reply(text="内容")` | ❌ |
| 发送群消息 | `await self.api.qq.post_group_msg(gid, text="内容")` | ❌ |
| 发送图片 | `await self.api.qq.send_group_image(gid, "url")` | ❌ |
| 读取配置 | `self.get_config("key")` | ✅ ConfigMixin |
| 写入配置 | `self.set_config("key", value)` | ✅ ConfigMixin |
| 持久化数据 | `self.data["key"] = value` | ✅ DataMixin |
| 权限检查 | `self.check_permission(uid, "perm")` | ✅ RBACMixin |
| 定时任务 | `self.add_scheduled_task("名称", "60s")` | ✅ TimeTaskMixin |
| 等待事件 | `await self.wait_event(predicate, timeout=30)` | ✅ EventMixin |
| 群管理 | `await self.api.qq.manage.set_group_ban(gid, uid)` | ❌ |
| 信息查询 | `await self.api.qq.query.get_group_info(gid)` | ❌ |

### 按需求找文档

| 我想… | 去这里 |
|-------|--------|
| 从零跑通第一个 Bot | [quick_start/](<1. 快速开始/>) |
| 开发插件 | [plugin/](<3. 插件开发/>) |
| 发消息、构造复杂消息 | [send_message/](<4. 消息发送/>) |
| 调用群管理/查询/文件 API | [api_usage/](<5. API 使用/>) |
| 管理 config.yaml | [configuration/](<6. 配置管理/>) |
| 用 CLI 管理项目 | [cli/](<8. 命令行工具/>) |
| 添加权限控制 | [rbac/](<7. RBAC 权限/>) |
| 写插件测试 | [testing/](<9. 测试指南/>) |
| 接入多平台 | [multi_platform/](<10. 多平台开发/>) |
| 各平台登录与配置 | [adapter/](<2. 适配器/>) |
| 零基础安装 Python/环境 | [best_practices/](<12. 最佳实践/1. 环境安装.md>) |
| 部署到服务器 | [best_practices/](<12. 最佳实践/2. 部署指南.md>) |
| 用 AI 工具加速开发 | [best_practices/](<12. 最佳实践/3. AI 辅助开发.md>) |

---

## 本目录索引

| 目录 | 说明 | 难度 |
|------|------|------|
| [quick_start/](<1. 快速开始/>) | 从零启动 — 安装、配置、两种模式启动 | ⭐ |
| [adapter/](<2. 适配器/>) | 适配器登录与使用 — NapCat / Bilibili / GitHub / Mock | ⭐ |
| [plugin/](<3. 插件开发/>) | 插件开发完整指南（12 篇） | ⭐ - ⭐⭐⭐ |
| [send_message/](<4. 消息发送/>) | 消息发送 — 消息段、MessageArray、转发、语法糖 | ⭐ |
| [api_usage/](<5. API 使用/>) | Bot API 使用 — 消息、群管理、查询 | ⭐⭐ |
| [configuration/](<6. 配置管理/>) | 配置管理 — config.yaml 结构与安全校验 | ⭐⭐ |
| [cli/](<8. 命令行工具/>) | CLI 工具 — init / run / dev / config / plugin | ⭐ |
| [rbac/](<7. RBAC 权限/>) | RBAC 权限管理 — 权限模型与插件集成 | ⭐⭐⭐ |
| [testing/](<9. 测试指南/>) | 插件测试 — Harness、工厂函数、Scenario | ⭐⭐ |
| [multi_platform/](<10. 多平台开发/>) | 多平台开发 — Trait 协议与跨平台插件 | ⭐⭐ |
| [best_practices/](<12. 最佳实践/>) | 最佳实践 — 环境安装、部署指南、AI 辅助开发 | ⭐ |

---

## 交叉引用

- API 完整签名 → [reference/](../reference/)
- 核心概念速查 → [concepts.md](<11. 架构与概念/2. 核心概念.md>)
- 架构全景 → [architecture.md](<11. 架构与概念/1. 架构总览.md>)
