# PO-DEC-AUTH-002: Authority Model 公开版本与兼容契约

Status: Proposed

Date: 2026-08-21

Stable proposal ID: `PO-DEC-AUTH-002`

Proposed amendment to: [ADR-0009](../0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../0010-core-owned-authority-evaluator.md)

Maintainer disposition: accepted for Candidate implementation on 2026-08-21; formal ADR numbering and Canonical authority remain deferred to integration.

## Context

ADR-0009 要求 Authority Meta Model 可被版本识别，ADR-0010 又要求未知模型版本失败关闭，但两者都故意没有决定公开字段、旧项目兼容和迁移方式。Candidate 已用内部标识 `amm-fixture-v1` 冻结 fixture，并在 Core、CLI 与 Observatory shadow 中验证语义；该标识目前不是项目 manifest、release manifest 或公共 API 契约。

现有公开兼容面已经分别记录：

- `.project-orrery.json:manifest_format`：项目安装元数据的结构格式；
- `.project-orrery.json:document_schema`：作者文档格式与结构；
- `toolchain_version`、组件版本和 Core API version：实际工具实现；
- release manifest compatibility：某个发布可以安全读取／升级哪些目标。

如果普通工具升级顺便把无版本项目写成当前 Authority Model，Orrery 就可能在没有维护者批准的情况下重新解释 Accepted、current、effective、validated 或 Unknown。反之，如果任何缺失字段都使 Markdown 无法阅读，现有 v0.2.0 项目又会被无必要地破坏。

Gate B 因此必须同时定义“选择哪一版语义”和“工具看不懂时还能安全做什么”，并保持安装、工具升级、语义迁移与发布四个动作相互独立。

## Proposed decision

### 1. 项目显式选择 Authority Model

在 `.project-orrery.json` 顶层增加可选的正整数：

```json
{
  "authority_model_version": 1
}
```

该字段选择用于解释 roles、lifecycles、claim dimensions、relations、fact scopes、evidence 和 derived-view constraints 的语义版本。它不表示文档已经迁移、决定已经实现或项目已经通过验证。

第一版公开模型编号为整数 `1`。Candidate fixture 标识 `amm-fixture-v1` 是模型 1 的内部 conformance corpus ID，不进入项目 manifest，也不能取代公开整数版本。

初次采用保持 `manifest_format = 1` 与 `document_schema = 1`：manifest v1 已允许附加字段，字段缺失又被本提案定义为合法的 legacy 状态，因此无需为了一个向后兼容的可选 capability selector 改写外层格式。未来若要把该字段变成所有项目的结构必填项，必须另行升级 manifest format，不得原地改变这项决定。

### 2. Release 声明默认模型与离散支持集

首次实现时，release manifest 增加：

```json
{
  "authority_model_version": 1,
  "compatibility": {
    "authority_model_versions": {
      "supported": [1]
    }
  }
}
```

- 顶层值是该 release 为新 scaffold／显式迁移建议的默认模型；
- `supported` 是该 release 实际拥有 evaluator 与 conformance evidence 的离散版本集合；
- 支持能力不能由 Skill、toolchain、component、Core API 或 `document_schema` 版本号推断；
- 发布不得声明尚无 evaluator／fixture／Validation 的模型版本。

独立发行的确定性 Authority consumer 以后也必须声明其支持集；Adapter、AI 与纯 projection 不得冒充 semantics owner。组件协商检查“项目所选模型是否包含在消费者支持集”，而不是要求所有组件版本号相等。

### 3. 缺失、已知与未知版本的行为

| 项目状态 | 确定性 Authority 结论 | 仍可执行 | 必须禁止或标注 |
| --- | --- | --- | --- |
| 字段缺失 | `legacy-unversioned`；Core-derived Authority 结论为 unavailable／Unknown | 读取 Markdown、legacy viewer、结构检查、迁移预演 | 不得静默按模型 1 解释，不得宣称 conformance |
| 版本位于消费者 `supported` | 按该精确版本 evaluator 解释 | 正常 Authority validation／projection | 输出仍须携带 model、snapshot、scope、visibility |
| 已知但当前消费者不再支持 | unsupported | 只读 Markdown、兼容报告、迁移／安装预演 | 不得用其他版本代替，不得产生 effective/current 等确定性结论 |
| 未知或更新版本 | unsupported-newer／unsupported-unknown | 只读 Markdown、明确的不兼容报告 | 失败关闭，不得静默降级或猜测相近版本 |
| 字段类型非法 | invalid manifest capability | 只读原始文件和修复指导 | Authority validation 必须失败 |

普通结构验证可以对 `legacy-unversioned` 保持成功但发出警告，以免破坏既有 v0.2.0 项目；任何要求 Authority conformance／integrated semantics 的严格验证必须把字段缺失或不支持视为未满足。Viewer 可以继续呈现原始文档，但必须显示 legacy／unsupported banner，并停止生成会被误认成 Core-derived 的 effective、current、implemented 或 validated 结论。

### 4. 工具升级与语义迁移分离

- 新 scaffold 可以记录 release 的默认 `authority_model_version`，但 `authority_status` 仍独立表示 adoption 是否完成。
- 对现有字段缺失项目，普通安装、Skill 更新和 `--upgrade-tools` 必须保留缺失状态；不得自动补写版本。
- 现有项目只有在维护者明确接受项目级迁移决定、审阅 dry-run／差异并完成备份后，才能写入或改变 `authority_model_version`。
- 升级到支持更多模型的工具不会自动改变项目所选模型；模型迁移是独立操作，并需要迁移后的 State／Validation 证据。
- 降级工具前必须验证目标工具仍支持项目所选模型；不支持时拒绝 Authority 操作，不得通过重写字段制造兼容。
- 任何语义迁移都保留旧 Snapshot／Validation 所使用的模型版本；历史证据不能被新 evaluator 静默重算后冒充原结论。

本提案只冻结行为，不提前规定迁移命令名称、UI 或 Python API。实现必须先提供只读 capability report 与 dry-run，再提供显式 apply 路径。

### 5. 版本矩阵保持正交

| 维度 | 决定什么 | 是否因模型 1 首次公开而变化 |
| --- | --- | --- |
| `manifest_format` | `.project-orrery.json` 外层结构 | 否，保持 1；字段先为可选 capability selector |
| `document_schema` | 作者文档格式／结构 | 否，保持 1 |
| `authority_model_version` | Authority 语义解释 | 新增公开选择，初始为 1 |
| release compatibility | 一个发布实际支持哪些目标与模型 | 新增离散 Authority Model 支持集 |
| Core API version | 稳定程序接口 | 不因仅增加 manifest capability 自动提升；若导出稳定 evaluator API，另行评审 |
| component／toolchain version | 实现与发行版本 | 按正常发布规则演进，不能代替模型版本 |

### 6. 实施与发布门

本提案在维护者接受前不授权实现。维护者现已授权前两项 Candidate 内部检查点；schema、manifest、installer、validator、managed docsite、README 或发布资产仍须等待正式 ADR 集成后再修改。总体实施顺序为：

1. 为 legacy／supported／unsupported／invalid 组合增加兼容 fixtures；
2. 在 Core 增加 provider-neutral capability judgment，不先改变消费者输出；
3. 让 CLI 与 Observatory 以 shadow／banner 方式双轨比较；
4. 增加显式迁移 dry-run 和备份验证；
5. 更新 project／release manifest 投影和 managed tools；
6. 完成 self-hosting 迁移、回滚、旧 v0.2.0 项目与发布包验证后，才允许 consumer production switch。

任何阶段都不能把“字段存在”当成项目已实现或已验证 Authority Model 的证据。

## Reasons

- 顶层项目字段使语义选择与 repository snapshot 同行，跨 CLI、Viewer、Agent 或机器都可重建。
- 正整数是协议大版本，不与发行 SemVer、文档 schema 或内部 fixture ID 混用。
- 离散支持集比最小／最大范围保守；语义版本可能非连续支持，不能靠数值区间猜测。
- `legacy-unversioned` 保留既有项目可读性，同时避免无依据地把旧文档解释成当前模型。
- 显式迁移符合“不覆盖作者文档、安装不等于采纳、accepted 不等于 implemented”的现有安全边界。
- 只读降级面让用户在遇到未来版本时仍能访问原始知识，但不会收到伪确定性结论。

## Rejected alternatives

### 从 toolchain／Core API 推断模型版本

同一工具可能支持多个模型，同一模型也可能由多个工具版本实现；推断会隐藏真实 conformance 输入。

### 把 `document_schema` 提升为语义版本

格式不变时语义仍可能升级，格式迁移也不必改变 Authority 结论；两者合并会使迁移原因不可审计。

### 字段缺失默认等于模型 1

这会把升级工具变成未获批准的语义迁移，并错误地给旧项目制造 conformance 声明。

### 未知版本回退到最近支持版本

Authority 语义没有安全的“近似解释”。回退可能把 Unknown、historical 或 failed validation 提升为当前事实。

### 首次新增字段即升级 manifest format

现有 manifest v1 已允许附加字段，且本提案要求缺失保持合法。立即升级格式只增加迁移负担，没有带来新的结构安全边界。

## Consequences

- 旧项目继续可读，但在显式迁移前不能宣称使用 Authority Model 1。
- CLI／Observatory 需要区分结构有效、Authority capability 可用和项目 adoption 已完成，不能再用一个布尔状态概括三者。
- release 与未来独立组件需要维护离散 support matrix 和对应 conformance evidence。
- 模型迁移将产生额外的 dry-run、备份、State 与 Validation 工作，但避免工具更新静默改变项目事实。
- v0.2.0 资产及其 checksum 保持历史事实；本提案不回写已发布 manifest。

## Confirmation record（Candidate）

维护者于 2026-08-21 接受以下六项 Candidate 实施边界；在集成者基于最新 integration ref 分配正式 ADR 编号前，本文件仍保持 Proposed，不能冒充 Canonical 决策：

1. 公开模型版本使用正整数，首版为 `1`；
2. `.project-orrery.json` 顶层记录项目选择；
3. release 使用默认值 + 离散 `supported` 集；
4. 缺失字段保持 `legacy-unversioned`，不自动迁移；
5. unsupported／unknown 只保留只读浏览并对 Authority 结论失败关闭；
6. 初次采用不提升 `manifest_format` 或 `document_schema`。

## Implementation and validation mapping

- Approved Design: acceptance 后 amend [Authority Meta Model](../../design/authority-meta-model.md)
- Implementation Plan: [Authority Meta Model conformance and gradual extraction](../../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)
- State Docs: [Authority Meta Model State](../../state/authority-meta-model.md), [release and toolchain](../../state/release-and-toolchain.md)
- Validation: [Authority Model compatibility Candidate](../../validation/2026-08-21-authority-model-compatibility-candidate.md)；仅证明内部 fixture／capability judgment，不证明公开契约或发布
