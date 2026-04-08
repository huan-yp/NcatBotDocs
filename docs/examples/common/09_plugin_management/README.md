# 09_plugin_management

> 分类：common

## 这个示例教什么

展示插件的动态管理能力：查看所有已加载/已索引插件、运行时热重载指定插件，以及利用 `on_load()` / `on_close()` 生命周期回调和 `self.data` 实现状态持久化。

## 你将学到

- `self._plugin_loader.list_plugins()` / `list_indexed()` 查询插件状态
- `self._plugin_loader.reload_plugin(name)` 热重载插件
- `on_load()` / `on_close()` 生命周期回调时机
- `self.data` 在重载中保持状态（DataMixin 自动持久化到 JSON）

## 前置知识

- [common/01_hello_world](../01_hello_world/) — 插件基础结构
- [common/02_config_and_data](../02_config_and_data/) — `self.data` 持久化机制

## 目录结构

```text
09_plugin_management/
├── main.py
├── manifest.toml
└── README.md
```

## 完整代码

```python
"""
common/09_plugin_management — 插件管理与生命周期演示

演示功能:
  - 通过 self._plugin_loader 动态查询/重载插件
  - on_load / on_close 生命周期回调
  - self.data 状态持久化（重载计数、时间戳）
  - @registrar.on_command() 跨平台命令

本示例不依赖任何平台，可在 QQ / Bilibili / GitHub 上运行。
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

import time

from ncatbot.core import registrar
from ncatbot.event import Replyable
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("PluginManagement")


class PluginManagementPlugin(NcatBotPlugin):
    name = "plugin_management_demo"
    version = "1.0.0"
    author = "NcatBot"
    description = "插件管理示例 — 动态加载/卸载、生命周期回调与状态持久化"

    async def on_load(self):
        # 持久化数据初始化
        self.data.setdefault("reload_count", 0)
        self.data["reload_count"] += 1
        self.data["last_load_time"] = time.time()

        LOG.info(
            "PluginManagement 已加载（第 %d 次）",
            self.data["reload_count"],
        )

    async def on_close(self):
        LOG.info("PluginManagement 正在卸载，累计加载 %d 次", self.data["reload_count"])

    # ------------------------------------------------------------------
    # 插件列表
    # ------------------------------------------------------------------

    @registrar.on_command("插件列表")
    async def on_list_plugins(self, event):
        """列出所有已加载插件及索引中的插件"""
        loader = self._plugin_loader

        loaded = loader.list_plugins()
        indexed = loader.list_indexed()

        lines = ["📦 插件列表:"]
        lines.append(f"  已加载: {len(loaded)} 个")
        lines.append(f"  已索引: {len(indexed)} 个")
        lines.append("")

        for name in sorted(indexed.keys()):
            manifest = indexed[name]
            status = "✅ 已加载" if name in loaded else "⬚ 未加载"
            lines.append(f"  {status} {name} v{manifest.version}")

        if isinstance(event, Replyable):
            await event.reply(text="\n".join(lines))

    # ------------------------------------------------------------------
    # 重载插件
    # ------------------------------------------------------------------

    @registrar.on_command("重载插件")
    async def on_reload_plugin(self, event, name: str):
        """重载指定插件（卸载 → 重索引 → 加载）"""
        loader = self._plugin_loader

        # 检查插件是否已索引
        indexed = loader.list_indexed()
        if name not in indexed:
            if isinstance(event, Replyable):
                await event.reply(text=f"❌ 未找到插件 [{name}]，请检查插件名")
            return

        if isinstance(event, Replyable):
            await event.reply(text=f"🔄 正在重载插件 [{name}]...")

        success = await loader.reload_plugin(name)
        if isinstance(event, Replyable):
            if success:
                await event.reply(text=f"✅ 插件 [{name}] 重载成功")
            else:
                await event.reply(text=f"❌ 插件 [{name}] 重载失败，请查看日志")

    # ------------------------------------------------------------------
    # 当前插件状态
    # ------------------------------------------------------------------

    @registrar.on_command("插件状态")
    async def on_plugin_status(self, event):
        """显示当前插件自身的运行状态"""
        reload_count = self.data.get("reload_count", 0)
        last_load = self.data.get("last_load_time", 0)
        uptime = time.time() - last_load if last_load else 0

        # 格式化运行时长
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        lines = [
            "📊 插件状态:",
            f"  名称: {self.name}",
            f"  版本: {self.version}",
            f"  累计加载次数: {reload_count}",
            f"  本次运行时长: {uptime_str}",
        ]

        if isinstance(event, Replyable):
            await event.reply(text="\n".join(lines))
```

## 关键代码讲解

### 生命周期回调与状态持久化

```python
async def on_load(self):
    self.data.setdefault("reload_count", 0)
    self.data["reload_count"] += 1
    self.data["last_load_time"] = time.time()
```

`on_load()` 在每次插件加载时调用。`self.data` 是 `DataMixin` 提供的字典，自动持久化到 `data.json`。这里用它记录累计加载次数和最后加载时间，即使 Bot 重启也不会丢失。

### 查询插件列表

```python
loaded = loader.list_plugins()     # 已加载插件名列表
indexed = loader.list_indexed()    # 所有已索引清单 {name: PluginManifest}
```

`list_plugins()` 返回当前内存中已加载的插件名，`list_indexed()` 返回框架扫描到的所有插件清单（含未加载的）。

### 热重载插件

```python
success = await loader.reload_plugin(name)
```

`reload_plugin` 内部执行 **卸载 → 重新扫描 manifest → 重新加载** 三步，支持代码和配置的热更新。

### on_close 清理

```python
async def on_close(self):
    LOG.info("正在卸载，累计加载 %d 次", self.data["reload_count"])
```

`on_close()` 在插件被卸载或 Bot 关闭时调用。`DataMixin` 会在 `_mixin_unload` 阶段自动保存 `self.data`，无需手动调用。

## 运行方式

将本文件夹复制到 `plugins/` 目录，启动 Bot。发送以下命令测试：

```text
插件列表            → 查看所有已加载/已索引插件
重载插件 hello_world → 热重载 hello_world 插件
插件状态            → 查看本插件的加载次数和运行时长
```

## 延伸阅读

- [common/02_config_and_data](../02_config_and_data/) — `self.data` 持久化机制详解
- [common/08_dispatch_filter](../08_dispatch_filter/) — 过滤规则管理（可配合插件管理使用）
