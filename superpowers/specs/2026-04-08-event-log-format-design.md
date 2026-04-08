# 事件日志格式可配置化

**日期**: 2026-04-08
**状态**: 已批准

## 背景

当前 `NapCatAdapter._on_event` 以 INFO 级别输出完整 JSON（`收到事件 message: {...}`），用户无法重写或关闭该输出格式。`event_log_levels` 只能控制日志级别和开关，不能控制格式。

用户需求：
1. 能关闭该输出（已有：`event_log_levels: { message: NONE }`）
2. 能将 raw JSON 改为人类可读摘要

## 设计

### 配置模型

在 `LoggingConfig` 新增 `event_log_format` 字段：

```yaml
logging:
  event_log_format: summary  # "summary" | "raw"
  event_log_levels:
    meta_event: NONE
    message: INFO
```

| 值 | 含义 |
|---|---|
| `summary` | **新默认值**，人类可读摘要 |
| `raw` | 当前行为，完整 JSON |

### 日志输出行为

| `event_log_format` | 以 resolved level 输出 | DEBUG 级别额外输出 |
|---|---|---|
| `summary` | 人类可读摘要 | 完整 JSON |
| `raw` | 完整 JSON | — |

当 `event_log_format == "summary"` 时，`_on_event` 会：
1. 以 resolved level 输出摘要
2. 额外以 DEBUG 级别输出完整 JSON（方便调试）

### 各事件类型 summary 格式

| 事件类型 | 摘要格式 |
|---|---|
| 群消息 | `[群消息] {group_name}({group_id}) {nickname}({user_id}): {raw_message_preview}` |
| 私聊消息 | `[私聊消息] {nickname}({user_id}): {raw_message_preview}` |
| 通知 | `[通知] {notice_type} 群:{group_id} 用户:{user_id}` |
| 请求 | `[请求] {request_type} 用户:{user_id}` |
| 元事件 | `[元事件] {meta_event_type}` |
| 未知/其他 | `[事件] {post_type}: {json_preview[:200]}` |

- `raw_message_preview` 截断到 100 字符
- 字段缺失时优雅降级（如无 `group_name` 则只显示 `group_id`）

### 跨平台复用

`format_event_summary()` 放在 `ncatbot/utils/logger/event_log.py`，作为所有适配器的通用能力。各适配器自行调用。

### Breaking Change

默认行为从输出 raw JSON 改为输出 summary。用户配置 `event_log_format: raw` 可恢复旧行为。

## 代码变更范围

| 文件 | 变更 |
|---|---|
| `ncatbot/utils/config/models.py` | `LoggingConfig` 新增 `event_log_format` 字段 |
| `ncatbot/utils/logger/event_log.py` | 新增 `format_event_summary()` 函数 |
| `ncatbot/utils/logger/__init__.py` | 导出新函数 |
| `ncatbot/utils/__init__.py` | 导出新函数 |
| `ncatbot/adapter/napcat/adapter.py` | `_on_event` 使用新格式逻辑 |

## 测试

- `format_event_summary()` 单元测试：覆盖各事件类型
- `_on_event` 集成测试：验证 summary / raw 模式的日志输出
- 配置验证测试：`event_log_format` 非法值拒绝
