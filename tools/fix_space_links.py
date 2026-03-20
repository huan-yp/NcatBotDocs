"""
修复 docs/notes/ 下所有 Markdown 文件中 URL 含空格的断链。

问题：`[text](1. 快速开始/)` 中的空格导致 markdown-it 无法解析。
修复：`[text](<1. 快速开始/>)` — CommonMark 角括号语法。
"""

import os
import re


def fix_links_in_content(content: str) -> str:
    def replace_link(m: re.Match) -> str:
        text = m.group(1)
        url = m.group(2)
        if " " in url and not url.startswith("<"):
            return f"[{text}](<{url}>)"
        return m.group(0)

    return re.sub(r"\[([^\]]*)\]\(([^)]+)\)", replace_link, content)


def main():
    notes_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "notes")
    notes_dir = os.path.normpath(notes_dir)

    fixed_files = []
    for root, _dirs, files in os.walk(notes_dir):
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as fh:
                original = fh.read()
            fixed = fix_links_in_content(original)
            if fixed != original:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(fixed)
                count = sum(
                    1
                    for a, b in zip(original.split("\n"), fixed.split("\n"))
                    if a != b
                )
                rel = os.path.relpath(path, notes_dir)
                fixed_files.append((rel, count))

    print(f"Fixed {len(fixed_files)} files:")
    for rel, count in fixed_files:
        print(f"  {rel} ({count} lines changed)")


if __name__ == "__main__":
    main()
