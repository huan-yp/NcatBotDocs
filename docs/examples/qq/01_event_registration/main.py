"""
qq/01_event_registration — QQ 事件注册方式演示

演示功能:
  - @registrar.qq.on_command()          群聊+私聊通用命令
  - @registrar.qq.on_group_command()    群聊专属命令
  - @registrar.qq.on_private_command()  私聊专属命令
  - @registrar.qq.on_message()          所有消息监听
  - @registrar.qq.on_group_message()    群聊消息监听
  - @registrar.qq.on_private_message()  私聊消息监听
  - @registrar.qq.on_notice()           通知事件监听
  - @registrar.qq.on_request()          请求事件监听
  - priority 参数                       优先级控制
  - ignore_case 参数                    大小写不敏感

本示例只回答"怎么注册事件处理器"，不涉及参数绑定、消息构造、
Notice/Request 细分处理等内容。

提及但不展开:
  - on_meta / on_message_sent
  - registrar.qq 下的细粒度快捷装饰器（如 on_group_increase）
  - platform 参数

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from ncatbot.core import registrar
from ncatbot.event.qq import (
    GroupMessageEvent,
    NoticeEvent,
    PrivateMessageEvent,
    RequestEvent,
)
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_log

LOG = get_log("EventRegistration")


class EventRegistrationPlugin(NcatBotPlugin):
    name = "event_registration_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 事件注册方式演示"

    # ================================================================
    # 1. on_command — 群聊 + 私聊通用命令
    # ================================================================
    # ignore_case=True 让 "Ping"、"PING"、"ping" 都能触发。

    @registrar.qq.on_command("ping", ignore_case=True)
    async def on_ping(self, event):
        """群聊和私聊都能触发的通用命令"""
        await event.reply(text="pong!")

    # ================================================================
    # 2. on_group_command / on_private_command — 平台专属命令
    # ================================================================

    @registrar.qq.on_group_command("group-only")
    async def on_group_only(self, event: GroupMessageEvent):
        """仅群聊可触发的命令"""
        await event.reply(text="这条命令只在群聊中生效 📢")

    @registrar.qq.on_private_command("private-only")
    async def on_private_only(self, event: PrivateMessageEvent):
        """仅私聊可触发的命令"""
        await event.reply(text="这条命令只在私聊中生效 🔒")

    # ================================================================
    # 3. on_message / on_group_message / on_private_message — 消息监听
    # ================================================================
    # 消息监听器会收到所有消息（不限于命令），适合做日志、统计等。

    @registrar.qq.on_message()
    async def on_any_message(self, event):
        """监听所有 QQ 消息（群聊 + 私聊）"""
        LOG.debug("收到消息: %s", event.data.raw_message)

    @registrar.qq.on_group_message()
    async def on_group_msg(self, event: GroupMessageEvent):
        """仅监听群聊消息"""
        LOG.debug("群 %s 消息: %s", event.data.group_id, event.data.raw_message)

    @registrar.qq.on_private_message()
    async def on_private_msg(self, event: PrivateMessageEvent):
        """仅监听私聊消息"""
        LOG.debug("私聊消息: %s", event.data.raw_message)

    # ================================================================
    # 4. on_notice / on_request — 通知与请求事件
    # ================================================================

    @registrar.qq.on_notice()
    async def on_notice(self, event: NoticeEvent):
        """监听所有通知事件（群成员变动、撤回、戳一戳等）"""
        LOG.info("收到通知事件: %s", event.data.notice_type)

    @registrar.qq.on_request()
    async def on_request(self, event: RequestEvent):
        """监听所有请求事件（加群申请、好友请求等）"""
        LOG.info("收到请求事件: %s", event.data.request_type)

    # ================================================================
    # 5. priority — 优先级控制
    # ================================================================
    # priority 值越小优先级越高（默认为 0）。
    # 下面两个处理器监听同一事件（群聊命令 "priority-demo"），
    # high_priority_handler 会先于 low_priority_handler 执行。

    @registrar.qq.on_group_command("priority-demo", priority=0)
    async def high_priority_handler(self, event: GroupMessageEvent):
        """高优先级处理器（priority=0，先执行）"""
        LOG.info("⚡ 高优先级处理器执行")
        await event.reply(text="高优先级处理器先响应 ⚡")

    @registrar.qq.on_group_command("priority-demo", priority=10)
    async def low_priority_handler(self, event: GroupMessageEvent):
        """低优先级处理器（priority=10，后执行）"""
        LOG.info("🐢 低优先级处理器执行")

    # ================================================================
    # 6. ignore_case — 大小写不敏感
    # ================================================================
    # 默认情况下命令匹配区分大小写。
    # 设置 ignore_case=True 后，"Help"、"HELP"、"help" 都能匹配。

    @registrar.qq.on_command("Help", ignore_case=True)
    async def on_help_ignore_case(self, event):
        """大小写不敏感：Help / HELP / help 都能触发"""
        await event.reply(text="输入 ping / group-only / private-only / priority-demo 试试")

    # ================================================================
    # 提及但不展开的注册方式
    # ================================================================
    # - @registrar.qq.on_meta()          元事件（心跳等）
    # - @registrar.qq.on_message_sent()  Bot 自身发送的消息
    # - registrar.qq 下还有更多细粒度快捷装饰器，例如：
    #     @registrar.qq.on_group_increase()  群成员增加
    #     @registrar.qq.on_group_decrease()  群成员减少
    #     @registrar.qq.on_friend_add()      好友添加
    #   这些装饰器是 on_notice() 的细分版本，详见 reference 文档。
    # - 跨平台注册可使用 @registrar.on_command() 或 platform 参数，
    #   详见 common/01_hello_world 示例。
