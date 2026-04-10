"""
qq/14_full_featured_bot — QQ 多功能 Bot 示例

演示功能:
  - 签到与积分系统
  - Config 双层配置
  - Data 持久化
  - 关键词管理
  - 帮助命令
  - 排行榜
"""

import time

from ncatbot.core import registrar
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("FullFeaturedBot")


class FullFeaturedPlugin(NcatBotPlugin):
    name = "full_featured_bot_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 多功能 Bot 示例"

    async def on_load(self):
        self.init_defaults({"welcome_msg": "欢迎！", "daily_score": 10})
        if "scores" not in self.data:
            self.data["scores"] = {}
        if "keywords" not in self.data:
            self.data["keywords"] = {}
        if "sign_dates" not in self.data:
            self.data["sign_dates"] = {}
        LOG.info("FullFeaturedBot 插件已加载")

    @registrar.on_command("签到")
    async def on_sign_in(self, event):
        """每日签到获取积分"""
        uid = str(event.user_id)
        today = time.strftime("%Y-%m-%d")

        if self.data["sign_dates"].get(uid) == today:
            await event.reply(text="📝 你今天已经签到过了！")
            return

        score = self.get_config("daily_score") or 10
        self.data["scores"][uid] = self.data["scores"].get(uid, 0) + score
        self.data["sign_dates"][uid] = today
        total = self.data["scores"][uid]
        await event.reply(text=f"✅ 签到成功！获得 {score} 积分，总计 {total} 积分")

    @registrar.on_command("积分")
    async def on_score(self, event):
        """查看积分"""
        uid = str(event.user_id)
        score = self.data["scores"].get(uid, 0)
        await event.reply(text=f"💰 你的积分: {score}")

    @registrar.on_command("帮助")
    async def on_help(self, event):
        """帮助命令"""
        await event.reply(
            text=(
                "📖 可用命令:\n"
                "  签到 — 每日签到获取积分\n"
                "  积分 — 查看积分余额\n"
                "  排行榜 — 查看积分排行\n"
                "  添加关键词 X=Y — 添加关键词回复\n"
                "  关键词列表 — 查看所有关键词\n"
                "  查看配置 — 查看当前配置"
            )
        )

    @registrar.on_command("添加关键词")
    async def on_add_keyword(self, event, content: str):
        """添加关键词: 添加关键词 触发词=回复"""
        if "=" not in content:
            await event.reply(text="❌ 格式错误，请使用: 添加关键词 触发词=回复")
            return
        key, value = content.split("=", 1)
        self.data["keywords"][key.strip()] = value.strip()
        await event.reply(text=f"✅ 已添加关键词: {key.strip()} → {value.strip()}")

    @registrar.on_command("关键词列表")
    async def on_keyword_list(self, event):
        """查看关键词列表"""
        kw = self.data.get("keywords", {})
        if not kw:
            await event.reply(text="📋 暂无关键词")
            return
        lines = ["📋 关键词列表:"]
        for k, v in kw.items():
            lines.append(f"  {k} → {v}")
        await event.reply(text="\n".join(lines))

    @registrar.on_command("查看配置")
    async def on_view_config(self, event):
        """查看当前配置"""
        lines = ["⚙️ 当前配置:"]
        for k, v in self.config.items():
            lines.append(f"  {k}: {v}")
        await event.reply(text="\n".join(lines))

    @registrar.on_command("排行榜")
    async def on_ranking(self, event):
        """积分排行榜"""
        scores = self.data.get("scores", {})
        if not scores:
            await event.reply(text="🏆 暂无排行数据")
            return
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        lines = ["🏆 积分排行榜:"]
        for i, (uid, score) in enumerate(sorted_scores, 1):
            lines.append(f"  {i}. 用户 {uid}: {score} 积分")
        await event.reply(text="\n".join(lines))
