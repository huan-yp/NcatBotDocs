# 01_hello_world

> 分类：lark

## 文件结构

~~~text
01_hello_world/
├── main.py
└── manifest.toml
~~~

## main.py

~~~python
"""
lark/01_hello_world — 飞书平台最小可运行插件

演示功能:
  - registrar.lark.on_group_message(): 群消息处理
  - registrar.lark.on_private_message(): 私聊消息处理
  - event.reply() 引用回复
  - LarkPostBuilder 富文本消息

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
  在飞书群聊发消息 "hello" → 收到引用回复
  私聊 Bot 发 "test_post"  → 收到富文本消息
"""

from ncatbot.core import registrar
from ncatbot.adapter.lark import LarkPostBuilder
from ncatbot.event.lark import LarkGroupMessageEvent, LarkPrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("LarkHelloWorld")


class LarkHelloWorldPlugin(NcatBotPlugin):
    name = "hello_world_lark"
    version = "1.0.0"
    author = "NcatBot"
    description = "飞书平台最小可运行插件"

    async def on_load(self):
        LOG.info("飞书 HelloWorld 插件已加载！")

    @registrar.lark.on_group_message()
    async def on_group_hello(self, event: LarkGroupMessageEvent):
        """收到群消息时回复"""
        if "hello" in event.content.lower():
            await event.reply("Hello! 欢迎使用飞书 Bot 👋")
            LOG.info("回复群消息: chat=%s user=%s", event.chat_id, event.user_id)

    @registrar.lark.on_private_message()
    async def on_private_hello(self, event: LarkPrivateMessageEvent):
        """收到私聊消息时回复"""
        if event.content == "test_post":
            # 演示 LarkPostBuilder 富文本
            content = (
                LarkPostBuilder("富文本示例")
                .text("加粗文本 ", styles=["bold"])
                .link("飞书官网", "https://www.feishu.cn")
                .newline()
                .text("这是第二行")
                .build()
            )
            await event.api.send_post(
                receive_id=event.user_id,
                content=content,
                receive_id_type="open_id",
            )
        else:
            await event.reply(f"你好！你说了: {event.content}")
            LOG.info("回复私聊: user=%s", event.user_id)
~~~

## manifest.toml

~~~toml
name = "hello_world_lark"
version = "1.0.0"
main = "main.py"
entry_class = "LarkHelloWorldPlugin"
author = "NcatBot"
description = "飞书平台最小可运行插件"
~~~
