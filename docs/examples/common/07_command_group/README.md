# 07_command_group

> 分类：common

## 这个示例教什么

展示 `CommandGroupHook` 命令组分层路由机制：用一个前缀命令管理多个子命令，支持参数绑定和多别名。

## 你将学到

- `CommandGroupHook` 的创建与注册
- `@hook.subcommand()` 子命令装饰器
- 子命令参数自动绑定（int / float / str）
- 命令别名支持（如 `/admin` 和 `/a`）
- `ignore_case` 大小写不敏感匹配

## 前置知识

- [common/01_hello_world](../01_hello_world/) — 插件基础结构
- 理解 `@registrar.on_group_message()` 装饰器

## 目录结构

```text
07_command_group/
├── main.py
└── manifest.toml
```

## 完整代码

```python
"""
common/07_command_group — 命令组分层路由插件

演示功能:
  - 使用 CommandGroupHook 实现分层命令
  - 参数类型自动绑定（int/float/str/At）
  - 命令别名支持
  - @hook.subcommand() 装饰器注册子命令并由主 handler 分发

使用方式:
  "/admin kick 12345"       → 踢出成员
  "/admin ban 12345 120"    → 禁言 120 分钟
  "/calc add 10 20"         → 计算加法
  "/help" 或 "/?"           → 查看帮助
"""

import inspect
from ncatbot.core import CommandGroupHook, registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
# ... (见 main.py 完整代码)
```

## 关键代码讲解

### 创建命令组

```python
admin_hook = CommandGroupHook("admin", "/admin", "a", ignore_case=True)
```

第一个参数是命令组名，后续参数是触发前缀（可多个），`ignore_case=True` 表示 `/Admin` 和 `/admin` 均可触发。

### 注册子命令

```python
@admin_hook.subcommand("kick", "remove")
async def admin_kick(self, event, user_id: int):
    ...
```

`subcommand()` 接受一个或多个别名。参数自动从消息中提取和绑定。

### 挂载到消息处理器

```python
@registrar.on_group_message()
@admin_hook
async def on_admin(self, event, **kwargs):
    ...
```

通过将 `@admin_hook` 作为装饰器叠加，实现命令组的自动分发。

## 运行方式

将本文件夹复制到 `plugins/` 目录，启动 Bot。在群里发送 `/admin kick 12345` 等命令即可测试。

## 延伸阅读

- [common/01_hello_world](../01_hello_world/) — 基础命令注册
- [qq/02_command_binding](../../qq/02_command_binding/) — QQ 平台命令参数绑定全貌
