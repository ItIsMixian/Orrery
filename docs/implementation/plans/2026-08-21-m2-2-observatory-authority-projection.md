# 实施计划：M2.2 Observatory Authority Candidate projection

Status: Completed; locally integrated, with projection still explicit opt-in

Date: 2026-08-21

Branch: `codex/m2-2-authority-observatory-projection`

Integration: `06ee3eb` was integrated through the M2 integration branch; this completes the checkpoint, not a default production switch.

Baseline: M2.1 Candidate `db81691`

Governing ADRs: [ADR-0009](../../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../../decisions/0011-authority-model-version-and-compatibility.md)

Approved Design: [Authority Meta Model](../../design/authority-meta-model.md)

Parent Plan: [Authority Meta Model conformance and gradual extraction](2026-08-21-authority-meta-model-conformance-and-extraction.md)

Predecessor: [M2.1 complete CLI Authority observations/claims](2026-08-21-m2-1-authority-cli-claims.md)

## 目标

把 M2.1 的完整 repository observation／claim bundle 接入 Observatory，形成正式但仍为 Candidate、
维护者显式启用且可独立回滚的 Authority 页面投影。投影必须在同一 Authority Model、repository
snapshot、fact scope 与 evidence visibility 下消费 Core-owned semantics，显示来源、Unknown、
effective decision 与分角色 claims；不得重新从 legacy prose、insights 或 AI 文本制造事实。

本检查点不改变默认 managed Observatory，不修改 release／installer／Skill 模板或组件版本，也不
构成稳定公共 API、production switch 或模型 1 发布声明。

## 硬边界

- 复用 M2.1 `cli-authority-observations-v1` bundle；Observatory 不实现第二套 Authority parser／evaluator。
- `project-orrery-cli` 已依赖 Observatory；为避免包依赖环，Observatory 包只消费调用方传入的 bundle，
  不 import CLI。根 managed integration layer 负责调用 CLI collector 后把结果交给 projection builder，
  并用独立 import 测试保护这一边界。
- 同一 model／snapshot／scope／visibility 下，Observatory projection 与 M2.1 bundle 必须逐值 reconciliation。
- 每个 projected claim 必须保留 source、source SHA-256、scope、evidence visibility 和 Core `must_not_infer`。
- unsupported／legacy／invalid model、collector／evaluator／reconciliation／render failure 必须失败关闭为
  只读 legacy 页面；不能展示残缺的确定性 Authority projection。
- 默认环境变量为空时，HTML、stats、启动行为和现有 shadow diagnostic 保持原样。
- 新 projection 使用独立显式 opt-in；关闭该开关即可回滚，不依赖 migration、installer 或 release 变更。
- legacy graph／prose、AI Q&A、insights 和 radar 只可作为旧视图或派生视图，不能覆写 Candidate claims。
- 不修改根 `docs/PROGRESS.md`、`docs/HANDOFF.md`、`docs/DEVLOG.md`；由唯一整合者在合流时同步。

## Candidate contract

1. Observatory runtime 从同一 repository root 构建一次 M2.1 bundle，并验证请求的 model、snapshot、scope、visibility。
2. 独立 projection model 只消费 bundle，输出 `observatory-authority-projection-v1`：
   - conformance inputs 与 reconciliation digest；
   - effective decisions 与 unresolved relations；
   - Seed／ADR／Design／Plan／State／Validation／Snapshot 分角色 claims；
   - 每项 source link、source hash、evidence provenance、Unknown 与不可推断项。
3. renderer 对 projection model 做 HTML escaping 与 repository-relative links；不重新解释 Markdown 正文。
4. runtime report 明确区分 legacy production、M1 shadow 与 M2.2 Candidate projection。
5. 任一 precondition 或 reconciliation 不满足时，projection status 为 unavailable，legacy 页面和 stats 原样返回。

## 实现步骤

1. 冻结默认 HTML／stats、现有 shadow 开关和 M2.1 bundle 的基线测试。
2. 在 Observatory 包新增只消费 bundle 的内部 projection builder 与 reconciliation contract；根 managed
   integration layer 复用 CLI collector 和 Core output，Observatory 包本身保持可单独 import。
3. 在根 `scripts/docsite/` 增加独立 opt-in runtime 接线与只读 Authority 页面 renderer。
4. 增加来源链接、scope／model／snapshot／visibility banner、Unknown 与 failure notice。
5. 增加 fixture 和负向测试，覆盖默认无变化、关闭即回滚、unsupported／legacy、collector/evaluator/
   reconciliation failure、HTML escaping、source link 与同输入一致性。
6. 运行 Authority 专项、全仓、integrated structure、静态站、Markdown link 与 diff 检查。
7. 同步 authority/documentation/test State、Validation 与索引；不触及 M2.3 路径。

## 主要路径

- `packages/project-orrery-observatory/src/project_orrery_observatory/authority_projection.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/runtime_shadow.py`
- `packages/project-orrery-cli/src/project_orrery_cli/authority_observations.py`（只消费；除非发现 M2.1 缺陷，不改契约）
- `scripts/docsite/build_authority_projection.py`（root-only managed Candidate entry）
- `scripts/docsite/build_docsite.py`（保持与发布模板逐字节一致；只消费 legacy builder）
- `scripts/docsite/docsite_insights.py`（不得成为 claims 来源）
- `tests/fixtures/authority-meta-model/v1/observatory-projection.json`
- `tests/test_authority_observatory_projection.py`
- `tests/test_authority_observatory_managed_shadow.py`
- `docs/state/authority-meta-model.md`
- `docs/state/documentation-system.md`
- `docs/state/test-coverage.md`
- `docs/validation/2026-08-21-m2-2-observatory-authority-projection.md`

## 验收门

- 默认 build／serve 逐字节保持 legacy 输出与 stats；现有 shadow report／diagnostic 语义不变。
- projection 只有在独立显式 opt-in 且 model supported、bundle 完整、reconciliation 通过时渲染。
- 同输入下 Observatory projection 的 conformance input、claims、relations、source hash 与 M2.1 bundle 一致。
- effective decision、role claims、Unknown、scope、visibility 和 source links 均可见且不会被 legacy/AI 改写。
- unsupported／legacy／invalid 和所有注入失败只返回 legacy 页面，并提供非权威 unavailable report。
- 关闭 projection 开关即可回滚，不需要写 manifest、修改文档或安装旧版本。
- Authority 专项、全仓、结构、静态站、链接和 diff 检查全部通过后，本分支最多称为
  `M2.2 Worktree Candidate validated`；不得称为 production-switched、released 或 stable API。
