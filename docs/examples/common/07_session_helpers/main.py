"""
common/07_session_helpers — Session 便利方法（跨平台）

演示功能:
  - session_prompt 一站式：发问题 + 等回复 + 超时/取消自动回复
  - session_choose 选择题模式：有效选项匹配 + 无效重试
  - wait_session_reply 手动控制返回值
  - SessionResult 统一判断 ok / cancelled / timed_out

本示例与 06_multi_step_dialog 功能等价，展示新 API 如何消除样板代码。
使用方式:
  发送 "注册" → 依次输入名字→年龄→确认 → 保存
  发送 "我的信息" → 查看已注册的信息
"""

from ncatbot.core import registrar
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("SessionHelpers")

TIMEOUT = 30
CANCEL_WORDS = ["取消", "退出"]


class SessionHelpersPlugin(NcatBotPlugin):
    name = "session_helpers"
    version = "1.0.0"
    author = "NcatBot"
    description = "Session 便利方法演示（跨平台）"

    async def on_load(self):
        self.data.setdefault("users", {})
        LOG.info("SessionHelpers 插件已加载，已注册用户: %d", len(self.data["users"]))

    @registrar.on_command("注册")
    async def on_register(self, event):
        """多步注册流程（使用 session 便利方法）"""
        uid = str(event.user_id)

        # 第 1 步：名字
        result = await self.session_prompt(
            f"📝 开始注册！请输入你的名字（{TIMEOUT}秒内回复，输入「取消」退出）：",
            event,
            timeout=TIMEOUT,
            cancel_words=CANCEL_WORDS,
            timeout_reply="⏰ 注册超时，已取消",
            cancel_reply="❌ 注册已取消",
        )
        if not result.ok:
            return
        name = result.text

        # 第 2 步：年龄
        result = await self.session_prompt(
            f"好的，{name}！请输入你的年龄：",
            event,
            timeout=TIMEOUT,
            cancel_words=CANCEL_WORDS,
            timeout_reply="⏰ 注册超时，已取消",
            cancel_reply="❌ 注册已取消",
        )
        if not result.ok:
            return

        if not result.text.isdigit():
            await event.reply("❌ 年龄必须是数字，注册已取消")
            return

        age = int(result.text)

        # 第 3 步：确认（选择题）
        result = await self.session_choose(
            f"请确认你的信息:\n  名字: {name}\n  年龄: {age}\n回复「确认」完成注册，「取消」退出：",
            event,
            choices={"确认": "confirm", "取消": "cancel"},
            timeout=TIMEOUT,
            timeout_reply="⏰ 确认超时，已取消",
            invalid_reply="请回复「确认」或「取消」",
            max_retries=2,
        )

        if not result.ok or result.key != "confirm":
            if not result.timed_out:
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
