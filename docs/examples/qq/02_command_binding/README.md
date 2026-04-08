# 02_command_binding

> 分类：qq

## 这个示例教什么

NcatBot 中**命令参数是怎么绑定的**。当你注册一个命令处理器时，只需在函数签名中声明参数类型，框架就会自动从用户消息中提取并转换参数——字符串、数值、@某人、引用消息、图片，甚至可选参数和多参数组合。

## 你将学到

- `str` 参数绑定 — 文本参数自动提取
- `int` / `float` 参数绑定 — 自动类型转换
- `At` 参数绑定 — 从消息中提取 @ 段
- `Reply` 参数绑定 — 从消息中提取引用消息段
- `Image` 参数绑定 — 从消息中提取图片段
- `Optional` 参数 — 带默认值的可选参数
- 多参数组合 — 同时绑定 `At` + `int`
- `aliases` — 一个处理器响应多个命令名
- `shlex` 引号解析 — `"hello world"` 视为一个参数
- 参数缺失时的自动用法提示

## 前置知识

- 了解 NcatBot 的事件注册方式（`@registrar.qq.on_group_command` 等）
- 建议先完成 [qq/01_event_registration](../01_event_registration/)

## 目录结构

~~~text
02_command_binding/
├── main.py          # 插件代码
├── manifest.toml    # 插件清单
└── README.md
~~~

## 完整代码

~~~python
"""
qq/02_command_binding — QQ 命令参数绑定体系演示

演示功能:
  - str 参数绑定              echo <content>
  - int / float 参数绑定      add <a> <b>
  - At 参数绑定               kick <target>
  - Reply 参数绑定            quote-info <ref>
  - Image 参数绑定            ocr <pic>
  - Optional 参数（带默认值）  ban <target> [duration]
  - 多参数组合                 ban = At + int
  - aliases 命令别名           hello / hi / 你好
  - shlex 引号行为             echo "hello world" → 一个参数
  - 参数缺失时的自动用法提示

提及但不展开:
  - event.params 兜底方案
  - MessageArray 参数绑定

边界:
  本示例不展开复杂富文本构造，只展示绑定结果如何被消费。

使用方式: 将本文件夹复制到 plugins/ 目录，启动 Bot。
"""

from typing import Optional

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.types import At, Image, Reply
from ncatbot.utils import get_log

LOG = get_log("CommandBinding")


class CommandBindingPlugin(NcatBotPlugin):
    name = "command_binding_qq"
    version = "1.0.0"
    author = "NcatBot"
    description = "QQ 命令参数绑定体系演示"

    # ================================================================
    # 1. str 参数绑定
    # ================================================================
    # 用户发送: echo hello
    # 框架自动将 "hello" 绑定到 content 参数。
    #
    # shlex 引号行为:
    #   echo "hello world"  → content = "hello world"（整体作为一个参数）
    #   echo hello world    → content = "hello"（只绑定第一个词，world 被丢弃）

    @registrar.qq.on_group_command("echo")
    async def on_echo(self, event: GroupMessageEvent, content: str):
        """str 绑定 — 'echo hello' → content='hello'"""
        await event.reply(text=f"你说了: {content}")

    # ================================================================
    # 2. int / float 参数绑定
    # ================================================================
    # 用户发送: add 1 2
    # 框架自动将 "1" 和 "2" 转为 int 并绑定。
    # 如果转换失败（如 "add abc 2"），框架自动回复用法提示。

    @registrar.qq.on_group_command("add")
    async def on_add(self, event: GroupMessageEvent, a: int, b: int):
        """int 绑定 — 'add 1 2' → a=1, b=2"""
        await event.reply(text=f"{a} + {b} = {a + b}")

    @registrar.qq.on_group_command("divide")
    async def on_divide(self, event: GroupMessageEvent, a: float, b: float):
        """float 绑定 — 'divide 10 3' → a=10.0, b=3.0"""
        if b == 0:
            await event.reply(text="除数不能为 0")
            return
        await event.reply(text=f"{a} / {b} = {a / b:.2f}")

    # ================================================================
    # 3. At 参数绑定
    # ================================================================
    # 用户发送: kick @某人
    # 框架从消息中提取 At 段并绑定到 target 参数。
    # target 是 At 对象，可通过 target.user_id 获取被 @ 的用户 ID。

    @registrar.qq.on_group_command("kick")
    async def on_kick(self, event: GroupMessageEvent, target: At):
        """At 绑定 — 'kick @某人' → target.user_id"""
        await event.reply(text=f"将踢出用户: {target.user_id}")

    # ================================================================
    # 4. Reply 参数绑定
    # ================================================================
    # 用户引用一条消息并发送: quote-info
    # 框架从消息中提取 Reply 段（即被引用的消息）并绑定到 ref 参数。
    # ref 是 Reply 对象，可通过 ref.id 获取被引用消息的 ID。

    @registrar.qq.on_group_command("quote-info")
    async def on_quote_info(self, event: GroupMessageEvent, ref: Reply):
        """Reply 绑定 — 引用消息后发送 'quote-info' → ref.id"""
        await event.reply(text=f"你引用的消息 ID: {ref.id}")

    # ================================================================
    # 5. Image 参数绑定
    # ================================================================
    # 用户发送一张图片并附带命令: ocr <图片>
    # 框架从消息中提取 Image 段并绑定到 pic 参数。
    # pic 是 Image 对象，可通过 pic.url 获取图片链接。

    @registrar.qq.on_group_command("ocr")
    async def on_ocr(self, event: GroupMessageEvent, pic: Image):
        """Image 绑定 — 发图并输入 'ocr' → pic.url"""
        await event.reply(text=f"收到图片: {pic.url}")

    # ================================================================
    # 6. Optional 参数（带默认值）+ 多参数组合
    # ================================================================
    # 用户发送: ban @某人       → target=At, duration=60（使用默认值）
    # 用户发送: ban @某人 120   → target=At, duration=120
    # At + int 多参数组合，Optional 用 Python 默认值语法。

    @registrar.qq.on_group_command("ban")
    async def on_ban(self, event: GroupMessageEvent, target: At, duration: int = 60):
        """多参数组合 + Optional — 'ban @某人 [秒数]'"""
        await event.reply(
            text=f"将禁言 {target.user_id}，时长 {duration} 秒"
        )

    # ================================================================
    # 7. aliases — 命令别名
    # ================================================================
    # 传入多个命令名即可注册别名。
    # 下面的处理器可被 "hello"、"hi"、"你好" 中任意一个触发。
    # 配合 ignore_case=True，"Hi"、"HI" 也能触发。

    @registrar.qq.on_group_command("hello", "hi", "你好", ignore_case=True)
    async def on_hello(self, event: GroupMessageEvent):
        """aliases — 'hello' / 'hi' / '你好' 都能触发"""
        await event.reply(text="你好！👋")

    # ================================================================
    # 8. 参数缺失时的自动用法提示
    # ================================================================
    # 当用户发送 "echo"（不带参数）时，框架自动回复:
    #   用法: echo <content: str>
    # 无需手动编写错误处理代码——框架根据函数签名自动生成提示。

    # （此行为由上面的 on_echo 等处理器自动获得，无需额外代码。）

    # ================================================================
    # 提及但不展开的绑定方式
    # ================================================================
    # - event.params 兜底方案:
    #   当内置绑定无法满足需求时，可通过 event.params 获取原始参数列表。
    #   event.params 是 list[str]，包含用户输入的所有参数（已 shlex 分词）。
    #
    #   @registrar.qq.on_group_command("raw")
    #   async def on_raw(self, event: GroupMessageEvent):
    #       params = event.params  # list[str]
    #       await event.reply(text=f"原始参数: {params}")
    #
    # - MessageArray 参数绑定:
    #   可将整个消息数组绑定到 MessageArray 类型参数，用于处理复杂富文本消息。
    #   详见消息构造相关文档。
~~~

## 关键代码讲解

### 基本类型绑定

| 参数类型 | 输入示例 | 绑定结果 |
|---------|---------|---------|
| `str` | `echo hello` | `content = "hello"` |
| `int` | `add 1 2` | `a = 1, b = 2` |
| `float` | `divide 10 3` | `a = 10.0, b = 3.0` |

框架根据函数签名中的类型注解自动解析参数。类型转换失败时（如 `add abc 2`），会自动回复用法提示。

### 消息段绑定

| 参数类型 | 使用场景 | 关键属性 |
|---------|---------|---------|
| `At` | `kick @某人` | `target.user_id` — 被 @ 的用户 ID |
| `Reply` | 引用消息后发送 `quote-info` | `ref.id` — 被引用消息的 ID |
| `Image` | 发图并输入 `ocr` | `pic.url` — 图片链接 |

消息段类型从 `ncatbot.types` 导入：

```python
from ncatbot.types import At, Reply, Image
```

### Optional 参数与多参数组合

```python
@registrar.qq.on_group_command("ban")
async def on_ban(self, event: GroupMessageEvent, target: At, duration: int = 60):
    ...
```

- `ban @某人` → `duration` 使用默认值 `60`
- `ban @某人 120` → `duration = 120`

Optional 参数使用 Python 标准默认值语法，无需额外装饰器。

### aliases 命令别名

```python
@registrar.qq.on_group_command("hello", "hi", "你好", ignore_case=True)
async def on_hello(self, event: GroupMessageEvent):
    ...
```

传入多个命令名即可注册别名。配合 `ignore_case=True`，`Hi`、`HI` 也能触发。

### shlex 引号行为

```text
echo hello world      → content = "hello"      （只绑定第一个词）
echo "hello world"    → content = "hello world" （引号内整体作为一个参数）
```

框架使用 `shlex` 对用户输入进行分词，双引号内的内容被视为单个参数。

### 参数缺失时的自动提示

当必选参数缺失时，框架自动根据函数签名生成用法提示并回复用户，例如：

```text
用法: echo <content: str>
```

无需手动编写参数校验代码。

### event.params 兜底

当内置绑定无法满足需求时，可直接访问 `event.params`（`list[str]`）获取原始参数列表：

```python
@registrar.qq.on_group_command("raw")
async def on_raw(self, event: GroupMessageEvent):
    params = event.params  # ['arg1', 'arg2', ...]
```

## 运行方式

1. 将 `02_command_binding/` 文件夹复制到项目的 `plugins/` 目录
2. 启动 Bot（`python main.py` 或 `ncatbot run`）
3. 在群聊中发送以下命令测试：
   - `echo hello` — str 绑定
   - `echo "hello world"` — shlex 引号行为
   - `echo` — 参数缺失，查看自动用法提示
   - `add 1 2` — int 绑定
   - `divide 10 3` — float 绑定
   - `kick @某人` — At 绑定
   - 引用一条消息后发送 `quote-info` — Reply 绑定
   - 发送图片并输入 `ocr` — Image 绑定
   - `ban @某人` — Optional 参数（默认 60 秒）
   - `ban @某人 120` — Optional 参数（指定 120 秒）
   - `hello` / `hi` / `你好` — aliases 别名

## 延伸阅读

- [qq/01_event_registration](../01_event_registration/) — 事件注册方式（前置知识）
- 消息段类型参考（Reference）— `At`、`Reply`、`Image` 等消息段的完整字段
- `MessageArray` 参数绑定 — 处理复杂富文本消息的高级绑定方式
