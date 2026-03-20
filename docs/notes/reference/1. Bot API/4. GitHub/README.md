---
title: GitHub API 参考
createTime: 2026/03/19 17:26:45
permalink: /reference/b8v2e8d2/
---

> GitHubBotAPI 完整方法签名与参数说明。

---

## Quick Reference

```python
api.github.create_issue(repo="owner/repo", title="Bug")
api.github.create_issue_comment(repo="owner/repo", issue_number=1, body="Fixed")
api.github.merge_pr(repo="owner/repo", pr_number=42)
api.github.get_repo(repo="owner/repo")
```

## 本目录索引

| 文件 | 说明 |
|------|------|
| [GitHub API 方法](<1. API.md>) | Issue / Comment / PR / Query 四大 Mixin 共 20 个方法的完整签名 |

> 用法示例请查阅 [guide/api_usage/github/](<../../../guide/5. API 使用/4. GitHub/>)。
