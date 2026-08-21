# 实施计划：Authority Meta Model 一致性基线与渐进提取

Status: Active Candidate Plan
Date: 2026-08-21
Governing ADR: [ADR-0009](../../decisions/0009-authority-meta-model-and-semantic-conformance.md)
Approved Design: [Authority Meta Model](../../design/authority-meta-model.md)
State: [Authority Meta Model State](../../state/authority-meta-model.md)

## 目标

在不把现有 Project Orrery 立即重构为一套新运行时的前提下，先固定可审阅的语义
conformance contract，再逐步提取已经稳定的 Authority Meta Model 判断。最终让 CLI、
Observatory、AI 派生视图与未来 Adapter 在相同输入下遵守同一组 authority 约束。

本计划的直接产出是实施顺序、决策门与验证矩阵；它本身不代表任何 evaluator、字段或
用户可见功能已经存在。

## 非目标与冻结边界

- 不决定 AUTH-1（产品核心定位）。
- Fixture-first 阶段不提前决定 AUTH-4（唯一 semantics implementation owner）；fixture 完成后已由 ADR-0010 选择平台中立 Core。
- 不修改 manifest、document schema、公开 API、模板或发布契约。
- 不以文件长度为理由大重构 Observatory，也不预先规定 Python package、parser 或 UI 的归属。
- 不实现多人协作、Coordinator runtime、AI UI、新作者文档类型，或把 Agent 任务/锁/队列伪装成 fact scope。
- 不把本 Candidate 分支的计划、盘点或测试意向叙述为 Canonical implementation、验证或发布状态。

若某阶段需要改变跨模块或发布契约，必须先新增 ADR 或 amendment；仅更新此计划不足以授权。

## 当前重复语义的区域级盘点

下表是规划用的区域级 inventory，不是逐函数 machine-readable rule catalog。其目的是避免把
已有实现误当作新的规范 owner。

| 区域 | 当前可观察职责 | 分类 | 计划中的处理 |
| --- | --- | --- | --- |
| ADR-0009、Approved Design、`docs/core/principles.md` | 定义 Meta Model 与产品 Seed 的边界、invariants、scope/evidence 规则 | `normative-source` | 保持为规范来源；Seed 内容不被提升为通用语义规则 |
| `AGENTS.md`、authoring 模板与 docs 索引 | 向人类/Agent 投影阅读链、角色和同步义务 | `projection` | 与规范对齐，不成为独立 evaluator |
| Core `schema.py`、`schema/authority-v1.json`、`manifests.py`、`compatibility.py` | 处理 scaffold、`document_schema`、manifest format 与 toolchain compatibility | `deterministic-evaluator`（仅现有格式兼容） | 不能据此声称已有 authority claim/scope/evidence evaluator |
| CLI `validate.py` 与 `authority_shadow.py` | 原扫描仍识别 Accepted ADR，并由 `AGENTS.md`/`PROGRESS.md` 推导 integrated candidate；Candidate shadow 只把 Accepted ADR 送入 Core 比较 | `deterministic-evaluator` + shadow adapter | 保持 legacy production path；先扩大可解释差异，再考虑独立切换 |
| `build_docsite.py` | 解析角色、ADR lifecycle、引用、图与统计，再渲染页面 | `deterministic-evaluator` + `projection` | 先分离语义解析结果与呈现；不要求一次性拆文件 |
| `docsite_insights.py` | 依据引用、Git recency、代码路径等给出断链/过期/悬置提示 | `heuristic-observation` | 保留启发式性质，不能升级为 authority fact |
| `docsite_qa.py`、`serve.py` | 选择语料、构造 prompt、输出问答/路线图等 | `derived-ai-view` | 只能消费确定性结果与证据引用，不得创造或升级事实 |
| Core canonical templates 与发布 Skill template | 有意保持的兼容投影 | `projection` | 继续由投影一致性测试保护，不能形成双规范 owner |
| `adapters/codex/**` | 平台入口与安装生命周期 | `projection` | 维持薄层；不得复制独立 authority semantics |
| `tests/test_project_orrery.py`、Adapter/投影兼容测试 | migration baseline、结构与投影保护 | `test-only` | 未来接入 fixture，不把现有通过误称为统一 conformance |
| 未来 Agent owner、依赖、锁、队列、心跳 | 协作调度状态 | `coordinator-only` | 不并入 Authority Meta Model 的 fact scope |

## 版本与 conformance 输入

`document_schema` 与 `authority_model_version` 必须独立演进；它们也都不同于外层 manifest
format 与组件/工具链版本。

| 维度 | 说明 | 当前状态 | 本计划中的约束 |
| --- | --- | --- | --- |
| `project_manifest_format` | `.project-orrery.json` 的外层格式 | 已有 | 不在本计划中变更 |
| `document_schema` | 作者文档字段、目录与结构格式 | 已有 | 不能代替 authority semantics 版本 |
| `authority_model_version` | roles、claims、relations、scopes、evidence 与 derived-view constraints 的解释版本 | 尚无字段 | 先作为 conformance input；公开字段编码留给 Gate B |
| component/toolchain version | Core、CLI、Adapter、viewer 等实际发行/运行版本 | 已有部分 | 不能据此推断语义版本 |

任何 conformance 判断的最小输入为：

1. `authority_model_version`；
2. 精确的 repository snapshot；
3. fact scope；
4. evidence visibility。

同输入必须给出兼容的确定性结论。不同 scope 或 evidence visibility 可以改变结论，但输出必须
显式保留来源、scope 与 `Unknown`，不得默默按 Canonical 补全。旧项目或未知版本在未来
evaluator 中应得到受限/未知结论，而非被无依据地当作当前版本。

## Versioned fixture / golden contract

第一份真实实现必须是 versioned fixture corpus 与期望输出，而不是抢先抽取某个 consumer。
每个 fixture 固定四项 conformance 输入，并记录结论、可见证据、不可推断项和规范引用。

| 必覆盖场景 | golden contract 要证明的边界 |
| --- | --- |
| accepted ≠ implemented ≠ validated | 三个独立 claim dimension，非线性状态机 |
| implementation 存在但 validation failed | failed evidence 不抹除 implementation fact |
| 历史实现、后续移除与 current State | Historical 不等于 current/Canonical |
| supersede 与 amend | effective decision 由关系决定，旧 ADR 不应被显示为 current |
| Draft / Approved 与 Plan / State | 各自 lifecycle 与角色不能互换 |
| Canonical / Candidate / Worktree / Local-only / Historical / Unknown | scope 改变可断言范围，不能制造证据 |
| Snapshot | 截面不自动成为 live State |
| evidence categories 与 visibility | revision、executable validation、trace、assertion、AI summary 的能力边界 |
| derived AI 输出 | 能解释/引用，不能创造、批准、验证或升级事实 |
| scope 与 Coordinator runtime | worktree/fact scope 不等于 owner、lock、queue、dependency |

Fixture 还必须覆盖“相同输入得到相同结果”以及“仅 evidence visibility 不同而结论差异被明确标注”。
它们是跨消费者的 golden contract，不是单一测试文件的快照，也不替代项目 State Docs。

## 决策门

### Gate A：实现 owner（AUTH-4）

Resolved by [ADR-0010](../../decisions/0010-core-owned-authority-evaluator.md): platform-neutral Core owns the
deterministic evaluator. Parsing, projection, AI prose and Coordinator runtime remain outside. The first
implementation is experimental/fixture-bound and does not cross Gate B. AUTH-1 remains unresolved.

### Gate B：公开版本与兼容契约

在需要把 `authority_model_version` 写入公开 manifest/schema/API 前，明确：字段位置、缺失字段的
旧项目策略、未知版本、升级/降级、`document_schema`/manifest/toolchain 的版本矩阵，以及自托管和
发布兼容性。任何跨模块/发布契约变化都需要 ADR 或 amendment。

Candidate 已形成 [PO-DEC-AUTH-002](../../decisions/proposals/PO-DEC-AUTH-002-authority-model-version-and-compatibility.md)：
建议项目 manifest 顶层使用正整数模型版本，release 声明默认值与离散支持集，缺失字段保持
`legacy-unversioned`，unsupported／unknown 只允许只读浏览并对 Authority 结论失败关闭，工具升级
不得自动执行语义迁移。维护者已接受 Candidate 实施；提案在集成者分配正式 ADR 前仍保持 Proposed，
因此首个检查点只建立兼容 fixture 与 Core 内部 capability judgment，继续阻塞 public
manifest/schema/managed-tool 变更。

## 渐进阶段

1. **Baseline 与 inventory**：冻结上述区域级盘点，补齐现有行为对 fixture 的可追溯映射；不改变运行路径。
2. **Fixture first**：实现 versioned fixture/golden contract，并以现有 CLI、docsite parser、AI prompt 的输出做差异报告；不选择 owner。
3. **最小 evaluator / shadow mode**：Gate A 已由 ADR-0010 解决；Core 先实现 normalized observations 到 roles/relations/claim dimensions/scopes/evidence 的确定性解释，并把 fixture comparison 分类为 missing expectation、extra observation 或 expected visibility difference。CLI/docsite 尚不切换生产行为。
4. **确定性消费者迁移**：按 CLI → docsite parser → insights/projection 的顺序逐一接入；每个消费者先双轨比对，再独立切换，并可回滚到原逻辑。CLI 第一检查点已在 Candidate 中完成：只比较 Accepted ADR，scope 保持 `Unknown`，不切换 legacy status／exit code。Observatory 已完成四个包级检查点：legacy ADR lifecycle、显式 relation/effective-decision、严格 Design／Plan／State／Validation role claims，以及组合真实 legacy `render_site()` 与前述 shadow 的 runtime bridge。第四检查点证明 HTML/stats 原样返回、shadow failure 被隔离，但没有修改 managed build/serve 或发布 projection。`Predecessor`、普通 refs、State 正文 implementation 推导、Validation 命令重放、insights/projection 与正式运行入口留给后续检查点。
5. **AI 派生视图**：`docsite_qa.py`/`serve.py` 仅消费已确定的语义、scope、visibility 与引用；对“AI 把 Unknown/Local-only/observed 升级为事实”的响应建立负向测试。
6. **兼容、自托管与发布**：Gate B Candidate 第一检查点已冻结 9-case legacy/supported/unsupported/invalid fixture，并在 Core 内部实现离散 support capability judgment；没有写 manifest、导出公共 API 或切换 consumer。后续仍须先完成正式 ADR 集成，再按 shadow CLI/banner → 显式 migration dry-run → manifest projection → self-host/release 顺序推进。

文件长度不是阶段完成条件。每个消费者都必须能在不阻塞其他消费者的情况下回滚自己的切换。

## 实现路径与剩余授权边界

- `tests/fixtures/authority-meta-model/**` 与 `tests/test_authority_meta_model.py`：fixture、golden contract 与 consumer conformance。
- `packages/project-orrery-core/src/project_orrery_core/authority.py`：ADR-0010 决定的最小 deterministic evaluator owner；当前实现仍是 experimental、fixture-bound Candidate。
- `packages/project-orrery-core/src/project_orrery_core/authority_compatibility.py`、`tests/fixtures/authority-meta-model/v1/compatibility.json`、`tests/test_authority_model_compatibility.py`：Gate B Candidate capability contract；公开模型 1 映射内部 fixture ID，但不导出顶层 API、不写 manifest，也不把 capability 误报为 conformance passed。
- `packages/project-orrery-cli/src/project_orrery_cli/authority_shadow.py`、`validate.py`：已有 Accepted ADR warning-only shadow；后续切换或扩大公开输出需要新的验证检查点。
- `packages/project-orrery-observatory/src/project_orrery_observatory/authority_shadow.py`：已有未导出的 lifecycle 与显式 relation/effective-decision shadow adapter；保持无公开依赖／API，直到运行时接线边界通过验证。
- `packages/project-orrery-observatory/src/project_orrery_observatory/authority_role_shadow.py`：已有未导出的 Design／Plan／State／Validation role adapter；只消费受控路径与严格元数据，不从文档存在或自由文本制造 implementation/validation 事实。
- `packages/project-orrery-observatory/src/project_orrery_observatory/runtime_shadow.py`：已有未导出的 warning-only runtime bridge；真实 legacy render 先完成，Authority 失败只进入独立 report，不改变 HTML/stats。managed build/serve 接线仍受 Gate B 约束。
- `scripts/docsite/build_docsite.py`、`docsite_insights.py`、`docsite_qa.py`、`serve.py`：尚未切换；解析、启发式、投影和 AI 约束继续按独立检查点接入。
- `adapters/**` 与 template projection tests：只消费既有确定性契约。
- `.project-orrery.json`、release manifest、schema 与 compatibility：仅在 Gate B 和 ADR/amendment 后考虑。

## 验证矩阵

| 阶段 | 证据 | 通过条件 |
| --- | --- | --- |
| 本计划 | 安装验证、静态站生成、既有测试、Markdown 链接、diff allowlist | 计划可被现有工具读取，且未越界修改产品/发布路径 |
| Fixture | versioned corpus + expected results | 所有必覆盖场景、同输入一致性与 visibility 差异明确 |
| Shadow evaluator | 旧/新双轨输出与差异清单 | 无未解释的 canonical 语义回归 |
| CLI/docsite | consumer-specific conformance tests | 相同输入遵守同一 fixture；旧路径可回滚 |
| AI view | deterministic references + negative tests | 不创造/升级事实，不把 AI 当批准或 validation |
| Compatibility/release | legacy/unknown/upgrade/downgrade/self-host tests | Gate B 契约成立且发布投影无漂移 |

本分支最低验证命令：

```powershell
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out "$env:TEMP\project-orrery-authority-meta-plan-20260821.html"
python -X utf8 -m unittest tests.test_project_orrery -v
```

另需运行 Markdown 本地链接扫描、`git diff --check`，并确认 diff 仅包含本计划与其 State/Validation
索引记录。

## 完成条件与同步边界

本计划在以下条件均满足后才能宣称“Authority Meta Model 已有实现”：Gate A 已决定、fixture/golden
contract 已版本化、最小 evaluator 经 shadow 验证、迁移消费者有 conformance/rollback evidence、AI
约束可测、Gate B（若触及公开契约）已通过，并完成兼容/self-host/release 验证。

本 Candidate worktree 只同步 `authority-meta-model` State 和对应 Validation/索引，不改写根
`PROGRESS.md`、`HANDOFF.md`、`DEVLOG.md`。唯一整合者在干净 integration worktree 合并后，才可
依据实际提交与验证更新这些 Canonical 入口。
