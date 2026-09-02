# Fast Candidate Freeze and Asynchronous Validation Closeout

Status: Approved

Date: 2026-09-01

Governing ADR: [ADR-0030](../decisions/0030-fast-candidate-freeze-and-asynchronous-validation.md)

Maintainer approval: approved on 2026-09-01. Approval makes the manual process effective immediately and authorizes
W3.1 automation; it does not claim the command, receipts or asynchronous validator are implemented.

## 1. User-facing workflow

```text
预览通过
  -> 快速冻结（<30 秒）
  -> 实现任务停止，状态为“候选已冻结 / 验证待执行”
  -> 验证在后台或独立阶段运行
  -> PASS: 可整合；FAIL: 重新打开原任务
  -> 任务闭合
  -> W6.2 另行决定是否删除 worktree
```

The maintainer never waits inside the implementation task for test suites, temporary Git fixtures, package builds or
evidence prose after accepting a preview.

## 2. Candidate Freeze contract

The logical command is `orrery worktree freeze-candidate` and produces `candidate-freeze-receipt-v1`.

Required inputs:

- Workstream/session identity and current scope revision;
- exact committed task-description version;
- maintainer acceptance receipt or local acceptance fingerprint;
- expected-write set and accepted surface IDs;
- target branch and intended commit message.

Blocking checks, all bounded and local:

1. current worktree/session/branch/authority versions match;
2. no unresolved scope finding, merge conflict marker or unexpected changed path;
3. current relevant-tree fingerprint equals the accepted preview fingerprint;
4. no forbidden secret/generated/release artifact in the candidate diff;
5. `git diff --check` passes;
6. declared exact-copy pairs changed by the task are byte-identical;
7. repository status can be converted into one commit without discarding user data.

Explicitly forbidden in freeze:

- unittest/pytest or temporary Git fixture execution;
- Fast, Checkpoint, Candidate or Promotion routing;
- browser replay, full site build, relation/history provider scan or package build;
- unrelated State/PROGRESS/HANDOFF expansion;
- worktree/branch deletion, integration, push or release.

The operation stages only expected paths, commits once and writes the Git-private receipt atomically. Any failure stops
before commit and returns one concise reason. It does not attempt repairs or rerun validation.

Receipt fields include schema/contract version, Workstream, task-description SHA, scope revision, accepted-surface
fingerprint, relevant-tree hash, exact Candidate SHA, expected/staged paths, structural checks, timestamp and
`validation_status=pending`. It stores no diff/source body or transcript.

## 3. Asynchronous validation contract

Validation accepts only an immutable Candidate SHA and freeze receipt. The implementation task need not remain active.

- CI7 routing selects the smallest authorized focused window for the changed surfaces.
- Existing fresh receipts are reused only when exact surface/relevant-tree fingerprints match.
- Long owners and temporary Git fixtures run here, never in freeze.
- The result appends `candidate-validation-receipt-v1` with exact tests, outcomes, timings and environment.
- PASS changes status to `validated`; FAIL changes status to `validation-failed` and identifies the original task.
- A failure never modifies the Candidate or automatically retries. Resuming requires a new task-description amendment,
  new commit/fingerprint and new acceptance where the visible surface changed.

Validation may run through existing CI, a bounded validator process or a separate task without owning product writes.
The first implementation may use the least invasive existing runner rather than creating a scheduler.

## 4. Status and UI

Orrery exposes distinct labels:

| Machine state | User label | Meaning |
|---|---|---|
| `preview-accepted` | 预览已接受 | experience accepted; source may still be dirty |
| `candidate-frozen` + pending | 候选已冻结 · 等待验证 | clean exact commit; no PASS claim |
| `validated` | 验证通过 · 等待整合 | authorized evidence exists |
| `validation-failed` | 验证未通过 · 需要返工 | candidate preserved, original task can resume |
| `closed` | 任务已闭合 | explicit lifecycle outcome |
| cleanup eligible | 可清理工作区 | separate W6/W6.2 judgment |

Personal/Graph must not display frozen/pending as completed or closed. Maintenance cannot treat it as deletion evidence.

## 5. Time and cost budgets

- Candidate Freeze: target `<30s`, hard refusal at 60s before commit.
- No test execution is allowed to consume this budget.
- Asynchronous validation retains existing per-stage budgets and no-repeat rules.
- Documentation written during freeze is limited to the receipt/Pending Validation pointer; detailed closeout is
  event-driven after validation/integration.

## 6. Existing-task adoption

For an already accepted preview such as W7.4:

1. stop any still-running post-acceptance validation command;
2. preserve completed outputs with final exit codes; incomplete outputs remain non-evidence;
3. confirm no product write occurred after acceptance, or obtain a new preview if it did;
4. perform only Candidate Freeze structural checks and commit;
5. stop the implementation task at validation-pending;
6. consume completed receipts or schedule missing validation asynchronously.

This avoids discarding useful evidence while ensuring that a long-running check is never required merely to stop the
implementation task.

## 7. Failure and recovery

- Freeze failure leaves the worktree unchanged and active with one blocker.
- Commit failure preserves index/worktree recovery information and writes no success receipt.
- Validator failure cannot mutate or delete the frozen worktree/branch.
- A stale acceptance fingerprint returns to preview; it is not overridden by an Agent.
- Physical removal remains separately authorized after closure/history/safety evidence.

## 8. Compatibility boundary

W3.1 adds the freeze/receipt/orchestration contracts without weakening branch protection, exact-SHA Promotion,
validation semantics or public release gates. Existing tasks may continue the legacy closeout path until explicitly
adopting the new process; W7.4 is the first manual adoption.
