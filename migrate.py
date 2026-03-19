"""
NcatBot docs -> NcatBotDocs VuePress migration script.

Reads all .md files from NcatBot/docs/, transforms them to VuePress 2 + Plume theme
format, and writes them to NcatBotDocs/docs/notes/ with proper directory structure,
frontmatter, and container syntax.
"""

import os
import re
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

# === Paths ===
SRC_ROOT = Path(r"c:\Users\huany\Desktop\workspace\Projects\QQ-Bot\NcatBot\docs")
DST_ROOT = Path(r"c:\Users\huany\Desktop\workspace\Projects\QQ-Bot\NcatBotDocs\docs\notes")

# === Directory mapping ===
# Maps source relative paths to destination directory names.
# Format: (src_prefix, dst_prefix)

GUIDE_DIR_MAP = {
    "guide/quick_start": "guide/1. 快速开始",
    "guide/adapter": "guide/2. 适配器",
    "guide/plugin": "guide/3. 插件开发",
    "guide/send_message": "guide/4. 消息发送",
    "guide/send_message/common": "guide/4. 消息发送/1. 通用",
    "guide/send_message/qq": "guide/4. 消息发送/2. QQ",
    "guide/send_message/bilibili": "guide/4. 消息发送/3. Bilibili",
    "guide/send_message/github": "guide/4. 消息发送/4. GitHub",
    "guide/api_usage": "guide/5. API 使用",
    "guide/api_usage/common": "guide/5. API 使用/1. 通用",
    "guide/api_usage/qq": "guide/5. API 使用/2. QQ",
    "guide/api_usage/bilibili": "guide/5. API 使用/3. Bilibili",
    "guide/api_usage/github": "guide/5. API 使用/4. GitHub",
    "guide/configuration": "guide/6. 配置管理",
    "guide/rbac": "guide/7. RBAC 权限",
    "guide/cli": "guide/8. 命令行工具",
    "guide/testing": "guide/9. 测试指南",
    "guide/multi_platform": "guide/10. 多平台开发",
}

REF_DIR_MAP = {
    "reference/api": "reference/1. Bot API",
    "reference/api/common": "reference/1. Bot API/1. 通用",
    "reference/api/qq": "reference/1. Bot API/2. QQ",
    "reference/api/bilibili": "reference/1. Bot API/3. Bilibili",
    "reference/api/github": "reference/1. Bot API/4. GitHub",
    "reference/events": "reference/2. 事件类型",
    "reference/types": "reference/3. 数据类型",
    "reference/core": "reference/4. 核心模块",
    "reference/plugin": "reference/5. 插件系统",
    "reference/services": "reference/6. 服务层",
    "reference/adapter": "reference/7. 适配器",
    "reference/utils": "reference/8. 工具模块",
    "reference/testing": "reference/9. 测试框架",
}

CONTRIB_DIR_MAP = {
    "contributing/development_setup": "contributing/1. 开发环境",
    "contributing/design_decisions": "contributing/2. 设计决策",
    "contributing/module_internals": "contributing/3. 模块内部实现",
}

ALL_DIR_MAP = {}
ALL_DIR_MAP.update(GUIDE_DIR_MAP)
ALL_DIR_MAP.update(REF_DIR_MAP)
ALL_DIR_MAP.update(CONTRIB_DIR_MAP)

# === File name mapping ===
# Maps source filename (without path) to target Chinese filename.
# Only non-README files need mapping. README.md stays as README.md.

FILE_NAME_MAP = {
    # guide/quick_start
    "1.install-config.md": "1. 安装与配置.md",
    "2.non-plugin-mode.md": "2. 非插件模式.md",
    "3.plugin-mode.md": "3. 插件模式.md",
    # guide/adapter
    "1_napcat_qq.md": "1. NapCat QQ.md",
    "2_bilibili.md": "2. Bilibili.md",
    "3_github.md": "3. GitHub.md",
    "4_mock.md": "4. Mock 适配器.md",
    # guide/plugin
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
    # guide/send_message/common
    "1_segments.md": "1. 消息段.md",
    "2_array.md": "2. 消息数组.md",
    # guide/send_message/qq
    "1_sugar.md": "1. 语法糖.md",
    "2_forward.md": "2. 合并转发.md",
    "3_examples.md": "3. 示例.md",
    # guide/send_message/bilibili & github
    "1_messaging.md": "1. 消息发送.md",
    # guide/api_usage/common
    "1_event_methods.md": "1. 事件方法.md",
    "2_traits.md": "2. Traits.md",
    # guide/api_usage/qq
    # "1_messaging.md" already mapped
    "2_manage.md": "2. 群管理.md",
    "3_query_support.md": "3. 查询与支持.md",
    # guide/api_usage/bilibili
    "1_live_room.md": "1. 直播间.md",
    "2_private_msg.md": "2. 私信.md",
    "3_comment.md": "3. 评论.md",
    "4_source_query.md": "4. 源查询.md",
    # guide/api_usage/github
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
    # reference/api/common
    "traits.md": "1. Traits.md",
    # reference/api/qq
    "1_message_api.md": "1. 消息 API.md",
    "2_manage_api.md": "2. 管理 API.md",
    "3_info_support_api.md": "3. 信息支持 API.md",
    # reference/api/bilibili
    "1_api.md": "1. API.md",
    # reference/api/github
    # "1_api.md" already mapped
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
    # contributing/development_setup
    "1_advanced.md": "1. 高级设置.md",
    # contributing/design_decisions
    "1_architecture.md": "1. 架构决策.md",
    "2_implementation.md": "2. 实现决策.md",
    "3_types.md": "3. 类型决策.md",
    # contributing/module_internals
    "1.core_modules.md": "1. 核心模块.md",
    "2.plugin_service_modules.md": "2. 插件服务模块.md",
}

# === Permalink generation ===
# Generate semantic permalinks based on section + slug

def make_permalink(section: str, src_rel: str) -> str:
    """Generate a semantic permalink from the source relative path."""
    # Remove .md extension
    slug = src_rel.replace("\\", "/").replace(".md", "")
    # Remove leading section prefix (guide/, reference/, contributing/)
    for prefix in ["guide/", "reference/", "contributing/"]:
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
            break
    # Clean up slug
    slug = slug.replace("/", "-").replace("_", "-").replace(".", "-")
    # Remove leading numbers and dots
    slug = re.sub(r'(\d+[a-z]?)-', lambda m: m.group(0), slug)
    # Make it URL-friendly
    slug = re.sub(r'-+', '-', slug).strip('-').lower()
    # Generate short hash for uniqueness
    h = hashlib.md5(src_rel.encode()).hexdigest()[:8]
    return f"/{section}/{h}/"


# === Content transformation ===

def extract_h1_title(content: str) -> tuple[str, str]:
    """Extract the first H1 title and return (title, content_without_h1)."""
    lines = content.split('\n')
    new_lines = []
    title = None
    found = False
    for line in lines:
        if not found and line.startswith('# ') and not line.startswith('##'):
            title = line[2:].strip()
            found = True
            # Skip the line after H1 if it's empty
            continue
        new_lines.append(line)
    
    # Remove leading empty lines after H1 removal
    while new_lines and new_lines[0].strip() == '':
        new_lines.pop(0)
    
    return title or "Untitled", '\n'.join(new_lines)


def convert_blockquote_containers(content: str) -> str:
    """Convert blockquote-style tips/warnings to VuePress container syntax."""
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for blockquote container patterns
        # Pattern: > **提示**：... or > **注意**：... or > **重要**：...
        match = re.match(r'^>\s*\*\*(提示|注意|重要|警告|版本|信息)\*\*[：:]\s*(.*)', line)
        if match:
            label = match.group(1)
            first_content = match.group(2)
            
            container_type = {
                '提示': 'tip',
                '信息': 'info',
                '版本': 'info',
                '注意': 'warning',
                '警告': 'warning',
                '重要': 'caution',
            }.get(label, 'tip')
            
            # Collect all continuation lines of this blockquote
            container_lines = []
            if first_content.strip():
                container_lines.append(first_content.strip())
            
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                cont = lines[i][1:].strip()
                if cont:
                    container_lines.append(cont)
                else:
                    container_lines.append('')
                i += 1
            
            result.append(f'::: {container_type}')
            for cl in container_lines:
                result.append(cl)
            result.append(':::')
            result.append('')
            continue
        
        # Also handle metadata badges like > **版本**: 5.2.0 | **Python**: >= 3.12
        match2 = re.match(r'^>\s*\*\*版本\*\*[：:]\s*(.*)', line)
        if match2:
            badge_content = match2.group(1)
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                badge_content += ' ' + lines[i][1:].strip()
                i += 1
            result.append(f'::: info 版本信息')
            result.append(badge_content.strip())
            result.append(':::')
            result.append('')
            continue
        
        result.append(line)
        i += 1
    
    return '\n'.join(result)


def add_frontmatter(content: str, title: str, permalink: str) -> str:
    """Add YAML frontmatter to the content."""
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    # Quote title if it contains special YAML characters
    if ':' in title or '#' in title or title.startswith('{') or title.startswith('['):
        # Remove colons from title to avoid YAML issues with Plume autoFrontmatter
        title = title.replace(':', ' -')
    safe_title = title
    frontmatter = f"""---
title: {safe_title}
createTime: {now}
permalink: {permalink}
---

"""
    return frontmatter + content


def get_dst_dir(src_rel_dir: str) -> str:
    """Get the destination directory for a source relative directory path."""
    src_rel_dir = src_rel_dir.replace("\\", "/").rstrip("/")
    
    # Sort by longest match first (most specific)
    sorted_maps = sorted(ALL_DIR_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    
    for src_prefix, dst_prefix in sorted_maps:
        if src_rel_dir == src_prefix:
            return dst_prefix
    
    # Fallback: direct mapping
    return src_rel_dir


def get_dst_filename(src_filename: str, src_rel_dir: str) -> str:
    """Get the destination filename for a source file."""
    if src_filename == "README.md":
        return "README.md"
    
    # Check for context-specific mapping first (using directory to disambiguate)
    # Some filenames like "1_messaging.md" appear in multiple directories
    src_rel = src_rel_dir.replace("\\", "/")
    
    # Special context-aware mappings for duplicate filenames
    context_map = {
        ("guide/api_usage/qq", "1_messaging.md"): "1. 消息发送.md",
        ("guide/api_usage/bilibili", "1_live_room.md"): "1. 直播间.md",
        ("guide/api_usage/bilibili", "2_private_msg.md"): "2. 私信.md",
        ("guide/api_usage/bilibili", "3_comment.md"): "3. 评论.md",
        ("guide/api_usage/bilibili", "4_source_query.md"): "4. 源查询.md",
        ("guide/api_usage/github", "1_issue_comment.md"): "1. Issue 评论.md",
        ("guide/api_usage/github", "2_pr_query.md"): "2. PR 查询.md",
        ("guide/send_message/bilibili", "1_messaging.md"): "1. 消息发送.md",
        ("guide/send_message/github", "1_messaging.md"): "1. 消息发送.md",
        ("reference/api/bilibili", "1_api.md"): "1. API.md",
        ("reference/api/github", "1_api.md"): "1. API.md",
    }
    
    key = (src_rel, src_filename)
    if key in context_map:
        return context_map[key]
    
    return FILE_NAME_MAP.get(src_filename, src_filename)


def process_file(src_path: Path, src_rel: str) -> tuple[Path, str]:
    """Process a single file: read, transform, return (dst_path, content)."""
    content = src_path.read_text(encoding='utf-8')
    
    src_rel_normalized = src_rel.replace("\\", "/")
    src_dir = str(Path(src_rel_normalized).parent)
    src_filename = Path(src_rel_normalized).name
    
    # Determine section
    if src_rel_normalized.startswith("guide/"):
        section = "guide"
    elif src_rel_normalized.startswith("reference/"):
        section = "reference"
    elif src_rel_normalized.startswith("contributing/"):
        section = "contributing"
    else:
        section = "concepts"
    
    # Get destination directory and filename
    dst_dir = get_dst_dir(src_dir)
    dst_filename = get_dst_filename(src_filename, src_dir)
    dst_path = DST_ROOT / dst_dir / dst_filename
    
    # Transform content
    title, content = extract_h1_title(content)
    content = convert_blockquote_containers(content)
    
    # Generate permalink
    permalink = make_permalink(section, src_rel_normalized)
    
    # Add frontmatter
    content = add_frontmatter(content, title, permalink)
    
    return dst_path, content


def main():
    # === Step 1: Clean old guide content ===
    old_guide = DST_ROOT / "guide"
    if old_guide.exists():
        print(f"Removing old guide content: {old_guide}")
        shutil.rmtree(old_guide)
    
    # Clean old reference/contributing if they exist
    for d in ["reference", "contributing"]:
        old_dir = DST_ROOT / d
        if old_dir.exists():
            print(f"Removing old {d} content: {old_dir}")
            shutil.rmtree(old_dir)
    
    # === Step 2: Collect all source files ===
    src_files = []
    
    # Guide files
    guide_dir = SRC_ROOT / "guide"
    if guide_dir.exists():
        for md_file in guide_dir.rglob("*.md"):
            rel = md_file.relative_to(SRC_ROOT)
            src_files.append((md_file, str(rel)))
    
    # Reference files
    ref_dir = SRC_ROOT / "reference"
    if ref_dir.exists():
        for md_file in ref_dir.rglob("*.md"):
            rel = md_file.relative_to(SRC_ROOT)
            src_files.append((md_file, str(rel)))
    
    # Special case: reference/cli.md -> reference/10. CLI/1. 命令参考.md
    cli_md = SRC_ROOT / "reference" / "cli.md"
    # Already included above, handle in mapping
    
    # Contributing files
    contrib_dir = SRC_ROOT / "contributing"
    if contrib_dir.exists():
        for md_file in contrib_dir.rglob("*.md"):
            rel = md_file.relative_to(SRC_ROOT)
            src_files.append((md_file, str(rel)))
    
    # Top-level concept files
    for name in ["architecture.md", "concepts.md"]:
        f = SRC_ROOT / name
        if f.exists():
            src_files.append((f, name))
    
    # === Step 3: Process and write ===
    processed = 0
    errors = []
    
    for src_path, src_rel in src_files:
        try:
            # Skip meta/
            if src_rel.replace("\\", "/").startswith("meta/"):
                continue
            # Skip top-level README.md (docs index, not needed)
            if src_rel == "README.md":
                continue
            # Skip guide/README.md (will create a new one)
            if src_rel.replace("\\", "/") == "guide/README.md":
                # Process it normally
                pass
            
            # Special handling for reference/cli.md
            src_rel_normalized = src_rel.replace("\\", "/")
            if src_rel_normalized == "reference/cli.md":
                content = src_path.read_text(encoding='utf-8')
                title, content = extract_h1_title(content)
                content = convert_blockquote_containers(content)
                permalink = make_permalink("reference", src_rel_normalized)
                content = add_frontmatter(content, title, permalink)
                dst_path = DST_ROOT / "reference" / "10. CLI" / "1. 命令参考.md"
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                dst_path.write_text(content, encoding='utf-8')
                processed += 1
                print(f"  [OK] {src_rel} → {dst_path.relative_to(DST_ROOT)}")
                continue
            
            # Special handling for top-level concept files
            if src_rel_normalized == "architecture.md":
                content = src_path.read_text(encoding='utf-8')
                title, content = extract_h1_title(content)
                content = convert_blockquote_containers(content)
                permalink = "/concepts/architecture/"
                content = add_frontmatter(content, title, permalink)
                dst_path = DST_ROOT / "guide" / "11. 架构与概念" / "1. 架构总览.md"
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                dst_path.write_text(content, encoding='utf-8')
                processed += 1
                print(f"  [OK] {src_rel} → {dst_path.relative_to(DST_ROOT)}")
                continue
            
            if src_rel_normalized == "concepts.md":
                content = src_path.read_text(encoding='utf-8')
                title, content = extract_h1_title(content)
                content = convert_blockquote_containers(content)
                permalink = "/concepts/core-concepts/"
                content = add_frontmatter(content, title, permalink)
                dst_path = DST_ROOT / "guide" / "11. 架构与概念" / "2. 核心概念.md"
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                dst_path.write_text(content, encoding='utf-8')
                processed += 1
                print(f"  [OK] {src_rel} → {dst_path.relative_to(DST_ROOT)}")
                continue
            
            dst_path, content = process_file(src_path, src_rel)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path.write_text(content, encoding='utf-8')
            processed += 1
            print(f"  [OK] {src_rel} → {dst_path.relative_to(DST_ROOT)}")
            
        except Exception as e:
            errors.append((src_rel, str(e)))
            print(f"  [ERR] {src_rel}: {e}")
    
    print(f"\n=== Migration complete ===")
    print(f"Processed: {processed} files")
    if errors:
        print(f"Errors: {len(errors)}")
        for rel, err in errors:
            print(f"  - {rel}: {err}")
    else:
        print("No errors!")


if __name__ == "__main__":
    main()
