"""
ai/02_mcp_tools — AI 适配器 MCP 工具调用

演示功能:
  - api.ai.chat() 配置 mcp_servers 后自动加载 MCP 工具
  - 模型自动决定何时调用工具（function calling）
  - 工具结果自动回传模型，形成多轮工具调用循环
  - 临时覆盖 mcp_servers 配置
  - max_tool_calls 上限控制

前置配置:
  adapters:
    - type: ai
      config:
        api_key: "sk-xxxx"             # 或通过环境变量 OPENAI_API_KEY
        completion_model: "gpt-4"
        mcp_servers:
          weather:                     # http 服务器示例（改为你的真实 MCP 服务）
            transport: "http"
            url: "https://mcp.example.com/weather"
          time:                        # stdio 服务器示例
            transport: "stdio"
            command: "npx"
            args: ["-y", "@mcp/time"]
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin


class AIMCPToolsPlugin(NcatBotPlugin):
    """AI 适配器 MCP 工具调用示例"""

    name = "mcp_tools_ai"

    @registrar.qq.on_group_command("ai-mcp")
    async def ai_mcp(self, event: GroupMessageEvent, prompt: str):
        """MCP 工具对话：ai-mcp 现在几点？
        使用 config.yaml 中配置的 mcp_servers，模型自动调用工具。
        """
        resp = await self.api.ai.chat(prompt)
        answer = resp.choices[0].message.content
        await event.reply(answer)

    @registrar.qq.on_group_command("ai-mcp-custom")
    async def ai_mcp_custom(self, event: GroupMessageEvent, prompt: str):
        """临时覆盖 MCP 服务器：ai-mcp-custom 帮我查个天气"""
        resp = await self.api.ai.chat(
            prompt,
            mcp_servers={
                "weather": {
                    "transport": "http",
                    "url": "https://mcp.example.com/weather",
                },
            },
        )
        await event.reply(resp.choices[0].message.content)

    @registrar.qq.on_group_command("ai-mcp-limit")
    async def ai_mcp_limit(self, event: GroupMessageEvent, prompt: str):
        """限制工具调用轮数：ai-mcp-limit 反复查数据（最多 3 轮）"""
        resp = await self.api.ai.chat(prompt, max_tool_calls=3)
        await event.reply(resp.choices[0].message.content)
