# 10_info_query

> 分类：qq

## 这个示例教什么

NcatBot 中如何使用 QQ 查询 API 构建一个**信息查询助手**。覆盖最常用的查询接口：Bot 自身信息、好友/群列表、群成员信息、消息历史、群公告、精华消息等。

## 你将学到

- `get_login_info` — 获取 Bot 登录信息
- `get_friend_list` — 获取好友列表
- `get_group_list` — 获取群列表
- `get_group_info` — 获取群信息
- `get_group_member_info` — 获取群成员信息（昵称 / 名片 / 角色 / 入群时间）
- `get_group_member_list` — 获取群成员列表
- `get_group_msg_history` — 获取群消息历史（可指定条数）
- `get_msg` — 通过消息 ID 获取单条消息（Reply 绑定）
- `get_forward_msg` — 获取合并转发内容（Reply 绑定）
- `get_group_notice` — 获取群公告
- `get_essence_msg_list` — 获取精华消息列表
- Query API 的两个命名空间：`self.api.qq.query` 与 `self.api.qq.messaging`

## 前置知识

- [01_event_registration](../01_event_registration/) — 事件注册基础
- [02_command_binding](../02_command_binding/) — 命令参数绑定（At / Reply / Optional）

## 目录结构

~~~text
10_info_query/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
└── README.md
~~~

## 完整代码

~~~python
"""
qq/10_info_query — QQ 信息查询助手

演示功能:
  - get_login_info           获取 Bot 登录信息
  - get_friend_list          获取好友列表
  - get_group_list           获取群列表
  - get_group_info           获取群信息
  - get_group_member_info    获取群成员信息
  - get_group_member_list    获取群成员列表
  - get_group_msg_history    获取群消息历史
  - get_msg                  通过消息 ID 获取单条消息
  - get_forward_msg          获取合并转发内容
  - get_group_notice         获取群公告
  - get_essence_msg_list     获取精华消息列表

提及但不展开:
  - get_friend_msg_history   好友消息历史（需私聊场景）
  - get_stranger_info        获取陌生人信息
  - get_group_honor_info     获取群荣誉信息
  - get_group_at_all_remain  获取 @全体成员 剩余次数
  - get_group_shut_list      获取群禁言列表
  - get_emoji_likes          获取表情回应列表

边界:
  本示例聚焦查询类 API 的实际使用，不涉及管理操作。
  管理类 API 详见 qq/09_group_admin。

前置知识: qq/01_event_registration, qq/02_command_binding
使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import At, Reply
from ncatbot.utils import get_log

LOG = get_log("InfoQuery")


class InfoQueryPlugin(NcatBotPlugin):
    name = "info_query_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 信息查询助手"

    # ================================================================
    # 1. 查登录 — get_login_info
    # ================================================================
    # 获取当前 Bot 的登录信息（昵称、QQ 号）。

    @registrar.qq.on_group_command("查登录")
    async def on_login_info(self, event: GroupMessageEvent):
        """查询 Bot 登录信息 — '查登录'"""
        try:
            result = await self.api.qq.query.get_login_info()
            await event.reply(
                f"🤖 Bot 登录信息\n"
                f"  昵称: {result.get('nickname', '未知')}\n"
                f"  QQ: {result.get('user_id', '未知')}"
            )
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 2. 查好友 — get_friend_list
    # ================================================================
    # 获取好友列表，展示总数和前 5 个好友。

    @registrar.qq.on_group_command("查好友")
    async def on_friend_list(self, event: GroupMessageEvent):
        """查询好友列表 — '查好友'"""
        try:
            result = await self.api.qq.query.get_friend_list()
            total = len(result)
            lines = [f"👥 好友列表（共 {total} 人）"]
            for friend in result[:5]:
                nick = friend.get("nickname", "未知")
                uid = friend.get("user_id", "?")
                remark = friend.get("remark", "")
                display = f"{nick}({uid})"
                if remark:
                    display += f" 备注: {remark}"
                lines.append(f"  · {display}")
            if total > 5:
                lines.append(f"  ... 还有 {total - 5} 人")
            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 3. 查群列表 — get_group_list
    # ================================================================
    # 获取 Bot 加入的群列表，展示总数和前 5 个群。

    @registrar.qq.on_group_command("查群列表")
    async def on_group_list(self, event: GroupMessageEvent):
        """查询群列表 — '查群列表'"""
        try:
            result = await self.api.qq.query.get_group_list()
            total = len(result)
            lines = [f"📋 群列表（共 {total} 个群）"]
            for group in result[:5]:
                name = group.get("group_name", "未知")
                gid = group.get("group_id", "?")
                count = group.get("member_count", "?")
                lines.append(f"  · {name}({gid}) 成员: {count}")
            if total > 5:
                lines.append(f"  ... 还有 {total - 5} 个群")
            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 4. 查群信息 — get_group_info
    # ================================================================
    # 查询当前群的详细信息（群名、成员数、最大成员数等）。

    @registrar.qq.on_group_command("查群信息")
    async def on_group_info(self, event: GroupMessageEvent):
        """查询当前群信息 — '查群信息'"""
        try:
            result = await self.api.qq.query.get_group_info(event.group_id)
            await event.reply(
                f"ℹ️ 群信息\n"
                f"  群名: {result.get('group_name', '未知')}\n"
                f"  群号: {result.get('group_id', '?')}\n"
                f"  成员数: {result.get('member_count', '?')}\n"
                f"  最大成员数: {result.get('max_member_count', '?')}"
            )
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 5. 查成员 — get_group_member_info
    # ================================================================
    # 用户发送: 查成员 @某人
    # At 参数绑定自动提取被 @ 用户，查询其群成员信息。

    @registrar.qq.on_group_command("查成员")
    async def on_member_info(self, event: GroupMessageEvent, target: At):
        """查询群成员信息 — '查成员 @某人'"""
        try:
            result = await self.api.qq.query.get_group_member_info(
                event.group_id, target.user_id
            )
            role_map = {"owner": "群主", "admin": "管理员", "member": "成员"}
            role = role_map.get(result.get("role", ""), result.get("role", "未知"))
            join_time = result.get("join_time", "未知")
            await event.reply(
                f"👤 成员信息\n"
                f"  昵称: {result.get('nickname', '未知')}\n"
                f"  名片: {result.get('card', '无')}\n"
                f"  角色: {role}\n"
                f"  入群时间: {join_time}"
            )
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 6. 查成员列表 — get_group_member_list
    # ================================================================
    # 获取当前群的成员列表，展示总数。

    @registrar.qq.on_group_command("查成员列表")
    async def on_member_list(self, event: GroupMessageEvent):
        """查询群成员列表 — '查成员列表'"""
        try:
            result = await self.api.qq.query.get_group_member_list(event.group_id)
            total = len(result)
            lines = [f"📊 群成员列表（共 {total} 人）"]
            for member in result[:5]:
                nick = member.get("nickname", "未知")
                card = member.get("card", "")
                uid = member.get("user_id", "?")
                display = card if card else nick
                lines.append(f"  · {display}({uid})")
            if total > 5:
                lines.append(f"  ... 还有 {total - 5} 人")
            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 7. 查历史 — get_group_msg_history
    # ================================================================
    # 用户发送: 查历史 5    → 获取最近 5 条消息
    # 用户发送: 查历史       → 默认获取最近 5 条
    # 通过 self.api.qq.messaging 而非 self.api.qq.query 调用。

    @registrar.qq.on_group_command("查历史")
    async def on_msg_history(self, event: GroupMessageEvent, count: int = 5):
        """查询群消息历史 — '查历史 [条数]'"""
        try:
            result = await self.api.qq.messaging.get_group_msg_history(
                event.group_id, count=count
            )
            messages = result.get("messages", [])
            if not messages:
                await event.reply("📭 没有查到历史消息")
                return

            lines = [f"📜 最近 {len(messages)} 条消息"]
            for msg in messages[:count]:
                sender = msg.get("sender", {}).get("nickname", "未知")
                content = str(msg.get("message", ""))[:50]
                lines.append(f"  [{sender}] {content}")
            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 8. 查消息 — get_msg（通过消息 ID 获取单条消息）
    # ================================================================
    # 引用一条消息后发送「查消息」，通过 Reply 绑定获取 message_id。

    @registrar.qq.on_group_command("查消息")
    async def on_get_msg(self, event: GroupMessageEvent, ref: Reply):
        """查询单条消息详情 — 引用消息后发送 '查消息'"""
        try:
            result = await self.api.qq.query.get_msg(ref.id)
            sender = result.get("sender", {}).get("nickname", "未知")
            content = str(result.get("message", ""))[:100]
            msg_time = result.get("time", "未知")
            await event.reply(
                f"📩 消息详情\n"
                f"  消息 ID: {ref.id}\n"
                f"  发送者: {sender}\n"
                f"  时间: {msg_time}\n"
                f"  内容: {content}"
            )
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 9. 查转发 — get_forward_msg（获取合并转发内容）
    # ================================================================
    # 引用一条合并转发消息后发送「查转发」。

    @registrar.qq.on_group_command("查转发")
    async def on_get_forward(self, event: GroupMessageEvent, ref: Reply):
        """查询合并转发内容 — 引用转发消息后发送 '查转发'"""
        try:
            result = await self.api.qq.query.get_forward_msg(ref.id)
            messages = result.get("messages", [])
            if not messages:
                await event.reply("📭 转发消息为空或格式不匹配")
                return

            lines = [f"📦 合并转发内容（共 {len(messages)} 条）"]
            for msg in messages[:10]:
                sender = msg.get("sender", {}).get("nickname", "未知")
                content = str(msg.get("content", ""))[:40]
                lines.append(f"  [{sender}] {content}")
            if len(messages) > 10:
                lines.append(f"  ... 还有 {len(messages) - 10} 条")
            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 10. 查公告 — get_group_notice
    # ================================================================

    @registrar.qq.on_group_command("查公告")
    async def on_group_notice(self, event: GroupMessageEvent):
        """查询群公告 — '查公告'"""
        try:
            result = await self.api.qq.query.get_group_notice(event.group_id)
            if not result:
                await event.reply("📭 当前群没有公告")
                return

            lines = ["📢 群公告"]
            notices = result if isinstance(result, list) else [result]
            for notice in notices[:5]:
                content = notice.get("message", {}).get("text", "无内容")
                sender = notice.get("sender_id", "未知")
                lines.append(f"  · [{sender}] {content[:60]}")
            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 11. 查精华 — get_essence_msg_list
    # ================================================================

    @registrar.qq.on_group_command("查精华")
    async def on_essence_list(self, event: GroupMessageEvent):
        """查询精华消息列表 — '查精华'"""
        try:
            result = await self.api.qq.query.get_essence_msg_list(event.group_id)
            if not result:
                await event.reply("📭 当前群没有精华消息")
                return

            lines = [f"⭐ 精华消息（共 {len(result)} 条）"]
            for msg in result[:5]:
                sender = msg.get("sender_nick", "未知")
                content = str(msg.get("content", ""))[:40]
                lines.append(f"  · [{sender}] {content}")
            if len(result) > 5:
                lines.append(f"  ... 还有 {len(result) - 5} 条")
            await event.reply("\n".join(lines))
        except Exception as e:
            await event.reply(f"❌ 查询失败: {e}")

    # ================================================================
    # 提及但不展开的 API
    # ================================================================
    # - get_friend_msg_history(user_id, message_seq, count)
    #   好友消息历史，与 get_group_msg_history 用法相同，
    #   但需在私聊场景触发（PrivateMessageEvent），此处仅做提及。
    #   调用: await self.api.qq.messaging.get_friend_msg_history(user_id, count=20)
    #
    # - get_stranger_info(user_id)          — 获取陌生人信息
    # - get_group_honor_info(group_id, type) — 获取群荣誉（龙王、群聊之火等）
    # - get_group_at_all_remain(group_id)   — 获取 @全体成员 剩余次数
    # - get_group_shut_list(group_id)       — 获取群禁言列表
    # - get_emoji_likes(message_id)         — 获取消息的表情回应列表
~~~

## 关键代码讲解

### Query API 分类速查

查询 API 分布在两个命名空间中：

| 命名空间 | API | 说明 |
|---|---|---|
| `self.api.qq.query` | `get_login_info()` | Bot 登录信息 |
| `self.api.qq.query` | `get_friend_list()` | 好友列表 |
| `self.api.qq.query` | `get_group_list()` | 群列表 |
| `self.api.qq.query` | `get_group_info(group_id)` | 群信息 |
| `self.api.qq.query` | `get_group_member_info(group_id, user_id)` | 群成员信息 |
| `self.api.qq.query` | `get_group_member_list(group_id)` | 群成员列表 |
| `self.api.qq.query` | `get_msg(message_id)` | 单条消息 |
| `self.api.qq.query` | `get_forward_msg(message_id)` | 合并转发内容 |
| `self.api.qq.query` | `get_group_notice(group_id)` | 群公告 |
| `self.api.qq.query` | `get_essence_msg_list(group_id)` | 精华消息列表 |
| `self.api.qq.messaging` | `get_group_msg_history(group_id, message_seq, count)` | 群消息历史 |
| `self.api.qq.messaging` | `get_friend_msg_history(user_id, message_seq, count)` | 好友消息历史 |

> **注意**：消息历史类 API 在 `self.api.qq.messaging` 下，而非 `self.api.qq.query`。

### 返回值处理模式

查询 API 的返回值通常是 dict 或 list，使用 `.get()` 安全取值：

~~~python
# 单对象查询 — 返回 dict
result = await self.api.qq.query.get_group_info(event.group_id)
name = result.get("group_name", "未知")

# 列表查询 — 返回 list
result = await self.api.qq.query.get_friend_list()
total = len(result)
for friend in result[:5]:  # 截取前 5 条展示
    nick = friend.get("nickname", "未知")
~~~

### 参数绑定技巧回顾

本示例复用了 [02_command_binding](../02_command_binding/) 中的绑定方式：

~~~python
# At 绑定 — 从消息中提取 @某人
async def on_member_info(self, event, target: At):
    target.user_id  # 被 @ 用户的 ID

# Reply 绑定 — 从引用消息中提取消息 ID
async def on_get_msg(self, event, ref: Reply):
    ref.id  # 被引用消息的 ID

# 默认值参数 — 可选数字
async def on_msg_history(self, event, count: int = 5):
    # count 可省略，默认 5
~~~

## 运行方式

1. 将 `10_info_query/` 文件夹复制到 `plugins/` 目录
2. 启动 Bot
3. 在群聊中发送以下命令测试：
   - **查登录** — 查看 Bot 信息
   - **查好友** — 好友列表
   - **查群列表** — Bot 加入的群
   - **查群信息** — 当前群详情
   - **查成员 @某人** — 群成员详情
   - **查成员列表** — 群成员列表
   - **查历史 10** — 最近 10 条消息
   - **查消息**（引用消息）— 消息详情
   - **查转发**（引用转发消息）— 合并转发内容
   - **查公告** — 群公告
   - **查精华** — 精华消息

## 延伸阅读

- [02_command_binding](../02_command_binding/) — 命令参数绑定详解（At / Reply / Optional）
- [09_group_admin](../09_group_admin/) — 群管理 API（写操作）
- 更多查询 API（陌生人信息、群荣誉、@全体剩余次数、禁言列表、表情回应等）详见 API Reference
