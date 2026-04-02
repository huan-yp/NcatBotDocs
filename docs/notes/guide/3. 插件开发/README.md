---
title: 插件开发指南
createTime: 2026/03/19 17:26:45
permalink: /guide/r3952n4t/
---

> 插件开发从入门到实战 — 覆盖插件结构、生命周期、事件处理、Mixin 能力、Hook 机制和高级主题。

---

## Quick Reference

### 最小可运行插件

```python
from ncatbot.plugin import NcatBotPlugin
from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent

class HelloPlugin(NcatBotPlugin):
    name = "hello"
    version = "1.0.0"

    @registrar.on_group_command("hello")
    async def on_hello(self, event: GroupMessageEvent):
        await event.reply(text="Hello!")
```

### 生命周期钩子

| 钩子 | 说明 |
|------|------|
| `_init_()` | 同步初始化（on_load 之前） |
| `on_load()` | 异步初始化（注册权限、定时任务等） |
| `on_close()` | 异步清理 |
| `_close_()` | 同步清理 |

### 运行时属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `self.api` | `BotAPIClient` | Bot API 客户端 |
| `self.services` | `ServiceManager` | 服务管理器 |
| `self.workspace` | `Path` | 插件工作目录 |
| `self.debug` | `bool` | 调试模式 |

### Registrar 装饰器

| 装饰器 | 监听事件 |
|--------|---------|
| `@registrar.on_group_command("cmd")` | 群命令 |
| `@registrar.on_private_command("cmd")` | 私聊命令 |
| `@registrar.on_command("cmd")` | 群+私聊命令 |
| `@registrar.on_group_message()` | 群消息 |
| `@registrar.on_private_message()` | 私聊消息 |
| `@registrar.on_message()` | 所有消息 |
| `@registrar.on_notice()` | 通知事件 |
| `@registrar.on_request()` | 请求事件 |
| `@registrar.qq.on_poke()` | QQ 戳一戳 |
| `@registrar.qq.on_group_msg_emoji_like()` | QQ 群消息表情回应 |
| `@registrar.qq.on_group_increase()` | QQ 群成员增加 |
| `@registrar.qq.on_group_decrease()` | QQ 群成员减少 |
| `@registrar.qq.on_friend_request()` | QQ 好友请求 |
| `@registrar.qq.on_group_request()` | QQ 群请求 |
| `@registrar.bilibili.on_danmu()` | B站弹幕 |
| `@registrar.bilibili.on_gift()` | B站礼物 |
| `@registrar.github.on_push()` | GitHub Push |
| `@registrar.github.on_issue()` | GitHub Issue |
| `@registrar.on(event_type, ...)` | 通用注册 |

> 所有装饰器支持 `priority=`（优先级）和 `platform=`（平台过滤）参数。命令装饰器额外支持 `ignore_case=`。

### Mixin 能力（继承 NcatBotPlugin 自动获得）

| Mixin | 方法 | 说明 |
|-------|------|------|
| **ConfigMixin** | `get_config(key, default=None)` | 读取 YAML 配置 |
| | `set_config(key, value)` | 写入并持久化 |
| | `remove_config(key)` | 移除配置项 |
| | `update_config(updates)` | 批量更新 |
| **DataMixin** | `self.data[key]` | 读写 JSON 持久化数据（字典） |
| **RBACMixin** | `check_permission(user, permission)` | 检查权限 |
| | `add_permission(path)` | 注册权限路径 |
| | `add_role(role, exist_ok=True)` | 创建角色 |
| | `self.rbac` | 访问 RBACService 实例 |
| **TimeTaskMixin** | `add_scheduled_task(name, interval, ...)` | 添加定时任务 |
| | `remove_scheduled_task(name)` | 移除定时任务 |
| | `list_scheduled_tasks()` | 列出任务 |
| **EventMixin** | `wait_event(predicate=, timeout=)` | 等待匹配事件 |
| | `self.events(type)` | 创建事件流（async for） |

### 阅读路线

- **新手**：1 → 2 → 4a（快速入门 → 插件结构 → 事件注册）
- **进阶**：5a / 5b → 6（Mixin 能力 → Hook 机制）
- **高级**：4c → 7a → 7b（Predicate DSL → 模式 → 实战）

---

## 本目录索引

| 章节 | 说明 | 难度 |
|------|------|------|
| [1. 快速开始](<1. 快速开始.md>) | 环境准备、安装、5 分钟跑通第一个插件 | ⭐ |
| [2. 插件结构](<2. 插件结构.md>) | manifest.toml 详解、基类选择、多文件组织 | ⭐ |
| [3. 生命周期](<3. 生命周期.md>) | 加载流程、卸载流程、生命周期钩子 | ⭐ |
| [4. 事件注册](<4. 事件注册.md>) | 事件类型体系、装饰器路由、优先级 | ⭐⭐ |
| [5. 事件高级](<5. 事件高级.md>) | 事件流、wait_event、实战组合 | ⭐⭐ |
| [6. 谓词 DSL](<6. 谓词 DSL.md>) | 谓词组合、P 基类、工厂函数 | ⭐⭐ |
| [7. 配置与数据](<7. 配置与数据.md>) | ConfigMixin + DataMixin | ⭐⭐ |
| [8. RBAC / 定时 / 事件](<8. RBAC 定时任务与事件.md>) | RBACMixin + TimeTaskMixin + EventMixin | ⭐⭐ |
| [9. Hooks](<9. Hooks.md>) | 三阶段模型、内置 Hook、自定义编写 | ⭐⭐ |
| [10. 模式](<10. 模式.md>) | 热重载、依赖管理、跨插件交互 | ⭐⭐⭐ |
| [11. 案例研究](<11. 案例研究.md>) | 群管理/定时报告/外部 API 案例 | ⭐⭐⭐ |
| [12. 内置管理命令](<12. 内置管理命令.md>) | 系统内置 `!` 命令、权限模型与 plugin.* 配置 | ⭐⭐ |
