# NcatBotDocs 自动文档生成

本项目包含了自动生成 AI 可读文档的功能，通过 pre-commit 钩子在每次提交前自动更新 `LLM.md` 文件。

## 功能特性

- 🚀 **自动化**: 每次 `git commit` 时自动生成最新文档
- 📝 **递归扫描**: 自动发现 `docs/notes/guide` 目录下所有 .md 文件
- 🔄 **手动触发**: 支持手动生成文档
- 🎯 **智能排序**: 按文件路径字母数字顺序排列
- 📊 **详细反馈**: 显示文件数量、大小等信息

## 快速开始

### 1. 安装 Git 钩子

```bash
npm run install:hooks
```

### 2. 手动生成文档

```bash
npm run generate:docs
```

### 3. 提交代码

```bash
git add .
git commit -m "更新文档"  # 会自动生成 LLM.md 并添加到提交中
git push
```

## 脚本说明

### NPM 脚本

- `npm run generate:docs` - 生成 AI 可读文档
- `npm run install:hooks` - 安装 Git pre-commit 钩子
- `npm run precommit` - Pre-commit 脚本（自动调用）

### 文件结构

```
scripts/
├── concat-md.js        # 主要的文档生成脚本
└── install-hooks.js    # Git 钩子安装脚本

.git/hooks/
└── pre-commit         # Git pre-commit 钩子
```

## 工作原理

1. **扫描文档**: 递归扫描 `docs/notes/guide` 目录
2. **文件排序**: 按路径字母数字顺序排列文件
3. **内容拼接**: 将所有 .md 文件内容拼接成一个大文件
4. **添加标题**: 为每个文件添加相对路径作为标题
5. **生成输出**: 保存为 `LLM.md` 文件

## 配置

### 修改输出文件名

编辑 `scripts/concat-md.js` 中的 `outputFilePath` 变量：

```javascript
const outputFilePath = path.join(__dirname, '../LLM.md');
```

### 修改扫描目录

编辑 `scripts/concat-md.js` 中的 `guideDir` 变量：

```javascript
const guideDir = path.join(__dirname, '../docs/notes/guide');
```

## 高级用法

### 跳过 Pre-commit 钩子

如果某次提交不想生成文档，可以使用：

```bash
git commit --no-verify -m "跳过文档生成"
```

### 手动运行 Pre-commit 钩子

```bash
.git/hooks/pre-commit
```

### 卸载钩子

删除钩子文件：

```bash
rm .git/hooks/pre-commit
```

## 故障排除

### 钩子不执行

- 确保 `.git/hooks/pre-commit` 文件存在且可执行
- 运行 `npm run install:hooks` 重新安装

### 文档生成失败

- 检查 `docs/notes/guide` 目录是否存在
- 确保 Node.js 版本支持 ES 模块
- 检查文件权限

### Windows 执行策略问题

如果 PowerShell 脚本无法执行，运行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个文档生成系统！