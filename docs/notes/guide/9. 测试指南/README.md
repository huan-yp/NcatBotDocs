---
title: 插件测试指南
createTime: 2026/03/19 17:26:45
permalink: /guide/2kgrpw5d/
---

> 为你的 NcatBot 插件编写自动化测试。

---

## Quick Reference

### 核心组件

| 组件 | 说明 |
|------|------|
| `PluginTestHarness` | 加载真实插件目录，模拟事件流的完整测试编排器 |
| `TestHarness` | 多平台测试编排器，直接注册 handler 并注入事件 |
| `Scenario` | 链式构建器，编排多步交互场景 |
| `APICallAssertion` | Fluent 断言 — 语义化 API 调用验证 |
| `MockAdapter` / `MockAPIBase` | 内存级模拟，无需网络 |

### 事件工厂

```python
from ncatbot.testing.factories import qq, bilibili, github
from ncatbot.testing.factories.qq import group_message, private_message
```

| 平台 | 工厂函数 |
|------|---------|
| QQ | `group_message`, `private_message`, `friend_request`, `group_request`, `group_increase`, `group_decrease`, `group_ban`, `poke` |
| Bilibili | `danmu`, `super_chat`, `gift`, `private_message`, `comment`, `dynamic` |
| GitHub | `issue_opened`, `issue_closed`, `issue_comment`, `pr_opened`, `push`, `star`, `release_published` |

### Harness 常用方法

| 方法 | 说明 |
|------|------|
| `h.inject(event)` | 注入事件 |
| `h.settle()` | 等待所有 handler 执行完成 |
| `h.assert_api("action").called()` | Fluent 断言：API 被调用 |
| `h.assert_api("action").not_called()` | Fluent 断言：API 未被调用 |
| `h.assert_api("action").with_params(k=v)` | Fluent 断言：参数匹配 |
| `h.assert_api("action").with_text("text")` | Fluent 断言：文本匹配 |
| `h.on("qq").assert_api("action")` | 平台作用域断言 |
| `h.reset_api()` | 清空 API 调用记录 |

### 典型测试示例

```python
import pytest
from pathlib import Path
from ncatbot.testing import PluginTestHarness
from ncatbot.testing.factories.qq import group_message

pytestmark = pytest.mark.asyncio(mode="strict")

async def test_hello_command():
    async with PluginTestHarness(plugin_names=["hello_world"], plugins_dir=Path("plugins/")) as h:
        await h.inject(group_message("hello", group_id="100", user_id="99"))
        await h.settle()
        h.assert_api("send_group_msg").called()
```

---

## 本目录索引

| 章节 | 说明 | 难度 |
|------|------|------|
| [1. 快速开始](<1. 快速开始.md>) | 5 分钟写出第一个插件测试 | ⭐ |
| [2. 测试工具](<2. 测试工具.md>) | TestHarness 与 PluginTestHarness 深入使用 | ⭐⭐ |
| [3. 工厂与场景](<3. 工厂与场景.md>) | 事件工厂、Scenario 构建器、自动冒烟测试 | ⭐⭐ |
