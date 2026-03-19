"""Remove permalink from all frontmatter in migrated files."""
import re
from pathlib import Path

root = Path(r"c:\Users\huany\Desktop\workspace\Projects\QQ-Bot\NcatBotDocs\docs\notes")
count = 0
for f in root.rglob("*.md"):
    content = f.read_text(encoding="utf-8")
    # Remove the permalink line (handle both \n and \r\n)
    new_content = re.sub(r"permalink:.*\r?\n", "", content, count=1)
    if new_content != content:
        f.write_text(new_content, encoding="utf-8")
        count += 1
        print(f"  Fixed: {f.relative_to(root)}")
print(f"\nRemoved permalink from {count} files")
