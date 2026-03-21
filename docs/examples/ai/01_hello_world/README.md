# 01_hello_world

> 分类：ai

## 文件结构

~~~text
01_hello_world/
├── main.py
└── manifest.toml
~~~

## main.py

~~~python
"""
ai/01_hello_world — AI 适配器基础用法

演示功能:
  - api.ai.chat(): Chat Completion（字符串 & messages 两种调用方式）
  - api.ai.embeddings(): 文本向量化
  - api.ai.image_generation(): 图像生成
  - 模型参数覆盖

前置配置:
  adapters:
    - type: ai
      config:
        api_key: "sk-xxxx"             # 或通过环境变量 OPENAI_API_KEY
        completion_model: "gpt-4"
        embedding_model: "text-embedding-3-small"
        image_model: "dall-e-3"
"""

from ncatbot.core import registrar
from ncatbot.event import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin


class AIHelloWorldPlugin(NcatBotPlugin):
    """AI 适配器基础用法示例"""

    name = "hello_world_ai"

    @registrar.on_group_command("ai")
    async def ai_chat(self, event: GroupMessageEvent):
        """简单 AI 对话：/ai 你好"""
        text = event.plain_text.strip()
        if not text:
            await event.reply("用法: /ai <你的问题>")
            return

        resp = await self.api.ai.chat(text)
        answer = resp.choices[0].message.content
        await event.reply(answer)

    @registrar.on_group_command("ai-multi")
    async def ai_multi_turn(self, event: GroupMessageEvent):
        """多轮对话示例：/ai-multi"""
        resp = await self.api.ai.chat([
            {"role": "system", "content": "你是一个简洁的助手，回答不超过50字"},
            {"role": "user", "content": event.plain_text or "你好"},
        ])
        await event.reply(resp.choices[0].message.content)

    @registrar.on_group_command("embed")
    async def ai_embed(self, event: GroupMessageEvent):
        """文本向量化：/embed 文本"""
        text = event.plain_text.strip()
        if not text:
            await event.reply("用法: /embed <文本>")
            return

        resp = await self.api.ai.embeddings(text)
        dim = len(resp.data[0].embedding)
        await event.reply(f"向量维度: {dim}")

    @registrar.on_group_command("imagine")
    async def ai_image(self, event: GroupMessageEvent):
        """图像生成：/imagine 描述"""
        prompt = event.plain_text.strip()
        if not prompt:
            await event.reply("用法: /imagine <图像描述>")
            return

        resp = await self.api.ai.image_generation(prompt, size="1024x1024")
        url = resp.data[0].url
        await event.reply(f"生成的图片: {url}")
~~~

## manifest.toml

~~~toml
name = "hello_world_ai"
version = "1.0.0"
main = "main.py"
entry_class = "AIHelloWorldPlugin"
author = "NcatBot"
description = "AI 适配器基础用法 — Chat / Embeddings / ImageGen"
~~~
