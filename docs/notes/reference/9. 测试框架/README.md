---
title: 测试框架参考
createTime: 2026/03/19 17:26:45
permalink: /reference/fy5e7eq8/
---

> `ncatbot.testing` 模块完整 API 参考

---

## Quick Reference

```python
from ncatbot.testing import TestHarness, PluginTestHarness, Scenario
from ncatbot.testing import APICallAssertion, PlatformScope, extract_text
from ncatbot.testing.factories import qq, bilibili, github
```

### 核心组件

| 组件 | 说明 |
|------|------|
| `TestHarness` | 多平台测试编排器 — 注册 handler 并注入事件 |
| `PluginTestHarness` | 插件测试编排器 — 加载真实插件目录并模拟事件流 |
| `Scenario` | 链式构建器 — 编排多步交互场景 |
| `APICallAssertion` | Fluent 断言 — 语义化 API 调用验证 |
| `PlatformScope` | 平台作用域 — 限定断言到单个平台 |
| `extract_text()` | 跨平台文本提取工具 |
| `MockAdapter` / `MockAPIBase` | 内存模拟 — 无需网络连接 |

### 事件工厂

| 平台 | 模块 | 工厂函数 |
|------|------|---------|
| QQ | `factories.qq` | `group_message`, `private_message`, `friend_request`, `group_request`, `napcat_comment`, `group_increase`, `group_decrease`, `group_ban`, `group_msg_emoji_like`, `poke`, `group_upload`, `group_admin`, `friend_add`, `group_recall`, `friend_recall`, `lucky_king`, `honor` |
| Bilibili | `factories.bilibili` | `danmu`, `super_chat`, `gift`, `private_message`, `comment`, `dynamic` |
| GitHub | `factories.github` | `issue_opened`, `issue_closed`, `issue_comment`, `pr_opened`, `push`, `star`, `release_published` |

### 典型用法

```python
async with PluginTestHarness(plugin_names=["my_plugin"], plugins_dir=Path("plugins/")) as h:
    await h.inject(qq.group_message("hello"))
    await h.settle()
    h.assert_api("send_group_msg").called().with_text("hello")
```

---

## 模块结构

```python
ncatbot/testing/              # 测试框架公开 API
├── __init__.py               # 公开导出
├── harness.py                # TestHarness（多平台）
├── plugin_harness.py         # PluginTestHarness
├── assertions.py             # APICallAssertion, PlatformScope, extract_text
├── factories/                # 平台事件工厂
│   ├── __init__.py           # 导出 qq, bilibili, github
│   ├── qq.py                 # QQ 事件工厂（8 个函数）
│   ├── bilibili.py           # Bilibili 事件工厂（6 个函数）
│   └── github.py             # GitHub 事件工厂（7 个函数）
├── scenario.py               # Scenario 链式构建器
├── discovery.py              # 插件发现 + 冒烟测试生成
└── conftest_plugin.py        # pytest 插件（marker + fixture）

ncatbot/adapter/mock/         # Mock 适配器
├── adapter.py                # MockAdapter
├── api_base.py               # MockAPIBase + APICall（共享基类）
├── api.py                    # MockBotAPI（QQ）
├── api_bilibili.py           # MockBiliAPI（Bilibili）
└── api_github.py             # MockGitHubAPI（GitHub）
```

---

## 公开导出

```python
from ncatbot.testing import (
    # 编排器
    TestHarness,
    PluginTestHarness,
    # 场景构建器
    Scenario,
    # Fluent 断言
    APICallAssertion,
    PlatformScope,
    extract_text,
    # 事件工厂（按平台子模块）
    factories,   # factories.qq, factories.bilibili, factories.github
    # 插件发现
    discover_testable_plugins,
    generate_smoke_tests,
)
```

---

## 类 / 函数索引

| 名称 | 类型 | 详细文档 |
|------|------|---------|
| `TestHarness` | class | [1. 测试工具](<1. 测试工具.md#testharness>) |
| `PluginTestHarness` | class | [1. 测试工具](<1. 测试工具.md#plugintestharness>) |
| `APICallAssertion` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#apicallassertion>) |
| `PlatformScope` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#platformscope>) |
| `extract_text()` | function | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#extract_text>) |
| `Scenario` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#scenario>) |
| `APICall` | dataclass | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#apicall>) |
| `MockAPIBase` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#mockapibase>) |
| `MockBotAPI` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#mockbotapi>) |
| `MockBiliAPI` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#mockbiliapi>) |
| `MockGitHubAPI` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#mockgithubapi>) |
| `MockAdapter` | class | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#mockadapter>) |
| `factories.qq.*` | functions | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#qq-事件工厂>) |
| `factories.bilibili.*` | functions | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#bilibili-事件工厂>) |
| `factories.github.*` | functions | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#github-事件工厂>) |
| `discover_testable_plugins()` | function | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#插件发现>) |
| `generate_smoke_tests()` | function | [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md#插件发现>) |

---

## 本目录索引

| 文件 | 说明 |
|------|------|
| [1. 测试工具](<1. 测试工具.md>) | TestHarness + PluginTestHarness 完整 API |
| [2. 工厂场景与 Mock](<2. 工厂场景与 Mock.md>) | 工厂函数、Scenario 构建器、MockAPIBase 体系、Fluent 断言 |
