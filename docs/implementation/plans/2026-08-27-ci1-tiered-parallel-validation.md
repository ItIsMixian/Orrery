# 实施计划：CI1 分级并行验证

Status: Completed (Worktree checkpoint)

Date: 2026-08-27

Fact scope: Worktree `codex/ci1-tiered-parallel-validation`，基线 `codex/w5d-lan-collaboration-harness@ae6913ee354511605ab9349244b1beaea913bfac`

Governing authority: [Product Seed](../../core/principles.md)、[Test Coverage State](../../state/test-coverage.md)、[Release and Toolchain State](../../state/release-and-toolchain.md)、[Candidate-first gate](../../validation/2026-08-22-candidate-first-main-promotion-gate.md)、[tiered validation policy](../../validation/2026-08-22-tiered-validation-policy.md)

## 目标与边界

把 self-host CI 从普通 push 的双平台串行全仓，改为 Fast 与显式 Promotion 两个角色。Promotion 必须绑定冻结 exact ref/SHA，在 Windows／Ubuntu 内并行分片，完整执行自动发现的最终 unittest ID，并以现有 `smoke-test (windows-latest)`／`smoke-test (ubuntu-latest)` 名称失败关闭聚合。Fast 只给局部反馈，不构成 Candidate／Promotion 完整证据。

不修改 branch protection、main、其他功能分支、tag 或 Release；不删除真实 Git/worktree/package/security 路径。无 hosted run 时只报告本机实测和投影，不宣称远端 90 秒／4 分钟目标达成。

## 实施阶段

1. 增加 dependency-free inventory 与 shard manifest：从最终 unittest discovery 取得 test ID；校验每项精确分配一次、未知／重复／漏项与失效 selector 全部失败。
2. 增加 dependency-free timing runner：逐项记录 SHA、OS、Python、shard、test ID、outcome、duration，并无损传播 unittest 失败／错误／skip 语义和 JSON artifact。
3. 建立 Fast workflow：每次非 main push／PR 运行结构、schema/contract、纯单元和最小高风险测试，并通过独立 validator 固定其非 Promotion 角色。
4. 建立 Promotion workflow：只接受显式 workflow dispatch 的冻结 ref 与 exact SHA；按 Authority/Core、W1-W2、W3、Team/LAN、Workspace Maintenance、Context Routing/Harness、Packaging/Adapters/docsite、Release/migration/restore 分片，拆开长模块。
5. 增加 fail-closed artifact aggregator 与静态 CI validator：检查 exact-SHA binding、所有 shard 成功且 artifact 齐全、test ID 全集恰好一次、动态构建标志、安全／结构／站点／链接／打包门，以及最终 required-check 名称。
6. 按 Fast→Checkpoint 验证；只选择性运行慢 shard。同步受影响 State、Validation、DEVLOG 与索引，不改根 PROGRESS／HANDOFF。

## 完成结果

- 最终 discovery 为 342 个唯一 unittest ID；26 个 Promotion shard 将每项恰好分配一次，所有 selector 在当前树上有效。W6 七个方法各自独立；Personal Observatory 再拆为三片。
- Fast 固定为 40 项非 Promotion 子集；最终本机 Windows runner 内 3.897s、端到端 4.639s。该结果只支持 hosted Windows ≤90s 的投影，不构成远端达标证据。
- timing JSON 在每项记录中绑定 SHA、OS、Python、shard、test ID、outcome 与 duration；runner 保留 unittest failure／error／skip／expected-failure／unexpected-success 语义。
- Promotion preflight 绑定冻结 ref 与 exact SHA；后续 job 只 checkout 该 SHA。普通 push／PR 只跑 Fast，完整 Promotion 只由显式 dispatch 或 `promotion/**` push 启动。
- Windows／Ubuntu 各自运行相同完整 inventory；最终 aggregator 复核 matrix/gate 状态、artifact 数、manifest/inventory hash、环境开关和 once-only test IDs，并保留既有 required-check 显示名。
- 本机最终 `workspace-remove` shard 1/1 PASS，runner 148.99s、端到端 149.81s；其余 hosted 分片并发、排队、缓存与总 wall-clock 必须由中央 exact-SHA run 验证。

## 验证矩阵

- Fast：manifest/inventory completeness、selector 失效、timing result schema/exit semantics、workflow static contract。
- Checkpoint：每个 shard selector dry validation，代表性短 shard与最慢 shard选择性实跑，聚合器的缺失／重复／失败／取消模拟。
- Worktree checkpoint：integrated structure、隔离 docsite、Markdown links、forbidden artifact、`git diff --check`，以及一次完整 test-ID 分配完整性验证。
- Promotion：中央整合者后续把冻结 Candidate exact SHA 推到 `promotion/**`，或从默认分支 workflow 显式 dispatch ref＋SHA；验证 hosted Windows Fast ≤90s、完整 Windows wall-clock ≤4m，并取得两个原 required checks。本 Workstream 不产生该远端证据。

## 预期写入

- `.github/workflows/`：Fast 与 Promotion workflow。
- `scripts/ci/`：manifest、inventory、runner、aggregator、静态 validator。
- `tests/`：CI 工具与 workflow fail-closed 回归。
- `docs/state/{test-coverage,release-and-toolchain,project-structure,documentation-system}.md`、本 Plan、独立 Validation、`docs/DEVLOG.md` 与 Validation 索引。
