# 04_forward_message

> 分类：qq

## 这个示例教什么

NcatBot 中**如何构造和发送合并转发消息**。QQ 的合并转发可以把多条消息打包成一个卡片，点击展开查看——群聊天记录、多人对话汇总、图文内容整理都离不开它。本示例从最基础的文本转发到多作者、图文混排、嵌套转发，一步步覆盖 `ForwardConstructor` 的全部核心用法。

## 你将学到

- `ForwardConstructor` 基础用法 — 创建构造器、添加文本节点、`build()` 生成转发对象
- `set_author()` — 切换后续消息的作者（头像 + 昵称）
- `attach_text()` / `attach_image()` — 添加文本和图片节点
- `attach_message()` — 添加 `MessageArray` 图文混排节点
- `attach_forward()` — 嵌套转发（转发中包含转发）
- `post_group_forward_msg()` — 发送合并转发消息

## 前置知识

- 了解 NcatBot 的事件注册方式（`@registrar.qq.on_group_command`）
- 了解 `MessageArray` 的基本构造方法
- 建议先完成 [qq/03_rich_message](../03_rich_message/)

## 目录结构

~~~text
04_forward_message/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
├── README.md
└── resources/       # 存放示例资源（图片、文件等）
    └── .gitkeep
~~~

## 完整代码

~~~python
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

    @registrar.qq.on_group_command("转发")
    async def on_basic_forward(self, event: GroupMessageEvent):
        """基础合并转发 — 多条文本消息打包"""

        fc = ForwardConstructor(user_id=str(event.user_id), nickname="示例用户")
        fc.attach_text("📬 这是合并转发的第一条消息")
        fc.attach_text("📬 这是第二条消息")
        fc.attach_text("📬 第三条，所有消息会被折叠为一个卡片")

        forward = fc.build()
        await self.api.qq.post_group_forward_msg(event.group_id, forward)

    # ================================================================
    # 2. 多作者转发 — set_author 切换发言人
    # ================================================================

    @registrar.qq.on_group_command("多作者转发")
    async def on_multi_author(self, event: GroupMessageEvent):
        """多作者转发 — set_author 切换消息发言人"""

        fc = ForwardConstructor(user_id="10001", nickname="小明")

        fc.attach_text("大家好，我是小明 👋")
        fc.attach_text("今天天气不错！")

        fc.set_author("10002", "小红")
        fc.attach_text("小明你好！我是小红 😊")
        fc.attach_text("确实是个好天气~")

        fc.set_author("10003", "小刚")
        fc.attach_text("你们在聊什么？带我一个！")

        forward = fc.build()
        await self.api.qq.post_group_forward_msg(event.group_id, forward)

    # ================================================================
    # 3. 图文转发 — attach_image + attach_message
    # ================================================================

    @registrar.qq.on_group_command("图文转发")
    async def on_rich_forward(self, event: GroupMessageEvent):
        """图文转发 — 在转发消息中包含图片和图文混排"""

        fc = ForwardConstructor(user_id=str(event.user_id), nickname="图文作者")

        fc.attach_text("下面是一些图文内容 📸")
        fc.attach_image("https://via.placeholder.com/200x200.png?text=NcatBot")

        msg = MessageArray()
        msg.add_text("这是图文混排消息 🖼️\n")
        msg.add_image("https://via.placeholder.com/300x200.png?text=Hello")
        fc.attach_message(msg)

        forward = fc.build()
        await self.api.qq.post_group_forward_msg(event.group_id, forward)

    # ================================================================
    # 4. 嵌套转发 — attach_forward 多层嵌套
    # ================================================================

    @registrar.qq.on_group_command("嵌套转发")
    async def on_nested_forward(self, event: GroupMessageEvent):
        """嵌套转发 — 转发消息中包含另一个合并转发"""

        inner_fc = ForwardConstructor(user_id="10001", nickname="内层用户A")
        inner_fc.attach_text("🔹 这是内层转发的第一条")
        inner_fc.set_author("10002", "内层用户B")
        inner_fc.attach_text("🔹 这是内层转发的第二条")
        inner_forward = inner_fc.build()

        outer_fc = ForwardConstructor(user_id=str(event.user_id), nickname="外层用户")
        outer_fc.attach_text("📦 下面嵌套了一条合并转发：")
        outer_fc.attach_forward(inner_forward)
        outer_fc.attach_text("📦 以上是嵌套内容，外层还能继续添加")

        forward = outer_fc.build()
        await self.api.qq.post_group_forward_msg(event.group_id, forward)
~~~

## 关键代码讲解

### ForwardConstructor 基础流程

~~~python
# 1. 创建构造器，指定默认作者（QQ号 + 昵称）
fc = ForwardConstructor(user_id="123456", nickname="Bot")

# 2. 逐条添加消息节点
fc.attach_text("第一条消息")
fc.attach_text("第二条消息")

# 3. build() 生成 Forward 对象
forward = fc.build()

# 4. 通过 API 发送
await self.api.qq.post_group_forward_msg(group_id, forward)
~~~

三步走：**创建构造器 → 添加节点 → build + 发送**。

### set_author — 切换发言人

~~~python
fc = ForwardConstructor(user_id="10001", nickname="小明")
fc.attach_text("我是小明")      # 显示为「小明」发的

fc.set_author("10002", "小红")  # 切换作者
fc.attach_text("我是小红")      # 显示为「小红」发的
~~~

`set_author` 修改的是构造器的**当前默认作者**，之后所有 `attach_*` 调用都使用新作者，直到再次调用 `set_author`。

### attach_message — 图文混排节点

~~~python
msg = MessageArray()
msg.add_text("图文混排 🖼️\n")
msg.add_image("image.jpg")
fc.attach_message(msg)
~~~

`attach_text` 和 `attach_image` 只能添加单类型节点。需要图文混排时，先用 `MessageArray` 构造内容，再通过 `attach_message` 添加。

### attach_forward — 嵌套转发

~~~python
# 先构建内层
inner_fc = ForwardConstructor(user_id="123", nickname="Inner")
inner_fc.attach_text("内层消息")
inner_forward = inner_fc.build()

# 外层通过 attach_forward 嵌入
outer_fc = ForwardConstructor(user_id="456", nickname="Outer")
outer_fc.attach_forward(inner_forward)
~~~

转发可以多层嵌套：内层 `build()` 得到 `Forward` 对象，外层通过 `attach_forward` 将其作为一个节点嵌入。

### 其他转发方式（只做提及）

~~~python
# 按消息 ID 转发 — 打包已有的历史消息，不需要构造 ForwardConstructor
await self.api.qq.send_group_forward_msg_by_id(group_id, [msg_id1, msg_id2])

# 私聊版 — 用法完全相同，只是目标改为 user_id
await self.api.qq.post_private_forward_msg(user_id, forward)

# 查询已有转发消息的展开内容
fwd = await self.api.qq.query.get_forward_msg(message_id)
~~~

## 运行方式

1. 将 `04_forward_message/` 文件夹复制到 `plugins/` 目录
2. 启动 Bot
3. 在 QQ 群中发送以下命令测试：

| 命令 | 效果 |
|------|------|
| `转发` | 基础合并转发（3 条文本消息打包） |
| `多作者转发` | 多人对话效果（小明、小红、小刚） |
| `图文转发` | 转发中包含图片和图文混排 |
| `嵌套转发` | 转发卡片中嵌套另一个转发卡片 |

## 延伸阅读

- [qq/03_rich_message](../03_rich_message/) — 普通富文本消息（MessageArray / Sugar / 底层 API）
- [qq/05 及后续示例](../) — 更多 QQ 功能演示
