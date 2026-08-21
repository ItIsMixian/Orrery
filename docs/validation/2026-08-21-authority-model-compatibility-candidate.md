# Validation：Authority Model compatibility Candidate

Date: 2026-08-21

Scope: PO-DEC-AUTH-002 获维护者接受后的第一个 Gate B Candidate 检查点。该记录验证 version capability contract 与 Core 内部 judgment，不验证公开 manifest、迁移命令、managed docsite、consumer switch 或发布兼容。

## 接受与事实边界

- 维护者于 2026-08-21 接受 PO-DEC-AUTH-002 的六项 Candidate 实施边界。
- 非集成 worktree 继续使用稳定 proposal ID；正式 ADR 编号和 Canonical authority 留给唯一整合者。
- 当前 self-host `.project-orrery.json` 仍缺少 `authority_model_version`，没有被测试或工具自动补写。
- `PUBLIC_AUTHORITY_MODEL_VERSION = 1` 只映射内部 `amm-fixture-v1`；它没有从 Core 顶层导出。
- Capability `eligible` 只表示消费者支持该模型，不能证明四项 conformance 输入已经提供或 Validation 已通过。

## 实现检查

| Check | Result |
| --- | --- |
| 9-case compatibility fixture | PASS — absent、supported、known unsupported、unknown newer、numeric gap、discrete model 3、null/string/bool invalid 均有冻结预期 |
| Discrete support | PASS — `[1, 3]` 不会把模型 2 当作范围内支持 |
| Legacy handling | PASS — 字段缺失为 `legacy-unversioned`；显式 null 为 `invalid`；二者均只保留 read-only browsing |
| Fail-closed claims | PASS — unavailable 时禁止推导 effective/current/implemented/validated |
| Capability declaration validation | PASS — duplicate、非正整数、bool 与 supported 非 known 子集均拒绝 |
| Upgrade orthogonality | PASS — fixture 冻结 ordinary tool upgrade 不选择模型，初次 capability 不改变 manifest/document schema version |
| Public surface | PASS — judgment 仍是未导出的 Core 内部模块，project/release manifests 和 schema 未修改 |

## 运行结果

- `python -X utf8 -m unittest tests.test_authority_model_compatibility -v`：8/8 PASS。
- Authority 六组专项：57/57 PASS。
- `python -X utf8 -m unittest discover -s tests`：118 项，116 PASS，2 项动态依赖按设计 SKIP。
- Integrated installation：PASS，authority status 仍为 integrated candidate。
- Static docsite：PASS，942 KB；10 ADR、6 State、12 Plan、68 classified docs。
- Markdown local-link scan：PASS，256 份 Markdown、536 个本地链接／图片、0 missing target。
- `git diff --check`：PASS。

## 不证明什么

- 不证明 PO-DEC-AUTH-002 已获得正式 ADR 编号或进入 Canonical history。
- 不证明旧项目已经迁移到模型 1。
- 不证明 release manifest、installer、validator、update checker 或 Viewer 已消费 capability judgment。
- 不证明 strict conformance 已通过；该判断还需要 model version、repository snapshot、fact scope 与 evidence visibility 四项输入。
- 不改变公开 v0.2.0、Core API 1 或任何 component support status。
