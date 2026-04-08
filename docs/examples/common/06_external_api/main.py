"""
common/07_external_api — 外部 API 集成（跨平台）

演示功能:
  - 异步 HTTP 请求 (aiohttp)
  - ConfigMixin 管理 API key / URL
  - @registrar.on_command() 跨平台命令
  - 错误处理与优雅降级

本示例不依赖任何平台。
使用方式:
  "每日一言"         → 调用一言 API 获取随机一句话
  "设置一言源 xxx"   → 修改一言 API 地址
  "api状态"          → 查看 API 配置和状态
"""

import aiohttp

from ncatbot.core import registrar
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("ExternalAPI")

DEFAULT_HITOKOTO_URL = "https://v1.hitokoto.cn"


class ExternalAPIPlugin(NcatBotPlugin):
    name = "external_api"
    version = "1.0.0"
    author = "NcatBot"
    description = "外部 API 集成演示（跨平台）"

    async def on_load(self):
        if not self.get_config("hitokoto_url"):
            self.set_config("hitokoto_url", DEFAULT_HITOKOTO_URL)
        self.data.setdefault("api_call_count", 0)
        LOG.info("ExternalAPI 已加载")

    @registrar.on_command("每日一言")
    async def on_hitokoto(self, event):
        """调用一言 API"""
        url = self.get_config("hitokoto_url", DEFAULT_HITOKOTO_URL)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params={"encode": "json"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status != 200:
                        await event.reply(f"⚠️ API 请求失败 (HTTP {resp.status})")
                        return
                    data = await resp.json()

            hitokoto = data.get("hitokoto", "获取失败")
            source = data.get("from", "未知")
            author = data.get("from_who", "")

            text = f"📜 {hitokoto}\n    —— {source}"
            if author:
                text += f" ({author})"

            self.data["api_call_count"] = self.data.get("api_call_count", 0) + 1
            await event.reply(text)

        except aiohttp.ClientError as e:
            LOG.error("一言 API 请求异常: %s", e)
            await event.reply("⚠️ 网络请求失败，请稍后重试")
        except Exception as e:
            LOG.error("一言 API 未知异常: %s", e)
            await event.reply("⚠️ 获取一言失败")

    @registrar.on_command("设置一言源")
    async def on_set_api(self, event, new_url: str):
        """修改一言 API 地址"""
        if not new_url.startswith("http"):
            await event.reply("⚠️ URL 必须以 http:// 或 https:// 开头")
            return
        self.set_config("hitokoto_url", new_url)
        await event.reply(f"一言 API 已更新为: {new_url}")

    @registrar.on_command("api状态")
    async def on_api_status(self, event):
        """查看 API 配置和状态"""
        url = self.get_config("hitokoto_url", DEFAULT_HITOKOTO_URL)
        count = self.data.get("api_call_count", 0)
        await event.reply(f"🔌 API 状态:\n  一言 API: {url}\n  累计调用: {count} 次")
