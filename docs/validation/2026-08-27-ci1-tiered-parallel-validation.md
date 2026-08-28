# Validation：CI1 分级并行验证 Worktree Candidate

Date: 2026-08-27

Status: Fast／Checkpoint PASS；hosted exact-SHA Promotion 待中央验证

Fact scope: `codex/ci1-tiered-parallel-validation`，基线 `codex/w5d-lan-collaboration-harness@ae6913ee354511605ab9349244b1beaea913bfac`

Governing authority: [Product Seed](../core/principles.md)、[CI1 Plan](../implementation/plans/2026-08-27-ci1-tiered-parallel-validation.md)、[tiered validation policy](2026-08-22-tiered-validation-policy.md)、[Candidate-first gate](2026-08-22-candidate-first-main-promotion-gate.md)

## 结论

CI1 在 Worktree scope 把普通 push／PR 与完整 Promotion 分开。Fast 只运行 40 项非 Promotion 子集；Promotion 只接受显式 workflow dispatch 的 candidate ref＋exact SHA，或限定 `promotion/**` 的冻结分支 push。preflight 绑定 ref/SHA 后，所有 Windows／Ubuntu job 只 checkout exact SHA。

最终 unittest discovery 为 342 个唯一 test ID。dependency-free manifest 将其恰好分配到 26 个 shard，覆盖 Authority/Core、W1-W2、W3、Team/LAN、Workspace Maintenance、Context Routing/Harness、Packaging/Adapters/docsite、Release/migration/restore。W6 七个方法各自独立分片；既有约 353s 的 Personal Observatory 邻接面拆为三片。漏分配、重复分配、dead selector、加载失败均在执行前失败。

runner 不改变 unittest verdict；每项 JSON record 绑定 SHA、OS、Python、shard、test ID、outcome 和 duration。Windows／Ubuntu aggregator 重新 discovery，并要求 matrix 与 repository gate 成功、每个 shard artifact 恰好一个、hash／SHA／OS／动态开关当前、每个 test ID 恰好执行一次。matrix/job 取消或跳过、artifact 缺失、test 漏失／重复、runner failure/error/unexpected-success 都不能变绿；unittest 的合法 skip／expected-failure 仍算实际执行并保留语义。

最终 required-check 显示名仍精确为 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`。本 Workstream 没有调用 GitHub API、改 branch protection、push、合并 main、tag 或 Release。

## 自动验证

| 命令／检查 | 结果 |
|---|---|
| `python -X utf8 scripts/ci/test_inventory.py --output <temp>/inventory.json` | PASS；342 unique IDs，26 shards，40 Fast IDs；0 missing／duplicate／dead selector。 |
| `python -X utf8 scripts/ci/validate_ci.py --all` | PASS；Fast/Promotion 角色、冻结 branch/dispatch、exact-SHA checkout、完整面、动态 build、repository gates、aggregator 与 required names 均存在。 |
| `python -X utf8 -m unittest tests.test_ci_validation -v` | 8/8 PASS，最终 3.012s；覆盖 inventory 漏项／重复／dead selector、runner failure 语义与 per-test timing binding、aggregate success 和 missing/duplicate/failure/cancel/skip、workflow 角色及 SHA mismatch/main/alias 拒绝。 |
| YAML parse（本机 PyYAML，只作语法辅助） | `fast-validation.yml` 与 `validate.yml` 均 PASS；CI 工具本身不依赖 PyYAML。 |
| `python -X utf8 scripts/ci/run_test_shard.py --profile fast ...` | 40/40 PASS；最终 runner 3.897s，本机端到端 4.639s，Windows 11／Python 3.13.5，`ORRERY_TEST_BUILD` 未设置。 |
| `ORRERY_TEST_BUILD=1 python -X utf8 scripts/ci/run_test_shard.py --shard workspace-remove ...` | 1/1 PASS；runner 148.990s，本机端到端 149.805s；per-test JSON 完整。 |
| `python -X utf8 scripts/ci/validate_repository_gates.py` | PASS；619 个 tracked/untracked repository paths、332 份 Markdown、911 个本地链接、0 forbidden runtime/generated artifact。 |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS；Authority status `integrated candidate`、Authority Model 1 strict eligible。 |
| 隔离 `scripts/docsite/build_docsite.py --out <temp>/index.html` | PASS；1,751,976 bytes，13 ADR、6 State、7 subsystem、2 Snapshot、132 docs、22 Plans、6 Library；未写 `docs/_site/index.html`。 |
| JSON／compile／`git diff --check` | PASS。 |

早一轮组合 `workspace-c` 在拆分前也以 `ORRERY_TEST_BUILD=1` 通过 2/2：remove 139.200s、scan 40.875s、runner 180.075s。该证据用于把两个方法进一步拆开，不是最终 shard artifact。

## 性能解释

已给定远端基线 run `33108760530` 为 Windows job 6m53s／测试 6m20s，Ubuntu job 1m14s／测试 59s；Windows 主要耗时 W3 150.6s、W1/W2 71.4s、context benchmark 51.1s、Oracle 24.3s、H2 22.6s，且尚未包含后续 W6/W5D。

CI1 本机 Fast 4.639s，支持 hosted Windows ≤90s 的强投影。Promotion 把上述模块分片，并将当前实测 148.990s 的 W6 最慢候选方法独立；`max-parallel: 20` 让所有 W6／Personal 重片进入 Windows 首波，Ubuntu 在 Windows shard 完成后启动以避免争抢 Windows 并发。按既有约 33s hosted job 非测试开销与本机最慢 shard估算，Windows ≤4m 是合理目标，但 runner 排队、cache 命中、hosted 性能和其他未逐项计时方法仍可能改变 wall-clock。本记录不宣称两个 hosted 目标已经达成。

## 维护者接线与远端验证

branch protection 继续要求原两个 context，无需也不得为 CI1 调用 GitHub API 改名或重配。中央整合者应：

1. 在干净 integration worktree 冻结并提交 Candidate，记录 exact 40-character SHA。
2. 首次自举可把同一 SHA 推到非 main 的 `promotion/<name>`；该受限 push 以 `github.ref`／`github.sha` 自动绑定。新 workflow 进入默认分支后，也可显式 dispatch 并填写 candidate ref＋SHA。
3. 确认 preflight inventory artifact、26 个 Windows 与 26 个 Ubuntu shard artifact、两侧 repository gate 和 aggregate receipt 全部属于同一 SHA。
4. 记录 Windows Fast 与 Promotion wall-clock；只有 `smoke-test (windows-latest)`／`smoke-test (ubuntu-latest)` 都 PASS，才可把完全相同的 SHA 快进 main。
5. 任一 ref 漂移、取消、跳过、缺 artifact、少／重 test 或 gate failure 都必须修复后冻结新 SHA 重跑，不能复用旧通过结果。

## 未完成边界

- 没有 push，因此没有 GitHub-hosted artifact transport、Windows/Ubuntu 分片、排队、cache、Fast ≤90s 或 Promotion Windows ≤4m 证据。
- 没有修改 branch protection；required context 的真实外部接线仍以现有 GitHub 状态和后续 run 为准。
- 没有自动影响分析、跨 SHA 结果缓存、fixture template/shared-clone 优化或跨 run 证据复用；所有 342 个 Promotion ID 仍各执行一次。
- `release.yml` 的 tag 发布流程保持原安全覆盖，不在 CI1 中发布或重接 Release。
