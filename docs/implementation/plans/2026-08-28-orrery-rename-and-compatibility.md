# 实施计划：Orrery Rename and Compatibility R3–R5

Status: Active; R3 completed and entered Canonical main, R4/R5 remain future independent Workstreams

Date: 2026-08-28

Governing decision: [ADR-0015](../../decisions/0015-orrery-brand-and-compatibility-contract.md)

Approved Design: [Orrery Rename and Compatibility Contract](../../design/orrery-rename-and-compatibility-contract.md)

## Goal and current stop

在不改写历史、不抢占 PyPI `orrery`、不破坏已安装用户的前提下，分三项后续 Workstream 完成品牌收口、
兼容 alias 和可选默认入口评审。R3 已在独立 Workstream 中完成本地 Candidate 实现与验收；它只改变
allowlisted 当前 display surfaces，不修改稳定 package/schema/CLI/Skill/Adapter identity、remote/tag/Release。

R3 exact Candidate SHA 已在 non-main ref 完成 Windows／Ubuntu required checks，并由后续 verified
descendant 进入 Canonical main；它仍未形成新 Release。R4、R5 不随 R3 自动启动，必须分别建立后续
独立 Workstream。

## R3 — Brand-only closeout

### Expected writes

- active `README.md`／`README.zh-CN.md` 与当前用户说明；
- self-host Observatory/Broker/Adapter display title/description 及对应 golden/UI tests；
- 必要的当前 State、Validation、DEVLOG 与普通索引；
- GitHub repository description 如需改动，必须拆成维护者显式远端操作，不与 source commit 混写。

### Explicit denylist

- `skills/project-orrery/release-manifest.json`、Core v0.2 bridge、phase-0 frozen baseline；
- 历史 ADR/Validation/Snapshot/DEVLOG 段、完成/停止 Plan、Pilot/benchmark fixture；
- distribution/import/CLI/Skill/Adapter IDs、project manifest path/name、schema `$id`、contract/hash/receipt、
  Authority Model、Workstream IDs、keyring/cache/backup namespaces。

### Acceptance

- brand allowlist 使用 Orrery，中英文和 self-host 页面一致；目标项目 title token 仍可定制；
- frozen denylist `git diff --exit-code`，v0.2 hashes 与 Release assets 只读核验不变；
- focused golden/UI tests、Fast、structure/build、links、forbidden artifact、`git diff --check` 通过；
- exact Candidate SHA 在非 main ref 取得 Windows/Ubuntu required checks。

### R3 completion

- `tests/fixtures/brand/orrery-brand-contract-v1.json` 已机械冻结 current-brand allowlist、stable/protocol/history denylist、8 份 schema 与 v0.2 frozen hashes；
- 当前 README／文档入口、默认 self-host docsite、Personal／Team／Graph、Broker 和安全 display metadata 已统一显示 Orrery，目标项目 title token 仍可定制；
- 本地 focused／Fast／integrated installation／isolated docsite／repository gates／links／diff 与 1280px、390×844 Browser 验收已通过，证据见 [R3 Validation](../../validation/2026-08-28-r3-orrery-brand-only-closeout.md)；
- remote description 只读核验，未修改 GitHub settings；source 已由 verified descendant 进入 `main`，但没有打 tag／Release、选择 SemVer 或迁移任何本地目录／Codex 数据；
- exact Candidate SHA 的 non-main Windows／Ubuntu required checks 已通过，R3 已由后续 verified
  descendant 进入 Canonical main。没有 tag／Release、本地目录迁移或技术 ID alias；R4/R5 未开始。

### Rollback

仅回退 display changes 与对应 tests；不迁移或回滚用户数据。repository description 由维护者独立恢复。

## R4 — Compatible aliases and identifier capability

### Expected writes

- future（非 v0.2）manifest/capability schema 与 old/new reader fixtures；
- Core resolver、CLI collision diagnostics 和机器稳定 warning；
- 显式 opt-in、collision-checked 的 `orrery` thin launcher，严格路由到单一 canonical CLI；不得复制完整实现；
- 各宿主默认只改 display metadata；仅在宿主独立证明 safe discovery/upgrade/uninstall 后增加 thin alias；
- 安装/升级/卸载/mixed-state tests；
- brownfield inspect/dry-run/apply/restore contract（若实际产生任何本地 identifier write）。

### Acceptance

- old only、alias only、same-implementation mixed、two-full-implementation、future/invalid manifest 全覆盖；
- 新旧 CLI route 相同 exit/JSON/write plan/result，warning 不污染 stdout；PATH 与第三方 `orrery` 冲突失败关闭；
- 每个宿主只有一个 canonical implementation；Codex/Claude/DeepSeek/Harness 各自验证，不互相外推；
- ordinary upgrade 零 identifier/secret/config/backup 写入；真实 keyring 内容不读出、不进入日志；
- v1 schema/contract/hash/receipt/Workstream 与 v0.2 frozen hashes 不变；
- Fast + relevant Checkpoint/Candidate + exact-SHA Windows/Ubuntu Promotion 全绿。

### Rollback

删除本阶段新增的 alias launcher/capability，旧 `project-orrery*` route 继续工作；若产生显式本地迁移，
restore 必须绑定 receipt 并只撤销该事务创建的对象。

## R5 — Optional package/CLI default transition

### Entry conditions

- 至少一个完整 0.3.x alias window 的已发布证据；
- registry/PATH、old-user upgrade、new install、mixed-version project 和各 Adapter matrix 当前；
- 维护者明确选择实际 SemVer、candidate manifest、release notes 与 preferred CLI behavior。

### Expected writes

- 可选 preferred `orrery` CLI launcher/default 与文档；旧命令不删除；
- 首个新 Release 固定使用 `project-orrery-*` archive/asset filename 并显示 Orrery 品牌；更晚的 filename
  变化另行评审，同时保留 updater 对旧名读取；
- **不**新增 `orrery` Python distribution/import；`project-orrery-*`／`project_orrery_*` 保持；
- release candidate manifest/tests、State/Validation/DEVLOG；远端 tag/Release 另需明确授权。

### Acceptance

- v0.2.0 tag/Release/assets/checksum/frozen manifest 与所有旧项目 reader 不变；
- old install→new、new install、mixed versions、offline update、downgrade/restore、wheel/import identity 通过；
- CLI default 切换可独立回滚且旧 route 仍在 0.3.x 全程支持；
- non-main exact SHA 的 Windows/Ubuntu required checks 通过后才可由维护者推广 main；发布另行确认。

### Rollback

恢复 preferred route/asset naming，保留 alias 和旧 reader；不得删除新版本已生成的可验证历史资产。
R5 可在证据不足时以“保持现有技术 ID/default”结束，不视为失败。

## Optional cleanup review

最早 0.4.0 才能建立新的 cleanup ADR/Plan；到达版本号不自动注册任务或删除入口。旧 project manifest、
v1 protocol、v0.2/frozen evidence、backup restore、secret fallback 和历史 receipt 永不属于字符串清理。

## Local directory and Codex data follow-up

R3 Brand-only 完成、exact Candidate SHA 通过规定门并进入 `main` 后，即可另开本机维护 Workstream：
freeze clean SHA → 保存并关闭或重建 worktrees → primary root 从 `project-orrery` 改为 `Orrery` → 更新 Codex
Saved Project → 验证并保留旧路径回滚。该维护不依赖 R4/R5 公共兼容周期，也不由本 Plan 自动执行。
随后才能另开 Codex application-data D 盘迁移；两项任务的 plan、backup、rollback 和确认不得复用。

## State and promotion obligations

每个实现 Workstream 同步受影响 subsystem State、独立 Validation、DEVLOG 和索引。普通功能分支不改根
PROGRESS/HANDOFF；唯一整合者在干净 integration worktree 同步全局入口。任何 v0.2 hash drift、历史批量
diff、双完整实现、secret access、mixed-state divergence、缺少 rollback 或 required checks 未通过立即停止。
