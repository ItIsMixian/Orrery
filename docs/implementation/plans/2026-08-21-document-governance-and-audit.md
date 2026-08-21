# 实施计划：文档治理与只读审计

Status: Active

Date: 2026-08-21

Branch: `codex/document-governance-policy`

Governing ADRs: [ADR-0001](../../decisions/0001-project-orrery-self-hosting.md), [ADR-0009](../../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0012](../../decisions/0012-document-governance-and-information-lifecycle.md)

Approved Design: [文档治理与信息生命周期](../../design/document-governance-and-information-lifecycle.md)

## 目标

先让 Project Orrery 以明确的生命周期规则维护自身作者文档，再逐步建立 provider-neutral、zero-network、只读的文档治理审计。审计只产生可复核 finding，不自动编辑 Markdown、不创造事实、不改变 Authority Model 或公开发布契约。

## Phase 0：规范与自托管对齐

- [x] 接受 ADR-0012，明确 Meta Model／Governance／Tooling 三层边界。
- [x] 批准文档角色、同步事件、拆分标准、soft budget 和人工审查闭环。
- [x] 同步 AGENTS、Documentation State、PROGRESS、HANDOFF、DEVLOG 和索引。
- [x] 记录文档级 Validation，并确认没有 CLI／runtime／release 实现声明。
- [x] 同步仓库级 Authority relation 回归中的 ADR-0012 amend 预期，不改变 evaluator 行为。
- [ ] 由整合者在干净 integration worktree 审阅并进入本地 Canonical；在此之前本分支事实仍是 Candidate。

## Phase 1：只读 contract 与 fixture

- [ ] 在平台中立 Core 定义 `documentation-governance-finding-v1` schema 和规则 registry；不读取正文之外的敏感数据。
- [ ] 建立合成 fixture，覆盖 PROGRESS 完成史堆积、State 计划／历史混入、失活 Plan、断链、结构化字段误用、证据重复、soft budget 和并发全局入口所有权。
- [ ] 明确 `info`／`warning`／`review-required` 与程序退出码的正交关系；长度 warning 默认退出 0。
- [ ] 定义 project-level advisory 配置和默认缺省行为；不把固定字数写入 Authority Model。
- [ ] 以负向测试证明 finding 不会变成 ADR／State／Validation，也不会触发文件写入。

## Phase 2：平台中立 CLI 审计

- [ ] 增加显式 `docs audit` 入口，支持人类文本与 JSON schema v1。
- [ ] 默认 zero-network，限定读取范围；报告 fact scope、repository snapshot、规则版本和不确定性。
- [ ] 对断链、非法结构和安全边界违规定义可复现失败；增长／长度／密度保持 advisory。
- [ ] 提供 dry-run 式建议目标，但不增加 `--fix` 或 LLM 自动重写。
- [ ] 运行 Windows／Ubuntu fixture、旧 CLI 兼容、安装／发布回归和秘密扫描。

## Phase 3：Observatory 投影与人工确认

- [ ] Observatory 只消费 CLI／Core finding bundle，不重新实现规则。
- [ ] 展示 finding scope、证据、Unknown、acknowledge／defer 状态和项目 soft budget。
- [ ] 中央视图只读；任何本地修改仍需成员本机确认并通过普通开发／验证流程。
- [ ] 关闭开关时保持 legacy 页面和输出不变，失败不得生成部分权威页面。

## Phase 4：模板、兼容与发布

- [ ] 在 self-host 证据稳定后，决定是否把 governance guidance 和 audit CLI 投影到公开模板。
- [ ] 定义版本／升级兼容和作者文档不覆盖验证；普通升级不得重写现有文档。
- [ ] 维护者另行选择 SemVer、manifest、release notes、tag 和 GitHub Release；Plan 完成不等于发布。

## 主要路径

- `docs/decisions/0012-document-governance-and-information-lifecycle.md`
- `docs/design/document-governance-and-information-lifecycle.md`
- `docs/state/documentation-system.md`
- `packages/project-orrery-core/`（Phase 1）
- `packages/project-orrery-cli/`（Phase 2）
- `packages/project-orrery-observatory/`（Phase 3）
- `tests/fixtures/` 与 `tests/`（Phase 1–4）

## 验收门

- 规范层：角色职责、当前／历史边界、同步事件、拆分标准和工具权限没有矛盾。
- 非升级：finding、ack 或 soft budget 不能成为 effective decision、current State 或 Validation success。
- 无副作用：Phase 1／2 默认不写作者文档、不联网、不读取秘密或 transcript。
- 兼容：未启用审计时 CLI／Observatory／发布模板保持既有行为。
- 可追溯：每个实现阶段都有 State、Validation、DEVLOG 和必要的 PROGRESS／HANDOFF 同步。

## 当前未决选择

- 初始项目级 soft budget 默认值和配置位置；必须先测量真实 corpus，不能凭偏好写死。
- Finding acknowledge／defer 的持久化位置和 lifecycle；不能与作者事实混存。
- 哪些结构违规可进入 CI review gate；长度和风格类 finding 已明确不能单独成为硬门。
- HANDOFF 首次专项压缩的人工保留清单；当前文件是首个 review candidate，但本 Plan 不授权自动清理。

## State 与 Validation 同步

- State: [文档系统 State](../../state/documentation-system.md)，后续实现时再同步 Test Coverage／Release State。
- Phase 0 Validation: [2026-08-21 文档治理采纳](../../validation/2026-08-21-document-governance-adoption.md)
- Phase 1–4 必须分别新增 Validation，不得用本 Plan 的 checklist 代替实现证据。
