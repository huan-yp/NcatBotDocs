"""
common/10_multi_step_dialog — 多步对话注册流程（跨平台）

演示功能:
  - session_prompt: 发送提示并等待回复
  - wait_session_reply: 等待同 session 回复
  - SessionCancelled: 用户取消
  - Data 持久化用户信息
"""

import asyncio

from ncatbot.core import registrar
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("MultiStepDialog")


class MultiStepDialogPlugin(NcatBotPlugin):
    name = "multi_step_dialog"
    version = "1.0.0"
    author = "NcatBot"
    description = "多步对话注册流程示例"

    async def on_load(self):
        if "users" not in self.data:
            self.data["users"] = {}
        LOG.info("MultiStepDialog 插件已加载")

    @registrar.on_command("注册")
    async def on_register(self, event):
        """注册流程: 名字 → 年龄 → 确认 → 保存"""
        cancel_words = ["取消"]

        # 第一步: 输入名字
        name_result = await self.session_prompt(
            "📝 请输入你的名字:",
            event,
            timeout=30.0,
            cancel_words=cancel_words,
            cancel_reply="❌ 注册已取消",
        )
        if not name_result.ok:
            return
        name = name_result.text

        # 第二步: 输入年龄
        age_result = await self.session_prompt(
            f"👋 {name}，请输入你的年龄:",
            event,
            timeout=30.0,
            cancel_words=cancel_words,
            cancel_reply="❌ 注册已取消",
        )
        if not age_result.ok:
            return

        try:
            age = int(age_result.text)
        except ValueError:
            await event.reply(text="❌ 年龄必须是数字，注册已取消")
            return

        # 第三步: 确认
        confirm_result = await self.session_prompt(
            f"请确认信息:\n  名字: {name}\n  年龄: {age}\n回复「确认」完成注册:",
            event,
            timeout=30.0,
            cancel_words=cancel_words,
            cancel_reply="❌ 注册已取消",
        )
        if not confirm_result.ok:
            return

        if confirm_result.text != "确认":
            await event.reply(text="❌ 未确认，注册已取消")
            return

        # 保存
        uid = str(event.user_id)
        self.data["users"][uid] = {"name": name, "age": age}
        await event.reply(text=f"✅ 注册成功！欢迎 {name}（{age}岁）")

    @registrar.on_command("我的信息")
    async def on_my_info(self, event):
        """查看注册信息"""
        uid = str(event.user_id)
        user = self.data.get("users", {}).get(uid)
        if user is None:
            await event.reply(text="❌ 你还没有注册，请发送「注册」开始")
            return
        await event.reply(
            text=f"👤 你的信息:\n  名字: {user['name']}\n  年龄: {user['age']}"
        )
