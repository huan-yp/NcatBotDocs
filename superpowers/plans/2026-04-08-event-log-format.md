# 事件日志格式可配置化 Implementation Plan

> **For agentic workers:** REQUIRED: Use the `subagent-driven-development` agent (recommended) or `executing-plans` agent to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让事件日志支持人类可读摘要格式，默认输出 summary，可配置切换回 raw JSON，DEBUG 级别保留完整 JSON。

**Architecture:** 在 `LoggingConfig` 新增 `event_log_format` 配置项（`summary` | `raw`），新增 `format_event_summary()` 纯函数将 `BaseEventData` 按事件类型格式化为摘要字符串，在 `NapCatAdapter._on_event` 中根据配置选择输出格式。

**Tech Stack:** Python, Pydantic, pytest

**Spec:** `docs/superpowers/specs/2026-04-08-event-log-format-design.md`

---

### File Structure

| 文件 | 职责 | 动作 |
|------|------|------|
| `ncatbot/utils/config/models.py` | `LoggingConfig.event_log_format` 配置字段 | 修改 |
| `ncatbot/utils/logger/event_log.py` | `format_event_summary()` 纯函数 | 修改 |
| `ncatbot/utils/logger/__init__.py` | 导出 `format_event_summary` | 修改 |
| `ncatbot/utils/__init__.py` | 导出 `format_event_summary` | 修改 |
| `ncatbot/adapter/napcat/adapter.py` | `_on_event` 使用新格式逻辑 | 修改 |
| `tests/unit/config/test_event_log_format_config.py` | 配置字段验证测试 | 新建 |
| `tests/unit/adapter/test_event_log_format.py` | `format_event_summary()` 单元测试 | 新建 |

---

### Task 1: 配置模型 — `event_log_format` 字段

**Files:**
- Modify: `ncatbot/utils/config/models.py:146-186` (`LoggingConfig` 类)
- Test: `tests/unit/config/test_event_log_format_config.py`

- [ ] **Step 1: Write the failing test for config validation**

Create `tests/unit/config/test_event_log_format_config.py`:

```python
"""事件日志格式配置验证。"""

import pytest
from ncatbot.utils.config.models import LoggingConfig


class TestEventLogFormatConfig:
    """ELF-01 ~ ELF-04: event_log_format 配置字段验证"""

    def test_default_is_summary(self):
        """ELF-01: 默认值为 summary"""
        cfg = LoggingConfig()
        assert cfg.event_log_format == "summary"

    def test_accepts_raw(self):
        """ELF-02: 接受 raw"""
        cfg = LoggingConfig(event_log_format="raw")
        assert cfg.event_log_format == "raw"

    def test_accepts_summary(self):
        """ELF-03: 接受 summary"""
        cfg = LoggingConfig(event_log_format="summary")
        assert cfg.event_log_format == "summary"

    def test_rejects_invalid_value(self):
        """ELF-04: 拒绝非法值"""
        with pytest.raises(ValueError, match="event_log_format"):
            LoggingConfig(event_log_format="fancy")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/config/test_event_log_format_config.py -v`
Expected: FAIL — `LoggingConfig` has no `event_log_format` field

- [ ] **Step 3: Add `event_log_format` field to `LoggingConfig`**

In `ncatbot/utils/config/models.py`, add the following field and validator to `LoggingConfig` (after the `event_log_levels` field and its validator):

```python
    event_log_format: str = Field(default="summary")
    """事件日志输出格式。

    - ``"summary"``: 人类可读摘要（默认），DEBUG 级别额外输出完整 JSON。
    - ``"raw"``: 完整 JSON（旧行为）。

    示例::

        logging:
          event_log_format: summary
    """

    @field_validator("event_log_format")
    @classmethod
    def _validate_event_log_format(cls, v: str) -> str:
        v = v.lower()
        if v not in ("summary", "raw"):
            raise ValueError(
                f"无效的 event_log_format '{v}'。可选值: summary, raw"
            )
        return v
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/config/test_event_log_format_config.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add ncatbot/utils/config/models.py tests/unit/config/test_event_log_format_config.py
git commit -m "feat: add event_log_format config field to LoggingConfig"
```

---

### Task 2: `format_event_summary()` 纯函数

**Files:**
- Modify: `ncatbot/utils/logger/event_log.py`
- Modify: `ncatbot/utils/logger/__init__.py`
- Modify: `ncatbot/utils/__init__.py`
- Test: `tests/unit/adapter/test_event_log_format.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/adapter/test_event_log_format.py`:

```python
"""事件日志摘要格式化。

测试 format_event_summary() 纯函数：
- 输入为 dict（raw event data），不依赖具体数据模型类
- 按 post_type 分发到不同格式模板
"""

import pytest
from ncatbot.utils.logger.event_log import format_event_summary


class TestFormatGroupMessage:
    """ELS-01 ~ ELS-03: 群消息摘要格式"""

    def test_group_message_full(self):
        """ELS-01: 群消息含 group_name 和 nickname"""
        data = {
            "post_type": "message",
            "message_type": "group",
            "group_id": "626192977",
            "group_name": "测试群",
            "user_id": "2663646956",
            "sender": {"nickname": "张三", "user_id": "2663646956"},
            "raw_message": "你好世界",
        }
        result = format_event_summary(data)
        assert result == "[群消息] 测试群(626192977) 张三(2663646956): 你好世界"

    def test_group_message_no_group_name(self):
        """ELS-02: 群消息缺少 group_name 时降级"""
        data = {
            "post_type": "message",
            "message_type": "group",
            "group_id": "626192977",
            "user_id": "2663646956",
            "sender": {"nickname": "张三"},
            "raw_message": "你好",
        }
        result = format_event_summary(data)
        assert result == "[群消息] 626192977 张三(2663646956): 你好"

    def test_group_message_long_raw_message_truncated(self):
        """ELS-03: raw_message 超过 100 字符被截断"""
        long_msg = "A" * 150
        data = {
            "post_type": "message",
            "message_type": "group",
            "group_id": "123",
            "group_name": "G",
            "user_id": "456",
            "sender": {"nickname": "U"},
            "raw_message": long_msg,
        }
        result = format_event_summary(data)
        assert result == f"[群消息] G(123) U(456): {'A' * 100}..."
        assert len(result.split(": ", 1)[1]) == 104  # 100 + "..."


class TestFormatPrivateMessage:
    """ELS-04 ~ ELS-05: 私聊消息摘要格式"""

    def test_private_message(self):
        """ELS-04: 私聊消息标准格式"""
        data = {
            "post_type": "message",
            "message_type": "private",
            "user_id": "100000004",
            "sender": {"nickname": "TestUser"},
            "raw_message": "/like 3051561876",
        }
        result = format_event_summary(data)
        assert result == "[私聊消息] TestUser(100000004): /like 3051561876"

    def test_private_message_no_nickname(self):
        """ELS-05: 缺少 nickname 降级显示 user_id"""
        data = {
            "post_type": "message",
            "message_type": "private",
            "user_id": "100000004",
            "sender": {},
            "raw_message": "hello",
        }
        result = format_event_summary(data)
        assert result == "[私聊消息] 100000004: hello"


class TestFormatNotice:
    """ELS-06 ~ ELS-08: 通知事件摘要格式"""

    def test_notice_with_group(self):
        """ELS-06: 通知事件含 group_id"""
        data = {
            "post_type": "notice",
            "notice_type": "group_recall",
            "group_id": "100000006",
            "user_id": "100000007",
        }
        result = format_event_summary(data)
        assert result == "[通知] group_recall 群:100000006 用户:100000007"

    def test_notice_without_group(self):
        """ELS-07: 通知事件无 group_id"""
        data = {
            "post_type": "notice",
            "notice_type": "friend_add",
            "user_id": "100000007",
        }
        result = format_event_summary(data)
        assert result == "[通知] friend_add 用户:100000007"

    def test_notice_poke_with_sub_type(self):
        """ELS-08: notify 类型含 sub_type"""
        data = {
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "poke",
            "group_id": "100000005",
            "user_id": "100000004",
            "target_id": "100000001",
        }
        result = format_event_summary(data)
        assert result == "[通知] notify.poke 群:100000005 用户:100000004"


class TestFormatRequest:
    """ELS-09 ~ ELS-10: 请求事件摘要格式"""

    def test_friend_request(self):
        """ELS-09: 好友请求"""
        data = {
            "post_type": "request",
            "request_type": "friend",
            "user_id": "100000004",
        }
        result = format_event_summary(data)
        assert result == "[请求] friend 用户:100000004"

    def test_group_request_with_group(self):
        """ELS-10: 入群请求含 group_id"""
        data = {
            "post_type": "request",
            "request_type": "group",
            "user_id": "100000004",
            "group_id": "100000005",
        }
        result = format_event_summary(data)
        assert result == "[请求] group 群:100000005 用户:100000004"


class TestFormatMetaEvent:
    """ELS-11: 元事件摘要格式"""

    def test_heartbeat(self):
        """ELS-11: 元事件标准格式"""
        data = {
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
        }
        result = format_event_summary(data)
        assert result == "[元事件] heartbeat"


class TestFormatUnknown:
    """ELS-12 ~ ELS-13: 未知/降级格式"""

    def test_unknown_post_type(self):
        """ELS-12: 未知 post_type 降级显示"""
        data = {
            "post_type": "some_new_type",
            "foo": "bar",
        }
        result = format_event_summary(data)
        assert result.startswith("[事件] some_new_type: ")

    def test_message_sent_uses_message_format(self):
        """ELS-13: message_sent 复用消息格式"""
        data = {
            "post_type": "message_sent",
            "message_type": "group",
            "group_id": "123",
            "group_name": "G",
            "user_id": "456",
            "sender": {"nickname": "Bot"},
            "raw_message": "hi",
        }
        result = format_event_summary(data)
        assert result == "[群消息] G(123) Bot(456): hi"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/adapter/test_event_log_format.py -v`
Expected: FAIL — `format_event_summary` does not exist

- [ ] **Step 3: Implement `format_event_summary()` in `event_log.py`**

Append to `ncatbot/utils/logger/event_log.py` (after the existing `_to_level` function):

```python


def format_event_summary(raw_data: dict) -> str:
    """将原始事件数据格式化为人类可读摘要。

    根据 ``post_type`` 分发到不同格式模板。字段缺失时优雅降级。
    输入为 dict 而非数据模型，以保持对平台的通用性。

    Args:
        raw_data: 原始事件字典，至少包含 ``post_type`` 键。

    Returns:
        格式化后的摘要字符串。
    """
    post_type = raw_data.get("post_type", "")

    if post_type in ("message", "message_sent"):
        return _format_message(raw_data)
    if post_type == "notice":
        return _format_notice(raw_data)
    if post_type == "request":
        return _format_request(raw_data)
    if post_type == "meta_event":
        return _format_meta(raw_data)

    # 未知事件类型降级
    import json

    preview = json.dumps(raw_data, ensure_ascii=False)
    if len(preview) > 200:
        preview = preview[:200] + "..."
    return f"[事件] {post_type}: {preview}"


def _format_message(data: dict) -> str:
    message_type = data.get("message_type", "")
    sender = data.get("sender") or {}
    nickname = sender.get("nickname") or ""
    user_id = data.get("user_id", "")
    raw_message = data.get("raw_message", "")

    if len(raw_message) > 100:
        raw_message = raw_message[:100] + "..."

    if message_type == "group":
        group_id = data.get("group_id", "")
        group_name = data.get("group_name", "")
        if group_name:
            group_part = f"{group_name}({group_id})"
        else:
            group_part = group_id
        if nickname:
            user_part = f"{nickname}({user_id})"
        else:
            user_part = user_id
        return f"[群消息] {group_part} {user_part}: {raw_message}"

    # private 或其他
    if nickname:
        user_part = f"{nickname}({user_id})"
    else:
        user_part = user_id
    return f"[私聊消息] {user_part}: {raw_message}"


def _format_notice(data: dict) -> str:
    notice_type = data.get("notice_type", "unknown")
    sub_type = data.get("sub_type")
    if sub_type:
        notice_type = f"{notice_type}.{sub_type}"

    group_id = data.get("group_id")
    user_id = data.get("user_id", "")

    parts = [f"[通知] {notice_type}"]
    if group_id:
        parts.append(f"群:{group_id}")
    parts.append(f"用户:{user_id}")
    return " ".join(parts)


def _format_request(data: dict) -> str:
    request_type = data.get("request_type", "unknown")
    user_id = data.get("user_id", "")
    group_id = data.get("group_id")

    parts = [f"[请求] {request_type}"]
    if group_id:
        parts.append(f"群:{group_id}")
    parts.append(f"用户:{user_id}")
    return " ".join(parts)


def _format_meta(data: dict) -> str:
    meta_type = data.get("meta_event_type", "unknown")
    return f"[元事件] {meta_type}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/adapter/test_event_log_format.py -v`
Expected: 13 PASSED

- [ ] **Step 5: Export from `ncatbot/utils/logger/__init__.py`**

Add `format_event_summary` to imports and `__all__`:

```python
from .event_log import resolve_event_log_level, format_event_summary
```

```python
__all__ = [
    ...
    "format_event_summary",
    ...
]
```

- [ ] **Step 6: Export from `ncatbot/utils/__init__.py`**

Add `format_event_summary` to the logger import block and `__all__`:

```python
from .logger import (
    ...
    format_event_summary,
    ...
)
```

```python
__all__ = [
    ...
    "format_event_summary",
    ...
]
```

- [ ] **Step 7: Run full test suite to verify no regressions**

Run: `python -m pytest tests/unit/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add ncatbot/utils/logger/event_log.py ncatbot/utils/logger/__init__.py ncatbot/utils/__init__.py tests/unit/adapter/test_event_log_format.py
git commit -m "feat: add format_event_summary() for human-readable event logs"
```

---

### Task 3: 适配器集成 — `_on_event` 使用新格式逻辑

**Files:**
- Modify: `ncatbot/adapter/napcat/adapter.py:90-110` (`_on_event` 方法)

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/adapter/test_event_log_format.py`:

```python
import logging
from unittest.mock import patch, MagicMock


class TestOnEventLogFormat:
    """ELS-14 ~ ELS-17: NapCatAdapter._on_event 日志格式集成"""

    def _make_adapter(self):
        """创建一个最小化的 NapCatAdapter 用于测试 _on_event"""
        from ncatbot.adapter.napcat.adapter import NapCatAdapter

        adapter = NapCatAdapter.__new__(NapCatAdapter)
        adapter._event_callback = None

        from ncatbot.adapter.napcat.parser import NapCatEventParser

        adapter._parser = NapCatEventParser()
        return adapter

    @pytest.mark.asyncio
    async def test_summary_format_logs_summary(self):
        """ELS-14: event_log_format=summary 时以 resolved level 输出摘要"""
        adapter = self._make_adapter()
        raw_data = {
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "group_id": "123",
            "group_name": "TestGroup",
            "user_id": "456",
            "sender": {"user_id": "456", "nickname": "Nick"},
            "raw_message": "hello",
            "message": [{"type": "text", "data": {"text": "hello"}}],
            "message_id": "789",
            "time": 1000000000,
            "self_id": "111",
            "font": 14,
        }
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {}
        mock_cfg.config.logging.event_log_format = "summary"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(raw_data)
                # 第一个 _log 调用：摘要
                calls = mock_log._log.call_args_list
                assert len(calls) >= 1
                summary_msg = calls[0][0][1]
                assert "[群消息]" in summary_msg
                assert "TestGroup(123)" in summary_msg

    @pytest.mark.asyncio
    async def test_summary_format_emits_debug_raw(self):
        """ELS-15: event_log_format=summary 时 DEBUG 级别额外输出完整 JSON"""
        adapter = self._make_adapter()
        raw_data = {
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "group_id": "123",
            "group_name": "TestGroup",
            "user_id": "456",
            "sender": {"user_id": "456", "nickname": "Nick"},
            "raw_message": "hello",
            "message": [{"type": "text", "data": {"text": "hello"}}],
            "message_id": "789",
            "time": 1000000000,
            "self_id": "111",
            "font": 14,
        }
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {}
        mock_cfg.config.logging.event_log_format = "summary"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(raw_data)
                calls = mock_log._log.call_args_list
                # 第二个 _log 调用：DEBUG + 完整 JSON
                assert len(calls) == 2
                debug_level = calls[1][0][0]
                assert debug_level == logging.DEBUG

    @pytest.mark.asyncio
    async def test_raw_format_logs_json(self):
        """ELS-16: event_log_format=raw 时输出完整 JSON（旧行为）"""
        adapter = self._make_adapter()
        raw_data = {
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "group_id": "123",
            "group_name": "TestGroup",
            "user_id": "456",
            "sender": {"user_id": "456", "nickname": "Nick"},
            "raw_message": "hello",
            "message": [{"type": "text", "data": {"text": "hello"}}],
            "message_id": "789",
            "time": 1000000000,
            "self_id": "111",
            "font": 14,
        }
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {}
        mock_cfg.config.logging.event_log_format = "raw"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(raw_data)
                calls = mock_log._log.call_args_list
                assert len(calls) == 1
                msg = calls[0][0][1]
                assert "收到事件 message:" in msg

    @pytest.mark.asyncio
    async def test_none_level_suppresses_all(self):
        """ELS-17: event_log_levels=NONE 时 summary 和 raw 都不输出"""
        adapter = self._make_adapter()
        raw_data = {
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "group_id": "123",
            "user_id": "456",
            "sender": {"user_id": "456", "nickname": "Nick"},
            "raw_message": "hello",
            "message": [{"type": "text", "data": {"text": "hello"}}],
            "message_id": "789",
            "time": 1000000000,
            "self_id": "111",
            "font": 14,
        }
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {"message": "NONE"}
        mock_cfg.config.logging.event_log_format = "summary"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(raw_data)
                mock_log._log.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/adapter/test_event_log_format.py::TestOnEventLogFormat -v`
Expected: FAIL — `_on_event` does not use `event_log_format` yet

- [ ] **Step 3: Modify `_on_event` in `ncatbot/adapter/napcat/adapter.py`**

Replace the import line and `_on_event` method. The new imports at the top of the file:

```python
from ncatbot.utils import get_config_manager, get_log
from ncatbot.utils import NapCatConfig
from ncatbot.utils import resolve_event_log_level, format_event_summary
```

Replace the `_on_event` method body:

```python
    async def _on_event(self, raw_data: dict) -> None:
        """收到事件推送，解析为数据模型后回调给分发器"""
        data_model = self._parser.parse(raw_data)
        if data_model is None:
            return

        # 根据配置决定事件日志级别
        event_type = data_model.resolve_type()
        logging_config = get_config_manager().config.logging
        log_level = resolve_event_log_level(event_type, logging_config.event_log_levels)

        if log_level is not None:
            if logging_config.event_log_format == "summary":
                summary = format_event_summary(raw_data)
                LOG._log(log_level, summary, (), {})
                # DEBUG 级别额外输出完整 JSON
                s = data_model.model_dump_json()
                if len(s) > 2000:
                    s = s[:2000] + "..."
                LOG._log(logging.DEBUG, f"收到事件 {data_model.post_type.value}: {s}", (), {})
            else:
                # raw 模式：旧行为
                s = data_model.model_dump_json()
                if len(s) > 2000:
                    s = s[:2000] + "..."
                LOG._log(log_level, f"收到事件 {data_model.post_type.value}: {s}", (), {})

        if self._event_callback:
            await self._event_callback(data_model)
```

Also add `import logging` at the top of the file (add to the existing imports block):

```python
import logging
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/adapter/test_event_log_format.py -v`
Expected: 17 PASSED

- [ ] **Step 5: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS, no regressions

- [ ] **Step 6: Commit**

```bash
git add ncatbot/adapter/napcat/adapter.py tests/unit/adapter/test_event_log_format.py
git commit -m "feat: integrate event_log_format into NapCatAdapter._on_event"
```

---

### Task 4: 文档更新

**Files:**
- Modify: `docs/docs/notes/reference/7. 适配器/1. 连接.md` (如有事件日志相关说明)
- Modify: `tests/README.md` (规范编号索引)

- [ ] **Step 1: 更新测试索引 `tests/README.md`**

在 `tests/README.md` 的规范编号体系表中追加新前缀：

```markdown
| ELF | Event Log Format Config | ELF-01 ~ ELF-04 |
| ELS | Event Log Summary | ELS-01 ~ ELS-17 |
```

- [ ] **Step 2: 检查 docs 中是否有 event_log_levels 文档需要同步更新**

搜索 docs 目录中的 `event_log_levels` 引用，如果有现有文档提到该配置，在文档中补充 `event_log_format` 说明。

典型补充位置：日志配置参考文档中，在 `event_log_levels` 说明的旁边添加：

```markdown
### event_log_format

事件日志输出格式。

| 值 | 含义 |
|---|---|
| `summary`（默认） | 人类可读摘要，DEBUG 级别额外输出完整 JSON |
| `raw` | 完整 JSON（旧行为） |

```yaml
logging:
  event_log_format: summary
```

- [ ] **Step 3: Commit**

```bash
git add tests/README.md docs/
git commit -m "docs: add event_log_format to test index and reference docs"
```

---

### Task 5: 四位一体验证

- [ ] **Step 1: 运行完整测试套件**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All PASS

- [ ] **Step 2: 检查导入规范**

Run: `python .agents/scripts/check_imports.py ncatbot/`
Expected: No violations

- [ ] **Step 3: 四位一体检查清单**

- [ ] Code: `event_log_format` 配置字段 + `format_event_summary()` + `_on_event` 集成
- [ ] Test: ELF-01~ELF-04 配置验证 + ELS-01~ELS-17 格式化 + 集成
- [ ] Docs: 参考文档 + 测试索引已更新
- [ ] Skill: 评估是否需要更新 `.agents/skills/` 中的知识（如 framework-usage 中的日志配置说明）

- [ ] **Step 4: Final commit (if any Skill updates needed)**

```bash
git add .agents/skills/
git commit -m "docs(skill): sync event_log_format knowledge"
```
