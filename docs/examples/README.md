# NcatBot 示例插件

> 按平台分类的示例插件集合，覆盖框架全部核心功能和常见用户场景。
> 每个插件都可以直接复制到 `plugins/` 目录中运行。

---

## 目录

### common/ — 通用框架特性（跨平台通用）

不依赖任何特定平台，使用纯 Trait 编程和 `registrar.on_*()` 通用装饰器。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](common/01_hello_world/) | NcatBotPlugin 基类、Trait 回复、跨平台命令 | ⭐ |
| 02 | [config_and_data](common/02_config_and_data/) | ConfigMixin / DataMixin 持久化 | ⭐ |
| 03 | [hook_and_filter](common/03_hook_and_filter/) | Hook 系统（BEFORE/AFTER/ON_ERROR）、add_hooks | ⭐⭐ |
| 04 | [rbac](common/04_rbac/) | RBAC 权限管理（角色/权限/检查） | ⭐⭐ |
| 05 | [scheduled_tasks](common/05_scheduled_tasks/) | 定时任务（多种时间格式/条件执行） | ⭐⭐ |
| 06 | [multi_step_dialog](common/06_multi_step_dialog/) | 多步对话（from_event/超时/取消） | ⭐⭐ |
| 07 | [external_api](common/07_external_api/) | 外部 API 集成（aiohttp/配置/错误处理） | ⭐⭐ |

### qq/ — QQ 平台专属

使用 `registrar.qq.*` 平台子注册器和 QQ 专用事件/API。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](qq/01_hello_world/) | registrar.qq 注册、群/私聊命令 | ⭐ |
| 02 | [event_handling](qq/02_event_handling/) | 三种事件消费模式（装饰器/事件流/wait_event） | ⭐ |
| 03 | [message_types](qq/03_message_types/) | MessageArray 链式构造、图文混排、合并转发 | ⭐ |
| 04 | [bot_api](qq/04_bot_api/) | self.api.qq 消息发送、群管理、信息查询 | ⭐ |
| 05 | [notice_and_request](qq/05_notice_and_request/) | 通知与请求事件（入群/退群/好友/撤回/戳） | ⭐⭐ |
| 06 | [group_manager](qq/06_group_manager/) | 群管理机器人（踢/禁言/欢迎/RBAC） | ⭐⭐⭐ |
| 07 | [qa_bot](qq/07_qa_bot/) | 问答机器人（多步对话/关键词匹配/数据持久化） | ⭐⭐⭐ |
| 08 | [scheduled_reporter](qq/08_scheduled_reporter/) | 定时统计报告（定时任务/合并转发/数据统计） | ⭐⭐⭐ |
| 09 | [full_featured_bot](qq/09_full_featured_bot/) | 全功能群助手（所有框架特性综合） | ⭐⭐⭐ |

### bilibili/ — Bilibili 平台专属

使用 `registrar.bilibili.*` 平台子注册器和 Bilibili 专用事件/API。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](bilibili/01_hello_world/) | 弹幕 + 私信基础响应 | ⭐ |
| 02 | [live_room](bilibili/02_live_room/) | 直播间全事件（弹幕/SC/礼物/大航海/互动） | ⭐⭐ |
| 03 | [private_message](bilibili/03_private_message/) | 私信收发 + 历史查询 | ⭐⭐ |
| 04 | [comment](bilibili/04_comment/) | 评论自动回复 + 点赞 | ⭐⭐ |
| 05 | [live_manager](bilibili/05_live_manager/) | 直播间管理（弹幕命令/禁言/静音） | ⭐⭐⭐ |

### github/ — GitHub 平台专属（开发中）

使用 `registrar.github.*` 平台子注册器。⚠️ GitHub Adapter 尚在开发阶段。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](github/01_hello_world/) | Issue/PR/Push 基础事件 | ⭐ |
| 02 | [issue_bot](github/02_issue_bot/) | Issue 自动回复机器人 | ⭐⭐ |

### cross_platform/ — 跨平台操作

同时使用多个平台的子注册器，或通过 Trait 实现跨平台逻辑。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [multi_adapter](cross_platform/01_multi_adapter/) | 双平台启动（QQ+Bilibili）、跨平台命令 | ⭐⭐ |
| 02 | [trait_programming](cross_platform/02_trait_programming/) | Replyable/HasSender/GroupScoped Trait 编程 | ⭐⭐ |
| 03 | [github_qq_bridge](cross_platform/03_github_qq_bridge/) | GitHub↔QQ 双向桥接（事件转发/消息映射）⚠️ | ⭐⭐⭐ |

---

## 使用方式

1. 将任意示例插件文件夹复制到项目根目录的 `plugins/` 下
2. 启动 Bot，插件自动加载

```text
plugins/
├── qq_01_hello_world/      # 从 examples/qq/01_hello_world/ 复制
│   ├── manifest.toml
│   └── main.py
```

---

## 框架功能覆盖矩阵

| 框架功能 | 覆盖插件 |
|---------|---------|
| NcatBotPlugin + manifest.toml | 全部 |
| on_load / on_close 生命周期 | common/01, common/02, qq/09 |
| registrar.on_*() 通用装饰器 | common/* |
| registrar.qq.* 子注册器 | qq/* |
| registrar.bilibili.* 子注册器 | bilibili/* |
| registrar.github.* 子注册器 | github/* |
| EventMixin.events() 事件流 | qq/02 |
| EventMixin.wait_event() | qq/02, common/06, qq/07 |
| MessageArray 链式构造 | qq/03, qq/08 |
| Forward / ForwardConstructor | qq/03, qq/08 |
| self.api.qq.* | qq/01–09 |
| self.api.bilibili.* | bilibili/01–05 |
| self.api.github.* | github/01–02, cross_platform/03 |
| ConfigMixin | common/02, qq/06, common/07, qq/09, cross_platform/03 |
| DataMixin | common/02, common/06, qq/07, qq/08, qq/09 |
| RBACMixin | common/04, qq/06, qq/09 |
| TimeTaskMixin | common/05, qq/08, qq/09 |
| Hook（自定义） | common/03 |
| Trait 跨平台编程 | common/01, cross_platform/02 |
| 多平台适配器 | cross_platform/01, cross_platform/03 |
| 跨平台双向桥接 | cross_platform/03 |
| 多步对话 | common/06, qq/07 |
| 外部 HTTP API | common/07 |
