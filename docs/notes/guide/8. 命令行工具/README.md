---
title: CLI 工具 — 命令行管理 NcatBot
createTime: 2026/03/19 17:26:45
permalink: /guide/txmbm7xd/
---

> 通过 `ncatbot` 命令完成项目初始化、启动、插件管理、适配器管理、配置管理和 NapCat 诊断。

## Quick Reference

安装 NcatBot 后即可使用 `ncatbot` 命令。

### 命令一览

| 命令 | 说明 |
|------|------|
| `ncatbot init [--dir PATH]` | 初始化项目（生成 config.yaml + plugins/ + 模板插件） |
| `ncatbot run [--debug] [--no-hot-reload] [--bot-uin] [--root] [--non-interactive]` | 启动 Bot |
| `ncatbot dev` | 开发模式启动（debug + 热重载） |
| `ncatbot` | 进入交互模式（REPL） |
| **配置管理** | |
| `ncatbot config show` | 显示完整配置 |
| `ncatbot config get <key>` | 读取配置值（支持点分路径） |
| `ncatbot config set <key> <value>` | 设置配置值（自动类型转换） |
| `ncatbot config check` | 检查配置安全性与必填项 |
| **插件管理** | |
| `ncatbot plugin list` | 列出已安装插件 |
| `ncatbot plugin create <name>` | 创建插件脚手架 |
| `ncatbot plugin info <name>` | 显示插件元信息 |
| `ncatbot plugin enable <name>` | 启用插件 |
| `ncatbot plugin disable <name>` | 禁用插件 |
| `ncatbot plugin remove <name>` | 删除插件 |
| `ncatbot plugin on` / `off` | 全局开关插件加载 |
| **适配器管理** | |
| `ncatbot adapter` | 进入副屏交互式适配器管理（启用/禁用/配置） |
| **NapCat 管理** | |
| `ncatbot napcat install [--yes]` | 安装 NapCat + QQ |
| `ncatbot napcat diagnose [ws\|webui]` | NapCat 连接诊断 |
| **参考资料** | |
| `ncatbot ref [--vscode\|--trae\|--cursor]` | 下载 AI 用户参考资料（按 IDE 适配） |

## 本目录索引

| 文件 | 说明 | 难度 |
|------|------|------|
| [1.commands.md](<1. 命令.md>) | 命令详解（初始化 / 启动 / 插件与配置管理） | ⭐ |

## 推荐阅读顺序

1. 先读 [命令详解](<1. 命令.md>) — 从零创建并运行 Bot，管理插件和配置
