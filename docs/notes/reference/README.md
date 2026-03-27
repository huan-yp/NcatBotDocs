---
title: API 参考
createTime: 2026/03/19 17:26:45
permalink: /reference/
---

> 所有模块的完整 API 参考文档

---

## Quick Reference

### 按需查找

| 你在找… | 去这里 | 关键类/模块 |
|---------|--------|------------|
| 消息发送方法签名 | [api/](<1. Bot API/>) | `QQMessaging`, `QQMessageSugarMixin` |
| 群管理/好友/账号操作 | [api/](<1. Bot API/>) | `QQManage` |
| 信息查询（群/好友/消息） | [api/](<1. Bot API/>) | `QQQuery` |
| 文件上传/下载 | [api/](<1. Bot API/>) | `QQFile` |
| 事件类型和属性 | [events/](<2. 事件类型/>) | `GroupMessageEvent`, `NoticeEvent`, `RequestEvent` |
| 消息段类型（PlainText/At/Image） | [types/](<3. 数据类型/>) | `MessageSegment`, `MessageArray` |
| 装饰器注册和 Hook | [core/](<4. 核心模块/>) | `Registrar`, `Hook`, `HookStage` |
| Predicate DSL | [core/](<4. 核心模块/>) | `same_user`, `has_keyword`, `msg_matches` |
| 插件基类和 Mixin | [plugin/](<5. 插件系统/>) | `NcatBotPlugin`, `ConfigMixin`, `EventMixin` |
| RBAC/定时任务服务 | [services/](<6. 服务层/>) | `RBACService`, `TimeTaskService` |
| 适配器接口 | [adapter/](<7. 适配器/>) | `BaseAdapter`, `AdapterRegistry` |
| 日志/网络/配置工具 | [utils/](<8. 工具模块/>) | `get_log`, `ConfigManager`, `post_json` |
| 测试框架 | [testing/](<9. 测试框架/>) | `PluginTestHarness`, `Scenario` |
| CLI 命令 | [cli.md](<10. CLI/1. 命令参考.md>) | `ncatbot init/run/dev` |

---

## 模块索引

| 目录 | 说明 |
|------|------|
| [api/](<1. Bot API/>) | Bot API 方法参考 |
| [events/](<2. 事件类型/>) | 事件类型参考 |
| [types/](<3. 数据类型/>) | 数据类型参考（消息段、MessageArray） |
| [core/](<4. 核心模块/>) | 核心模块参考（Dispatcher、Predicate DSL、Registry / Hook） |
| [plugin/](<5. 插件系统/>) | 插件系统参考（基类、Mixin） |
| [services/](<6. 服务层/>) | 服务层参考（RBAC、定时任务、配置存储） |
| [adapter/](<7. 适配器/>) | 适配器参考（WebSocket、协议处理） |
| [utils/](<8. 工具模块/>) | 工具模块参考（日志、IO、装饰器） |
| [cli.md](<10. CLI/1. 命令参考.md>) | CLI 命令参考（全部命令签名与参数） |
| [testing/](<9. 测试框架/>) | 测试框架参考（TestHarness、事件工厂、Mock） |

---

## 交叉引用

| 如果你在找… | 去这里 |
|------------|--------|
| 插件开发教程 | [guide/plugin/](<../guide/3. 插件开发/>) |
| 消息发送教程 | [guide/send_message/](<../guide/4. 消息发送/>) |
| 插件测试教程 | [guide/testing/](<../guide/9. 测试指南/>) |
| CLI 命令用法 | [guide/cli/](<../guide/8. 命令行工具/>) |
| 设计决策（为什么这样设计） | [contributing/design_decisions/](<../contributing/2. 设计决策/>) |
| 模块内部实现细节 | [contributing/module_internals/](<../contributing/3. 模块内部实现/>) |
