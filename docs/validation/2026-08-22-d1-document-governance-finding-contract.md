# D1：文档治理 Phase 1 finding contract

Status: Worktree Candidate validation

Governing decision: [ADR-0012](../decisions/0012-document-governance-and-information-lifecycle.md)

Approved Design: [文档治理与信息生命周期](../design/document-governance-and-information-lifecycle.md)

Implementation Plan: [文档治理与只读审计](../implementation/plans/2026-08-21-document-governance-and-audit.md)

## Scope 与事实边界

本记录覆盖 `codex/document-governance-finding-contract` 功能分支的 D1 Candidate。它只新增平台中立
Core 内部 schema／registry／validator、合成 fixture 和测试；不包含 scanner、CLI、Observatory UI、自动修复、
模板迁移、用户级 Skill 修改、HANDOFF 压缩、push、merge、tag 或 Release。

finding contract 固定以下边界：

- schema version 1、稳定 contract／rule／finding ID、八类 category 与三档 severity；
- source document role、Canonical／Candidate／Worktree 等 fact scope、repository snapshot、精确 line range 与
  SHA-256 source evidence；
- `open`／`acknowledged`／`deferred`／`resolved` 和匹配的 acknowledgement disposition／actor／reason／时间；
- `must_not_infer` 必须同时禁止 Authority 变化、文档失效、自动作者文档写入、Validation success 和自动关闭；
- producer 明确 `network_access: false`，review 只能触发 `human-review`，Authority／author-document effect 恒为
  `none`；
- 规则 severity 与程序结果正交。所有 D1 规则默认 exit 0；soft budget 为 advisory，断链仅为
  `eligible-not-enabled`，没有启用程序硬门或 Authority gate。

项目 soft budget 的配置位置和值仍未选择；registry 只固定“缺省禁用、项目本地、非 Authority”。fixture 中
12 行／50% 的阈值只服务合成正负例，不能外推为项目默认值。

## 合成 fixture

11 组正负 Markdown 对照覆盖：过长入口、高链接密度、重复当前事实、当前入口滞留已解决历史、断链、State
混入计划、Plan 冒充实现／验证、Validation 混入未来计划、失活 Plan、结构化 success metadata 误用，以及
普通功能分支把 PROGRESS／HANDOFF 列入 expected writes。所有内容均为人工合成，不含真实项目事实、源码、
Prompt、回答、transcript、凭据或成员未 push diff。

Golden finding 绑定输入文件 SHA-256 与行区间；负例冻结空 findings。测试还把同一 open finding 投影为
acknowledged／deferred／resolved 合法状态，并拒绝缺失或不匹配的 acknowledgement。

首次最终全仓复跑在高密度入口正例中捕获 `line_end: 9` 与修正后 8 行正文不一致；SHA-256、密度观察和规则
结果均正确。D1 只把 golden source range 收紧为 8，没有放宽 validator 或改变产品规则，随后重新执行专项与
全仓验收。

## 验证证据

环境：Windows 11 build 26200、PowerShell、Python 3.13；测试不调用模型、Provider、网络服务或远端 Git。

| 命令／procedure | Observed outcome |
|---|---|
| `python -m unittest tests.test_documentation_governance_contract -v` | PASS — 11/11。 |
| `python -m unittest discover -s tests -v` | PASS — 259 项中 254 passed、5 skipped；3 项为既有 Windows symlink privilege，2 项为既有可选动态依赖。 |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — integrated candidate，Authority Model 1 eligible。 |
| `python -X utf8 scripts/docsite/build_docsite.py --out C:\Users\1\AppData\Local\Temp\project-orrery-d1-docsite-20260822\index.html` | PASS — 隔离静态站生成；`docs/_site/index.html` 未修改。 |
| PowerShell 本地 Markdown link scan | PASS — 322 个 Markdown 文件、795 个本地链接、0 个意外缺失；另精确允许 D1 断链正例中的 1 个冻结 synthetic missing target。 |
| `git diff --check` | PASS。 |

专项测试逐字节比较 fixture before／after，重复 canonical serialization，并拒绝 `patch_content`、
`authority_status`、`validation_result`、非 `none` author-document effect 与 Authority escalation。该证据证明
本模块的 contract validation 路径无写入；它不证明尚不存在的 audit runtime。

## 后续边界

- Phase 2 才能实现只读 scanner／`docs audit` CLI，并需单独决定哪些结构问题可在程序层失败；D1 不授权。
- ack／defer 持久化位置与 lifecycle 尚未选择，不能混入作者事实；fixture lifecycle 只冻结 payload semantics。
- Observatory 只能在后续消费 Core bundle，不能重写规则或提供无需本机确认的编辑能力。
- 公开 v0.2.0、managed template、Adapter、组件公开 API 与 release 状态均未改变。
