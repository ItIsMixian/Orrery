# Validation：W1 与第二平台 Adapter 本地集成

Date: 2026-08-22
Scope: 从当前 `main@8df974f` 在独立 integration worktree 中吸收 W1 Personal collaboration Phase 0 与 Claude Code／DeepSeek Harness Adapter 候选，解决编号／状态冲突并验证联合源码；不含 push、tag、Release、公开分发或支持状态提升
Result: PASS — combined source, authority relations, structure, isolated docsite, links and full regression passed; local main absorption authorized, but no push, tag, Release or support promotion occurred

## 输入与整合顺序

- 基线：`main@8df974f66be032fe27f9305bd6cceedef70ccfdb`。
- W1 输入：`codex/w1-personal-core-contract@0188818d693dcadabc50387bd8f4af815e612a88`，先以 no-ff merge 吸收。
- 第二平台输入：`codex/claude-deepseek-adapters@b72daeb0322076782dcee453f518054f69fbcd16`，按 `209cfc3`、`b72daeb` 两个逻辑提交重放。
- 整合目录：`D:\coding warehouse\project-orrery-integration-w1-p3-20260822`；分支：`codex/integrate-w1-p3-20260822`。

两个来源未共享工作目录；主 worktree 在验证完成前保持 clean。原始分支与 worktree 均保留，不在本轮清理。

## 冲突与修复

- W1 与当前 main 无文本冲突。
- 第二平台第一提交与 W1／main 在 ADR 索引及多个 State／Validation 索引上重叠；整合保留主线 Authority／治理事实，并以附加方式加入平台事实。
- 第二平台旧分支创建时把 Phase 4 决定占为 `ADR-0010`，但当前主线的 0010–0012 已分别分配给 Authority evaluator、Authority Model compatibility 与文档治理。整合将该决定改为 [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)，只更新该 Workstream 的引用，不改写既有 ADR。
- Authority relation 专项首次发现冻结期望少了 `ADR-0013 amends ADR-0004`。Core 解析结果正确；测试夹具补入新 Canonical 关系后，Authority／W1／Adapter 联合专项 31/31 通过。
- `packages/component-versions.json` 保留 W1 的 Core 0.1.1／CLI 0.1.6，同时增加 Claude Code／DeepSeek Harness 0.1.0；两种 Adapter 的 CLI 要求 `>=0.1.1,<0.2.0` 与当前源码兼容。

## 权威边界

- W1 Phase 0 进入本地 Canonical source，只证明版本化 contract、Git fixture、只读解析与 zero-network 默认；Phase 1–5 未因此完成。
- Claude Code／DeepSeek Harness 均保持 `experimental`／`unreleased`。Claude 没有成功认证后的模型响应；DeepSeek 的 editable 路径已有真实模型证据，但普通 wheel CLI 的 Observatory assets 定位仍阻止完整兼容门，`verified` 为空。
- 本地 Canonical source 不等于 `origin/main`、tag 或 Release。本轮只有本地 `main` 快进后才形成 Canonical；推送须另行执行。

## 验证

- W1／Claude／DeepSeek 专项：16/16 PASS。
- Authority relation + W1／Claude／DeepSeek 联合专项：31/31 PASS。
- 首轮全仓：247 项，241 PASS、5 expected skips、1 failure；唯一 failure 为 ADR-0013 的新 amendment 未加入冻结测试期望，已按上文修复。
- 最终全仓：247 项，242 PASS、5 expected skips、0 failures。
- `validate_installation.py --target . --require-integrated`：PASS；Authority model 1 为 supported／strict-evaluation eligible，authority status 为 integrated candidate。
- 静态站首次用相对 `--docs docs` 调用时，构建器拒绝将相对路径与绝对仓库根比较；改为绝对 `--docs`／`--agents` 后 PASS。输出位于仓库外 `D:\coding warehouse\project-orrery-validation-w1-p3-20260822\index.html`，1,337,774 bytes；13 ADR、6 State、7 subsystem、2 Snapshot、100 docs、16 Plan、6 Library。
- Markdown 扫描：295 个文件、765 个本地链接、0 missing；旧 `0010-claude-code-and-deepseek-harness-adapters` 路径 0 命中；`git diff --check` PASS。
- `docs/_site/index.html` 未创建或修改，真实凭据、原始 transcript、缓存和发布资产均未加入整合提交。

## 结论

整合候选通过本地验收，可以按 fast-forward 吸收到本地 `main`。该结论不等于已推送或已发布；公开 `origin/main`、tag 与 v0.2.0 Release 在另行推送前保持不变。
