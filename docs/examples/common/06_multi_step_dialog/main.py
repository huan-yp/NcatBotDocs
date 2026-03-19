"""
common/06_multi_step_dialog — 多步对话（跨平台）

演示功能:
  - wait_event 连续多次使用实现多步交互
  - Predicate 语法糖（from_event 自动推导同 session 条件）
  - 超时自动取消
  - 中途输入 "取消" 退出对话
  - @registrar.on_command() 跨平台命令

本示例不依赖任何平台。
使用方式:
  发送 "注册" → 依次输入名字→年龄→确认 → 保存
  发送 "我的信息" → 查看已注册的信息
"""

import asyncio

from ncatbot.core import from_event, registrar
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("MultiStepDialog")

TIMEOUT = 30


class MultiStepDialogPlugin(NcatBotPlugin):
    name = "multi_step_dialog"
    version = "1.0.0"
    author = "NcatBot"
    description = "多步对话演示（跨平台）"

    async def on_load(self):
        self.data.setdefault("users", {})
        LOG.info("MultiStepDialog 插件已加载，已注册用户: %d", len(self.data["users"]))

    async def _wait_user_reply(self, event):
        """等待同 session 的下一条消息"""
        reply = await self.wait_event(
            predicate=from_event(event),
            timeout=TIMEOUT,
        )
        return reply.data.raw_message.strip()

    @registrar.on_command("注册")
    async def on_register(self, event):
        """多步注册流程"""
        uid = str(event.user_id)

        await event.reply(
            f"📝 开始注册！请输入你的名字（{TIMEOUT}秒内回复，输入「取消」退出）："
        )

        try:
            name = await self._wait_user_reply(event)
        except asyncio.TimeoutError:
            await event.reply("⏰ 注册超时，已取消")
            return

        if name == "取消":
            await event.reply("❌ 注册已取消")
            return

        await event.reply(f"好的，{name}！请输入你的年龄：")

        try:
            age_str = await self._wait_user_reply(event)
        except asyncio.TimeoutError:
            await event.reply("⏰ 注册超时，已取消")
            return

        if age_str == "取消":
            await event.reply("❌ 注册已取消")
            return

        if not age_str.isdigit():
            await event.reply("❌ 年龄必须是数字，注册已取消")
            return

        age = int(age_str)

        await event.reply(
            f"请确认你的信息:\n  名字: {name}\n  年龄: {age}\n回复「确认」完成注册："
        )

        try:
            confirm = await self._wait_user_reply(event)
        except asyncio.TimeoutError:
            await event.reply("⏰ 确认超时，已取消")
            return

        if confirm != "确认":
            await event.reply("❌ 注册已取消")
            return

        self.data.setdefault("users", {})[uid] = {
            "name": name,
            "age": age,
        }
        await event.reply(f"✅ 注册成功！欢迎你，{name}（{age}岁）")
        LOG.info("用户 %s 完成注册: %s, %d岁", uid, name, age)

    @registrar.on_command("我的信息")
    async def on_my_info(self, event):
        """查看已注册的信息"""
        uid = str(event.user_id)
        users = self.data.get("users", {})
        info = users.get(uid)

        if info:
            await event.reply(
                f"👤 你的注册信息:\n  名字: {info['name']}\n  年龄: {info['age']}"
            )
        else:
            await event.reply("你还没有注册，发送「注册」开始注册流程")
