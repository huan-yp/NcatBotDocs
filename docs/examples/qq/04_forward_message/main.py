"""
qq/04_forward_message — QQ 合并转发消息演示

演示功能:
  - ForwardConstructor 基础用法    构造合并转发消息
  - set_author                    切换后续消息的作者
  - attach_text / attach_image    各类内容节点
  - attach_forward                嵌套转发
  - post_group_forward_msg        发送合并转发

只做提及:
  - 私聊版转发接口 (post_private_forward_msg)
  - get_forward_msg 查询已有转发消息

边界:
  只讲转发消息。普通富文本在 03_rich_message 中讲。

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from pathlib import Path

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import MessageArray
from ncatbot.types.qq import ForwardConstructor
from ncatbot.utils import get_log

LOG = get_log("ForwardMessage")

# 资源目录，用于存放示例图片、文件等
PLUGIN_DIR = Path(__file__).parent
RESOURCE_DIR = PLUGIN_DIR / "resources"


class ForwardMessagePlugin(NcatBotPlugin):
    name = "forward_message_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 合并转发消息演示"

    # ================================================================
    # 1. 基础合并转发 — ForwardConstructor + attach_text
    # ================================================================
    # ForwardConstructor 是构造合并转发消息的核心工具。
    # 通过 attach_text / attach_image 等方法添加节点，
    # 最终调用 build() 生成 Forward 对象，再通过 API 发送。

    @registrar.qq.on_group_command("转发")
    async def on_basic_forward(self, event: GroupMessageEvent):
        """基础合并转发 — 多条文本消息打包"""

        # 创建构造器，指定默认作者
        fc = ForwardConstructor(user_id=str(event.user_id), nickname="示例用户")

        # 逐条添加文本节点
        fc.attach_text("📬 这是合并转发的第一条消息")
        fc.attach_text("📬 这是第二条消息")
        fc.attach_text("📬 第三条，所有消息会被折叠为一个卡片")

        # build() 生成 Forward 对象
        forward = fc.build()

        # 通过 post_group_forward_msg 发送
        await self.api.qq.post_group_forward_msg(event.group_id, forward)

    # ================================================================
    # 2. 多作者转发 — set_author 切换发言人
    # ================================================================
    # set_author 会修改构造器的当前作者信息，
    # 后续通过 attach_* 添加的消息都会使用新作者。
    # 效果：展开后每条消息可以显示不同的头像和昵称。

    @registrar.qq.on_group_command("多作者转发")
    async def on_multi_author(self, event: GroupMessageEvent):
        """多作者转发 — set_author 切换消息发言人"""

        fc = ForwardConstructor(user_id="10001", nickname="小明")

        # 第一位作者：小明
        fc.attach_text("大家好，我是小明 👋")
        fc.attach_text("今天天气不错！")

        # 切换到第二位作者：小红
        fc.set_author("10002", "小红")
        fc.attach_text("小明你好！我是小红 😊")
        fc.attach_text("确实是个好天气~")

        # 切换到第三位作者：小刚
        fc.set_author("10003", "小刚")
        fc.attach_text("你们在聊什么？带我一个！")

        forward = fc.build()
        await self.api.qq.post_group_forward_msg(event.group_id, forward)

    # ================================================================
    # 3. 图文转发 — attach_image + attach_message
    # ================================================================
    # attach_image 添加单图节点，attach_message 添加 MessageArray 节点。
    # MessageArray 可以包含图文混排内容，适合更复杂的消息。

    @registrar.qq.on_group_command("图文转发")
    async def on_rich_forward(self, event: GroupMessageEvent):
        """图文转发 — 在转发消息中包含图片和图文混排"""

        fc = ForwardConstructor(user_id=str(event.user_id), nickname="图文作者")

        # 纯文本节点
        fc.attach_text("下面是一些图文内容 📸")

        # 纯图片节点
        fc.attach_image("https://via.placeholder.com/200x200.png?text=NcatBot")

        # 图文混排节点 — 通过 MessageArray 构造
        msg = MessageArray()
        msg.add_text("这是图文混排消息 🖼️\n")
        msg.add_image("https://via.placeholder.com/300x200.png?text=Hello")
        fc.attach_message(msg)

        forward = fc.build()
        await self.api.qq.post_group_forward_msg(event.group_id, forward)

    # ================================================================
    # 4. 嵌套转发 — attach_forward 多层嵌套
    # ================================================================
    # 合并转发可以嵌套：在外层转发中包含另一个合并转发。
    # 先用 ForwardConstructor 构建内层，build() 后
    # 通过外层的 attach_forward 嵌入。

    @registrar.qq.on_group_command("嵌套转发")
    async def on_nested_forward(self, event: GroupMessageEvent):
        """嵌套转发 — 转发消息中包含另一个合并转发"""

        # 构建内层转发
        inner_fc = ForwardConstructor(user_id="10001", nickname="内层用户A")
        inner_fc.attach_text("🔹 这是内层转发的第一条")
        inner_fc.set_author("10002", "内层用户B")
        inner_fc.attach_text("🔹 这是内层转发的第二条")
        inner_forward = inner_fc.build()

        # 构建外层转发，嵌入内层
        outer_fc = ForwardConstructor(user_id=str(event.user_id), nickname="外层用户")
        outer_fc.attach_text("📦 下面嵌套了一条合并转发：")
        outer_fc.attach_forward(inner_forward)
        outer_fc.attach_text("📦 以上是嵌套内容，外层还能继续添加")

        forward = outer_fc.build()
        await self.api.qq.post_group_forward_msg(event.group_id, forward)

    # ================================================================
    # 5. 按消息 ID 转发 — send_group_forward_msg_by_id
    # ================================================================
    # 如果不需要重新构造消息内容，可以直接通过历史消息 ID
    # 将已有消息打包转发。适用于"帮我把这几条消息转发到某群"的场景。

    @registrar.qq.on_group_command("ID转发", aliases=["id转发"])
    async def on_forward_by_id(self, event: GroupMessageEvent):
        """按消息 ID 转发 — 将历史消息直接打包转发"""

        # 教学说明：实际场景中 message_ids 可来自用户输入或历史记录查询
        # 这里用当前消息 ID 做演示
        message_ids = [event.message_id]

        await self.api.qq.send_group_forward_msg_by_id(
            event.group_id, message_ids
        )

    # ================================================================
    # 补充说明
    # ================================================================
    # 1. 私聊版：post_private_forward_msg 用法完全相同，只是目标改为 user_id
    # 2. 查询已有转发：self.api.qq.query.get_forward_msg(message_id)
    #    获取一条转发消息的展开内容
