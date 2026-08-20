# 文档系统 State

Updated: 2026-08-19
Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md) | [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md) | [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md) | [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md)

## 当前事实

- Project Orrery 已在本仓库正式采纳自身权威链。
- Agent 入口是根 `AGENTS.md`；维护者入口是本目录 `README.md`、`PROGRESS.md` 与本地观测台。
- Seed、ADR、Approved Design、Implementation Plan、State、Validation 和 Snapshot 已各有独立职责。
- 根观测台由模板 v0.2.0 安装；其输出 `docs/_site/index.html` 为可重建生成物。
- 未发布 Core 包现持有 canonical 作者文档模板；Skill 下的 project-template 是兼容投影，测试要求作者模板内容一致。Observatory 工具不属于作者事实，并由独立组件清单管理。
- 未发布 Codex Adapter 只把 Codex 调用路由到目标仓库根 `AGENTS.md` 和平台中立 CLI；它不携带 State、ADR、Validation、canonical 模板或项目摘要，因此没有形成第二套文档事实。
- AI 问答、路线综合和趋势雷达保持可选，且没有事实权威。
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
