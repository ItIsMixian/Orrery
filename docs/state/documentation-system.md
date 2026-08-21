# 文档系统 State

Updated: 2026-08-21
Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md) | [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md) | [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md) | [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md) | [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md) | [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md) | [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md)

## 当前事实

- Project Orrery 已在本仓库正式采纳自身权威链。
- Agent 入口是根 `AGENTS.md`；维护者入口是本目录 `README.md`、`PROGRESS.md` 与本地观测台。
- Seed、ADR、Approved Design、Implementation Plan、State、Validation 和 Snapshot 已各有独立职责。
- ADR-0009 已把这些职责、各对象 lifecycle、独立 Decision／Implementation／Validation claim dimensions、fact scopes、evidence categories 和 derived-view constraints 正式定义为 Authority Meta Model；`docs/core/principles.md` 明确只是 Project Orrery Product Seed。
- 文档事实现在显式区分 Canonical（integration ref 已集成）、Candidate（功能分支 HEAD）和 Worktree（本地未提交）三个作用域；分支 State 只能陈述候选事实，不能冒充 canonical 当前状态。
- 根 `PROGRESS.md` 与 `HANDOFF.md` 是集成视角入口。普通功能分支应让代码、测试和 subsystem State 同行，并在合流时由唯一整合者同步全局入口，避免多个 Agent 持续争写同一份全局状态。
- ADR-0008 已接受默认 zero-network Personal Mode、手动开启 Team Mode、Local-only 元数据和中央只读／本机执行边界；这些目前只是有效设计约束，现有观测台还没有 Workstream 指挥台、Team 页签、成员或同步实现。
- 根观测台由模板 v0.2.0 安装；其输出 `docs/_site/index.html` 为可重建生成物。
- 未发布 Core 包现持有 canonical 作者文档模板；Skill 下的 project-template 是兼容投影，测试要求作者模板内容一致。Observatory 工具不属于作者事实，并由独立组件清单管理。
- 未发布 Codex Adapter 只把 Codex 调用路由到目标仓库根 `AGENTS.md` 和平台中立 CLI；它不携带 State、ADR、Validation、canonical 模板或项目摘要，因此没有形成第二套文档事实。
- AI 问答、项目简报、路线综合、里程碑和趋势雷达保持可选，且没有事实权威。Candidate 动态观测台已给这些输出附加不可由模型覆盖的 `derived-ai-view` 非权威 receipt；问答另有可见提示。Authority report 缺失时保留 `Unknown`，Candidate shadow 也只作为 `shadow-only` context，不会被 AI 输出升级成 State、ADR、批准或 Validation。
- Authority 诊断页面与 sidecar 分开 opt-in：`ORRERY_AUTHORITY_SHADOW_REPORT` 只生成可丢弃 report，`ORRERY_AUTHORITY_SHADOW_VIEW=1` 才显示只读诊断面板。面板显式标注非权威／未切换，只展示 comparison health、scope 和计数，不展示或创造项目 claims。
- 动态观测台把 AI 服务设置入口放在顶栏、主题切换按钮左侧；静态 HTML 不注入设置入口，仍保持只读。
- 动态观测台的问答、仪表盘、趋势雷达、连接测试与独立 Q&A CLI 都只构造 Broker Provider；OpenAI、DeepSeek 和 Custom 只是上游注册项。项目 `ai-config.json` 的有效 Provider 恒为 `broker`。
- 默认本机托管 Broker 使用专用 Provider 凭据 namespace、client token、缓存、single-flight、模型白名单和预算门；一次“保存并启用”不强制额外测试请求。
- 本机托管只提供统一路由和成本控制，不隔离同一 OS 用户进程；只有在独立 OS 身份或等价外层隔离下运行外部 Broker 时才能隔离 Provider Key。
- 手动刷新、设置与问答写操作都要求同源 POST；旧查询参数 GET 不再触发模型调用。

## 同步状态

- Pilot 001–004 已在 Research State、DEVLOG、PROGRESS 和实验报告之间建立链接。
- 详细原始运行不复制进 Docs。
- 公开用户文档仍由 `README.md` 与 `README.zh-CN.md` 承担。

## 实现证据

- `AGENTS.md`
- `docs/decisions/0001-project-orrery-self-hosting.md`
- `docs/design/self-hosting-documentation-system.md`
- `scripts/docsite/build_docsite.py`
- `scripts/docsite/serve.py`
- `scripts/docsite/_llm.py`
- `scripts/docsite/llm_broker.py`
- `docs/decisions/0006-broker-only-docsite-provider-gateway.md`
- `docs/validation/2026-08-19-broker-first-docsite-gateway.md`
- `adapters/codex/SKILL.md`
- `adapters/codex/adapter-manifest.json`

## 已知缺口

- 当前观测台界面主要为中文，完整国际化仍未实施。
- 尚未建立自动检查 State 与实现链接是否过期的机制。
- 观测台尚未显示 branch、HEAD、integration OID、merge base、dirty、Workstream 生命周期或事实作用域；worktree 私有 session、自动重叠报告、审查包、清理建议和 Team Mode 也未实现。因此当前作用域纪律依赖入口规则、独立目录和集成者审阅。
- Authority Meta Model 已有 Candidate fixture、experimental Core evaluator、self-host 模型选择、managed shadow sidecar／诊断面板与 AI non-escalation guard，但仍无稳定公共 parser／domain API、默认 Authority 页面 projection、consumer production switch 或公开 release 实现。
