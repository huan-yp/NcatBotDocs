# NcatBot 示例插件

> 按平台分类的示例插件集合，覆盖框架全部核心功能和常见用户场景。
> 每个插件都可以直接复制到 `plugins/` 目录中运行。

---

## 目录

### common/ — 通用框架特性（跨平台通用）

不依赖任何特定平台，使用纯 Trait 编程和 `registrar.on_*()` 通用装饰器。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](common/01_hello_world/) | NcatBotPlugin 基类、Trait 回复、跨平台命令、参数绑定 vs 手动解析 | ⭐ |
| 02 | [config_and_data](common/02_config_and_data/) | ConfigMixin / DataMixin 持久化 | ⭐ |
| 03 | [hook_and_filter](common/03_hook_and_filter/) | Hook 系统（BEFORE/AFTER/ON_ERROR）、add_hooks | ⭐⭐ |
| 04 | [rbac](common/04_rbac/) | RBAC 权限管理（角色/权限/检查） | ⭐⭐ |
| 05 | [scheduled_tasks](common/05_scheduled_tasks/) | 定时任务（多种时间格式/条件执行） | ⭐⭐ |
| 06 | [external_api](common/06_external_api/) | 外部 API 集成（aiohttp/配置/错误处理） | ⭐⭐ |
| 07 | [command_group](common/07_command_group/) | 命令组分层路由（CommandGroupHook/子命令/参数绑定） | ⭐⭐ |
| 08 | [dispatch_filter](common/08_dispatch_filter/) | DispatchFilterMixin 群/用户/命令级禁用管理 | ⭐⭐ |
| 09 | [plugin_management](common/09_plugin_management/) | 插件动态加载、卸载、生命周期状态持久化 | ⭐⭐ |

### qq/ — QQ 平台专属

使用 `registrar.qq.*` 平台子注册器和 QQ 专用事件/API。

**基础层**（01-07）：建立命令、事件、消息、会话的核心心智模型。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [event_registration](qq/01_event_registration/) | 事件注册方式（on_command/on_message/on_notice/on_request/priority/ignore_case） | ⭐ |
| 02 | [command_binding](qq/02_command_binding/) | 命令参数绑定（str/int/float/At/Reply/Image/Optional/aliases/shlex） | ⭐ |
| 03 | [rich_message](qq/03_rich_message/) | 富文本消息三路径（MessageArray/Sugar/底层 API） | ⭐ |
| 04 | [forward_message](qq/04_forward_message/) | 合并转发（ForwardConstructor/set_author/嵌套转发） | ⭐ |
| 05 | [notice_and_request](qq/05_notice_and_request/) | 通知与请求事件（入群/退群/撤回/戳/表情回应/好友/群请求） | ⭐⭐ |
| 06 | [session_basics](qq/06_session_basics/) | 会话等待与过滤（wait_session_reply/SessionResult/谓词组合） | ⭐⭐ |
| 07 | [dialog_and_menu](qq/07_dialog_and_menu/) | 多步对话与菜单（session_prompt/session_choose/嵌套菜单） | ⭐⭐ |

**场景层**（08-11）：用完整小助手串联真实使用场景。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 08 | [receive_attachment](qq/08_receive_attachment/) | 消息解析与附件处理（filter/Attachment/download/is_at） | ⭐⭐ |
| 09 | [group_admin](qq/09_group_admin/) | 群管理助手（踢/禁言/名片/头衔/公告/精华/RBAC） | ⭐⭐⭐ |
| 10 | [info_query](qq/10_info_query/) | 信息查询助手（群/成员/消息/好友/公告/精华） | ⭐⭐ |
| 11 | [file_and_folder](qq/11_file_and_folder/) | 文件上传与群文件夹管理（upload/download/folder/转存） | ⭐⭐⭐ |

### bilibili/ — Bilibili 平台专属

使用 `registrar.bilibili.*` 平台子注册器和 Bilibili 专用事件/API。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](bilibili/01_hello_world/) | 弹幕 + 私信基础响应 | ⭐ |
| 02 | [live_room](bilibili/02_live_room/) | 直播间全事件（弹幕/SC/礼物/大航海/互动） | ⭐⭐ |
| 03 | [private_message](bilibili/03_private_message/) | 私信收发 + 历史查询 | ⭐⭐ |
| 04 | [comment](bilibili/04_comment/) | 评论自动回复 + 点赞 | ⭐⭐ |
| 05 | [live_manager](bilibili/05_live_manager/) | 直播间管理（弹幕命令/禁言/静音） | ⭐⭐⭐ |
| 06 | [dynamic](bilibili/06_dynamic/) | 动态页多 UP 主合并监听 | ⭐⭐ |
| 07 | [video_parser](bilibili/07_video_parser/) | QQ 群自动解析 B 站视频链接（含小程序卡片） | ⭐⭐ |

### github/ — GitHub 平台专属（开发中）

使用 `registrar.github.*` 平台子注册器。⚠️ GitHub Adapter 尚在开发阶段。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](github/01_hello_world/) | Issue/PR/Push 基础事件 | ⭐ |
| 02 | [issue_bot](github/02_issue_bot/) | Issue 自动回复机器人 | ⭐⭐ |

### lark/ — 飞书平台专属

使用 `registrar.lark.*` 平台子注册器和飞书专用事件/API。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](lark/01_hello_world/) | 群聊/私聊基础响应、LarkPostBuilder 富文本 | ⭐ |

### ai/ — AI 平台

使用 `api.ai.*` 调用 LLM 提供商 API（Chat / Embeddings / Image Generation）。

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](ai/01_hello_world/) | Chat Completion、Embeddings、图像生成、参数自动绑定 | ⭐ |

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
├── qq_01_event_registration/   # 从 examples/qq/01_event_registration/ 复制
│   ├── manifest.toml
│   └── main.py
```

---

## 框架功能覆盖矩阵

| 框架功能 | 覆盖插件 |
|---------|---------|
| NcatBotPlugin + manifest.toml | 全部 |
| on_load / on_close 生命周期 | common/01, common/02, common/09 |
| registrar.on_*() 通用装饰器 | common/* |
| registrar.qq.* 子注册器 | qq/* |
| registrar.bilibili.* 子注册器 | bilibili/* |
| registrar.github.* 子注册器 | github/* |
| registrar.lark.* 子注册器 | lark/* |
| CommandHook 参数绑定 | qq/02, common/01, common/07, ai/01 |
| on_command / on_group_command / on_private_command | qq/01, qq/02 |
| on_message / on_group_message / on_private_message | qq/01 |
| on_notice / on_request + 细粒度装饰器 | qq/01, qq/05 |
| priority / ignore_case | qq/01, qq/02 |
| MessageArray 链式构造 | qq/03, qq/08 |
| Sugar 发送方法 (send_group_text / image / file 等) | qq/03 |
| Forward / ForwardConstructor | qq/04 |
| 通知事件 (increase/decrease/recall/poke/emoji_like) | qq/05 |
| 请求事件 (friend_request/group_request) | qq/05 |
| wait_session_reply / wait_session_event | qq/06, qq/07 |
| SessionResult (ok/text/timed_out/cancelled) | qq/06, qq/07 |
| session_prompt / session_choose | qq/07 |
| 谓词 (from_event/has_keyword/msg_in/msg_matches) | qq/06 |
| 谓词组合运算 (& \| ~) | qq/06 |
| MessageArray.filter / filter_text / filter_at / filter_image | qq/08 |
| Attachment (download/as_bytes/to_segment) | qq/08, qq/11 |
| event.message.text / is_at 消息解析 | qq/08 |
| 群管理 API (kick/ban/admin/card/title/notice/essence) | qq/09 |
| 信息查询 API (group/member/friend/login/history) | qq/10 |
| 文件 API (upload/download/folder/file_url) | qq/11 |
| self.api.qq.* | qq/01–11 |
| self.api.bilibili.* | bilibili/01–07 |
| self.api.github.* | github/01–02, cross_platform/03 |
| self.api.lark.* | lark/01 |
| self.api.ai.* | ai/01 |
| ConfigMixin | common/02, common/06, qq/09 |
| DataMixin | common/02, common/09, qq/07 |
| RBACMixin | common/04, qq/09 |
| TimeTaskMixin | common/05 |
| DispatchFilterMixin | common/08 |
| 插件动态管理 | common/09 |
| Hook（自定义） | common/03 |
| CommandGroupHook 命令组 | common/07 |
| Trait 跨平台编程 | common/01, cross_platform/02 |
| 多平台适配器 | cross_platform/01, cross_platform/03 |
| 跨平台双向桥接 | cross_platform/03 |
| 外部 HTTP API | common/06 |
| MessageArray.filter(Json) 小程序卡片解析 | bilibili/06 |
