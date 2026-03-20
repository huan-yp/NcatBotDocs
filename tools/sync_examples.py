"""
同步 docs/docs/examples 中的源码文件（.py / .toml）和对应 README.md 中的代码块。

用法:
    python docs/tools/sync_examples.py [--dry-run] [--examples-dir PATH]

选项:
    --dry-run        仅显示差异，不写入文件
    --examples-dir   examples 目录路径（默认：docs/docs/examples，相对于脚本位置推断）

工作流:
    1. 遍历 examples 中每个 platform/example_name 二级目录
    2. 对每个包含 README.md 的目录：
       a. 更新 ## 文件结构 代码块（反映真实文件列表）
       b. 对每个 .py/.toml 源文件，更新 README 中对应的 ## filename 代码块
       c. 若 README 中没有该文件的代码块，则追加到末尾
    3. 报告：更新了哪些 README，哪些已是最新
"""

import argparse
import re
import sys
from pathlib import Path

# ── 配置 ───────────────────────────────────────────────────────────────────────

# 按此顺序处理（决定新追加的代码块在 README 中的排列顺序）
SOURCE_EXTENSIONS = [".py", ".toml"]

# 扩展名 → Markdown 代码块语言标识
LANG_MAP: dict[str, str] = {
    ".py": "python",
    ".toml": "toml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "bash",
}

FENCE = "~~~"  # VuePress Plume 主题惯例，用 ~~~ 而非 ```

# ──────────────────────────────────────────────────────────────────────────────


def make_file_tree(example_dir: Path) -> str:
    """生成该示例目录的文件树字符串（仅列一级，跳过 README.md）。"""
    items = sorted(
        [e for e in example_dir.iterdir() if e.name != "README.md"],
        key=lambda p: (p.is_file(), p.name),
    )
    lines = [f"{example_dir.name}/"]
    for i, item in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "
        lines.append(f"{connector}{item.name}{'/' if item.is_dir() else ''}")
    return "\n".join(lines)


def get_source_files(example_dir: Path) -> list[Path]:
    """返回该目录下需要嵌入 README 的源文件列表（按扩展名顺序，同扩展名按文件名排序）。"""
    files: list[Path] = []
    for ext in SOURCE_EXTENSIONS:
        files.extend(sorted(example_dir.glob(f"*{ext}")))
    return files


def get_lang(filepath: Path) -> str:
    return LANG_MAP.get(filepath.suffix, "text")


# ── 核心：更新单个 README ─────────────────────────────────────────────────────

# 匹配形如:
#   ## <section_name>
#   <可选空行>
#   ~~~<lang>
#   <body>
#   ~~~
_SECTION_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}


def _section_pattern(section_name: str) -> re.Pattern[str]:
    if section_name not in _SECTION_PATTERN_CACHE:
        _SECTION_PATTERN_CACHE[section_name] = re.compile(
            r"(##\s+" + re.escape(section_name) + r"\s*\n)"  # ## heading
            r"(\n*)"                                           # optional blank lines
            r"(" + re.escape(FENCE) + r")[^\n]*\n"            # opening ~~~lang
            r"(.*?)"                                           # body (non-greedy)
            r"(" + re.escape(FENCE) + r"(?:\n|$))",           # closing ~~~
            re.DOTALL,
        )
    return _SECTION_PATTERN_CACHE[section_name]


def update_section_codeblock(
    content: str,
    section_name: str,
    lang: str,
    new_body: str,
) -> str:
    """
    将 content 中 `## section_name` 后的第一个围栏代码块替换为新内容。
    若该节不存在，则追加到文件末尾。
    """
    block = f"{FENCE}{lang}\n{new_body}{FENCE}\n"

    def _replace(m: re.Match[str]) -> str:
        return m.group(1) + m.group(2) + block

    new_content, count = _section_pattern(section_name).subn(_replace, content, count=1)
    if count == 0:
        # 节不存在 → 追加
        trailing = "" if content.endswith("\n\n") else ("\n" if content.endswith("\n") else "\n\n")
        new_content = content + trailing + f"## {section_name}\n\n{block}"

    return new_content


def update_readme(readme_path: Path, example_dir: Path, dry_run: bool) -> bool:
    """
    原地更新 README.md：
      1. ## 文件结构 → 反映真实目录内容
      2. ## <filename> 各节 → 嵌入最新源码

    返回 True 表示内容有变化（或 dry_run 时检测到变化）。
    """
    original = readme_path.read_text(encoding="utf-8")
    content = original

    # 1. 文件结构
    content = update_section_codeblock(content, "文件结构", "text", make_file_tree(example_dir) + "\n")

    # 2. 各源文件
    for src in get_source_files(example_dir):
        file_body = src.read_text(encoding="utf-8")
        # 保证末尾只有一个换行
        file_body = file_body.rstrip("\n") + "\n"
        content = update_section_codeblock(content, src.name, get_lang(src), file_body)

    if content == original:
        return False

    if not dry_run:
        readme_path.write_text(content, encoding="utf-8")
    return True


# ── 入口 ──────────────────────────────────────────────────────────────────────


def sync_examples(examples_dir: Path, dry_run: bool) -> int:
    """同步整个 examples 目录，返回实际更新（或 dry-run 检测到需更新）的文件数。"""
    changed: list[Path] = []
    skipped: list[Path] = []
    missing_readme: list[Path] = []

    for platform_dir in sorted(examples_dir.iterdir()):
        if not platform_dir.is_dir() or platform_dir.name.startswith("."):
            continue
        for example_dir in sorted(platform_dir.iterdir()):
            if not example_dir.is_dir():
                continue
            readme = example_dir / "README.md"
            if not readme.exists():
                missing_readme.append(example_dir.relative_to(examples_dir))
                continue
            modified = update_readme(readme, example_dir, dry_run)
            rel = readme.relative_to(examples_dir.parent.parent)
            (changed if modified else skipped).append(rel)

    # ── 报告 ──
    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}同步结果:")
    if changed:
        verb = "检测到需更新" if dry_run else "已更新"
        print(f"  {verb}: {len(changed)} 个 README")
        for f in changed:
            print(f"    ✏️  {f}")
    if skipped:
        print(f"  无需更新: {len(skipped)} 个 README")
    if missing_readme:
        print(f"  ⚠️  缺少 README（已跳过）:")
        for d in missing_readme:
            print(f"    {d}")

    return len(changed)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="同步 examples 目录源码文件（.py/.toml）到对应 README.md 代码块",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="只检测变更，不写入文件")
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=None,
        help="examples 目录路径（默认：docs/docs/examples，相对于脚本位置推断）",
    )
    args = parser.parse_args()

    if args.examples_dir:
        examples_dir = args.examples_dir.resolve()
    else:
        # 脚本位于 docs/tools/，向上一级 → docs/，再进 docs/examples/
        script_dir = Path(__file__).resolve().parent
        examples_dir = (script_dir.parent / "docs" / "examples").resolve()

    if not examples_dir.exists():
        print(f"❌ 目录不存在: {examples_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"examples 目录: {examples_dir}")
    if args.dry_run:
        print("模式: DRY-RUN（不写入文件）")

    n = sync_examples(examples_dir, dry_run=args.dry_run)
    sys.exit(0 if (not args.dry_run or n == 0) else 1)


if __name__ == "__main__":
    main()
