# 07_dialog_and_menu

> 分类：qq

## 这个示例教什么

NcatBot 中如何用 `session_prompt` 和 `session_choose` 构建**多步对话**和**嵌套菜单**。这两个高级 API 在 `wait_session_reply` 基础上封装了"发问题 → 等回复 → 超时/取消/无效输入自动处理"的完整流程，让你用最少的代码实现复杂的交互体验。

## 你将学到

- `session_prompt` — 一站式：发问题 + 等回复 + 超时/取消自动回复
- `session_choose` — 选择题模式：有效选项匹配 + 无效重试
- `timeout_reply` — 超时自动回复文本
- `cancel_reply` — 取消自动回复文本
- `invalid_reply` — 无效输入提示文本
- `max_retries` — 最大重试次数（0 = 不重试）
- 多步流程 — 连续多个 `session_prompt` / `session_choose` 串联
- 嵌套菜单 — 一级选择触发二级子菜单

## 前置知识

- [06_session_basics](../06_session_basics/) — 会话等待与过滤基础（`wait_session_reply`、`SessionResult`）

## 目录结构

~~~text
07_dialog_and_menu/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
└── README.md
~~~

## 完整代码

~~~python
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
            invalid_reply="⚠️ 无效输入，请输入 1/2/3（还剩 {remaining} 次机会）",
            max_retries=2,
        )

        if not result.ok:
            await event.reply("❌ 多次输入无效，设置已取消")
            return

        labels = {"all": "每条消息都通知", "mention": "仅 @我 时通知", "off": "关闭通知"}
        await event.reply(f"✅ 通知频率已设置为：{labels[result.key]}")
~~~

## 关键代码讲解

### session_prompt vs session_choose 对比表

| | `session_prompt` | `session_choose` |
|---|---|---|
| 用途 | 开放式文本输入 | 固定选项选择 |
| 返回值 | `SessionResult`（`.text` 为用户回复） | `SessionResult`（`.key` 为匹配的选项值） |
| `timeout_reply` | ✅ 超时自动回复 | ✅ 超时自动回复 |
| `cancel_reply` | ✅ 取消自动回复 | ❌ 不支持（选择题无取消词） |
| `cancel_words` | ✅ 取消词列表 | ❌ 不支持 |
| `invalid_reply` | ❌ 不支持 | ✅ 无效输入提示 |
| `max_retries` | ❌ 不支持 | ✅ 最大重试次数 |
| 验证方式 | 需手动在代码中验证 | 通过 `choices` 字典自动匹配 |

### 多步流程控制模式

多步对话的核心模式：**每步检查 `result.ok`，不通过则 `return` 终止流程**。

~~~python
# 典型三步流程
step1 = await self.session_prompt("第一个问题", event, ...)
if not step1.ok:
    return  # 超时/取消，自动回复已发送

step2 = await self.session_prompt("第二个问题", event, ...)
if not step2.ok:
    return

step3 = await self.session_choose("确认？", event, choices={...}, ...)
if not step3.ok or step3.key != "confirm":
    return
~~~

**自定义验证**（如年龄必须是数字）需用 `while True` 循环包裹 `session_prompt`：

~~~python
while True:
    result = await self.session_prompt("请输入数字：", event, ...)
    if not result.ok:
        return
    if result.text.isdigit():
        break
    await event.reply("格式错误，请重试")
~~~

### 嵌套菜单模式

用 `session_choose` 串联多级菜单，每级根据 `result.key` 分发到下级：

~~~python
level1 = await self.session_choose("主菜单\n1. A\n2. B", event, choices={...})
if not level1.ok:
    return

if level1.key == "a":
    level2 = await self.session_choose("子菜单\n1. A1\n2. A2", event, choices={...})
    ...
elif level1.key == "b":
    ...
~~~

### choices 字典设计技巧

`choices` 的键是用户输入文本，值是程序内部使用的语义 key。支持多个键映射到同一个值：

~~~python
choices = {
    "1": "confirm",    # 数字输入
    "确认": "confirm",  # 中文输入
    "是": "confirm",    # 简短输入
    "2": "cancel",
    "取消": "cancel",
}
~~~

这样无论用户输入 `1`、`确认` 还是 `是`，都会得到 `result.key == "confirm"`。

## 运行方式

将 `07_dialog_and_menu/` 文件夹复制到 `plugins/` 目录，启动 Bot 后在群内发送：
- **注册** — 体验多步表单（名字 → 年龄 → 确认）
- **我的信息** — 查看已注册信息
- **菜单** — 体验嵌套菜单（主菜单 → 子菜单）
- **设置** — 体验 `max_retries` 重试机制

## 延伸阅读

- [06_session_basics](../06_session_basics/) — `wait_session_reply`、`SessionResult`、谓词过滤
- `ncatbot.plugin.mixin.event_mixin` — `session_prompt` / `session_choose` 源码实现
- `ncatbot.plugin.mixin.session_types` — `SessionResult` 数据类定义
