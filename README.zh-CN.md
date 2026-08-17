<div align="center">

# Project Orrery

**面向长期软件项目的可追溯文档系统与本地项目观测台。**

[English](README.md) · [简体中文](README.zh-CN.md)

[![Validate Project Orrery](https://github.com/yw9299-stack/project-orrery/actions/workflows/validate.yml/badge.svg)](https://github.com/yw9299-stack/project-orrery/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](skills/project-orrery/SKILL.md)

</div>

Project Orrery 是一套同时面向人类与软件 Agent 的仓库级项目记忆。它把本地 Markdown 组织成持续生长的项目观测台，让产品意图、架构决策、实施计划、当前状态和验证证据保持关联，同时避免把这些性质不同的信息误当成同一种事实。

项目以可迁移的 [Codex Skill](skills/project-orrery/) 形式发布，包含安全脚手架和本地文档阅读器。它既适合个人长期开发，也适合团队与多个 Agent 跨会话协作，尤其关注一个问题：最初对话消失很久以后，后来者还能否读懂一次改变为什么发生。

## 为什么需要 Project Orrery

Project Orrery 最初来自两个很实际的目标：

1. **保持意图连续。** Agent 应当能够长期贯彻人的产品方向，并追溯已经决定了什么、当时发生了什么冲突、为什么后来的决定替代了旧选择。
2. **保持状态可读。** 维护者或新 Agent 不应依靠旧聊天、散落文件和提交考古，才能判断项目现在正在做什么、已经做到哪里。

Git 很擅长保存版本，却不会主动说明某份文档是设想还是决策、某项决策是否仍然有效、已经批准的设计是否真的交付，以及什么证据能够证明当前状态。在 AI 辅助开发中，这种歧义会迅速累积：文件产出更快，过期方案继续存在，未来的 Agent 还可能很自信地读错事实源。

当多人协作时，这又会变成协调问题。Project Orrery 为提案、决策、计划、状态和证据提供职责稳定的文档位置，让并行工作汇入共享的项目记忆，而不是各自产生一套互相竞争的叙述。

Project Orrery 为不同知识赋予清晰职责：

![Project Orrery 文档系统架构](docs/assets/document-architecture.zh-CN.svg)

核心规则很简单：**已经接受不等于已经实现，列入计划也不等于已经证明。**

### 它是一套项目协议，而不是巨型 LLM Wiki

Project Orrery 的本体是服务于代码仓库与 Agent Harness 的权威模型和维护流程。AI 问答、综合分析与检索只是可选的读取层；它们无权决定什么是真的，也不能取代原始文档。

对于中小型仓库，分类明确的 Markdown、稳定的阅读入口、显式链接和直接搜索，通常比过早把全部资料切块并向量化更能保留上下文。等仓库规模真正需要时，可以再叠加全文索引、向量索引或 RAG，但这些索引始终是可重建、可替换的派生层。即使没有模型、外部数据库或托管服务，核心权威链仍然能够被阅读和维护。

## 主要能力

- **可追溯的权威模型**：以 Seed 原则、不可改写的 ADR 历史、已批准设计、实施计划、事实型 State Docs、验证记录和带日期快照组成完整链路。
- **安全的采纳流程**：支持预演；默认只创建缺失文件；明确区分安装、迁移和正式采纳，不会暗示目标仓库已经接受 Orrery 的权威模型。
- **非破坏式升级**：阅读器工具只允许从严格白名单更新；替换前会备份已有文件。
- **本地文档观测台**：提供可搜索的单文件阅读器、分类导航、文档健康信号和项目交接视图。
- **可选智能能力**：支持 AI 文档问答与综合分析，以及 GitHub 趋势雷达；不配置这些功能也能正常维护核心文档。
- **同时面向人和 Agent 的项目记忆**：为维护者与 Agent 提供清晰入口，同时不制造第二套互相竞争的事实源。
- **适合团队协作的稳定输出面**：并行贡献者分别写入不同职责的文档，减少提案、决策、计划与实际状态之间的意外冲突。

## 快速开始

### 1. 安装 Codex Skill

向 Codex 提出：

> Install Project Orrery from https://github.com/yw9299-stack/project-orrery/tree/main/skills/project-orrery

Skill 会从下一轮对话开始可用。你也可以把 [`skills/project-orrery`](skills/project-orrery/) 手动复制到 Codex 的 Skill 目录。

### 2. 审计并建立文档系统

打开目标仓库，然后告诉 Codex：

> 使用 Project Orrery 审计这个仓库。先展示 dry run，再建立文档观测台。

也可以直接通过命令行执行：

```bash
git clone https://github.com/yw9299-stack/project-orrery.git
python project-orrery/skills/project-orrery/scripts/install_project_orrery.py \
  --target /path/to/project \
  --title "我的项目" \
  --dry-run
```

检查所有 `CREATE`、`SKIP`、`UPGRADE` 和 mixed-toolchain 警告，再去掉 `--dry-run` 正式安装。

### 3. 验证安装结果

第一次结构验证不需要安装第三方依赖：

```bash
python project-orrery/skills/project-orrery/scripts/validate_installation.py \
  --target /path/to/project
```

安装脚手架不等于正式采纳权威模型。只有在目标项目接受自己的采纳 ADR，并更新真实的 Agent 入口、进度源和 State Docs 之后，才应使用 `--require-integrated`。

### 4. 启动本地观测台

进入目标仓库后运行：

```bash
python -m pip install -r scripts/docsite/requirements.txt
python -X utf8 scripts/docsite/serve.py
```

Windows 用户也可以运行 `start-docsite.bat`。服务默认只监听本机回环地址，并在 `8765` 至 `8784` 中选择可用端口。

#### 配置可选 AI 能力

在本地观测台中打开**问文档**，点击设置按钮即可进入图形化配置面板。面板支持 OpenAI、DeepSeek 和自定义 OpenAI 兼容服务，可配置 Base URL、默认模型、可选的意图／审计模型以及 API Key。

- API Key 只写入操作系统凭据存储，不会返回浏览器，也不会保存到 `ai-config.json`。
- 非敏感的服务商和模型配置保存到目标项目根目录下、已被 Git 忽略的 `ai-config.json`。
- **测试连接**会发起一次最小模型请求，可能产生少量服务商费用。
- 生成的静态阅读器 `docs/_site/index.html` 是只读的，不能写入凭据。
- 无界面或终端工作流仍可使用 `python scripts/docsite/set_key.py`。

如需同时验证静态阅读器构建：

```bash
python project-orrery/skills/project-orrery/scripts/validate_installation.py \
  --target /path/to/project \
  --build
```

## 采纳与升级安全

Project Orrery 对既有项目采取保守策略。

- 默认安装器只创建缺失文件。
- 脚手架不会覆盖已有的作者文档。
- 生成的采纳文档只是未编号提案，不是一条已经接受的 ADR。
- `--upgrade-tools` 只能替换白名单中的阅读器文件，并先生成带时间戳的备份。
- API Key、本地 AI 配置、缓存、生成站点、虚拟环境和机器专属路径都不应随 Skill 公开发布。
- Monorepo 或多根项目应把 Orrery 安装到文档权威根；不需要为了适配模板而移动实际实现。

在迁移成熟文档系统前，请阅读完整的[架构说明](skills/project-orrery/references/architecture.md)与[迁移契约](skills/project-orrery/references/migration-contract.md)。

## 仓库结构

| 路径 | 用途 |
|---|---|
| [`skills/project-orrery/SKILL.md`](skills/project-orrery/SKILL.md) | Codex Skill 入口与操作规则 |
| [`skills/project-orrery/scripts/`](skills/project-orrery/scripts/) | 安全安装器与安装验证器 |
| [`skills/project-orrery/assets/project-template/`](skills/project-orrery/assets/project-template/) | 可迁移文档脚手架与本地阅读器 |
| [`skills/project-orrery/references/`](skills/project-orrery/references/) | 权威架构与迁移契约 |
| [`tests/`](tests/) | 隔离安装和升级烟雾测试 |
| [`.github/workflows/validate.yml`](.github/workflows/validate.yml) | Windows 与 Linux 持续验证 |

## 可选能力与隐私

静态阅读器和文档权威模型不依赖 AI 服务。AI 文档问答、路线图综合和里程碑视图需要由目标项目自行提供服务商配置；动态本地观测台提供图形化配置面板，密钥仍只保存在操作系统凭据存储中。趋势雷达可以使用 GitHub Search，并可选接入网页搜索。

观测台默认只在本地运行。Project Orrery 不包含托管服务、遥测收集器或预置凭据。启用可选联网能力前，请先审查目标项目的服务商和网络配置。

## 当前状态

Project Orrery 目前处于早期公开版本。迁移契约、安装器安全规则、隔离烟雾测试、静态构建、图形化 AI 服务配置以及 Windows／Linux CI 已可运行。当前阅读器界面以中文为主，但仓库内容可以使用任意语言；更完整的阅读器国际化将作为独立工作推进，不与本次双语项目说明混为一谈。

## 参与贡献

欢迎提交 Issue 和 Pull Request。贡献内容应保持可迁移性，避免加入特定项目假设，并继续遵守非破坏式迁移契约。

提交 PR 前请运行本地烟雾测试：

```bash
python -m unittest discover -s tests -v
```

安装模板阅读器依赖后，可以设置 `ORRERY_TEST_BUILD=1`，把静态站点构建纳入测试。GitHub Actions 会在 Windows 和 Ubuntu 上执行完整验证。

## 许可证

Project Orrery 使用 [MIT License](LICENSE) 发布。
