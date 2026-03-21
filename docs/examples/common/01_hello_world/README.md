# 01_hello_world

> 分类：common

## 文件结构

~~~text
01_hello_world/
├── main.py
└── manifest.toml
~~~

## main.py

~~~python
"""
common/01_hello_world — 跨平台最小可运行插件

演示功能:
  - NcatBotPlugin 基类继承
  - manifest.toml 插件清单
  - on_load / on_close 生命周期
  - @registrar.on_command() 跨平台命令装饰器
  - Replyable Trait 跨平台回复
  - 命令参数自动绑定 vs 手动解析对比

本示例不依赖任何平台，可在 QQ / Bilibili / GitHub 上运行。
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event import Replyable
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("HelloWorld")


class HelloWorldPlugin(NcatBotPlugin):
    name = "hello_world_common"
    version = "1.0.0"
    author = "NcatBot"
    description = "跨平台最小可运行插件 — 纯 Trait 编程"

    async def on_load(self):
        LOG.info("HelloWorld 插件已加载！")

    async def on_close(self):
        LOG.info("HelloWorld 插件已卸载。")

    @registrar.on_command("hello", ignore_case=True)
    async def on_hello(self, event):
        """任何平台收到 'hello' 命令时回复（跨平台）"""
        if isinstance(event, Replyable):
            await event.reply(text="Hello, World! 👋")

    @registrar.on_command("hi", ignore_case=True)
    async def on_hi(self, event):
        """用 event.reply() 快速回复（跨平台）"""
        if isinstance(event, Replyable):
            await event.reply(text="你好呀！这是跨平台 hello world 🎉")

    # ---- echo: 自动参数绑定（推荐） ----
    # 实现含参数命令时，建议使用自动参数绑定，框架自动提取并转换参数，
    # 无需手动解析消息。上方 hello / hi 是无参数命令的示例。

    @registrar.on_command("echo")
    async def on_echo(self, event, content: str):
        """'echo 你好' → content='你好'（自动参数绑定）
        'echo "hello world"' → content='hello world'（引号包裹视为整体）
        """
        if isinstance(event, Replyable):
            await event.reply(text=f"🔊 {content}")

    # ---- echo-manual: 手动解析参数（不推荐） ----
    # 同样的功能也可以通过手动解析消息文本实现，但代码更繁琐，
    # 且不支持自动引号处理、类型转换、缺失提示等特性。

    @registrar.on_command("echo-manual")
    async def on_echo_manual(self, event):
        """手动解析版本的 echo（不推荐，仅作对比）"""
        text = getattr(event.data, "raw_message", "") if hasattr(event, "data") else ""
        parts = text.split(maxsplit=1)
        content = parts[1] if len(parts) > 1 else ""
        if not content:
            if isinstance(event, Replyable):
                await event.reply(text="用法: echo-manual <内容>")
            return
        if isinstance(event, Replyable):
            await event.reply(text=f"🔊 {content}")
~~~

## manifest.toml

~~~toml
name = "hello_world_common"
version = "1.0.0"
main = "main.py"
entry_class = "HelloWorldPlugin"
author = "NcatBot"
description = "跨平台最小可运行插件 — 纯 Trait 编程"
~~~

