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

Project Orrery 经历了两个阶段，最初都来自一种非常具体的感受：在个人项目中，Agent 不断生成源码和文档，但这些文件的用途、权威性和相互关系越来越难以判断，最终让维护者对自己的代码库产生强烈的失控感。

### 第一阶段：区分阅读界面，但不分裂事实

第一个设计启发是：Agent 和人类进入项目时需要的信息并不相同。Agent 需要精确的导航、当前约束、文件级事实和安全的下一步；人类更需要解释、决策背景、里程碑和清晰的全局概览。把同一堆没有分工的文档同时交给两类读者，对谁都不友好。

因此，Project Orrery 区分的是**面向不同读者的入口与视图**，而不是底层事实。`AGENTS.md`、State 地图和操作性交接帮助 Agent 定位；叙事型文档与项目观测台帮助人类理解。两条阅读路径最终都回到同一组 Seed、有效 ADR、实际实现、当前 State 和验证证据。这是恢复控制感的第一层机制：Agent 可以在明确边界内行动，维护者也能看见项目为什么朝这个方向推进。

### 第二阶段：把文档增长转化为项目可观测性

随着项目继续推进，即使是专门面向人类的文档也越来越多，关键决定、里程碑、优先级和仓库全局状态再次开始变得模糊。此时需要的已经不是更多文档，而是一个项目级仪表盘。

本地观测台由此产生。它通过结构化文档，并可选调用专门的模型 API，生成总览、路线、里程碑、健康度和趋势视图，帮助维护者判断项目在哪里、什么值得关注以及接下来如何规划。所有综合结果都必须能够回到原始文档；仪表盘只是投影与导航层，不能成为新的事实源。

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

> Install the tagged Project Orrery v0.2.0 Skill from https://github.com/yw9299-stack/project-orrery/tree/v0.2.0/skills/project-orrery

Skill 会从下一轮对话开始可用。请通过 [GitHub 最新发布页](https://github.com/yw9299-stack/project-orrery/releases/latest)确认当前稳定标签。你也可以先验证发布包的 SHA-256 校验和，再把其中的 `project-orrery` 文件夹手动复制到 Codex Skill 目录。

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

## 更新通知与兼容性

Project Orrery 可以提醒用户存在新的稳定版 Skill，但不会静默修改已安装 Skill 或项目文档。对已经安装 Orrery 的项目使用该 Skill 时，工作流默认最多每 24 小时执行一次只读更新检查；如果用户要求离线，则不会访问网络：

```bash
python /path/to/project-orrery-skill/scripts/check_project_orrery_update.py \
  --target /path/to/project
```

检查结果会明确区分**可直接兼容更新**、**需要迁移审查**、**本地版本比稳定版更新**、**当前目标不兼容**和**无法得知最新版本**。网络失败不会阻塞普通文档工作；检查器可以使用缓存，也可以显式传入 `--offline`。

兼容性不会被压缩成一个含糊的版本号：

| 版本维度 | 表示什么 |
|---|---|
| Skill 版本 | Agent 工作流、安装器、验证器和发布工具 |
| 目标工具链版本 | 项目内实际安装的观测台托管文件 |
| 项目清单格式 | `.project-orrery.json` 的机器可读结构 |
| 文档架构版本 | 作者文档中被当前版本理解的权威职责 |

Project Orrery 遵循语义化版本，但是否能够直接兼容，以机器可读的 [`release-manifest.json`](skills/project-orrery/release-manifest.json) 为准。补丁版和次版本以保持兼容为目标；主版本可能需要显式迁移。任何版本都无权批量改写项目作者文档。

如果希望主动收到版本通知，可在 [GitHub 仓库](https://github.com/yw9299-stack/project-orrery)选择 **Watch → Custom → Releases**。正式发布包来自不可变标签，并附带 SHA-256 校验和。先安装精确标签对应的新 Skill，再单独预演目标项目的阅读器升级：

```bash
python /path/to/new-project-orrery-skill/scripts/install_project_orrery.py \
  --target /path/to/project \
  --upgrade-tools \
  --dry-run
```

确认兼容性和备份位置后才能正式应用。已有 v0.1 安装需要有意识地升级一次到 v0.2 或更高版本，才能获得更新检查器；完成这次引导后，每次使用 Skill 都会按缓存周期报告后续稳定版。由于 Skill 安装器通常不会覆盖已存在目录，正确做法是先下载到临时位置、验证并备份，而不是先删除仍可工作的旧 Skill。

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
| [`skills/project-orrery/release-manifest.json`](skills/project-orrery/release-manifest.json) | 稳定发布与兼容性契约 |
| [`skills/project-orrery/scripts/`](skills/project-orrery/scripts/) | 安全安装器与安装验证器 |
| [`skills/project-orrery/assets/project-template/`](skills/project-orrery/assets/project-template/) | 可迁移文档脚手架与本地阅读器 |
| [`skills/project-orrery/references/`](skills/project-orrery/references/) | 权威架构与迁移契约 |
| [`tests/`](tests/) | 隔离安装和升级烟雾测试 |
| [`.github/workflows/validate.yml`](.github/workflows/validate.yml) | Windows 与 Linux 持续验证 |
| [`.github/workflows/release.yml`](.github/workflows/release.yml) | 标签发布的打包与公开流程 |

## 可选能力与隐私

静态阅读器和文档权威模型不依赖 AI 服务。AI 文档问答、路线图综合和里程碑视图需要由目标项目自行提供服务商配置；动态本地观测台提供图形化配置面板，密钥仍只保存在操作系统凭据存储中。趋势雷达可以使用 GitHub Search，并可选接入网页搜索。

观测台默认只在本地运行。Project Orrery 不包含托管服务、遥测收集器或预置凭据。启用可选联网能力前，请先审查目标项目的服务商和网络配置。

## 当前状态

Project Orrery 目前处于早期公开版本。迁移契约、安装器安全规则、带缓存的兼容性检查器、版本化发布打包、隔离烟雾测试、静态构建、图形化 AI 服务配置以及 Windows／Linux CI 已可运行。当前阅读器界面以中文为主，但仓库内容可以使用任意语言；更完整的阅读器国际化将作为独立工作推进，不与本次双语项目说明混为一谈。

## 参与贡献

欢迎提交 Issue 和 Pull Request。贡献内容应保持可迁移性，避免加入特定项目假设，并继续遵守非破坏式迁移契约。

提交 PR 前请运行本地烟雾测试：

```bash
python -m unittest discover -s tests -v
```

安装模板阅读器依赖后，可以设置 `ORRERY_TEST_BUILD=1`，把静态站点构建纳入测试。GitHub Actions 会在 Windows 和 Ubuntu 上执行完整验证。

## 许可证

Project Orrery 使用 [MIT License](LICENSE) 发布。
