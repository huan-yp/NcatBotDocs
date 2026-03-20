"""
修复 .agents/skills/ 下所有 .md 文件中的旧文档路径引用。

Skill 文件中的路径格式如:
  docs/guide/plugin/4a.event-registration.md
  guide/adapter/1_napcat_qq.md
  reference/api/qq/2_manage_api.md
  docs/architecture.md

需要替换为新的中文目录/文件名格式。
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SKILLS_ROOT = ".agents/skills"

# ── 目录名映射 ──
# guide 子目录
GUIDE_DIR = {
    "quick_start": "1. 快速开始",
    "adapter": "2. 适配器",
    "plugin": "3. 插件开发",
    "send_message": "4. 消息发送",
    "api_usage": "5. API 使用",
    "configuration": "6. 配置管理",
    "rbac": "7. RBAC 权限",
    "cli": "8. 命令行工具",
    "testing": "9. 测试指南",
    "multi_platform": "10. 多平台开发",
}

# reference 子目录
REF_DIR = {
    "api": "1. Bot API",
    "events": "2. 事件类型",
    "types": "3. 数据类型",
    "core": "4. 核心模块",
    "plugin": "5. 插件系统",
    "services": "6. 服务层",
    "adapter": "7. 适配器",
    "utils": "8. 工具模块",
    "testing": "9. 测试框架",
    "cli": "10. CLI",
}

# contributing 子目录
CONTRIB_DIR = {
    "development_setup": "1. 开发环境",
    "design_decisions": "2. 设计决策",
    "module_internals": "3. 模块内部实现",
}

# 子子目录 (send_message/xxx, api_usage/xxx, api/xxx)
SUB_DIR = {
    "common": "1. 通用",
    "qq": "2. QQ",
    "bilibili": "3. Bilibili",
    "github": "4. GitHub",
}

# ── 文件名映射 ──
FILE_MAP = {
    # guide/plugin (3. 插件开发)
    "1.quick-start.md": "1. 快速开始.md",
    "2.structure.md": "2. 插件结构.md",
    "3.lifecycle.md": "3. 生命周期.md",
    "4a.event-registration.md": "4. 事件注册.md",
    "4b.event-advanced.md": "5. 事件高级.md",
    "4c.predicate-dsl.md": "6. 谓词 DSL.md",
    "5a.config-data.md": "7. 配置与数据.md",
    "5b.rbac-schedule-event.md": "8. RBAC 定时任务与事件.md",
    "6.hooks.md": "9. Hooks.md",
    "7a.patterns.md": "10. 模式.md",
    "7b.case-studies.md": "11. 案例研究.md",
    # guide/send_message 子文件
    "1_segments.md": "1. 消息段.md",
    "2_array.md": "2. 消息数组.md",
    "1_sugar.md": "1. 语法糖.md",
    "2_forward.md": "2. 合并转发.md",
    "3_examples.md": "3. 示例.md",
    "1_messaging.md": "1. 消息发送.md",
    # guide/api_usage 子文件
    "1_event_methods.md": "1. 事件方法.md",
    "2_traits.md": "2. Traits.md",
    "2_manage.md": "2. 群管理.md",
    "3_query_support.md": "3. 查询与支持.md",
    "1_live_room.md": "1. 直播间.md",
    "2_private_msg.md": "2. 私信.md",
    "3_comment.md": "3. 评论.md",
    "4_source_query.md": "4. 源查询.md",
    "1_issue_comment.md": "1. Issue 评论.md",
    "2_pr_query.md": "2. PR 查询.md",
    # guide/configuration
    "1.config-security.md": "1. 配置安全.md",
    # guide/rbac
    "1_model.md": "1. RBAC 模型.md",
    "2.integration.md": "2. 集成.md",
    # guide/cli
    "1.commands.md": "1. 命令.md",
    # guide/testing
    "1.quick-start.md": "1. 快速开始.md",
    "2.harness.md": "2. 测试工具.md",
    "3.factory-scenario.md": "3. 工厂与场景.md",
    # guide/adapter
    "1_napcat_qq.md": "1. NapCat QQ.md",
    "2_bilibili.md": "2. Bilibili.md",
    "3_github.md": "3. GitHub.md",
    "4_mock.md": "4. Mock 适配器.md",
    # reference/api 子文件
    "traits.md": "1. Traits.md",
    "1_message_api.md": "1. 消息 API.md",
    "2_manage_api.md": "2. 管理 API.md",
    "3_info_support_api.md": "3. 信息支持 API.md",
    "1_api.md": "1. API.md",
    # reference/events
    "1_common.md": "1. 通用事件.md",
    "2_qq_events.md": "2. QQ 事件.md",
    "3_bilibili_events.md": "3. Bilibili 事件.md",
    "4_github_events.md": "4. GitHub 事件.md",
    # reference/types
    "1_common_segments.md": "1. 通用消息段.md",
    "2_message_array.md": "2. 消息数组.md",
    "3_qq_segments.md": "3. QQ 消息段.md",
    "4_qq_responses.md": "4. QQ 响应.md",
    "5_bilibili_types.md": "5. Bilibili 类型.md",
    "6_github_types.md": "6. GitHub 类型.md",
    # reference/core
    "1_internals.md": "1. 内部实现.md",
    "2_predicate.md": "2. 谓词系统.md",
    "3_registry.md": "3. 注册表.md",
    # reference/plugin
    "1_base_class.md": "1. 基类.md",
    "2_mixins.md": "2. Mixins.md",
    # reference/services
    "1_rbac_service.md": "1. RBAC 服务.md",
    "2_config_task_service.md": "2. 配置任务服务.md",
    # reference/adapter
    "1_connection.md": "1. 连接.md",
    "2_protocol.md": "2. 协议.md",
    # reference/utils
    "1a_config.md": "1. 配置.md",
    "1b_io_logging.md": "2. IO 与日志.md",
    "2_decorators_misc.md": "3. 装饰器与杂项.md",
    # reference/testing
    "1_harness.md": "1. 测试工具.md",
    "2_factory_scenario_mock.md": "2. 工厂场景与 Mock.md",
    # contributing
    "1_advanced.md": "1. 高级设置.md",
    "1_architecture.md": "1. 架构决策.md",
    "2_implementation.md": "2. 实现决策.md",
    "3_types.md": "3. 类型决策.md",
    "1.core_modules.md": "1. 核心模块.md",
    "2.plugin_service_modules.md": "2. 插件服务模块.md",
    # reference/cli
    "cli.md": "10. CLI/1. 命令参考.md",
}


def fix_doc_path(text):
    """在文本中替换所有旧文档路径片段为新路径。"""
    original = text

    # 1. 顶层特殊文件
    text = text.replace("docs/architecture.md", "docs/guide/11. 架构与概念/1. 架构总览.md")
    text = text.replace("docs/concepts.md", "docs/guide/11. 架构与概念/2. 核心概念.md")
    # 无 docs/ 前缀版本
    text = re.sub(r'(?<![/\w])architecture\.md(?!\w)', "guide/11. 架构与概念/1. 架构总览.md", text)

    # 2. guide/ 目录替换
    for old, new in GUIDE_DIR.items():
        text = text.replace(f"guide/{old}/", f"guide/{new}/")
        text = text.replace(f"guide/{old}`", f"guide/{new}`")

    # 3. reference/ 目录替换
    for old, new in REF_DIR.items():
        text = text.replace(f"reference/{old}/", f"reference/{new}/")
        text = text.replace(f"reference/{old}`", f"reference/{new}`")

    # 4. contributing/ 目录替换
    for old, new in CONTRIB_DIR.items():
        text = text.replace(f"contributing/{old}/", f"contributing/{new}/")
        text = text.replace(f"contributing/{old}`", f"contributing/{new}`")

    # 5. 子子目录替换 (在 guide 子目录内的 common/qq/bilibili/github)
    for parent in ["4. 消息发送", "5. API 使用", "1. Bot API"]:
        for old, new in SUB_DIR.items():
            text = text.replace(f"{parent}/{old}/", f"{parent}/{new}/")
            text = text.replace(f"{parent}/{old}`", f"{parent}/{new}`")

    # 6. 文件名替换 — 逐个匹配
    for old_file, new_file in FILE_MAP.items():
        text = text.replace(f"/{old_file}", f"/{new_file}")
        # 行首或路径开始
        if old_file in text:
            text = text.replace(old_file, new_file)

    return text


def main():
    total_files = 0
    total_changes = 0

    for root, dirs, files in os.walk(SKILLS_ROOT):
        for f in files:
            if not f.endswith(".md"):
                continue
            fpath = os.path.join(root, f)
            with open(fpath, encoding="utf-8") as fh:
                content = fh.read()

            new_content = fix_doc_path(content)

            if new_content != content:
                with open(fpath, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
                # Count changed lines
                old_lines = content.split("\n")
                new_lines = new_content.split("\n")
                changes = sum(1 for a, b in zip(old_lines, new_lines) if a != b)
                total_files += 1
                total_changes += changes
                rel = os.path.relpath(fpath, SKILLS_ROOT)
                print(f"  {changes:3d} lines  {rel}")

    print(f"\nTotal: {total_changes} lines changed in {total_files} files")


if __name__ == "__main__":
    main()
