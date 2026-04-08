# NcatBot 测试 WebUI 设计文档

**日期**: 2026-04-08  
**状态**: Draft  
**范围**: V1 — QQ 平台测试 Playground

---

## 1. 概述

### 1.1 目标

为 NcatBot 构建一个可视化测试 WebUI，提供：

- **平台事件模拟器**：模拟 QQ 平台的交互 UI，可视化地发送消息、触发通知/请求事件
- **测试预言渲染**：将 Bot 的 API 调用结果渲染为可视化的输出（结构化日志 + 仿真 QQ 界面）
- **录制与回放**：记录用户在 WebUI 上的操作序列，自动生成可执行的 Scenario DSL 测试代码
- **架构可扩展**：预留 Bot 监控、插件管理、权限管理等管理功能扩展点

### 1.2 用户

| 用户角色 | 使用场景 |
|----------|----------|
| 框架开发者（NcatBot 核心团队） | 调试框架本身、验证跨平台事件链路、回归测试 |
| 插件开发者（第三方用户） | 开发/调试插件时可视化事件流、录制测试用例 |

### 1.3 V1 版本范围

**包含**：

- QQ 平台事件模拟器（群消息、私聊、请求、通知等完整事件类型）
- 输入/输出分屏布局（左侧事件模拟 + 右侧结果展示）
- 结构化日志视图 + 可切换仿真渲染视图
- 录制操作 → 生成 Scenario DSL Python 代码
- CLI 启动命令 `ncatbot test-ui`
- 架构预留多平台和管理 UI 扩展点

**不包含**（后续版本）：

- Bilibili / GitHub / Lark 平台模拟器
- Bot 状态监控面板
- 插件管理界面
- 权限管理（RBAC）界面
- 真实事件捕获与离线回放

### 1.4 与现有测试框架的关系

**保留现有框架，WebUI 叠加在上层**。

```
┌─────────────────┐
│   WebUI 前端     │  ← 新增
├─────────────────┤
│ WebUI Server    │  ← 新增
│ (HarnessProxy)  │
├─────────────────┤
│ ncatbot.testing │  ← 不变
│ TestHarness     │
│ MockAdapter     │
│ Scenario        │
└─────────────────┘
```

WebUI Server 作为 TestHarness 的"远程控制器"，复用全部现有测试引擎能力。

---

## 2. 架构设计

### 2.1 整体架构

```
┌──────────────────────────────────────────────┐
│  Vue 3 SPA (Vite)                            │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ QQ 模拟器 │  │ 结果视图  │  │ 录制控制台 │  │
│  │ 面板      │  │ 面板     │  │            │  │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       └──────────────┴──────────────┘         │
│                    WebSocket                  │
└────────────────────┬─────────────────────────┘
                     │
┌────────────────────┴─────────────────────────┐
│  WebUI Server (aiohttp)                       │
│  ┌─────────────┐  ┌────────────────────────┐ │
│  │ WS Handler  │  │ SessionManager         │ │
│  │ (路由协议)   │  │ 管理多个 TestHarness   │ │
│  └──────┬──────┘  └───────────┬────────────┘ │
│         └─────────────────────┘              │
│                    │                          │
│  ┌─────────────────┴──────────────────────┐  │
│  │ HarnessProxy                           │  │
│  │ - inject(event) → harness.inject()     │  │
│  │ - settle() → harness.settle()          │  │
│  │ - get_calls() → mock_api.calls         │  │
│  │ - hook: on_api_call → push to WS       │  │
│  └─────────────────┬──────────────────────┘  │
│                    │                          │
│  ┌─────────────────┴──────────────────────┐  │
│  │ RecordingEngine                        │  │
│  │ - start/stop recording                 │  │
│  │ - capture inject + assert pairs        │  │
│  │ - export to Scenario DSL code          │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────┐
│  现有 ncatbot.testing                         │
│  TestHarness / MockAdapter / MockBotAPI       │
│  Scenario / APICallAssertion / factories      │
└──────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 职责 | 位置 |
|------|------|------|
| **WebUI Server** | aiohttp HTTP/WS 服务，路由请求 | `ncatbot/webui/server.py` |
| **SessionManager** | 管理多个独立测试会话（每个浏览器 tab 一个 TestHarness） | `ncatbot/webui/session.py` |
| **HarnessProxy** | TestHarness 的 WebSocket 适配层，事件注入 + 实时推送 API 调用 | `ncatbot/webui/session.py` |
| **RecordingEngine** | 录制操作序列，导出为 Scenario DSL Python 代码 | `ncatbot/webui/recorder.py` |
| **Protocol** | WebSocket 消息协议定义（类型、结构体） | `ncatbot/webui/protocol.py` |
| **Vue SPA** | 前端界面（QQ 模拟器 + 结果视图 + 录制控制台） | `ncatbot/webui/frontend/` |

### 2.3 项目结构

```
ncatbot/webui/
├── __init__.py
├── server.py              # aiohttp 应用入口
├── session.py             # SessionManager + HarnessProxy
├── recorder.py            # RecordingEngine
├── protocol.py            # WebSocket 消息协议定义
├── static/                # Vue 构建产物（生产模式）
│   ├── index.html
│   └── assets/
└── frontend/              # Vue 3 + Vite 源码
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    └── src/
        ├── App.vue
        ├── main.ts
        ├── router/
        │   └── index.ts
        ├── views/
        │   └── TestPlayground.vue
        ├── components/
        │   ├── qq/            # QQ 平台模拟 UI 组件
        │   │   ├── QQSimulator.vue
        │   │   ├── MessageInput.vue
        │   │   ├── EventPanel.vue
        │   │   └── EventForm.vue
        │   ├── results/       # 结果展示组件
        │   │   ├── ResultPanel.vue
        │   │   ├── StructuredView.vue
        │   │   └── MockView.vue
        │   └── recorder/      # 录制控制组件
        │       ├── RecorderBar.vue
        │       └── CodePreview.vue
        ├── composables/
        │   ├── useWebSocket.ts
        │   └── useRecorder.ts
        └── types/
            └── protocol.ts
```

---

## 3. WebSocket 协议

### 3.1 消息格式

```typescript
interface WSMessage {
  type: string;        // 消息类型
  id?: string;         // 请求 ID（用于请求-响应配对）
  payload: any;        // 消息体
}
```

### 3.2 前端 → 后端

| type | 说明 | payload |
|------|------|---------|
| `session.create` | 创建测试会话 | `{ platform: "qq", plugins?: string[] }` |
| `session.destroy` | 销毁会话 | `{ session_id: string }` |
| `event.inject` | 注入模拟事件 | `{ session_id: string, event_type: string, data: dict }` |
| `event.inject_raw` | 注入原始 JSON 事件 | `{ session_id: string, raw: dict }` |
| `session.settle` | 等待所有 handler 完成 | `{ session_id: string }` |
| `recording.start` | 开始录制 | `{ session_id: string }` |
| `recording.stop` | 停止录制 | `{ session_id: string }` |
| `recording.export` | 导出录制代码 | `{ session_id: string, format: "scenario_dsl" }` |

### 3.3 后端 → 前端

| type | 说明 | payload |
|------|------|---------|
| `session.created` | 会话已创建 | `{ session_id: string, platform: string }` |
| `api.called` | Bot API 调用（实时推送） | `{ session_id: string, action: string, params: dict, timestamp: float }` |
| `api.called.rendered` | API 调用渲染友好格式 | `{ session_id: string, action: string, rendered_text: string, rendered_images: string[] }` |
| `settle.done` | 所有 handler 已完成 | `{ session_id: string, api_calls: list[dict] }` |
| `recording.exported` | 录制代码已生成 | `{ session_id: string, code: string }` |
| `error` | 错误信息 | `{ message: string, detail?: string }` |

### 3.4 事件类型映射

前端 `event.inject` 的 `event_type` 字段映射到 `ncatbot.testing.factories.qq` 工厂函数：

| event_type | 工厂函数 | data 字段 |
|------------|----------|-----------|
| `message.group` | `qq.group_message()` | `content`, `group_id`, `user_id` |
| `message.private` | `qq.private_message()` | `content`, `user_id` |
| `request.friend` | `qq.friend_request()` | `user_id`, `comment` |
| `request.group` | `qq.group_request()` | `group_id`, `user_id`, `sub_type` |
| `notice.group_increase` | `qq.group_increase()` | `group_id`, `user_id`, `sub_type` |
| `notice.group_decrease` | `qq.group_decrease()` | `group_id`, `user_id`, `sub_type` |
| `notice.group_ban` | `qq.group_ban()` | `group_id`, `user_id`, `duration` |
| `notice.group_upload` | `qq.group_upload()` | `group_id`, `user_id`, `file_name` |
| `notice.group_admin` | `qq.group_admin()` | `group_id`, `user_id`, `sub_type` |
| `notice.group_recall` | `qq.group_recall()` | `group_id`, `user_id`, `message_id` |
| `notice.friend_recall` | `qq.friend_recall()` | `user_id`, `message_id` |
| `notice.poke` | `qq.poke_notify()` | `group_id`, `user_id`, `target_id` |
| `notice.emoji_like` | `qq.group_emoji_like()` | `group_id`, `user_id`, `emoji_id` |

---

## 4. 后端详细设计

### 4.1 HarnessProxy

TestHarness 的 WebSocket 适配层。解决 TestHarness 为 `async with` 同步生命周期设计，而 WebUI 需要长期保持会话的问题。

```python
class HarnessProxy:
    """WebUI ↔ TestHarness 适配层"""
    
    def __init__(self, platform: str = "qq", plugins: list[str] | None = None):
        self._harness: TestHarness | PluginTestHarness | None = None
        self._platform = platform
        self._plugins = plugins
        self._api_call_hooks: list[Callable] = []
    
    async def start(self):
        """启动 harness（等价于 __aenter__）"""
        if self._plugins:
            self._harness = PluginTestHarness(plugin_names=self._plugins)
        else:
            self._harness = TestHarness(platforms=[self._platform])
        await self._harness.__aenter__()
        self._install_api_hooks()
    
    async def stop(self):
        """停止 harness（等价于 __aexit__）"""
        await self._harness.__aexit__(None, None, None)
    
    async def inject(self, event_type: str, data: dict):
        """将前端事件转换为 factory 调用 → inject"""
        event_data = self._build_event(event_type, data)
        await self._harness.inject(event_data)
    
    async def settle(self) -> list[dict]:
        """等待完成，返回期间所有 API 调用"""
        await self._harness.settle()
        return self._get_recent_calls()
    
    def on_api_call(self, callback: Callable):
        """注册 API 调用回调（实时推送给 WebSocket）"""
        self._api_call_hooks.append(callback)
    
    def _install_api_hooks(self):
        """在 MockBotAPI 上安装 hook，拦截 API 调用
        
        注意：实现时需确认 MockBotAPI 的实际拦截点。
        可能的方案：
        - monkey-patch MockAPIBase 的 __call__ / _record_call
        - 为 MockAPIBase 新增 on_call callback 机制（更干净）
        实现阶段根据实际代码选择最佳切入点。
        """
        mock_api = self._harness.mock_api_for(self._platform)
        original_record = mock_api._record_call
        async def hooked_record(action, **params):
            result = await original_record(action, **params)
            for hook in self._api_call_hooks:
                await hook(action, params)
            return result
        mock_api._record_call = hooked_record
    
    def _build_event(self, event_type: str, data: dict):
        """event_type + data → factory 函数调用"""
        from ncatbot.testing.factories import qq
        factory_map = {
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
            "notice.poke": qq.poke_notify,
            "notice.emoji_like": qq.group_emoji_like,
        }
        factory = factory_map[event_type]
        return factory(**data)
    
    def _get_recent_calls(self) -> list[dict]:
        """获取最近的 API 调用列表"""
        mock_api = self._harness.mock_api_for(self._platform)
        return [
            {"action": c.action, "params": c.params, "timestamp": c.timestamp}
            for c in mock_api.calls
        ]
```

### 4.2 SessionManager

```python
class SessionManager:
    """管理多个 WebUI 测试会话"""
    
    SESSION_TIMEOUT = 1800  # 30 分钟超时
    
    def __init__(self):
        self._sessions: dict[str, HarnessProxy] = {}
        self._last_activity: dict[str, float] = {}
    
    async def create_session(self, platform="qq", plugins=None) -> str:
        session_id = uuid4().hex[:8]
        proxy = HarnessProxy(platform, plugins)
        await proxy.start()
        self._sessions[session_id] = proxy
        self._last_activity[session_id] = time.time()
        return session_id
    
    async def destroy_session(self, session_id: str):
        proxy = self._sessions.pop(session_id, None)
        self._last_activity.pop(session_id, None)
        if proxy:
            await proxy.stop()
    
    def get(self, session_id: str) -> HarnessProxy:
        self._last_activity[session_id] = time.time()
        return self._sessions[session_id]
    
    async def cleanup_expired(self):
        """清理超时会话"""
        now = time.time()
        expired = [
            sid for sid, t in self._last_activity.items()
            if now - t > self.SESSION_TIMEOUT
        ]
        for sid in expired:
            await self.destroy_session(sid)
```

### 4.3 RecordingEngine

```python
@dataclass
class RecordedStep:
    """录制的单步操作"""
    event_type: str
    event_data: dict
    api_calls: list[dict]
    timestamp: float

class RecordingEngine:
    """录制操作序列，生成 Scenario DSL 代码"""
    
    def __init__(self):
        self._recording = False
        self._steps: list[RecordedStep] = []
        self._pending_event: tuple[str, dict] | None = None
    
    def start(self):
        self._recording = True
        self._steps.clear()
    
    def stop(self):
        self._recording = False
    
    @property
    def is_recording(self) -> bool:
        return self._recording
    
    def record_inject(self, event_type: str, event_data: dict):
        """记录一次事件注入"""
        if not self._recording:
            return
        self._pending_event = (event_type, event_data)
    
    def record_settle(self, api_calls: list[dict]):
        """记录 settle 后的 API 调用结果"""
        if not self._recording or not self._pending_event:
            return
        event_type, event_data = self._pending_event
        self._steps.append(RecordedStep(
            event_type=event_type,
            event_data=event_data,
            api_calls=api_calls,
            timestamp=time.time(),
        ))
        self._pending_event = None
    
    def export_scenario_dsl(self) -> str:
        """导出为 Scenario DSL Python 代码"""
        lines = [
            'import pytest',
            'from ncatbot.testing import TestHarness, Scenario',
            'from ncatbot.testing.factories import qq',
            '',
            'pytestmark = pytest.mark.asyncio(mode="strict")',
            '',
            '',
            f'async def test_recorded_scenario():',
            f'    """录制生成 - {datetime.now().strftime("%Y-%m-%d %H:%M")}"""',
            f'    async with TestHarness() as h:',
            f'        scenario = Scenario()',
        ]
        
        for i, step in enumerate(self._steps, 1):
            lines.append(f'')
            lines.append(f'        # Step {i}')
            factory_call = self._build_factory_call(step.event_type, step.event_data)
            lines.append(f'        scenario.inject({factory_call})')
            lines.append(f'        scenario.settle()')
            
            for call in step.api_calls:
                lines.append(f'        scenario.assert_api_called("{call["action"]}")')
                # 尝试提取文本断言
                text = self._extract_text_from_call(call)
                if text:
                    lines.append(f'        scenario.assert_api_text("{call["action"]}", {text!r})')
        
        lines.append(f'')
        lines.append(f'        await scenario.run(h)')
        lines.append('')
        
        return '\n'.join(lines)
    
    def _build_factory_call(self, event_type: str, data: dict) -> str:
        """构建工厂函数调用代码"""
        factory_names = {
            "message.group": "qq.group_message",
            "message.private": "qq.private_message",
            "request.friend": "qq.friend_request",
            "request.group": "qq.group_request",
            "notice.group_increase": "qq.group_increase",
            "notice.group_decrease": "qq.group_decrease",
            "notice.group_ban": "qq.group_ban",
            "notice.poke": "qq.poke_notify",
        }
        name = factory_names.get(event_type, f"qq.{event_type}")
        args = ", ".join(f'{k}={v!r}' for k, v in data.items())
        return f'{name}({args})'
    
    def _extract_text_from_call(self, call: dict) -> str | None:
        """从 API 调用中提取文本内容"""
        params = call.get("params", {})
        message = params.get("message", [])
        texts = []
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") == "text":
                texts.append(seg["data"]["text"])
        return "".join(texts) if texts else None
```

### 4.4 WebUI Server

```python
# server.py
from aiohttp import web
import aiohttp

async def start_webui(port: int = 8765, plugins: list[str] | None = None, dev: bool = False):
    """启动 WebUI 服务"""
    app = web.Application()
    session_mgr = SessionManager()
    
    # WebSocket 端点
    app.router.add_get("/ws", lambda req: ws_handler(req, session_mgr))
    
    if dev:
        # 开发模式：代理到 Vite dev server (localhost:5173)
        app.router.add_route("*", "/{path:.*}", vite_proxy_handler)
    else:
        # 生产模式：直接服务静态文件
        static_dir = Path(__file__).parent / "static"
        app.router.add_static("/assets", static_dir / "assets")
        app.router.add_get("/{path:.*}", lambda req: serve_index(req, static_dir))
    
    # 定期清理超时会话
    async def periodic_cleanup(app):
        while True:
            await asyncio.sleep(300)
            await session_mgr.cleanup_expired()
    app.on_startup.append(lambda app: asyncio.create_task(periodic_cleanup(app)))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", port)
    await site.start()
    print(f"NcatBot TestUI: http://localhost:{port}")
    
    # 保持运行
    await asyncio.Event().wait()


async def ws_handler(request: web.Request, session_mgr: SessionManager) -> web.WebSocketResponse:
    """WebSocket 消息路由"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    recorders: dict[str, RecordingEngine] = {}
    
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            msg_type = data["type"]
            payload = data.get("payload", {})
            msg_id = data.get("id")
            
            if msg_type == "session.create":
                session_id = await session_mgr.create_session(
                    platform=payload.get("platform", "qq"),
                    plugins=payload.get("plugins"),
                )
                proxy = session_mgr.get(session_id)
                recorders[session_id] = RecordingEngine()
                
                # 注册 API 调用实时推送
                async def on_api_call(action, params, sid=session_id):
                    await ws.send_json({
                        "type": "api.called",
                        "payload": {
                            "session_id": sid,
                            "action": action,
                            "params": params,
                            "timestamp": time.time(),
                        }
                    })
                proxy.on_api_call(on_api_call)
                
                await ws.send_json({
                    "type": "session.created",
                    "id": msg_id,
                    "payload": {"session_id": session_id, "platform": payload.get("platform", "qq")}
                })
            
            elif msg_type == "event.inject":
                session_id = payload["session_id"]
                proxy = session_mgr.get(session_id)
                recorder = recorders.get(session_id)
                
                await proxy.inject(payload["event_type"], payload["data"])
                if recorder:
                    recorder.record_inject(payload["event_type"], payload["data"])
            
            elif msg_type == "event.inject_raw":
                session_id = payload["session_id"]
                proxy = session_mgr.get(session_id)
                await proxy.inject_raw(payload["raw"])
            
            elif msg_type == "session.settle":
                session_id = payload["session_id"]
                proxy = session_mgr.get(session_id)
                recorder = recorders.get(session_id)
                
                calls = await proxy.settle()
                if recorder:
                    recorder.record_settle(calls)
                
                await ws.send_json({
                    "type": "settle.done",
                    "id": msg_id,
                    "payload": {"session_id": session_id, "api_calls": calls}
                })
            
            elif msg_type == "recording.start":
                session_id = payload["session_id"]
                recorder = recorders.get(session_id)
                if recorder:
                    recorder.start()
            
            elif msg_type == "recording.stop":
                session_id = payload["session_id"]
                recorder = recorders.get(session_id)
                if recorder:
                    recorder.stop()
            
            elif msg_type == "recording.export":
                session_id = payload["session_id"]
                recorder = recorders.get(session_id)
                code = recorder.export_scenario_dsl() if recorder else ""
                await ws.send_json({
                    "type": "recording.exported",
                    "id": msg_id,
                    "payload": {"session_id": session_id, "code": code}
                })
            
            elif msg_type == "session.destroy":
                session_id = payload["session_id"]
                await session_mgr.destroy_session(session_id)
                recorders.pop(session_id, None)
    
    return ws
```

---

## 5. 前端详细设计

### 5.1 页面布局

```
┌─────────────────────────────────────────────────────────┐
│                    NcatBot TestUI                        │
│  [Test Playground] [Monitor*] [Plugins*] [Settings*]    │
├───────────────────────┬─────────────────────────────────┤
│   QQ 模拟器            │       结果视图                   │
│                       │  [结构化] [仿真]  ← 视图切换      │
│  ┌─ 群聊 ─┬─ 私聊 ─┐   │                                │
│  │         │        │   │  [14:32:01] ← inject:         │
│  │  [群号输入]      │   │    message.group {/help}       │
│  │                  │   │  [14:32:01] → api:             │
│  │                  │   │    send_group_msg              │
│  │                  │   │    └─ message: "帮助信息..."    │
│  │                  │   │  [14:32:01] ✓ settle: 12ms    │
│  │                  │   │                                │
│  │                  │   │                                │
│  └──────────────────┘   │                                │
│  [消息输入框] [发送]     │                                │
│                        │                                │
│  ▼ 事件面板 ─────────  │                                │
│  [戳一戳] [入群] [退群] │                                │
│  [禁言] [好友请求]      │                                │
│  [加群请求] [撤回] ...  │                                │
├───────────────────────┴─────────────────────────────────┤
│  🔴 录制中  [停止]  [导出代码]  │ Steps: 3               │
└─────────────────────────────────────────────────────────┘

* 标注的是未来扩展页面
```

### 5.2 核心组件

#### QQSimulator.vue

QQ 模拟器顶层组件，包含：
- 群聊/私聊标签页切换
- 群号/用户号输入
- 消息输入框 + 发送按钮
- 事件按钮面板（折叠式）

#### EventPanel.vue

事件按钮面板，按分类展示：

| 分类 | 事件按钮 | 弹出表单字段 |
|------|----------|-------------|
| 通知 | 戳一戳 | user_id, target_id |
| 通知 | 群成员增加 | group_id, user_id, sub_type(join/invite) |
| 通知 | 群成员减少 | group_id, user_id, sub_type(leave/kick) |
| 通知 | 群禁言 | group_id, user_id, duration |
| 通知 | 群文件上传 | group_id, user_id, file_name |
| 通知 | 群管理变动 | group_id, user_id, sub_type(set/unset) |
| 通知 | 消息撤回 | group_id/user_id, message_id |
| 通知 | 表情回应 | group_id, user_id, emoji_id |
| 请求 | 加好友请求 | user_id, comment |
| 请求 | 加群请求 | group_id, user_id, sub_type(add/invite) |

#### ResultPanel.vue

右侧结果展示，两种视图可切换：

**StructuredView**：时间线式 API 调用日志
- 每行展示：时间戳 + 方向箭头 + 消息类型 + 关键参数
- inject 用 `←` 标记，api call 用 `→` 标记
- settle 用 `✓` 标记并显示耗时

**MockView**：仿真 QQ 界面
- 用户发的消息显示为右侧气泡（蓝色）
- Bot 的回复显示为左侧气泡（白色）
- 系统事件（入群、禁言等）显示为居中灰色文字
- 图片消息显示缩略图占位 + URL

### 5.3 WebSocket 通信层

```typescript
// composables/useWebSocket.ts
export function useWebSocket(url: string) {
  const connected = ref(false)
  const sessionId = ref<string | null>(null)
  const apiCalls = ref<APICall[]>([])
  let ws: WebSocket | null = null
  let reconnectTimer: number | null = null
  
  function connect() {
    ws = new WebSocket(url)
    ws.onopen = () => { connected.value = true }
    ws.onclose = () => {
      connected.value = false
      // 指数退避重连（3s, 6s, 12s, max 30s）
      scheduleReconnect()
    }
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      handleMessage(msg)
    }
  }
  
  function send(type: string, payload: any) {
    ws?.send(JSON.stringify({ type, payload, id: crypto.randomUUID() }))
  }
  
  async function createSession(platform = "qq", plugins?: string[]) {
    send("session.create", { platform, plugins })
  }
  
  async function injectEvent(eventType: string, data: Record<string, any>) {
    send("event.inject", { session_id: sessionId.value, event_type: eventType, data })
  }
  
  async function settle() {
    send("session.settle", { session_id: sessionId.value })
  }
  
  return { connected, sessionId, apiCalls, connect, createSession, injectEvent, settle }
}
```

---

## 6. 录制引擎详细设计

### 6.1 录制流程

```
用户点击 [开始录制]
    │
    ├── RecordingEngine.start()
    │
    ├── 用户在 QQ 模拟器操作（发消息、触发事件）
    │   ├── event.inject → recorder.record_inject(type, data)
    │   └── session.settle → recorder.record_settle(api_calls)
    │       └── 每次 inject+settle 产生一个 RecordedStep
    │
    ├── 用户点击 [停止录制]
    │   └── RecordingEngine.stop()
    │
    ├── (可选) 用户在前端编辑断言
    │   ├── 勾选/取消哪些 API 调用需要断言
    │   ├── 编辑文本匹配内容
    │   └── 删除不需要的步骤
    │
    └── 用户点击 [导出代码]
        └── RecordingEngine.export_scenario_dsl() → Python 代码
```

### 6.2 生成代码示例

用户操作：
1. 发送群消息 `/help`（群号 123456）→ Bot 回复帮助信息
2. 发送群消息 `/ping` → Bot 回复 `pong`
3. 触发戳一戳事件 → Bot 回复"别戳了"

生成代码：

```python
import pytest
from ncatbot.testing import TestHarness, Scenario
from ncatbot.testing.factories import qq

pytestmark = pytest.mark.asyncio(mode="strict")


async def test_recorded_scenario():
    """录制生成 - 2026-04-08 14:32"""
    async with TestHarness() as h:
        scenario = Scenario()

        # Step 1: 群消息 /help
        scenario.inject(qq.group_message(content="/help", group_id="123456"))
        scenario.settle()
        scenario.assert_api_called("send_group_msg")
        scenario.assert_api_text("send_group_msg", "帮助信息...")

        # Step 2: 群消息 /ping
        scenario.inject(qq.group_message(content="/ping", group_id="123456"))
        scenario.settle()
        scenario.assert_api_called("send_group_msg")
        scenario.assert_api_text("send_group_msg", "pong")

        # Step 3: 戳一戳
        scenario.inject(qq.poke_notify(user_id="789", target_id="bot"))
        scenario.settle()
        scenario.assert_api_called("send_group_msg")
        scenario.assert_api_text("send_group_msg", "别戳了")

        await scenario.run(h)
```

---

## 7. CLI 集成

### 7.1 命令定义

```bash
# 基本启动
ncatbot test-ui

# 指定端口
ncatbot test-ui --port 9000

# 加载特定插件
ncatbot test-ui --plugins hello_world,my_plugin

# 开发模式（前端 HMR + Vite dev server 代理）
ncatbot test-ui --dev
```

### 7.2 实现位置

在 `ncatbot/cli/commands/` 下新增 `test_ui.py`：

```python
import click
import asyncio

@click.command("test-ui")
@click.option("--port", default=8765, help="WebUI 服务端口")
@click.option("--plugins", default=None, help="要加载的插件列表（逗号分隔）")
@click.option("--dev", is_flag=True, help="开发模式（代理 Vite dev server）")
def test_ui_command(port, plugins, dev):
    """启动测试 WebUI"""
    from ncatbot.webui.server import start_webui
    plugin_list = plugins.split(",") if plugins else None
    asyncio.run(start_webui(port=port, plugins=plugin_list, dev=dev))
```

---

## 8. 依赖管理

### 8.1 Python 依赖

WebUI 作为可选依赖组（aiohttp 已是核心依赖，无需额外添加）：

```toml
# pyproject.toml - 无需新增 Python 依赖
# aiohttp>=3.9 已在核心依赖中
```

### 8.2 前端依赖

```json
// ncatbot/webui/frontend/package.json
{
  "dependencies": {
    "vue": "^3.4",
    "vue-router": "^4.3"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0",
    "vite": "^5.4",
    "typescript": "^5.4"
  }
}
```

### 8.3 构建产物

前端构建产物输出到 `ncatbot/webui/static/`，随 Python 包分发。

开发模式下前端由 Vite dev server (`:5173`) 提供，aiohttp 代理所有非 API 请求到 Vite。

---

## 9. 可扩展性设计

### 9.1 多平台扩展

前端平台面板注册机制：

```typescript
interface PlatformPanel {
  name: string;                    // "qq" | "bilibili" | "github"
  label: string;                   // 显示名
  EventInputComponent: Component;  // 该平台的事件输入 UI 组件
  ResultRenderer: Component;       // 该平台的仿真渲染组件
}
```

V1 只实现 `qq` 面板，但组件接口便于后续添加 `bilibili` / `github` 面板。

### 9.2 管理 UI 扩展

后端路由模块化：

```
/ws                    # 测试交互 WebSocket（V1）
/api/sessions          # 会话管理 REST（V1）
/api/bot/status        # Bot 状态（未来）
/api/plugins           # 插件管理（未来）
/api/rbac              # 权限管理（未来）
```

前端 Vue Router 对应规划：

```
/test                  # 测试 Playground（V1）
/monitor               # Bot 监控面板（未来）
/plugins               # 插件管理（未来）
/settings              # 权限/配置（未来）
```

### 9.3 错误处理

- WebSocket 断连自动重连（前端指数退避：3s → 6s → 12s → max 30s）
- Handler 异常 → 推送 `error` 消息到前端，不影响会话
- 会话超时清理（30 分钟无操作自动销毁 TestHarness）
- 前端网络错误 → 显示连接状态指示器

---

## 10. 技术决策总结

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 架构模式 | TestHarness 代理模式 | 复用现有测试引擎，最小改动 |
| 部署模式 | 本地优先，架构可扩展 | 满足开发工具 + 未来管理 UI 需求 |
| 前端框架 | Vue 3 + Vite | 生态成熟、组件库丰富、上手快 |
| 后端框架 | aiohttp | 已有依赖，不增加安装体积 |
| 实时通信 | WebSocket 双向 | 事件注入 + API 调用实时推送 |
| 测试代码格式 | Scenario DSL (Python) | 与现有测试框架统一 |
| 平台范围 (V1) | 仅 QQ | 快速验证方案 |
| 项目位置 | `ncatbot/webui/` 独立模块 | 不耦合 service/plugin 体系 |
