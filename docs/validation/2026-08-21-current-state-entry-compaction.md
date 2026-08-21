# 2026-08-21 当前状态入口压缩验证

Status: Completed documentation-maintenance review

## Scope

验证根 `PROGRESS.md` 与 `docs/state/authority-meta-model.md` 的职责压缩没有改变有效 ADR、Approved Design、活动 Plan、实现、发布契约或 Authority runtime 行为。

本轮只执行信息归位：

- PROGRESS 保留当前线路、结论、活动计划、阻塞、近期完成和下一里程碑；累计完成史继续由 DEVLOG、Validation 与 Git 历史承担。
- Authority State 保留当前规范、分层能力、默认边界、关键实现入口、综合 Validation 与缺口；逐检查点测试历史继续由 Validation 索引承担。
- Documentation System State 明确全局入口不是历史总账。

没有新增、修改或取代 ADR；没有创建 Snapshot，因为本轮不是新的阶段评估，只是当前入口的无损职责修复。

## Size and responsibility check

| Document | Before | After | Result |
|---|---:|---:|---|
| `docs/PROGRESS.md` | 146 lines / 14,984 chars | 55 lines / 3,845 chars | 当前控制面保留；累计 `[x]` 历史移出必读入口 |
| `docs/state/authority-meta-model.md` | 147 lines / 16,544 chars | 60 lines / 5,602 chars | 当前能力与缺口保留；74-line 逐文件证据目录改为分层入口 |

人工复核确认以下边界仍显式存在：

- public v0.2.0、local Canonical、runtime-verified 与 released 分开表达；
- Authority Model 1 self-host 选择不等于公开 release 选择；
- M2 `candidate_ready` 不等于 `release_ready`；
- M2.2 仍为 root-only opt-in，不是默认 managed production consumer；
- multi-worktree 自动化、Context-routing 采纳门、Broker 隔离边界和下一维护者决定仍可从 PROGRESS 直接定位。

## Reproducible checks

1. Full repository regression:

   `python -X utf8 -m unittest discover -s tests`

   The first final-tree attempt exposed one semantic regression: the new record used exact `Result: Passed`, so the strict role collector treated documentation maintenance as structured Validation success and `test_repository_roles_are_observed_without_inventing_validation_success` failed. The record was changed to non-authoritative `Status:` wording without weakening the collector or its test.

   Focused rerun: 32 Authority role／claim／projection tests passed；1 Windows symlink privilege skip.

   Final result: 231 tests discovered；226 passed；5 existing environment／optional-dependency skips；0 failures.

2. Integrated structure and static build:

   `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --build`

   Result: PASS；authority status `integrated candidate`；Authority Model 1 `supported` and strict-evaluation eligible.

3. Legacy／Authority projection rollback:

   - build the default reader and record its SHA-256;
   - set `ORRERY_AUTHORITY_PROJECTION_VIEW=1` and run `build_authority_projection.py`；projection reports `ready` and produces a different output;
   - remove the opt-in, rebuild the default reader and compare SHA-256.

   Result: explicit projection differs as expected；default rollback is byte-identical.

4. Markdown local-link scan:

   Result: 278 Markdown files；655 local links/images；0 missing targets.

5. Git whitespace check:

   `git diff --check`

   Result: PASS.

## Remaining boundary

本 Validation 只证明文档入口压缩后的结构、链接和现有运行行为保持有效。它不证明 Authority production switch、公开模型 1 release、多 Workstream 自动化或新的 Context-routing treatment 已实现。
