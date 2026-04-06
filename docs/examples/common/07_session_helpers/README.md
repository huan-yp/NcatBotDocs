# 07_session_helpers

> 分类：common

## 文件结构

~~~text
07_session_helpers/
├── main.py
└── manifest.toml
~~~

## main.py

~~~python
"""
common/07_session_helpers — Session 便利方法（跨平台）

演示功能:
  - session_prompt 一站式：发问题 + 等回复 + 超时/取消自动回复
  - session_choose 选择题模式：有效选项匹配 + 无效重试
  - wait_session_reply 手动控制返回值
  - SessionResult 统一判断 ok / cancelled / timed_out

本示例与 06_multi_step_dialog 功能等价，展示新 API 如何消除样板代码。
使用方式:
  发送 "注册" → 依次输入名字→年龄→确认 → 保存
  发送 "我的信息" → 查看已注册的信息
"""
~~~

## 演示功能

| 功能 | API | 说明 |
|------|-----|------|
| 一站式问答 | `session_prompt()` | 发送提示 → 等回复 → 超时/取消自动回复 |
| 选择题 | `session_choose()` | 有效选项匹配 + 无效输入自动重试 |
| 结果判断 | `SessionResult` | `.ok` / `.text` / `.cancelled` / `.timed_out` / `.key` |

## 与 06_multi_step_dialog 的对比

| 维度 | 06（旧模式） | 07（新模式） |
|------|------------|------------|
| session 绑定 | 手动 `from_event(event)` | 自动绑定 |
| 超时处理 | `try/except TimeoutError` | `result.timed_out` |
| 取消检测 | 手动 `if text == "取消"` | `cancel_words=["取消"]` |
| 文本提取 | `reply.data.raw_message.strip()` | `result.text` |
| 自动回复 | 手动 `await event.reply(...)` | `timeout_reply=` / `cancel_reply=` |
| 选择题 | 手动 `if confirm != "确认"` | `session_choose(choices=...)` |

## 运行方式

同其他 common 示例，无平台依赖。

## 相关

- [06_multi_step_dialog](../06_multi_step_dialog/README.md) — 旧模式对照
- [Mixin 详解 — EventMixin](/reference/hp5alcki/) — 完整 API 参考
- [事件高级用法](/guide/fzk8vub0/) — Session 便利方法指南
