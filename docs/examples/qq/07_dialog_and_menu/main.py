"""
qq/07_dialog_and_menu — QQ 多步对话与菜单交互演示

演示功能:
  - session_prompt     一站式：发问题 + 等回复 + 超时/取消自动回复
  - session_choose     选择题模式：有效选项匹配 + 无效重试
  - timeout_reply      超时自动回复文本
  - cancel_reply       取消自动回复文本
  - invalid_reply      无效输入提示文本
  - max_retries        最大重试次数
  - 多步流程           连续多个 session_prompt / session_choose 组合
  - 嵌套菜单           选择触发下级选择

边界:
  本示例以高级会话交互为核心，不再回头讲 wait_event 原语。

前置知识: qq/06_session_basics
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("DialogAndMenu")

TIMEOUT = 30
CANCEL_WORDS = ["取消", "退出"]


class DialogAndMenuPlugin(NcatBotPlugin):
    name = "dialog_and_menu_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 多步对话与菜单交互演示"

    # ================================================================
    # 1. 注册 — 多步流程：session_prompt + session_choose 组合
    # ================================================================

    @registrar.qq.on_group_command("注册")
    async def on_register(self, event: GroupMessageEvent):
        """多步表单：收集名字 → 年龄 → 确认 → 保存"""

        # ---- 第 1 步：收集名字 ----
        name_result = await self.session_prompt(
            "📝 请输入你的名字：",
            event,
            timeout=TIMEOUT,
            cancel_words=CANCEL_WORDS,
            timeout_reply="⏰ 操作超时，注册已取消",
            cancel_reply="❌ 已取消注册",
        )
        if not name_result.ok:
            return

        user_name = name_result.text

        # ---- 第 2 步：收集年龄（需验证为数字） ----
        while True:
            age_result = await self.session_prompt(
                "📝 请输入你的年龄（纯数字）：",
                event,
                timeout=TIMEOUT,
                cancel_words=CANCEL_WORDS,
                timeout_reply="⏰ 操作超时，注册已取消",
                cancel_reply="❌ 已取消注册",
            )
            if not age_result.ok:
                return

            if age_result.text.isdigit() and 1 <= int(age_result.text) <= 150:
                user_age = int(age_result.text)
                break

            await event.reply("⚠️ 请输入有效的年龄数字（1~150），请重试：")

        # ---- 第 3 步：确认信息 ----
        confirm_result = await self.session_choose(
            f"请确认你的信息：\n"
            f"  姓名：{user_name}\n"
            f"  年龄：{user_age}\n\n"
            f"回复 1 或「确认」提交，2 或「取消」放弃",
            event,
            choices={
                "1": "confirm",
                "确认": "confirm",
                "2": "cancel",
                "取消": "cancel",
            },
            timeout=TIMEOUT,
            timeout_reply="⏰ 确认超时，注册已取消",
            invalid_reply="⚠️ 请输入 1/2 或 确认/取消",
            max_retries=3,
        )

        if not confirm_result.ok or confirm_result.key != "confirm":
            await event.reply("❌ 注册已取消")
            return

        # ---- 保存到 DataMixin ----
        uid = str(event.user_id)
        self.data[uid] = {"name": user_name, "age": user_age}
        await self.save_data()

        await event.reply(f"✅ 注册成功！\n姓名：{user_name}\n年龄：{user_age}")

    # ================================================================
    # 2. 我的信息 — 查询已保存的数据
    # ================================================================

    @registrar.qq.on_group_command("我的信息")
    async def on_my_info(self, event: GroupMessageEvent):
        """查询已注册的用户信息"""
        uid = str(event.user_id)
        info = self.data.get(uid)

        if not info:
            await event.reply("📭 你还没有注册，请发送「注册」开始")
            return

        await event.reply(
            f"📋 你的信息：\n姓名：{info['name']}\n年龄：{info['age']}"
        )

    # ================================================================
    # 3. 菜单 — 嵌套菜单：一级选择 → 二级选择 → 执行
    # ================================================================

    @registrar.qq.on_group_command("菜单")
    async def on_menu(self, event: GroupMessageEvent):
        """嵌套菜单演示：一级菜单 → 二级子菜单 → 动作"""

        # ---- 一级菜单 ----
        level1 = await self.session_choose(
            "📋 主菜单\n"
            "1. 🔍 查询服务\n"
            "2. ⚙️ 系统管理\n"
            "3. 📖 帮助说明",
            event,
            choices={
                "1": "query",
                "查询": "query",
                "查询服务": "query",
                "2": "admin",
                "管理": "admin",
                "系统管理": "admin",
                "3": "help",
                "帮助": "help",
                "帮助说明": "help",
            },
            timeout=TIMEOUT,
            timeout_reply="⏰ 菜单操作超时",
            invalid_reply="⚠️ 请输入 1/2/3 或对应功能名称",
            max_retries=3,
        )
        if not level1.ok:
            return

        # ---- 二级菜单：查询服务 ----
        if level1.key == "query":
            level2 = await self.session_choose(
                "🔍 查询服务\n"
                "1. 查天气\n"
                "2. 查汇率\n"
                "3. 返回上级",
                event,
                choices={
                    "1": "weather",
                    "查天气": "weather",
                    "2": "exchange",
                    "查汇率": "exchange",
                    "3": "back",
                    "返回": "back",
                    "返回上级": "back",
                },
                timeout=TIMEOUT,
                timeout_reply="⏰ 操作超时",
                invalid_reply="⚠️ 请输入 1/2/3",
                max_retries=3,
            )
            if not level2.ok or level2.key == "back":
                await event.reply("↩️ 已返回")
                return

            await event.reply(f"✅ 你选择了：{level2.text}（功能开发中…）")

        # ---- 二级菜单：系统管理 ----
        elif level1.key == "admin":
            level2 = await self.session_choose(
                "⚙️ 系统管理\n"
                "1. 查看状态\n"
                "2. 清除缓存\n"
                "3. 返回上级",
                event,
                choices={
                    "1": "status",
                    "查看状态": "status",
                    "2": "clear",
                    "清除缓存": "clear",
                    "3": "back",
                    "返回": "back",
                    "返回上级": "back",
                },
                timeout=TIMEOUT,
                timeout_reply="⏰ 操作超时",
                invalid_reply="⚠️ 请输入 1/2/3",
                max_retries=3,
            )
            if not level2.ok or level2.key == "back":
                await event.reply("↩️ 已返回")
                return

            await event.reply(f"✅ 你选择了：{level2.text}（功能开发中…）")

        # ---- 帮助说明 ----
        elif level1.key == "help":
            await event.reply(
                "📖 帮助说明\n\n"
                "可用命令：\n"
                "  注册 — 填写个人信息\n"
                "  我的信息 — 查看已注册信息\n"
                "  菜单 — 打开功能菜单\n"
                "  设置 — 体验选择重试机制"
            )

    # ================================================================
    # 4. 设置 — 演示 max_retries 和 invalid_reply
    # ================================================================

    @registrar.qq.on_group_command("设置")
    async def on_settings(self, event: GroupMessageEvent):
        """演示 max_retries 耗尽和 invalid_reply 提示"""

        result = await self.session_choose(
            "⚙️ 选择通知频率：\n"
            "1. 每条消息都通知\n"
            "2. 仅 @我 时通知\n"
            "3. 关闭通知",
            event,
            choices={
                "1": "all",
                "每条": "all",
                "2": "mention",
                "@我": "mention",
                "仅@我": "mention",
                "3": "off",
                "关闭": "off",
            },
            timeout=TIMEOUT,
            timeout_reply="⏰ 设置超时，保持原有配置",
            invalid_reply="⚠️ 无效输入，请输入 1/2/3",
            max_retries=2,
        )

        if not result.ok:
            await event.reply("❌ 多次输入无效，设置已取消")
            return

        labels = {"all": "每条消息都通知", "mention": "仅 @我 时通知", "off": "关闭通知"}
        await event.reply(f"✅ 通知频率已设置为：{labels[result.key]}")
