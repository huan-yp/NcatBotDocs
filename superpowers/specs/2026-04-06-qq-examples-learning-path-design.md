# NcatBot QQ 示例插件学习路径重规划设计

日期：2026-04-06

状态：已确认，可进入实现计划

## 1. 背景

当前 NcatBot 示例插件体系已经覆盖了大量能力，但对完全新手并不友好，主要问题有：

1. QQ 示例的组织方式偏“能力堆放”，从入门到高级的认知台阶不够平滑。
2. 部分示例信息密度过高，例如一个示例同时展示过多事件类型，用户难以形成稳定心智模型。
3. 若干重要 QQ 能力没有被单独、明确地呈现，例如命令参数绑定全貌、富文本发送细分方式、Attachment 接收处理、session 便利方法与 dialog、文件与群文件夹联动。
4. common 层与 QQ 层之间存在边界不清的问题，部分通用能力与 QQ 专属能力交叉重复。
5. 现有 common 示例编号存在重复，目录编排本身已经开始削弱文档可信度。

本设计的目标不是“补几个例子”，而是重建一条面向完全新手、但能最终带到大部分 QQ 高级功能的学习路径。

## 2. 目标与非目标

### 2.1 目标

1. 面向完全新手，建立一条清晰、低摩擦的学习主线。
2. 让用户从第一个示例开始，逐步理解命令、事件、消息、会话、查询、管理、文件等 QQ 平台核心能力。
3. 将 QQ 平台专属能力与 common 通用能力明确分层，避免重复教学。
4. 每个示例只承担一个清晰教学目标，避免“全能示例”过早出现。
5. 保持示例可直接复制到 plugins/ 目录运行的现有使用习惯。
6. 让 docs/examples 成为用户主入口，而不是仅作为开发者内部样例堆放区。

### 2.2 非目标

1. 不改动 data 目录。data 是插件数据目录，不属于示例体系。
2. 不在本设计阶段处理具体代码迁移、实现细节和测试编排。
3. 不追求在单个示例中展示“全部相关 API”；只展示最适合作为教学入口的能力面。
4. 不把 DispatchFilter、插件动态加载/卸载、定时任务这类通用能力硬塞进 QQ 示例主线。

## 3. 设计原则

### 3.1 主用户是完全新手

学习路径默认用户还没有稳定的 NcatBot 心智模型，因此顺序必须服务于“先理解，再组合”，而不是服务于“覆盖率最大化”。

### 3.2 采用混合式路径，但以能力递进为主

主线先按能力递进建立基础，再用场景示例把能力串起来。原因是：

1. 纯能力拆分容易查阅，但前期成就感不足。
2. 纯场景驱动更有趣，但新手容易只会抄，不知道每一步在学什么。
3. 混合方案能兼顾认知台阶和完成感。

### 3.3 common 与 QQ 必须分层

通用框架能力放 common，QQ 平台专属能力放 qq。一个能力只保留一个主要教学入口：

1. 如果能力跨平台成立，应放 common。
2. 如果能力明显依赖 QQ 事件、QQ API 或 QQ 消息模型，应放 qq。
3. QQ 示例可以引用 common 概念，但不重复承担其完整教学职责。

### 3.4 每个示例有单一主问题

用户读完一个示例后，应该能明确回答“这个示例教会了我什么”。如果一个示例同时回答三个问题，说明边界划分失败。

### 3.5 示例既是代码样例，也是文档节点

每个示例目录仍沿用现有形态：

1. README.md：说明目标、能力点、使用方式、关键代码讲解。
2. main.py：最小但完整的可运行示例。
3. manifest.toml：保持可以直接复制运行。

## 4. 范围

本设计覆盖以下位置：

1. docs/docs/examples/qq
2. docs/docs/examples/common
3. docs/docs/examples/README.md 中的示例索引与功能覆盖矩阵

本设计不覆盖：

1. data/
2. plugins/
3. tests/
4. guide/reference 的具体文本改写细节

## 5. 总体结构

重规划后，QQ 层使用“两阶递进”：

1. 基础层 01-07：建立命令、事件、消息、会话的核心心智模型。
2. 场景层 08-11：用完整小助手串联真实使用场景。

重规划后，common 层使用“平级专题”结构：

1. 每个目录都服务一个跨平台能力。
2. 不再与 QQ 层重复展示 session/dialog 的完整路径。
3. 新增 dispatch_filter 和 plugin_management 两个高价值专题。

## 6. QQ 示例设计

### 6.1 QQ 示例目录

```text
docs/docs/examples/qq/
├── 01_event_registration/
├── 02_command_binding/
├── 03_rich_message/
├── 04_forward_message/
├── 05_notice_and_request/
├── 06_session_basics/
├── 07_dialog_and_menu/
├── 08_receive_attachment/
├── 09_group_admin/
├── 10_info_query/
└── 11_file_and_folder/
```

### 6.2 基础层 01-07

#### 01_event_registration

教学目标：让用户看懂 NcatBot 中“事件处理器是怎么注册的”。

必须覆盖：

1. on_command
2. on_group_command / on_private_command
3. on_message / on_group_message / on_private_message
4. on_notice / on_request
5. priority
6. ignore_case

只做提及，不展开：

1. on_meta
2. on_message_sent
3. registrar.qq 下的细粒度 QQ 专属快捷装饰器
4. platform 参数

边界：本示例只回答“怎么注册”，不回答“参数怎么绑定”“消息怎么构造”“Notice/Request 怎么细分处理”。

#### 02_command_binding

教学目标：完整展示命令参数绑定体系。

必须覆盖：

1. str
2. int / float
3. At
4. Reply
5. Image
6. Optional
7. 多参数组合
8. aliases
9. shlex 引号行为
10. 参数缺失时的自动用法提示

只做提及：

1. event.params 兜底方案
2. MessageArray 参数绑定

边界：本示例不展开复杂富文本构造，只展示绑定结果如何被消费。

#### 03_rich_message

教学目标：教会用户用三种路径发送富文本消息。

必须覆盖：

1. MessageArray 链式构造
2. 各类常用消息段：Text、Image、At、Reply、Face、Record、Video、File
3. event.reply
4. Sugar 发送接口
5. 底层 post_group_msg / post_group_array_msg 的定位
6. send_group_text、send_group_image、send_group_file、send_group_record、send_group_video、send_group_sticker、send_poke

边界：本示例不承担合并转发教学职责，转发消息在 04 单独讲。

#### 04_forward_message

教学目标：专门讲清合并转发消息的构造和发送。

必须覆盖：

1. ForwardConstructor 基础用法
2. set_author
3. attach_text / attach_image / attach_file / attach_video
4. attach_forward 嵌套转发
5. post_group_forward_msg
6. send_group_forward_msg_by_id

只做提及：

1. 私聊版转发接口
2. get_forward_msg

#### 05_notice_and_request

教学目标：精选最常用的 Notice/Request 事件处理模式，避免一次性塞入全部事件类型。

必须覆盖：

1. on_group_increase
2. on_group_decrease
3. on_group_recall
4. on_poke
5. on_group_msg_emoji_like
6. on_friend_request
7. on_group_request
8. 通用 on_notice 兜底分支

只做提及：

1. on_group_admin
2. on_group_ban
3. on_friend_add
4. on_message_sent

#### 06_session_basics

教学目标：以 EventMixin 的 session 便利方法为主线，建立会话等待的基础模型。

必须覆盖：

1. wait_session_event
2. wait_session_reply
3. SessionResult 的 ok、text、timed_out、cancelled、cancel_word
4. cancel_words
5. extra_predicate
6. from_event
7. has_keyword、msg_in、msg_matches
8. 谓词组合运算

只做提及：

1. wait_event 是底层基础
2. events 是持续事件流工具

边界：本示例只讲“等待和过滤”，不讲多步对话 UI 和菜单流程。

#### 07_dialog_and_menu

教学目标：展示多步对话和菜单交互的完整用户体验。

必须覆盖：

1. session_prompt
2. session_choose
3. timeout_reply
4. cancel_reply
5. invalid_reply
6. max_retries
7. 多步流程
8. 嵌套菜单

边界：本示例以高级会话交互为核心，不再回头讲 wait_event 原语。

### 6.3 场景层 08-11

#### 08_receive_attachment

教学目标：从接收侧讲清富文本和 Attachment 的解析与处理。

必须覆盖：

1. event.message.filter(Image)
2. filter_text / filter_at / filter_image
3. event.message.get_attachments
4. Attachment.download
5. Attachment.as_bytes
6. Attachment.to_segment
7. ImageAttachment 元信息
8. event.message.text
9. event.message.is_at(bot_id)

#### 09_group_admin

教学目标：构造一个群管小助手，展示 QQ 管理 API 的常见使用方式。

必须覆盖：

1. set_group_kick
2. set_group_ban
3. set_group_whole_ban
4. set_group_admin
5. set_group_card
6. set_group_special_title
7. send_group_notice
8. set_essence_msg
9. set_friend_add_request
10. set_group_add_request

只做提及：

1. RBAC 建议与 common/04 联动
2. 删除公告、删除精华、批量踢人、群头像、群待办等扩展接口

#### 10_info_query

教学目标：构造一个信息助手，展示最有代表性的查询 API。

必须覆盖：

1. get_group_msg_history
2. get_friend_msg_history
3. get_msg
4. get_forward_msg
5. get_group_info
6. get_group_list
7. get_group_member_info
8. get_group_member_list
9. get_login_info
10. get_friend_list
11. get_group_notice
12. get_essence_msg_list

只做提及：

1. get_stranger_info
2. get_group_honor_info
3. get_group_at_all_remain
4. get_group_shut_list
5. get_emoji_likes

#### 11_file_and_folder

教学目标：展示文件上传、群文件夹、Attachment 联动和上传语法糖。

必须覆盖：

1. upload_group_file(本地路径)
2. upload_group_file(Attachment)
3. 上传到指定文件夹的语法糖
4. upload_private_file
5. create_group_file_folder
6. get_group_root_files
7. get_group_files_by_folder
8. get_group_file_url
9. download_file
10. 接收文件再转存到文件夹的串联场景

只做提及：

1. delete_group_file
2. delete_group_folder
3. get_group_file_system_info

### 6.4 QQ 示例依赖关系

1. 01 无前置。
2. 02-05 依赖 01 的基本注册概念。
3. 06 依赖 01 与 02 的事件和命令理解。
4. 07 依赖 06。
5. 08-11 依赖 01-07，但应在 README 中标注“可带着问题跳读”。

## 7. common 示例设计

### 7.1 common 示例目录

```text
docs/docs/examples/common/
├── 01_hello_world/
├── 02_config_and_data/
├── 03_hook_and_filter/
├── 04_rbac/
├── 05_scheduled_tasks/
├── 06_external_api/
├── 07_command_group/
├── 08_dispatch_filter/
└── 09_plugin_management/
```

### 7.2 目录调整决策

1. 删除旧的 multi_step_dialog。其职责已被 QQ 层 06 和 07 更完整承接。
2. 删除旧的 session_helpers 作为独立 common 专题。session 便利方法虽然通用，但当前最有价值的教学入口仍在 QQ 示例主线。
3. 修复 common 目录原有编号重复问题。
4. 新增 dispatch_filter 和 plugin_management 两个专题，以承接从 QQ 主线剥离出来的通用高级能力。

### 7.3 各目录职责

#### 01_hello_world

最小可运行插件：manifest、NcatBotPlugin、on_load、on_command、reply、main.py 启动方式。

#### 02_config_and_data

展示 ConfigMixin 与 DataMixin 的基本持久化使用，不掺入 QQ 专属能力。

#### 03_hook_and_filter

展示 BEFORE_CALL / AFTER_CALL / ON_ERROR、自定义 Hook、add_hooks，以及常用内置 Hook 和 Filter。

#### 04_rbac

展示 RBAC 的角色、权限、检查流程，以及 RBAC 与 Hook 结合的实际保护场景。

#### 05_scheduled_tasks

展示 TimeTaskMixin 的时间格式、条件执行、最大次数、移除任务、状态查询与 DataMixin 联动。

#### 06_external_api

展示插件中安全调用外部 HTTP API 的模式。

#### 07_command_group

展示 CommandGroupHook、子命令、ignore_case 和参数绑定组合。

#### 08_dispatch_filter

展示群级和用户级禁用、命令级禁用及管理命令封装。

#### 09_plugin_management

展示插件动态加载、动态卸载、生命周期回调与状态持久化。

## 8. 索引与阅读体验要求

### 8.1 docs/docs/examples/README.md 必须同步调整

必须同步以下内容：

1. common 表格改为 01-09 新结构。
2. qq 表格改为 01-11 新结构。
3. 更新“演示功能”和“难度”描述，使其与新边界一致。
4. 重新整理功能覆盖矩阵，去掉已删除示例，加入新增示例。

### 8.2 每个示例 README 的统一结构

每个示例 README 应统一包含以下区块：

1. 这个示例教什么
2. 你将学到
3. 前置知识
4. 目录结构
5. 完整代码
6. 关键代码讲解
7. 运行方式
8. 延伸阅读

统一结构的目的不是形式化，而是降低新手在不同示例之间切换时的认知成本。

### 8.3 示例 README 的边界说明

每个示例 README 顶部都应明确写出：

1. 本示例重点展示什么
2. 本示例不解决什么
3. 下一步建议读哪个示例

这样可以避免用户把某个示例误认为“完整最佳实践”。

## 9. 迁移策略

本次重规划按“保留目录资产、重写教学内容”的思路执行：

1. 允许复用现有示例中的可运行代码片段。
2. 不保留“因为已经存在所以继续沿用”的目录设计。
3. 以教学边界清晰为第一原则，必要时直接重写 README 与 main.py。
4. 目录更名时，同步更新 examples 总索引。
5. 由于 common 和 qq 的职责边界已调整，迁移过程中允许将部分现有能力整体挪到新的主题目录。

## 10. 风险与约束

### 10.1 风险

1. 若只改目录、不重写 README，最终仍会保留旧的高信息密度问题。
2. 若 QQ 示例继续夹带通用专题，common 与 qq 会再次失去边界。
3. 若索引表和覆盖矩阵不同步，示例体系会再次失去可信度。

### 10.2 约束

1. 示例必须保持可直接复制运行。
2. 示例代码量应克制，避免再次出现一个示例承担过多职责。
3. common 与 qq 的重复内容应以“一个完整入口 + 另一侧提及跳转”的方式处理，而不是双写。

## 11. 验收标准

在实现完成后，应满足以下标准：

1. 完全新手可以按照 qq/01 → qq/11 的顺序逐步学习，不会在前四个示例就遇到明显认知断层。
2. 用户能在 examples/README 中直接看出 common 和 qq 的职责边界。
3. QQ 专属重点能力都有明确入口：命令绑定、富文本、转发、Notice/Request、session/dialog、Attachment、群管理、信息查询、文件与文件夹。
4. common 层不再保留重复编号，也不再和 QQ 层重复承担 session/dialog 教学主线。
5. DispatchFilter、插件管理、定时任务三类高级但通用的能力被放到 common，而不是继续混入 QQ 主线。

## 12. 实施顺序建议

推荐实施顺序如下：

1. 先改 docs/docs/examples/README.md 的目标结构和目录表。
2. 再重建 common 目录，先解决编号和边界问题。
3. 最后重建 qq 目录，从 01-07 基础层开始，再写 08-11 场景层。

这样做的原因是：总索引先变更后，后续每个示例的落位和命名不会反复摇摆。