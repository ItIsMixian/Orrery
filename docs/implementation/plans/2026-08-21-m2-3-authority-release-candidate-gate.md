# 实施计划：M2.3 Authority Model 1 release／installer candidate gate

Status: Completed; local gate integrated, actual release still blocked

Date: 2026-08-21

Branch: `codex/m2-3-authority-release-gate`

Integration: `cfd76e4` was integrated through merge commit `bb03040`; no SemVer, tag, public manifest or release was selected.

Baseline: M2.1 validated Candidate `db81691`

Governing ADRs: [ADR-0004](../../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0009](../../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../../decisions/0011-authority-model-version-and-compatibility.md)

Approved Designs: [平台中立 Core 与 Adapter 架构](../../design/platform-neutral-core-and-adapter-architecture.md), [Authority Meta Model](../../design/authority-meta-model.md)

Parent Plans: [平台中立 Core 与 Adapter](2026-08-19-platform-neutral-core-and-adapters.md), [Authority Meta Model conformance and gradual extraction](2026-08-21-authority-meta-model-conformance-and-extraction.md)

State: [发布与工具链](../../state/release-and-toolchain.md), [Authority Meta Model](../../state/authority-meta-model.md), [测试覆盖](../../state/test-coverage.md)

## 目标

建立一个不依赖网络、不会改写公开 v0.2.0 历史资产的本地 release-candidate gate。给定维护者另行选择的
候选 SemVer 与候选 release manifest，Gate 必须验证 Authority Model 1 默认值和离散 `[1]` 支持集、
离线归档、standalone installer、目标项目兼容、显式迁移／恢复、回滚和秘密排除，然后才输出可审阅的
Candidate receipt。

本检查点只证明候选发布输入在本地满足已接受契约。它不选择实际下一 SemVer，不修改公开 source
release manifest，不创建 tag／Release，不推送，也不构成 Authority consumer production switch。

## 硬边界

- `skills/project-orrery/release-manifest.json`、Core bundled `release-v0.2.0.json`、v0.2.0 fixture、归档和
  checksum 必须逐字节保持历史不变。
- Candidate manifest 必须由调用者显式提供具体 SemVer；仓库只保存 provider-neutral gate policy，不能
  把测试中的 synthetic version 宣称为实际下一版本。
- Candidate release 必须同时声明正整数 `authority_model_version: 1` 和离散
  `compatibility.authority_model_versions.supported: [1]`；缺失、非法、重复、默认值不在支持集或未支持
  模型全部失败关闭。
- 新 scaffold 选择 candidate 默认模型；既有 legacy project 的普通 install／`--upgrade-tools` 仍保留
  缺失字段，不能把工具更新变成语义迁移。
- legacy adoption 只能通过现有 receipt-gated `migrate-authority-model` 明确 apply，并可由受限
  `restore-authority-model` 恢复；Gate 不增加隐式写入路径。
- Authority Model 字段存在只表示 selector；不得据此声称 implemented、validated、integrated 或
  released。
- 不导出稳定 Core API，不修改根 `scripts/docsite/**`、managed Observatory projection、用户级 Skill、
  root `PROGRESS/HANDOFF/DEVLOG`，不启动 M2.2。

## Candidate contract

Gate 输入：

1. 待打包 Skill source tree；
2. 独立 candidate release manifest；
3. 输出目录；
4. 可选 expected candidate version，用于防止操作者把错误 manifest 当作待发布版本。

Gate 输出一个确定性 JSON receipt，至少记录：

- gate contract version、candidate SemVer 与 release manifest SHA-256；
- Authority Model 默认值、离散支持集与 Core capability judgment；
- staged archive／checksum 与逐条目 hash；
- new scaffold、legacy ordinary upgrade、unsupported／invalid target、migration／restore、self-host、
  offline standalone install 的判定；
- secrets／cache／generated artifacts 排除结果；
- `m2_2_consumer_evidence` 和 `maintainer_version_selection` 两个 release blocker；
- `candidate_ready` 与 `release_ready` 必须分开：前者可通过，后者在上述 blocker 未关闭时必须为 false。

同一 source bytes、candidate manifest 与 policy 必须生成相同 archive bytes 和相同 evidence（输出路径、
时间戳等非语义信息不得进入 receipt hash）。任何验证失败都不得留下“成功”receipt 或修改 target。

## 实现步骤

1. 冻结 provider-neutral gate policy／fixture，不写入实际下一版本号。
2. 抽取可复用的确定性 Skill archive builder；保留公开 `package_release.py` 历史行为，并允许 Gate 在
   staging tree 中只替换 candidate manifest。
3. 让 standalone fallback installer 仅在 candidate release 真正声明模型时：新项目选择默认值、已有
   项目保持原选择／缺失；v0.2.0 manifest 下行为不变。
4. 实现 local gate runner：校验 release contract，构造 staging／archive，解压到隔离目录，并运行新项目、
   legacy、invalid／unsupported、migration／restore、self-host 和秘密排除检查。
5. 所有临时目录都位于显式输出或 OS temp；失败后删除临时写入，不触碰输入 source／target。
6. 增加恶意 manifest、路径穿越／symlink、归档重复、receipt 过期、失败不写入和可回滚专项测试。
7. 运行 release gate 专项、Authority／产品回归、全仓、integrated structure、静态站、Markdown links 与
   `git diff --check`。
8. 只同步 subsystem State、Validation 与索引；由唯一整合者在后续集成时同步全局入口。

## 主要路径

- `packaging/authority-release-candidate-policy.json`
- `scripts/authority_release_candidate_gate.py`
- `scripts/package_release.py`（只允许兼容性抽取，不改变公开默认输入）
- `skills/project-orrery/scripts/_legacy_install_project_orrery.py`
- `tests/fixtures/authority-meta-model/v1/release-candidate-gate.json`
- `tests/test_authority_release_candidate_gate.py`
- `docs/state/authority-meta-model.md`
- `docs/state/release-and-toolchain.md`
- `docs/state/test-coverage.md`
- `docs/validation/2026-08-21-m2-3-authority-release-candidate-gate.md`

## 验收门

- 候选 manifest 的 Authority 默认值／支持集合法，公开 v0.2.0 两份 manifest 与历史 fixture hashes 不变；
- 同一 candidate input 两次打包 archive／checksum 相同；归档没有绝对路径、`..`、重复条目、symlink、
  API Key、`ai-config.json`、keyring、cache、`.port`、生成站点或 benchmark raw；
- standalone offline install 的新项目选择模型 1，普通 legacy upgrade 保持缺字段；
- invalid／unsupported project 在 Authority 门失败关闭且 target bytes 不变；
- legacy 显式 migration apply 与 restore 都需匹配 receipt，且恢复后 manifest bytes 与原始完全一致；
- self-host project 选择模型 1，但 selector 不被写成 implemented／validated 证据；
- Gate 可以给出 `candidate_ready=true`，但只要 M2.2 consumer evidence 或维护者实际版本选择未完成，
  `release_ready` 必须保持 false；
- 完整验证后最多称为 M2.3 Worktree Candidate validated，不称 released、public support、stable API 或
  production-switched。
