# Test WebUI Implementation Plan

> **For agentic workers:** REQUIRED: Use the `subagent-driven-development` agent (recommended) or `executing-plans` agent to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a visual test WebUI for NcatBot that provides a QQ platform event simulator, real-time API call rendering, and test recording with Scenario DSL code generation.

**Architecture:** aiohttp backend as TestHarness proxy + Vue 3 SPA frontend. WebSocket for bidirectional real-time communication. HarnessProxy wraps TestHarness lifecycle for long-lived WebUI sessions, RecordingEngine captures operations and exports Scenario DSL code.

**Tech Stack:** Python aiohttp (existing dep), Vue 3 + Vite + TypeScript (frontend), WebSocket (real-time)

**Spec:** `docs/superpowers/specs/2026-04-08-test-webui-design.md`

**Spec→Code discrepancies (MUST use actual code names):**
- Factory: `qq.poke()` not `qq.poke_notify()`
- Factory: `qq.group_msg_emoji_like()` not `qq.group_emoji_like()`
- Factory: first positional param is `text` not `content`
- MockAPIBase: method is `_record(action, **params)` not `_record_call()`
- `APICall` dataclass has `action` + `params` only — no `timestamp` field

---

### Task 1: Backend — WebSocket Protocol Types

**Files:**
- Create: `ncatbot/webui/__init__.py`
- Create: `ncatbot/webui/protocol.py`

- [ ] **Step 1: Create `ncatbot/webui/__init__.py`**

```python
"""NcatBot Test WebUI — 可视化测试与管理界面"""
```

- [ ] **Step 2: Write the protocol types**

Create `ncatbot/webui/protocol.py`:

```python
"""WebSocket 消息协议定义"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


# ---- 前端 → 后端 ----

@dataclass
class SessionCreatePayload:
    platform: str = "qq"
    plugins: Optional[List[str]] = None


@dataclass
class SessionDestroyPayload:
    session_id: str = ""


@dataclass
class EventInjectPayload:
    session_id: str = ""
    event_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventInjectRawPayload:
    session_id: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionSettlePayload:
    session_id: str = ""


@dataclass
class RecordingControlPayload:
    session_id: str = ""


@dataclass
class RecordingExportPayload:
    session_id: str = ""
    format: str = "scenario_dsl"


# ---- 后端 → 前端 ----

@dataclass
class APICallInfo:
    """一次 API 调用的序列化表示"""
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


# ---- 消息类型常量 ----

class MsgType:
    # 前端 → 后端
    SESSION_CREATE = "session.create"
    SESSION_DESTROY = "session.destroy"
    EVENT_INJECT = "event.inject"
    EVENT_INJECT_RAW = "event.inject_raw"
    SESSION_SETTLE = "session.settle"
    RECORDING_START = "recording.start"
    RECORDING_STOP = "recording.stop"
    RECORDING_EXPORT = "recording.export"

    # 后端 → 前端
    SESSION_CREATED = "session.created"
    API_CALLED = "api.called"
    SETTLE_DONE = "settle.done"
    RECORDING_EXPORTED = "recording.exported"
    ERROR = "error"


def make_response(msg_type: str, payload: dict, msg_id: Optional[str] = None) -> dict:
    """构造后端→前端的 JSON 消息"""
    msg: dict = {"type": msg_type, "payload": payload}
    if msg_id:
        msg["id"] = msg_id
    return msg
```

- [ ] **Step 3: Commit**

```bash
git add ncatbot/webui/
git commit -m "feat(webui): add protocol types and module init"
```

---

### Task 2: Backend — HarnessProxy

**Files:**
- Create: `ncatbot/webui/session.py`
- Test: `tests/unit/webui/test_session.py`

- [ ] **Step 1: Write the failing test for HarnessProxy**

Create `tests/unit/webui/__init__.py` (empty) and `tests/unit/webui/test_session.py`:

```python
"""WUI-01 ~ WUI-04: HarnessProxy wraps TestHarness for WebUI sessions"""

import pytest
from ncatbot.webui.session import HarnessProxy


pytestmark = pytest.mark.asyncio(mode="strict")


async def test_proxy_start_stop():
    """WUI-01: HarnessProxy can start and stop a TestHarness"""
    proxy = HarnessProxy(platform="qq")
    await proxy.start()
    assert proxy._harness is not None
    await proxy.stop()
    assert proxy._harness is None


async def test_proxy_inject_and_settle():
    """WUI-02: HarnessProxy can inject events and settle"""
    proxy = HarnessProxy(platform="qq")
    await proxy.start()
    try:
        await proxy.inject("message.group", {"text": "hello"})
        calls = await proxy.settle()
        # No handler registered, so no API calls expected
        assert isinstance(calls, list)
    finally:
        await proxy.stop()


async def test_proxy_api_call_hook():
    """WUI-03: HarnessProxy notifies hooks on API calls"""
    captured = []

    proxy = HarnessProxy(platform="qq")
    await proxy.start()
    try:
        proxy.on_api_call(lambda action, params: captured.append((action, params)))

        # Register a handler that calls an API
        async def echo_handler(event):
            await event.reply("pong")

        proxy._harness.bot.handler_dispatcher.register_handler(
            "message.group", echo_handler
        )

        await proxy.inject("message.group", {"text": "/ping"})
        await proxy.settle()

        assert len(captured) > 0
        assert captured[0][0] == "send_group_msg"
    finally:
        await proxy.stop()


async def test_proxy_unknown_event_type():
    """WUI-04: HarnessProxy raises KeyError for unknown event types"""
    proxy = HarnessProxy(platform="qq")
    await proxy.start()
    try:
        with pytest.raises(KeyError):
            await proxy.inject("unknown.event", {})
    finally:
        await proxy.stop()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/unit/webui/test_session.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ncatbot.webui.session'`

- [ ] **Step 3: Implement HarnessProxy**

Create `ncatbot/webui/session.py`:

```python
"""Session management: HarnessProxy + SessionManager"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Sequence
from uuid import uuid4

from ncatbot.adapter.mock.api_base import APICall, MockAPIBase
from ncatbot.testing.harness import TestHarness
from ncatbot.testing.plugin_harness import PluginTestHarness


# ---- Event type → factory function mapping ----

def _build_event(event_type: str, data: dict):
    """Map event_type string to factory function call."""
    from ncatbot.testing.factories import qq

    _FACTORY_MAP = {
        "message.group": qq.group_message,
        "message.private": qq.private_message,
        "request.friend": qq.friend_request,
        "request.group": qq.group_request,
        "notice.group_increase": qq.group_increase,
        "notice.group_decrease": qq.group_decrease,
        "notice.group_ban": qq.group_ban,
        "notice.group_upload": qq.group_upload,
        "notice.group_admin": qq.group_admin,
        "notice.group_recall": qq.group_recall,
        "notice.friend_recall": qq.friend_recall,
        "notice.poke": qq.poke,
        "notice.emoji_like": qq.group_msg_emoji_like,
    }
    factory = _FACTORY_MAP[event_type]  # KeyError if unknown
    return factory(**data)


class HarnessProxy:
    """WebUI ↔ TestHarness adapter.

    Wraps TestHarness lifecycle (start/stop instead of async-with)
    and adds real-time API call hooks for WebSocket push.
    """

    def __init__(
        self,
        platform: str = "qq",
        plugins: list[str] | None = None,
        plugins_dir: str | None = None,
    ):
        self._harness: TestHarness | None = None
        self._platform = platform
        self._plugins = plugins
        self._plugins_dir = plugins_dir
        self._api_call_hooks: list[Callable] = []
        self._call_index = 0  # track which calls have been seen

    async def start(self):
        """Start the underlying TestHarness."""
        if self._plugins:
            from pathlib import Path

            self._harness = PluginTestHarness(
                plugin_names=self._plugins,
                plugins_dir=Path(self._plugins_dir or "plugins"),
                platforms=(self._platform,),
            )
        else:
            self._harness = TestHarness(platforms=(self._platform,))
        await self._harness.start()
        self._install_api_hooks()

    async def stop(self):
        """Stop the underlying TestHarness."""
        if self._harness:
            await self._harness.stop()
            self._harness = None

    async def inject(self, event_type: str, data: dict):
        """Convert event_type + data → factory call → harness.inject()."""
        event_data = _build_event(event_type, data)
        await self._harness.inject(event_data)

    async def inject_raw(self, raw: dict):
        """Inject raw event data dict directly."""
        # Determine platform from raw data or use default
        from ncatbot.event.common import BaseEventData

        event_data = BaseEventData.model_validate(raw)
        await self._harness.inject(event_data)

    async def settle(self) -> list[dict]:
        """Wait for handlers to finish, return new API calls since last settle."""
        await self._harness.settle()
        return self._drain_new_calls()

    def on_api_call(self, callback: Callable):
        """Register callback invoked on each API call: callback(action, params)."""
        self._api_call_hooks.append(callback)

    def _install_api_hooks(self):
        """Monkey-patch MockAPIBase._record to intercept API calls."""
        mock_api = self._harness.mock_api_for(self._platform)
        original_record = mock_api._record

        def hooked_record(action: str, **params):
            result = original_record(action, **params)
            for hook in self._api_call_hooks:
                hook(action, params)
            return result

        mock_api._record = hooked_record

    def _drain_new_calls(self) -> list[dict]:
        """Return API calls recorded since last drain."""
        mock_api = self._harness.mock_api_for(self._platform)
        all_calls = mock_api.calls
        new_calls = all_calls[self._call_index :]
        self._call_index = len(all_calls)
        return [{"action": c.action, "params": c.params} for c in new_calls]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/unit/webui/test_session.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add ncatbot/webui/session.py tests/unit/webui/
git commit -m "feat(webui): add HarnessProxy with API call hooks"
```

---

### Task 3: Backend — SessionManager

**Files:**
- Modify: `ncatbot/webui/session.py` (append class)
- Test: `tests/unit/webui/test_session_manager.py`

- [ ] **Step 1: Write the failing test for SessionManager**

Create `tests/unit/webui/test_session_manager.py`:

```python
"""WUI-05 ~ WUI-08: SessionManager manages multiple HarnessProxy sessions"""

import pytest
from ncatbot.webui.session import SessionManager


pytestmark = pytest.mark.asyncio(mode="strict")


async def test_create_and_get_session():
    """WUI-05: SessionManager can create and retrieve sessions"""
    mgr = SessionManager()
    sid = await mgr.create_session(platform="qq")
    assert isinstance(sid, str)
    assert len(sid) == 8
    proxy = mgr.get(sid)
    assert proxy is not None
    await mgr.destroy_all()


async def test_destroy_session():
    """WUI-06: SessionManager can destroy a session"""
    mgr = SessionManager()
    sid = await mgr.create_session(platform="qq")
    await mgr.destroy_session(sid)
    with pytest.raises(KeyError):
        mgr.get(sid)


async def test_cleanup_expired(monkeypatch):
    """WUI-07: SessionManager cleans up expired sessions"""
    mgr = SessionManager()
    mgr.SESSION_TIMEOUT = 0  # expire immediately
    sid = await mgr.create_session(platform="qq")
    # Force timestamp to be in the past
    mgr._last_activity[sid] = 0
    await mgr.cleanup_expired()
    with pytest.raises(KeyError):
        mgr.get(sid)


async def test_get_unknown_session():
    """WUI-08: SessionManager raises KeyError for unknown session"""
    mgr = SessionManager()
    with pytest.raises(KeyError):
        mgr.get("nonexistent")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/unit/webui/test_session_manager.py -v`
Expected: FAIL — `ImportError: cannot import name 'SessionManager'`

- [ ] **Step 3: Implement SessionManager**

Append to `ncatbot/webui/session.py`:

```python
class SessionManager:
    """Manage multiple independent WebUI test sessions."""

    SESSION_TIMEOUT = 1800  # 30 minutes

    def __init__(self):
        self._sessions: dict[str, HarnessProxy] = {}
        self._last_activity: dict[str, float] = {}

    async def create_session(
        self,
        platform: str = "qq",
        plugins: list[str] | None = None,
        plugins_dir: str | None = None,
    ) -> str:
        session_id = uuid4().hex[:8]
        proxy = HarnessProxy(platform, plugins, plugins_dir)
        await proxy.start()
        self._sessions[session_id] = proxy
        self._last_activity[session_id] = time.time()
        return session_id

    async def destroy_session(self, session_id: str):
        proxy = self._sessions.pop(session_id)  # KeyError if missing
        self._last_activity.pop(session_id, None)
        await proxy.stop()

    def get(self, session_id: str) -> HarnessProxy:
        proxy = self._sessions[session_id]  # KeyError if missing
        self._last_activity[session_id] = time.time()
        return proxy

    async def cleanup_expired(self):
        now = time.time()
        expired = [
            sid
            for sid, t in self._last_activity.items()
            if now - t > self.SESSION_TIMEOUT
        ]
        for sid in expired:
            try:
                await self.destroy_session(sid)
            except KeyError:
                pass

    async def destroy_all(self):
        for sid in list(self._sessions):
            try:
                await self.destroy_session(sid)
            except KeyError:
                pass
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/unit/webui/ -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add ncatbot/webui/session.py tests/unit/webui/test_session_manager.py
git commit -m "feat(webui): add SessionManager with timeout cleanup"
```

---

### Task 4: Backend — RecordingEngine

**Files:**
- Create: `ncatbot/webui/recorder.py`
- Test: `tests/unit/webui/test_recorder.py`

- [ ] **Step 1: Write the failing test for RecordingEngine**

Create `tests/unit/webui/test_recorder.py`:

```python
"""WUI-09 ~ WUI-14: RecordingEngine captures operations and exports Scenario DSL"""

import pytest
from ncatbot.webui.recorder import RecordingEngine


def test_recording_lifecycle():
    """WUI-09: RecordingEngine start/stop/is_recording"""
    rec = RecordingEngine()
    assert not rec.is_recording
    rec.start()
    assert rec.is_recording
    rec.stop()
    assert not rec.is_recording


def test_record_inject_and_settle():
    """WUI-10: RecordingEngine captures inject+settle pairs as steps"""
    rec = RecordingEngine()
    rec.start()
    rec.record_inject("message.group", {"text": "/help"})
    rec.record_settle([{"action": "send_group_msg", "params": {"message": [{"type": "text", "data": {"text": "帮助"}}]}}])
    assert len(rec.steps) == 1
    assert rec.steps[0].event_type == "message.group"


def test_record_ignores_when_not_recording():
    """WUI-11: RecordingEngine ignores calls when not recording"""
    rec = RecordingEngine()
    rec.record_inject("message.group", {"text": "hi"})
    rec.record_settle([])
    assert len(rec.steps) == 0


def test_record_settle_without_inject():
    """WUI-12: RecordingEngine ignores settle without preceding inject"""
    rec = RecordingEngine()
    rec.start()
    rec.record_settle([{"action": "foo", "params": {}}])
    assert len(rec.steps) == 0


def test_start_clears_previous_steps():
    """WUI-13: RecordingEngine.start() clears previous recording"""
    rec = RecordingEngine()
    rec.start()
    rec.record_inject("message.group", {"text": "hi"})
    rec.record_settle([])
    assert len(rec.steps) == 1
    rec.start()
    assert len(rec.steps) == 0


def test_export_scenario_dsl():
    """WUI-14: RecordingEngine exports valid Scenario DSL code"""
    rec = RecordingEngine()
    rec.start()
    rec.record_inject("message.group", {"text": "/ping", "group_id": "123"})
    rec.record_settle([{
        "action": "send_group_msg",
        "params": {"message": [{"type": "text", "data": {"text": "pong"}}]},
    }])
    rec.record_inject("notice.poke", {"user_id": "111", "target_id": "222"})
    rec.record_settle([])
    rec.stop()

    code = rec.export_scenario_dsl()
    assert "from ncatbot.testing import TestHarness, Scenario" in code
    assert "from ncatbot.testing.factories import qq" in code
    assert "qq.group_message" in code
    assert 'text="/ping"' in code
    assert "qq.poke" in code
    assert "scenario.assert_api_called" in code
    assert 'scenario.assert_api_text("send_group_msg", "pong")' in code
    assert "await scenario.run(h)" in code
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/unit/webui/test_recorder.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ncatbot.webui.recorder'`

- [ ] **Step 3: Implement RecordingEngine**

Create `ncatbot/webui/recorder.py`:

```python
"""RecordingEngine — capture WebUI operations and export as Scenario DSL code"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RecordedStep:
    """A single recorded inject + settle pair."""

    event_type: str
    event_data: Dict[str, Any]
    api_calls: List[Dict[str, Any]]


# event_type → Scenario factory call name
_FACTORY_NAMES = {
    "message.group": "qq.group_message",
    "message.private": "qq.private_message",
    "request.friend": "qq.friend_request",
    "request.group": "qq.group_request",
    "notice.group_increase": "qq.group_increase",
    "notice.group_decrease": "qq.group_decrease",
    "notice.group_ban": "qq.group_ban",
    "notice.group_upload": "qq.group_upload",
    "notice.group_admin": "qq.group_admin",
    "notice.group_recall": "qq.group_recall",
    "notice.friend_recall": "qq.friend_recall",
    "notice.poke": "qq.poke",
    "notice.emoji_like": "qq.group_msg_emoji_like",
}


class RecordingEngine:
    """Record WebUI operations and export as Scenario DSL Python code."""

    def __init__(self) -> None:
        self._recording = False
        self._steps: List[RecordedStep] = []
        self._pending_event: Optional[Tuple[str, Dict[str, Any]]] = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def steps(self) -> List[RecordedStep]:
        return self._steps

    def start(self) -> None:
        self._recording = True
        self._steps.clear()
        self._pending_event = None

    def stop(self) -> None:
        self._recording = False

    def record_inject(self, event_type: str, event_data: Dict[str, Any]) -> None:
        if not self._recording:
            return
        self._pending_event = (event_type, event_data)

    def record_settle(self, api_calls: List[Dict[str, Any]]) -> None:
        if not self._recording or self._pending_event is None:
            return
        event_type, event_data = self._pending_event
        self._steps.append(
            RecordedStep(
                event_type=event_type,
                event_data=event_data,
                api_calls=api_calls,
            )
        )
        self._pending_event = None

    def export_scenario_dsl(self) -> str:
        lines = [
            "import pytest",
            "from ncatbot.testing import TestHarness, Scenario",
            "from ncatbot.testing.factories import qq",
            "",
            'pytestmark = pytest.mark.asyncio(mode="strict")',
            "",
            "",
            "async def test_recorded_scenario():",
            f'    """录制生成 - {datetime.now().strftime("%Y-%m-%d %H:%M")}"""',
            "    async with TestHarness() as h:",
            "        scenario = Scenario()",
        ]

        for i, step in enumerate(self._steps, 1):
            lines.append("")
            lines.append(f"        # Step {i}")
            factory_call = self._build_factory_call(step.event_type, step.event_data)
            lines.append(f"        scenario.inject({factory_call})")
            lines.append("        scenario.settle()")

            for call in step.api_calls:
                action = call["action"]
                lines.append(f'        scenario.assert_api_called("{action}")')
                text = self._extract_text(call)
                if text:
                    lines.append(
                        f'        scenario.assert_api_text("{action}", {text!r})'
                    )

        lines.append("")
        lines.append("        await scenario.run(h)")
        lines.append("")
        return "\n".join(lines)

    def _build_factory_call(self, event_type: str, data: Dict[str, Any]) -> str:
        name = _FACTORY_NAMES.get(event_type, f"qq.{event_type}")
        args = ", ".join(f"{k}={v!r}" for k, v in data.items())
        return f"{name}({args})"

    def _extract_text(self, call: Dict[str, Any]) -> Optional[str]:
        params = call.get("params", {})
        message = params.get("message", [])
        texts = []
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") == "text":
                data = seg.get("data", {})
                texts.append(data.get("text", ""))
        return "".join(texts) if texts else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/unit/webui/test_recorder.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add ncatbot/webui/recorder.py tests/unit/webui/test_recorder.py
git commit -m "feat(webui): add RecordingEngine with Scenario DSL export"
```

---

### Task 5: Backend — WebUI Server (aiohttp + WebSocket)

**Files:**
- Create: `ncatbot/webui/server.py`
- Test: `tests/integration/test_webui_server.py`

- [ ] **Step 1: Write the failing integration test**

Create `tests/integration/test_webui_server.py`:

```python
"""WUI-I-01 ~ WUI-I-04: WebUI server accepts WS connections and routes messages"""

import asyncio
import json

import aiohttp
import pytest

from ncatbot.webui.server import create_app


pytestmark = pytest.mark.asyncio(mode="strict")


@pytest.fixture
async def webui_server():
    """Start WebUI server on a random port, yield URL, then teardown."""
    app = create_app()
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    # Extract the actual port
    port = site._server.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    await runner.cleanup()


async def _ws_send_recv(url, msg):
    """Helper: open WS, send JSON, receive one JSON response."""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{url}/ws") as ws:
            await ws.send_json(msg)
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            return resp


async def test_session_create(webui_server):
    """WUI-I-01: session.create returns session_id"""
    resp = await _ws_send_recv(webui_server, {
        "type": "session.create",
        "id": "req-1",
        "payload": {"platform": "qq"},
    })
    assert resp["type"] == "session.created"
    assert resp["id"] == "req-1"
    assert "session_id" in resp["payload"]


async def test_inject_and_settle(webui_server):
    """WUI-I-02: inject event + settle returns api_calls list"""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{webui_server}/ws") as ws:
            # Create session
            await ws.send_json({
                "type": "session.create",
                "id": "req-1",
                "payload": {"platform": "qq"},
            })
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            sid = resp["payload"]["session_id"]

            # Inject event
            await ws.send_json({
                "type": "event.inject",
                "payload": {
                    "session_id": sid,
                    "event_type": "message.group",
                    "data": {"text": "/hello"},
                },
            })

            # Settle
            await ws.send_json({
                "type": "session.settle",
                "id": "req-2",
                "payload": {"session_id": sid},
            })
            # May receive api.called pushes before settle.done
            while True:
                resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
                if resp["type"] == "settle.done":
                    break
            assert resp["id"] == "req-2"
            assert isinstance(resp["payload"]["api_calls"], list)


async def test_recording_export(webui_server):
    """WUI-I-03: recording start → inject → settle → export returns code"""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{webui_server}/ws") as ws:
            # Create session
            await ws.send_json({
                "type": "session.create",
                "id": "r1",
                "payload": {"platform": "qq"},
            })
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            sid = resp["payload"]["session_id"]

            # Start recording
            await ws.send_json({
                "type": "recording.start",
                "payload": {"session_id": sid},
            })

            # Inject
            await ws.send_json({
                "type": "event.inject",
                "payload": {
                    "session_id": sid,
                    "event_type": "message.group",
                    "data": {"text": "/test"},
                },
            })

            # Settle
            await ws.send_json({
                "type": "session.settle",
                "id": "r2",
                "payload": {"session_id": sid},
            })
            while True:
                resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
                if resp["type"] == "settle.done":
                    break

            # Stop recording
            await ws.send_json({
                "type": "recording.stop",
                "payload": {"session_id": sid},
            })

            # Export
            await ws.send_json({
                "type": "recording.export",
                "id": "r3",
                "payload": {"session_id": sid, "format": "scenario_dsl"},
            })
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            assert resp["type"] == "recording.exported"
            assert "qq.group_message" in resp["payload"]["code"]


async def test_session_destroy(webui_server):
    """WUI-I-04: session.destroy cleans up resources"""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{webui_server}/ws") as ws:
            # Create
            await ws.send_json({
                "type": "session.create",
                "id": "d1",
                "payload": {"platform": "qq"},
            })
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            sid = resp["payload"]["session_id"]

            # Destroy
            await ws.send_json({
                "type": "session.destroy",
                "payload": {"session_id": sid},
            })
            # No error means success; settle after destroy should error
            await ws.send_json({
                "type": "session.settle",
                "id": "d2",
                "payload": {"session_id": sid},
            })
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            assert resp["type"] == "error"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/integration/test_webui_server.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'ncatbot.webui.server'`

- [ ] **Step 3: Implement WebUI Server**

Create `ncatbot/webui/server.py`:

```python
"""WebUI aiohttp server — WebSocket message routing"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import aiohttp
from aiohttp import web

from .protocol import MsgType, make_response
from .recorder import RecordingEngine
from .session import SessionManager

logger = logging.getLogger(__name__)


def create_app(session_mgr: Optional[SessionManager] = None) -> web.Application:
    """Create aiohttp Application with WebSocket endpoint."""
    app = web.Application()
    if session_mgr is None:
        session_mgr = SessionManager()
    app["session_mgr"] = session_mgr

    app.router.add_get("/ws", ws_handler)
    return app


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    """WebSocket message router."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session_mgr: SessionManager = request.app["session_mgr"]
    recorders: dict[str, RecordingEngine] = {}

    async for raw_msg in ws:
        if raw_msg.type == aiohttp.WSMsgType.TEXT:
            try:
                data = json.loads(raw_msg.data)
            except json.JSONDecodeError:
                await ws.send_json(
                    make_response(MsgType.ERROR, {"message": "Invalid JSON"})
                )
                continue

            msg_type = data.get("type", "")
            payload = data.get("payload", {})
            msg_id = data.get("id")

            try:
                await _route_message(
                    ws, session_mgr, recorders, msg_type, payload, msg_id
                )
            except KeyError as exc:
                await ws.send_json(
                    make_response(
                        MsgType.ERROR,
                        {"message": f"Unknown session or event type: {exc}"},
                        msg_id,
                    )
                )
            except Exception as exc:
                logger.exception("WebSocket handler error")
                await ws.send_json(
                    make_response(
                        MsgType.ERROR,
                        {"message": str(exc)},
                        msg_id,
                    )
                )
        elif raw_msg.type == aiohttp.WSMsgType.ERROR:
            logger.error("WebSocket error: %s", ws.exception())

    # Cleanup sessions owned by this WS connection
    for sid in list(recorders):
        try:
            await session_mgr.destroy_session(sid)
        except KeyError:
            pass

    return ws


async def _route_message(
    ws: web.WebSocketResponse,
    session_mgr: SessionManager,
    recorders: dict[str, RecordingEngine],
    msg_type: str,
    payload: dict,
    msg_id: Optional[str],
):
    if msg_type == MsgType.SESSION_CREATE:
        session_id = await session_mgr.create_session(
            platform=payload.get("platform", "qq"),
            plugins=payload.get("plugins"),
        )
        proxy = session_mgr.get(session_id)
        recorders[session_id] = RecordingEngine()

        # Register real-time API call push
        def on_api_call(action, params, sid=session_id):
            asyncio.ensure_future(
                ws.send_json(
                    make_response(
                        MsgType.API_CALLED,
                        {
                            "session_id": sid,
                            "action": action,
                            "params": _serialize_params(params),
                        },
                    )
                )
            )

        proxy.on_api_call(on_api_call)

        await ws.send_json(
            make_response(
                MsgType.SESSION_CREATED,
                {
                    "session_id": session_id,
                    "platform": payload.get("platform", "qq"),
                },
                msg_id,
            )
        )

    elif msg_type == MsgType.EVENT_INJECT:
        session_id = payload["session_id"]
        proxy = session_mgr.get(session_id)
        recorder = recorders.get(session_id)

        await proxy.inject(payload["event_type"], payload["data"])
        if recorder:
            recorder.record_inject(payload["event_type"], payload["data"])

    elif msg_type == MsgType.EVENT_INJECT_RAW:
        session_id = payload["session_id"]
        proxy = session_mgr.get(session_id)
        await proxy.inject_raw(payload["raw"])

    elif msg_type == MsgType.SESSION_SETTLE:
        session_id = payload["session_id"]
        proxy = session_mgr.get(session_id)
        recorder = recorders.get(session_id)

        calls = await proxy.settle()
        if recorder:
            recorder.record_settle(calls)

        await ws.send_json(
            make_response(
                MsgType.SETTLE_DONE,
                {"session_id": session_id, "api_calls": calls},
                msg_id,
            )
        )

    elif msg_type == MsgType.RECORDING_START:
        session_id = payload["session_id"]
        recorder = recorders.get(session_id)
        if recorder:
            recorder.start()

    elif msg_type == MsgType.RECORDING_STOP:
        session_id = payload["session_id"]
        recorder = recorders.get(session_id)
        if recorder:
            recorder.stop()

    elif msg_type == MsgType.RECORDING_EXPORT:
        session_id = payload["session_id"]
        recorder = recorders.get(session_id)
        code = recorder.export_scenario_dsl() if recorder else ""
        await ws.send_json(
            make_response(
                MsgType.RECORDING_EXPORTED,
                {"session_id": session_id, "code": code},
                msg_id,
            )
        )

    elif msg_type == MsgType.SESSION_DESTROY:
        session_id = payload["session_id"]
        await session_mgr.destroy_session(session_id)
        recorders.pop(session_id, None)

    else:
        await ws.send_json(
            make_response(
                MsgType.ERROR,
                {"message": f"Unknown message type: {msg_type}"},
                msg_id,
            )
        )


def _serialize_params(params: dict) -> dict:
    """Best-effort JSON serialization of API call params."""
    result = {}
    for k, v in params.items():
        try:
            json.dumps(v)
            result[k] = v
        except (TypeError, ValueError):
            result[k] = str(v)
    return result


async def start_webui(
    port: int = 8765,
    plugins: list[str] | None = None,
    dev: bool = False,
):
    """Start the WebUI server (blocking)."""
    app = create_app()

    if dev:
        logger.info("Dev mode: proxy non-API requests to Vite dev server")
    else:
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.router.add_static("/assets", static_dir / "assets")

            async def serve_index(request: web.Request) -> web.FileResponse:
                return web.FileResponse(static_dir / "index.html")

            app.router.add_get("/{path:.*}", serve_index)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", port)
    await site.start()
    print(f"NcatBot TestUI: http://localhost:{port}")

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/integration/test_webui_server.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add ncatbot/webui/server.py tests/integration/test_webui_server.py
git commit -m "feat(webui): add aiohttp server with WebSocket routing"
```

---

### Task 6: Backend — CLI Command

**Files:**
- Create: `ncatbot/cli/commands/test_ui.py`
- Modify: `ncatbot/cli/main.py`

- [ ] **Step 1: Create CLI command**

Create `ncatbot/cli/commands/test_ui.py`:

```python
"""ncatbot test-ui — 启动测试 WebUI"""

import asyncio

import click


@click.command("test-ui")
@click.option("--port", default=8765, help="WebUI 服务端口")
@click.option("--plugins", default=None, help="要加载的插件列表（逗号分隔）")
@click.option("--dev", is_flag=True, help="开发模式（代理 Vite dev server）")
def test_ui(port: int, plugins: str | None, dev: bool):
    """启动测试 WebUI"""
    from ncatbot.webui.server import start_webui

    plugin_list = [p.strip() for p in plugins.split(",") if p.strip()] if plugins else None
    asyncio.run(start_webui(port=port, plugins=plugin_list, dev=dev))
```

- [ ] **Step 2: Register command in CLI main**

Add to `ncatbot/cli/main.py` — add import and `add_command`:

Import line (after `from .commands.ref import ref`):
```python
from .commands.test_ui import test_ui
```

Add command line (after `cli.add_command(ref)`):
```python
cli.add_command(test_ui)
```

- [ ] **Step 3: Verify CLI help**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m ncatbot test-ui --help`
Expected output includes: `启动测试 WebUI`, `--port`, `--plugins`, `--dev`

- [ ] **Step 4: Commit**

```bash
git add ncatbot/cli/commands/test_ui.py ncatbot/cli/main.py
git commit -m "feat(cli): add 'ncatbot test-ui' command"
```

---

### Task 7: Frontend — Vue 3 + Vite Project Scaffold

**Files:**
- Create: `ncatbot/webui/frontend/package.json`
- Create: `ncatbot/webui/frontend/vite.config.ts`
- Create: `ncatbot/webui/frontend/tsconfig.json`
- Create: `ncatbot/webui/frontend/index.html`
- Create: `ncatbot/webui/frontend/src/main.ts`
- Create: `ncatbot/webui/frontend/src/App.vue`
- Create: `ncatbot/webui/frontend/src/router/index.ts`
- Create: `ncatbot/webui/frontend/src/types/protocol.ts`

- [ ] **Step 1: Create package.json**

Create `ncatbot/webui/frontend/package.json`:

```json
{
  "name": "ncatbot-webui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "~5.4.0",
    "vite": "^5.4.0",
    "vue-tsc": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

Create `ncatbot/webui/frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/ws': {
        target: 'http://localhost:8765',
        ws: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create tsconfig.json**

Create `ncatbot/webui/frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"]
}
```

- [ ] **Step 4: Create index.html**

Create `ncatbot/webui/frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NcatBot TestUI</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 5: Create protocol types**

Create `ncatbot/webui/frontend/src/types/protocol.ts`:

```typescript
export interface WSMessage {
  type: string
  id?: string
  payload: Record<string, any>
}

export interface APICallInfo {
  action: string
  params: Record<string, any>
}

export interface TimelineEntry {
  type: 'inject' | 'api_call' | 'settle'
  timestamp: number
  action?: string
  eventType?: string
  data?: Record<string, any>
  params?: Record<string, any>
  apiCalls?: APICallInfo[]
  durationMs?: number
}

export const MsgType = {
  SESSION_CREATE: 'session.create',
  SESSION_DESTROY: 'session.destroy',
  EVENT_INJECT: 'event.inject',
  SESSION_SETTLE: 'session.settle',
  RECORDING_START: 'recording.start',
  RECORDING_STOP: 'recording.stop',
  RECORDING_EXPORT: 'recording.export',
  SESSION_CREATED: 'session.created',
  API_CALLED: 'api.called',
  SETTLE_DONE: 'settle.done',
  RECORDING_EXPORTED: 'recording.exported',
  ERROR: 'error',
} as const
```

- [ ] **Step 6: Create Vue Router**

Create `ncatbot/webui/frontend/src/router/index.ts`:

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/test',
    },
    {
      path: '/test',
      name: 'test',
      component: () => import('../views/TestPlayground.vue'),
    },
  ],
})

export default router
```

- [ ] **Step 7: Create main.ts and App.vue**

Create `ncatbot/webui/frontend/src/main.ts`:

```typescript
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
```

Create `ncatbot/webui/frontend/src/App.vue`:

```vue
<script setup lang="ts">
</script>

<template>
  <div id="ncatbot-app">
    <header class="app-header">
      <h1>NcatBot TestUI</h1>
      <nav>
        <router-link to="/test">Test Playground</router-link>
      </nav>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  color: #333;
}

.app-header {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 0.75rem 1.5rem;
  background: #1a1a2e;
  color: white;
}

.app-header h1 {
  font-size: 1.2rem;
  font-weight: 600;
}

.app-header nav a {
  color: #a0a0c0;
  text-decoration: none;
  font-size: 0.9rem;
}

.app-header nav a.router-link-active {
  color: white;
}

main {
  height: calc(100vh - 3rem);
}
</style>
```

- [ ] **Step 8: Create placeholder TestPlayground.vue**

Create `ncatbot/webui/frontend/src/views/TestPlayground.vue`:

```vue
<script setup lang="ts">
</script>

<template>
  <div class="playground">
    <div class="left-panel">
      <p>QQ Simulator (coming in Task 9)</p>
    </div>
    <div class="right-panel">
      <p>Results (coming in Task 10)</p>
    </div>
  </div>
</template>

<style scoped>
.playground {
  display: flex;
  height: 100%;
}

.left-panel {
  flex: 1;
  border-right: 1px solid #ddd;
  padding: 1rem;
  background: white;
}

.right-panel {
  flex: 1;
  padding: 1rem;
  background: #fafafa;
}
</style>
```

- [ ] **Step 9: Install frontend dependencies and verify build**

Run:
```bash
cd ncatbot/webui/frontend && npm install
```
Expected: `node_modules/` created, no errors

Run:
```bash
cd ncatbot/webui/frontend && npx vue-tsc --noEmit
```
Expected: No type errors

- [ ] **Step 10: Add frontend to .gitignore**

Check if `node_modules` is already in `.gitignore`. If not, add `ncatbot/webui/frontend/node_modules/` to the project's `.gitignore`.

- [ ] **Step 11: Commit**

```bash
git add ncatbot/webui/frontend/ .gitignore
git commit -m "feat(webui): scaffold Vue 3 + Vite frontend project"
```

---

### Task 8: Frontend — WebSocket Composable

**Files:**
- Create: `ncatbot/webui/frontend/src/composables/useWebSocket.ts`

- [ ] **Step 1: Create useWebSocket composable**

Create `ncatbot/webui/frontend/src/composables/useWebSocket.ts`:

```typescript
import { ref, readonly } from 'vue'
import type { APICallInfo, TimelineEntry, WSMessage } from '../types/protocol'
import { MsgType } from '../types/protocol'

export function useWebSocket() {
  const connected = ref(false)
  const sessionId = ref<string | null>(null)
  const timeline = ref<TimelineEntry[]>([])
  const recordingCode = ref<string>('')

  let ws: WebSocket | null = null
  let reconnectDelay = 3000
  let reconnectTimer: number | null = null
  const pendingCallbacks = new Map<string, (resp: WSMessage) => void>()

  function connect(url?: string) {
    const wsUrl = url || `ws://${location.host}/ws`
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      connected.value = true
      reconnectDelay = 3000
    }

    ws.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      connected.value = false
    }

    ws.onmessage = (event: MessageEvent) => {
      const msg: WSMessage = JSON.parse(event.data)
      handleMessage(msg)
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    ws?.close()
    ws = null
    connected.value = false
  }

  function scheduleReconnect() {
    reconnectTimer = window.setTimeout(() => {
      connect()
      reconnectDelay = Math.min(reconnectDelay * 2, 30000)
    }, reconnectDelay)
  }

  function send(type: string, payload: Record<string, any>): string {
    const id = crypto.randomUUID()
    ws?.send(JSON.stringify({ type, id, payload }))
    return id
  }

  function sendAndWait(type: string, payload: Record<string, any>): Promise<WSMessage> {
    return new Promise((resolve) => {
      const id = send(type, payload)
      pendingCallbacks.set(id, resolve)
    })
  }

  function handleMessage(msg: WSMessage) {
    // Check for pending request callback
    if (msg.id && pendingCallbacks.has(msg.id)) {
      const cb = pendingCallbacks.get(msg.id)!
      pendingCallbacks.delete(msg.id)
      cb(msg)
    }

    switch (msg.type) {
      case MsgType.SESSION_CREATED:
        sessionId.value = msg.payload.session_id
        break

      case MsgType.API_CALLED:
        timeline.value.push({
          type: 'api_call',
          timestamp: Date.now(),
          action: msg.payload.action,
          params: msg.payload.params,
        })
        break

      case MsgType.SETTLE_DONE:
        timeline.value.push({
          type: 'settle',
          timestamp: Date.now(),
          apiCalls: msg.payload.api_calls,
        })
        break

      case MsgType.RECORDING_EXPORTED:
        recordingCode.value = msg.payload.code
        break

      case MsgType.ERROR:
        console.error('[WebUI]', msg.payload.message)
        break
    }
  }

  async function createSession(platform = 'qq', plugins?: string[]) {
    const resp = await sendAndWait(MsgType.SESSION_CREATE, { platform, plugins })
    sessionId.value = resp.payload.session_id
    return resp.payload.session_id
  }

  function injectEvent(eventType: string, data: Record<string, any>) {
    timeline.value.push({
      type: 'inject',
      timestamp: Date.now(),
      eventType,
      data,
    })
    send(MsgType.EVENT_INJECT, {
      session_id: sessionId.value,
      event_type: eventType,
      data,
    })
  }

  async function settle() {
    const t0 = Date.now()
    const resp = await sendAndWait(MsgType.SESSION_SETTLE, {
      session_id: sessionId.value,
    })
    // Update last settle entry with duration
    const lastSettle = timeline.value.findLast((e) => e.type === 'settle')
    if (lastSettle) {
      lastSettle.durationMs = Date.now() - t0
    }
    return resp.payload.api_calls
  }

  function startRecording() {
    send(MsgType.RECORDING_START, { session_id: sessionId.value })
  }

  function stopRecording() {
    send(MsgType.RECORDING_STOP, { session_id: sessionId.value })
  }

  async function exportRecording() {
    const resp = await sendAndWait(MsgType.RECORDING_EXPORT, {
      session_id: sessionId.value,
      format: 'scenario_dsl',
    })
    recordingCode.value = resp.payload.code
    return resp.payload.code
  }

  function clearTimeline() {
    timeline.value = []
  }

  return {
    connected: readonly(connected),
    sessionId: readonly(sessionId),
    timeline: readonly(timeline),
    recordingCode: readonly(recordingCode),
    connect,
    disconnect,
    createSession,
    injectEvent,
    settle,
    startRecording,
    stopRecording,
    exportRecording,
    clearTimeline,
  }
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run:
```bash
cd ncatbot/webui/frontend && npx vue-tsc --noEmit
```
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add ncatbot/webui/frontend/src/composables/useWebSocket.ts
git commit -m "feat(webui): add useWebSocket composable with reconnect"
```

---

### Task 9: Frontend — QQ Simulator Panel

**Files:**
- Create: `ncatbot/webui/frontend/src/components/qq/QQSimulator.vue`
- Create: `ncatbot/webui/frontend/src/components/qq/MessageInput.vue`
- Create: `ncatbot/webui/frontend/src/components/qq/EventPanel.vue`
- Create: `ncatbot/webui/frontend/src/components/qq/EventForm.vue`
- Modify: `ncatbot/webui/frontend/src/views/TestPlayground.vue`

- [ ] **Step 1: Create MessageInput.vue**

Create `ncatbot/webui/frontend/src/components/qq/MessageInput.vue`:

```vue
<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  send: [text: string]
}>()

const text = ref('')

function handleSend() {
  const trimmed = text.value.trim()
  if (!trimmed) return
  emit('send', trimmed)
  text.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="message-input">
    <textarea
      v-model="text"
      placeholder="输入消息..."
      rows="2"
      @keydown="handleKeydown"
    />
    <button @click="handleSend" :disabled="!text.trim()">发送</button>
  </div>
</template>

<style scoped>
.message-input {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  border-top: 1px solid #e0e0e0;
}

textarea {
  flex: 1;
  resize: none;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
}

button {
  padding: 0.5rem 1rem;
  background: #1677ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

button:disabled {
  background: #bbb;
  cursor: not-allowed;
}
</style>
```

- [ ] **Step 2: Create EventForm.vue**

Create `ncatbot/webui/frontend/src/components/qq/EventForm.vue`:

```vue
<script setup lang="ts">
import { reactive, computed } from 'vue'

interface FieldDef {
  key: string
  label: string
  type: 'text' | 'select'
  default: string
  options?: { value: string; label: string }[]
}

const props = defineProps<{
  title: string
  eventType: string
  fields: FieldDef[]
}>()

const emit = defineEmits<{
  submit: [eventType: string, data: Record<string, any>]
  cancel: []
}>()

const form = reactive<Record<string, string>>({})
for (const f of props.fields) {
  form[f.key] = f.default
}

function handleSubmit() {
  emit('submit', props.eventType, { ...form })
}
</script>

<template>
  <div class="event-form-overlay" @click.self="emit('cancel')">
    <div class="event-form">
      <h3>{{ title }}</h3>
      <div v-for="f in fields" :key="f.key" class="field">
        <label>{{ f.label }}</label>
        <select v-if="f.type === 'select'" v-model="form[f.key]">
          <option v-for="opt in f.options" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <input v-else v-model="form[f.key]" />
      </div>
      <div class="actions">
        <button class="btn-cancel" @click="emit('cancel')">取消</button>
        <button class="btn-submit" @click="handleSubmit">发送事件</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.event-form-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.event-form {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  min-width: 350px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.event-form h3 {
  margin-bottom: 1rem;
}

.field {
  margin-bottom: 0.75rem;
}

.field label {
  display: block;
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.field input,
.field select {
  width: 100%;
  padding: 0.4rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-cancel {
  padding: 0.4rem 1rem;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.btn-submit {
  padding: 0.4rem 1rem;
  background: #1677ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

- [ ] **Step 3: Create EventPanel.vue**

Create `ncatbot/webui/frontend/src/components/qq/EventPanel.vue`:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import EventForm from './EventForm.vue'

const emit = defineEmits<{
  event: [eventType: string, data: Record<string, any>]
}>()

const activeEvent = ref<string | null>(null)

const eventButtons = [
  { category: '通知', events: [
    { type: 'notice.poke', label: '戳一戳', fields: [
      { key: 'user_id', label: '发起者 ID', type: 'text' as const, default: '99999' },
      { key: 'target_id', label: '目标 ID', type: 'text' as const, default: '10001' },
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
    ]},
    { type: 'notice.group_increase', label: '群成员增加', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'sub_type', label: '类型', type: 'select' as const, default: 'approve', options: [
        { value: 'approve', label: '管理员同意' },
        { value: 'invite', label: '被邀请' },
      ]},
    ]},
    { type: 'notice.group_decrease', label: '群成员减少', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'sub_type', label: '类型', type: 'select' as const, default: 'leave', options: [
        { value: 'leave', label: '主动退出' },
        { value: 'kick', label: '被踢出' },
      ]},
    ]},
    { type: 'notice.group_ban', label: '群禁言', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'duration', label: '时长(秒)', type: 'text' as const, default: '600' },
    ]},
    { type: 'notice.group_recall', label: '消息撤回', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '操作者 ID', type: 'text' as const, default: '99999' },
      { key: 'message_id', label: '消息 ID', type: 'text' as const, default: 'msg_001' },
    ]},
  ]},
  { category: '请求', events: [
    { type: 'request.friend', label: '加好友请求', fields: [
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'comment', label: '验证消息', type: 'text' as const, default: '请求加好友' },
    ]},
    { type: 'request.group', label: '加群请求', fields: [
      { key: 'group_id', label: '群号', type: 'text' as const, default: '100200' },
      { key: 'user_id', label: '用户 ID', type: 'text' as const, default: '99999' },
      { key: 'sub_type', label: '类型', type: 'select' as const, default: 'add', options: [
        { value: 'add', label: '申请加群' },
        { value: 'invite', label: '被邀请' },
      ]},
    ]},
  ]},
]

function onSubmit(eventType: string, data: Record<string, any>) {
  emit('event', eventType, data)
  activeEvent.value = null
}
</script>

<template>
  <div class="event-panel">
    <details open>
      <summary>事件面板</summary>
      <div v-for="cat in eventButtons" :key="cat.category" class="category">
        <span class="cat-label">{{ cat.category }}</span>
        <button
          v-for="ev in cat.events"
          :key="ev.type"
          @click="activeEvent = ev.type"
          class="event-btn"
        >
          {{ ev.label }}
        </button>
      </div>
    </details>
    <EventForm
      v-if="activeEvent"
      :title="eventButtons.flatMap(c => c.events).find(e => e.type === activeEvent)!.label"
      :event-type="activeEvent"
      :fields="eventButtons.flatMap(c => c.events).find(e => e.type === activeEvent)!.fields"
      @submit="onSubmit"
      @cancel="activeEvent = null"
    />
  </div>
</template>

<style scoped>
.event-panel {
  padding: 0.5rem;
}

details summary {
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #555;
}

.category {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.5rem;
}

.cat-label {
  font-size: 0.8rem;
  color: #999;
  width: 3rem;
}

.event-btn {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.event-btn:hover {
  background: #e0e0e0;
}
</style>
```

- [ ] **Step 4: Create QQSimulator.vue**

Create `ncatbot/webui/frontend/src/components/qq/QQSimulator.vue`:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import MessageInput from './MessageInput.vue'
import EventPanel from './EventPanel.vue'

const emit = defineEmits<{
  inject: [eventType: string, data: Record<string, any>]
}>()

const chatMode = ref<'group' | 'private'>('group')
const groupId = ref('100200')
const userId = ref('99999')

function handleSendMessage(text: string) {
  if (chatMode.value === 'group') {
    emit('inject', 'message.group', {
      text,
      group_id: groupId.value,
      user_id: userId.value,
    })
  } else {
    emit('inject', 'message.private', {
      text,
      user_id: userId.value,
    })
  }
}

function handleEvent(eventType: string, data: Record<string, any>) {
  emit('inject', eventType, data)
}
</script>

<template>
  <div class="qq-simulator">
    <div class="mode-tabs">
      <button :class="{ active: chatMode === 'group' }" @click="chatMode = 'group'">群聊</button>
      <button :class="{ active: chatMode === 'private' }" @click="chatMode = 'private'">私聊</button>
    </div>

    <div class="context-bar">
      <template v-if="chatMode === 'group'">
        <label>群号</label>
        <input v-model="groupId" size="8" />
      </template>
      <label>用户 ID</label>
      <input v-model="userId" size="8" />
    </div>

    <div class="message-area">
      <p class="placeholder-text">在下方输入消息或使用事件面板发送模拟事件</p>
    </div>

    <MessageInput @send="handleSendMessage" />
    <EventPanel @event="handleEvent" />
  </div>
</template>

<style scoped>
.qq-simulator {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.mode-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
}

.mode-tabs button {
  flex: 1;
  padding: 0.5rem;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
}

.mode-tabs button.active {
  background: white;
  border-bottom: 2px solid #1677ff;
  font-weight: 600;
}

.context-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f9f9f9;
  font-size: 0.85rem;
}

.context-bar input {
  padding: 0.2rem 0.4rem;
  border: 1px solid #ddd;
  border-radius: 3px;
}

.message-area {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.placeholder-text {
  color: #999;
  text-align: center;
  margin-top: 2rem;
}
</style>
```

- [ ] **Step 5: Update TestPlayground.vue to use QQSimulator**

Replace `ncatbot/webui/frontend/src/views/TestPlayground.vue`:

```vue
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import QQSimulator from '../components/qq/QQSimulator.vue'
import { useWebSocket } from '../composables/useWebSocket'

const ws = useWebSocket()
const initialized = ref(false)

onMounted(async () => {
  ws.connect()
  // Wait for connection, then create session
  const waitForConnection = setInterval(async () => {
    if (ws.connected.value && !initialized.value) {
      clearInterval(waitForConnection)
      await ws.createSession('qq')
      initialized.value = true
    }
  }, 200)
})

onUnmounted(() => {
  ws.disconnect()
})

async function handleInject(eventType: string, data: Record<string, any>) {
  ws.injectEvent(eventType, data)
  await ws.settle()
}
</script>

<template>
  <div class="playground">
    <div class="left-panel">
      <QQSimulator @inject="handleInject" />
    </div>
    <div class="right-panel">
      <div class="connection-status">
        <span :class="ws.connected.value ? 'online' : 'offline'">
          {{ ws.connected.value ? '● 已连接' : '○ 断开' }}
        </span>
        <span v-if="ws.sessionId.value" class="session-id">
          Session: {{ ws.sessionId.value }}
        </span>
      </div>
      <p>结果视图 (Task 10)</p>
      <pre class="timeline-debug">{{ JSON.stringify(ws.timeline.value, null, 2) }}</pre>
    </div>
  </div>
</template>

<style scoped>
.playground {
  display: flex;
  height: 100%;
}

.left-panel {
  flex: 1;
  border-right: 1px solid #ddd;
  background: white;
}

.right-panel {
  flex: 1;
  padding: 1rem;
  background: #fafafa;
  overflow-y: auto;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
}

.online { color: #52c41a; }
.offline { color: #ff4d4f; }

.session-id {
  color: #999;
  font-family: monospace;
}

.timeline-debug {
  font-size: 0.75rem;
  color: #666;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
```

- [ ] **Step 6: Verify TypeScript compiles**

Run:
```bash
cd ncatbot/webui/frontend && npx vue-tsc --noEmit
```
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add ncatbot/webui/frontend/src/
git commit -m "feat(webui): add QQ simulator panel with event buttons"
```

---

### Task 10: Frontend — Result Panel (Structured + Mock Views)

**Files:**
- Create: `ncatbot/webui/frontend/src/components/results/ResultPanel.vue`
- Create: `ncatbot/webui/frontend/src/components/results/StructuredView.vue`
- Create: `ncatbot/webui/frontend/src/components/results/MockView.vue`
- Modify: `ncatbot/webui/frontend/src/views/TestPlayground.vue`

- [ ] **Step 1: Create StructuredView.vue**

Create `ncatbot/webui/frontend/src/components/results/StructuredView.vue`:

```vue
<script setup lang="ts">
import type { TimelineEntry } from '../../types/protocol'

defineProps<{
  entries: readonly TimelineEntry[]
}>()

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour12: false })
}

function formatParams(params: Record<string, any>): string {
  const msg = params?.message
  if (Array.isArray(msg)) {
    const texts = msg
      .filter((s: any) => s.type === 'text')
      .map((s: any) => s.data?.text || '')
    if (texts.length) return texts.join('')
  }
  return JSON.stringify(params).slice(0, 100)
}
</script>

<template>
  <div class="structured-view">
    <div v-for="(entry, i) in entries" :key="i" :class="['entry', entry.type]">
      <span class="time">{{ formatTime(entry.timestamp) }}</span>
      <template v-if="entry.type === 'inject'">
        <span class="arrow">←</span>
        <span class="label">inject:</span>
        <span class="detail">{{ entry.eventType }} {{ JSON.stringify(entry.data) }}</span>
      </template>
      <template v-else-if="entry.type === 'api_call'">
        <span class="arrow">→</span>
        <span class="label">api:</span>
        <span class="action">{{ entry.action }}</span>
        <span class="detail">{{ formatParams(entry.params || {}) }}</span>
      </template>
      <template v-else-if="entry.type === 'settle'">
        <span class="arrow">✓</span>
        <span class="label">settle:</span>
        <span class="detail">
          {{ entry.apiCalls?.length || 0 }} call(s)
          <template v-if="entry.durationMs">, {{ entry.durationMs }}ms</template>
        </span>
      </template>
    </div>
    <div v-if="entries.length === 0" class="empty">
      等待事件注入...
    </div>
  </div>
</template>

<style scoped>
.structured-view {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
}

.entry {
  display: flex;
  gap: 0.5rem;
  padding: 0.2rem 0;
  border-bottom: 1px solid #f0f0f0;
  align-items: baseline;
}

.time { color: #999; min-width: 5rem; }
.arrow { font-weight: bold; min-width: 1rem; text-align: center; }
.label { color: #666; }
.action { color: #1677ff; font-weight: 600; }
.detail { color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.entry.inject .arrow { color: #faad14; }
.entry.api_call .arrow { color: #1677ff; }
.entry.settle .arrow { color: #52c41a; }

.empty {
  color: #999;
  text-align: center;
  padding: 2rem;
}
</style>
```

- [ ] **Step 2: Create MockView.vue**

Create `ncatbot/webui/frontend/src/components/results/MockView.vue`:

```vue
<script setup lang="ts">
import type { TimelineEntry } from '../../types/protocol'

defineProps<{
  entries: readonly TimelineEntry[]
}>()

function extractBubbles(entries: readonly TimelineEntry[]) {
  const bubbles: Array<{
    side: 'user' | 'bot' | 'system'
    text: string
    ts: number
  }> = []

  for (const entry of entries) {
    if (entry.type === 'inject' && entry.eventType?.startsWith('message.')) {
      bubbles.push({
        side: 'user',
        text: entry.data?.text || JSON.stringify(entry.data),
        ts: entry.timestamp,
      })
    } else if (entry.type === 'api_call') {
      const params = entry.params || {}
      const msg = params.message
      if (Array.isArray(msg)) {
        const texts = msg
          .filter((s: any) => s.type === 'text')
          .map((s: any) => s.data?.text || '')
        if (texts.length) {
          bubbles.push({ side: 'bot', text: texts.join(''), ts: entry.timestamp })
        }
        const images = msg.filter((s: any) => s.type === 'image')
        for (const img of images) {
          bubbles.push({
            side: 'bot',
            text: `[图片] ${img.data?.url || img.data?.file || ''}`,
            ts: entry.timestamp,
          })
        }
      } else if (entry.action && !entry.action.startsWith('send_')) {
        bubbles.push({
          side: 'system',
          text: `${entry.action}(${JSON.stringify(params).slice(0, 80)})`,
          ts: entry.timestamp,
        })
      }
    } else if (entry.type === 'inject' && entry.eventType?.startsWith('notice.')) {
      bubbles.push({
        side: 'system',
        text: `[${entry.eventType}] ${JSON.stringify(entry.data)}`,
        ts: entry.timestamp,
      })
    }
  }
  return bubbles
}
</script>

<template>
  <div class="mock-view">
    <div
      v-for="(b, i) in extractBubbles(entries)"
      :key="i"
      :class="['bubble-row', b.side]"
    >
      <div class="bubble">{{ b.text }}</div>
    </div>
    <div v-if="entries.length === 0" class="empty">
      等待消息...
    </div>
  </div>
</template>

<style scoped>
.mock-view {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bubble-row {
  display: flex;
}

.bubble-row.user { justify-content: flex-end; }
.bubble-row.bot { justify-content: flex-start; }
.bubble-row.system { justify-content: center; }

.bubble {
  max-width: 70%;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  word-break: break-word;
}

.user .bubble {
  background: #1677ff;
  color: white;
  border-bottom-right-radius: 2px;
}

.bot .bubble {
  background: white;
  border: 1px solid #e0e0e0;
  border-bottom-left-radius: 2px;
}

.system .bubble {
  background: transparent;
  color: #999;
  font-size: 0.75rem;
}

.empty {
  color: #999;
  text-align: center;
  padding: 2rem;
}
</style>
```

- [ ] **Step 3: Create ResultPanel.vue**

Create `ncatbot/webui/frontend/src/components/results/ResultPanel.vue`:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import type { TimelineEntry } from '../../types/protocol'
import StructuredView from './StructuredView.vue'
import MockView from './MockView.vue'

defineProps<{
  entries: readonly TimelineEntry[]
}>()

const viewMode = ref<'structured' | 'mock'>('structured')
</script>

<template>
  <div class="result-panel">
    <div class="view-tabs">
      <button :class="{ active: viewMode === 'structured' }" @click="viewMode = 'structured'">
        结构化
      </button>
      <button :class="{ active: viewMode === 'mock' }" @click="viewMode = 'mock'">
        仿真
      </button>
    </div>
    <div class="view-content">
      <StructuredView v-if="viewMode === 'structured'" :entries="entries" />
      <MockView v-else :entries="entries" />
    </div>
  </div>
</template>

<style scoped>
.result-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.view-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.view-tabs button {
  padding: 0.5rem 1rem;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
}

.view-tabs button.active {
  background: white;
  border-bottom: 2px solid #1677ff;
  font-weight: 600;
}

.view-content {
  flex: 1;
  overflow-y: auto;
}
</style>
```

- [ ] **Step 4: Update TestPlayground.vue to use ResultPanel**

Replace the right panel in `ncatbot/webui/frontend/src/views/TestPlayground.vue`:

Change the `<div class="right-panel">` section to:

```vue
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import QQSimulator from '../components/qq/QQSimulator.vue'
import ResultPanel from '../components/results/ResultPanel.vue'
import { useWebSocket } from '../composables/useWebSocket'

const ws = useWebSocket()
const initialized = ref(false)

onMounted(async () => {
  ws.connect()
  const waitForConnection = setInterval(async () => {
    if (ws.connected.value && !initialized.value) {
      clearInterval(waitForConnection)
      await ws.createSession('qq')
      initialized.value = true
    }
  }, 200)
})

onUnmounted(() => {
  ws.disconnect()
})

async function handleInject(eventType: string, data: Record<string, any>) {
  ws.injectEvent(eventType, data)
  await ws.settle()
}
</script>

<template>
  <div class="playground">
    <div class="left-panel">
      <QQSimulator @inject="handleInject" />
    </div>
    <div class="right-panel">
      <div class="connection-status">
        <span :class="ws.connected.value ? 'online' : 'offline'">
          {{ ws.connected.value ? '● 已连接' : '○ 断开' }}
        </span>
        <span v-if="ws.sessionId.value" class="session-id">
          Session: {{ ws.sessionId.value }}
        </span>
      </div>
      <ResultPanel :entries="ws.timeline.value" />
    </div>
  </div>
</template>
```

(Keep the same `<style scoped>` block from Task 9, Step 5.)

- [ ] **Step 5: Verify TypeScript compiles**

Run:
```bash
cd ncatbot/webui/frontend && npx vue-tsc --noEmit
```
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add ncatbot/webui/frontend/src/components/results/
git add ncatbot/webui/frontend/src/views/TestPlayground.vue
git commit -m "feat(webui): add result panel with structured + mock views"
```

---

### Task 11: Frontend — Recorder Bar + Code Preview

**Files:**
- Create: `ncatbot/webui/frontend/src/components/recorder/RecorderBar.vue`
- Create: `ncatbot/webui/frontend/src/components/recorder/CodePreview.vue`
- Modify: `ncatbot/webui/frontend/src/views/TestPlayground.vue`

- [ ] **Step 1: Create RecorderBar.vue**

Create `ncatbot/webui/frontend/src/components/recorder/RecorderBar.vue`:

```vue
<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  recording: boolean
}>()

const emit = defineEmits<{
  start: []
  stop: []
  export: []
}>()
</script>

<template>
  <div :class="['recorder-bar', { recording }]">
    <div class="left">
      <template v-if="recording">
        <span class="rec-indicator">🔴 录制中</span>
        <button @click="emit('stop')">停止</button>
      </template>
      <template v-else>
        <button @click="emit('start')">开始录制</button>
      </template>
    </div>
    <div class="right">
      <button @click="emit('export')" :disabled="recording">导出代码</button>
    </div>
  </div>
</template>

<style scoped>
.recorder-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #fafafa;
  border-top: 1px solid #e0e0e0;
}

.recorder-bar.recording {
  background: #fff2f0;
  border-top-color: #ff4d4f;
}

.left, .right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.rec-indicator {
  font-size: 0.85rem;
  font-weight: 600;
}

button {
  padding: 0.3rem 0.8rem;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

button:hover { background: #e0e0e0; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
```

- [ ] **Step 2: Create CodePreview.vue**

Create `ncatbot/webui/frontend/src/components/recorder/CodePreview.vue`:

```vue
<script setup lang="ts">
const props = defineProps<{
  code: string
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function copyToClipboard() {
  navigator.clipboard.writeText(props.code)
}
</script>

<template>
  <div v-if="visible" class="code-overlay" @click.self="emit('close')">
    <div class="code-modal">
      <div class="modal-header">
        <h3>生成的测试代码</h3>
        <div class="actions">
          <button @click="copyToClipboard">复制</button>
          <button @click="emit('close')">关闭</button>
        </div>
      </div>
      <pre class="code-block"><code>{{ code }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
.code-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.code-modal {
  background: white;
  border-radius: 8px;
  width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.actions button {
  padding: 0.3rem 0.8rem;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.code-block {
  flex: 1;
  overflow: auto;
  padding: 1rem 1.5rem;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  line-height: 1.5;
  background: #f7f7f7;
  margin: 0;
  white-space: pre;
}
</style>
```

- [ ] **Step 3: Integrate recorder into TestPlayground.vue**

Update `ncatbot/webui/frontend/src/views/TestPlayground.vue`:

Add imports:
```typescript
import RecorderBar from '../components/recorder/RecorderBar.vue'
import CodePreview from '../components/recorder/CodePreview.vue'
```

Add state:
```typescript
const isRecording = ref(false)
const showCodePreview = ref(false)
```

Add handlers:
```typescript
function handleStartRecording() {
  ws.startRecording()
  isRecording.value = true
}

function handleStopRecording() {
  ws.stopRecording()
  isRecording.value = false
}

async function handleExport() {
  await ws.exportRecording()
  showCodePreview.value = true
}
```

Add template at the bottom (before closing `</div>` of `.playground`):
```html
<RecorderBar
  :recording="isRecording"
  @start="handleStartRecording"
  @stop="handleStopRecording"
  @export="handleExport"
/>
<CodePreview
  :code="ws.recordingCode.value"
  :visible="showCodePreview"
  @close="showCodePreview = false"
/>
```

Update `.playground` style to:
```css
.playground {
  display: flex;
  flex-wrap: wrap;
  height: 100%;
}

.left-panel, .right-panel {
  flex: 1;
  min-width: 0;
}
```

Add RecorderBar to span full width at the bottom of the flex container.

- [ ] **Step 4: Verify TypeScript compiles**

Run:
```bash
cd ncatbot/webui/frontend && npx vue-tsc --noEmit
```
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add ncatbot/webui/frontend/src/components/recorder/
git add ncatbot/webui/frontend/src/views/TestPlayground.vue
git commit -m "feat(webui): add recorder bar and code preview modal"
```

---

### Task 12: Integration Smoke Test — Full End-to-End

**Files:**
- Test: `tests/e2e/test_webui_e2e.py`

- [ ] **Step 1: Write E2E smoke test**

Create `tests/e2e/test_webui_e2e.py`:

```python
"""WUI-E2E-01: Full end-to-end WebUI flow: create → inject → settle → record → export"""

import asyncio
import json

import aiohttp
import pytest

from ncatbot.webui.server import create_app


pytestmark = pytest.mark.asyncio(mode="strict")


@pytest.fixture
async def webui_url():
    app = create_app()
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    await runner.cleanup()


async def test_full_e2e_flow(webui_url):
    """WUI-E2E-01: create session → start recording → inject → settle → stop → export"""
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{webui_url}/ws") as ws:
            # 1) Create session
            await ws.send_json({"type": "session.create", "id": "1", "payload": {"platform": "qq"}})
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            assert resp["type"] == "session.created"
            sid = resp["payload"]["session_id"]

            # 2) Start recording
            await ws.send_json({"type": "recording.start", "payload": {"session_id": sid}})

            # 3) Inject a group message
            await ws.send_json({
                "type": "event.inject",
                "payload": {"session_id": sid, "event_type": "message.group", "data": {"text": "/test"}},
            })

            # 4) Settle
            await ws.send_json({"type": "session.settle", "id": "2", "payload": {"session_id": sid}})
            while True:
                resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
                if resp["type"] == "settle.done":
                    break
            assert isinstance(resp["payload"]["api_calls"], list)

            # 5) Stop recording
            await ws.send_json({"type": "recording.stop", "payload": {"session_id": sid}})

            # 6) Export
            await ws.send_json({"type": "recording.export", "id": "3", "payload": {"session_id": sid, "format": "scenario_dsl"}})
            resp = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
            assert resp["type"] == "recording.exported"
            code = resp["payload"]["code"]
            assert "from ncatbot.testing import TestHarness, Scenario" in code
            assert "qq.group_message" in code
            assert "await scenario.run(h)" in code

            # 7) Destroy session
            await ws.send_json({"type": "session.destroy", "payload": {"session_id": sid}})
```

- [ ] **Step 2: Run E2E test**

Run: `cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/e2e/test_webui_e2e.py -v`
Expected: 1 passed

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/test_webui_e2e.py
git commit -m "test(webui): add full E2E smoke test for WebUI flow"
```

---

### Task 13: Build Frontend and Verify End-to-End

**Files:**
- Create: `ncatbot/webui/static/` (build output)

- [ ] **Step 1: Build frontend**

Run:
```bash
cd ncatbot/webui/frontend && npm run build
```
Expected: Build output in `ncatbot/webui/static/` — `index.html` + `assets/`

- [ ] **Step 2: Start server manually and verify in browser**

Run:
```bash
cd /Users/mi/Desktop/projects/NcatBot && python -m ncatbot test-ui --port 8765
```
Open `http://localhost:8765` in the browser. Verify:
- Page loads with "NcatBot TestUI" header
- QQ Simulator panel on the left
- Result panel on the right (structured view)
- WebSocket connects (green "● 已连接" indicator)
- Typing a message and clicking Send → appears in timeline
- Clicking event buttons → event form pops up

Stop the server with Ctrl+C.

- [ ] **Step 3: Add static build output to .gitignore**

Add to `.gitignore`:
```
ncatbot/webui/static/
```

The static files are build artifacts, not committed. They are produced by `npm run build`.

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: add webui static build output to gitignore"
```

---

### Task 14: Update Test Index and Documentation

**Files:**
- Modify: `tests/README.md`

- [ ] **Step 1: Add WUI spec entries to tests/README.md**

Add a new section for WebUI tests in the test index:

```markdown
### WebUI (WUI-01 ~ WUI-14, WUI-I-01 ~ WUI-I-04, WUI-E2E-01)

| ID | 描述 | 位置 |
|----|------|------|
| WUI-01 | HarnessProxy start/stop | `tests/unit/webui/test_session.py` |
| WUI-02 | HarnessProxy inject+settle | `tests/unit/webui/test_session.py` |
| WUI-03 | HarnessProxy API call hooks | `tests/unit/webui/test_session.py` |
| WUI-04 | HarnessProxy unknown event type | `tests/unit/webui/test_session.py` |
| WUI-05 | SessionManager create+get | `tests/unit/webui/test_session_manager.py` |
| WUI-06 | SessionManager destroy | `tests/unit/webui/test_session_manager.py` |
| WUI-07 | SessionManager cleanup expired | `tests/unit/webui/test_session_manager.py` |
| WUI-08 | SessionManager unknown session | `tests/unit/webui/test_session_manager.py` |
| WUI-09 | RecordingEngine lifecycle | `tests/unit/webui/test_recorder.py` |
| WUI-10 | RecordingEngine capture steps | `tests/unit/webui/test_recorder.py` |
| WUI-11 | RecordingEngine ignore when not recording | `tests/unit/webui/test_recorder.py` |
| WUI-12 | RecordingEngine settle without inject | `tests/unit/webui/test_recorder.py` |
| WUI-13 | RecordingEngine start clears steps | `tests/unit/webui/test_recorder.py` |
| WUI-14 | RecordingEngine export Scenario DSL | `tests/unit/webui/test_recorder.py` |
| WUI-I-01 | Server session.create | `tests/integration/test_webui_server.py` |
| WUI-I-02 | Server inject+settle | `tests/integration/test_webui_server.py` |
| WUI-I-03 | Server recording export | `tests/integration/test_webui_server.py` |
| WUI-I-04 | Server session.destroy | `tests/integration/test_webui_server.py` |
| WUI-E2E-01 | Full E2E flow | `tests/e2e/test_webui_e2e.py` |
```

- [ ] **Step 2: Commit**

```bash
git add tests/README.md
git commit -m "docs: add WebUI test spec entries to test index"
```

---

### Task 15: Run Full Test Suite

- [ ] **Step 1: Run all WebUI tests**

Run:
```bash
cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/unit/webui/ tests/integration/test_webui_server.py tests/e2e/test_webui_e2e.py -v
```
Expected: All 19 tests pass (14 unit + 4 integration + 1 E2E)

- [ ] **Step 2: Run full project tests to check no regressions**

Run:
```bash
cd /Users/mi/Desktop/projects/NcatBot && python -m pytest tests/ -v --ignore=tests/e2e/napcat
```
Expected: All existing tests still pass

- [ ] **Step 3: Final commit with all changes**

```bash
git add -A
git status
# Verify no unintended changes
git commit -m "feat(webui): complete V1 test WebUI implementation

- Backend: protocol types, HarnessProxy, SessionManager, RecordingEngine, aiohttp server
- Frontend: Vue 3 + Vite SPA with QQ simulator, result panel, recorder
- CLI: 'ncatbot test-ui' command
- Tests: 14 unit + 4 integration + 1 E2E"
```
