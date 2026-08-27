# Validation：W4 health／W5B 最终 non-main integration candidate

Date: 2026-08-27

Status: 本地 Candidate gate 已完成到 exact-SHA 推送前；Promotion required checks 待运行；未合并 `main`、未发布

Scope: 在非 `main` 分支 `codex/integrate-w4-w5-20260823` 上，把 W4 健康语义修复与 W5B Team Observatory 接入已经通过双平台门的 W4／W5A integration base。本文只描述 Candidate；只有包含本文的 exact SHA 通过 Windows／Ubuntu required checks 并经维护者确认后，才具备推广资格。

## Candidate 输入

- Integration base：`31f04ff33592f71343983572ccbd16292c0d5920`；
- W4 health implementation：`a900087`；
- W5B Team Observatory implementation：`b31e1d1`；
- subsystem State／Plan／Validation checkpoint：`31b12f7`；
- 组件版本：Core 0.1.9、CLI 0.1.13、Observatory 0.1.4，均为 `unreleased`；
- `main` 仍为 `7932a9c01efb2e5125da1962873e67383982d98c`，没有 tag、Release 或公开支持变化。

## W4 健康语义验收

- Personal Observatory 不再把历史工作区债务全部累计为当前危险：首层固定为 Delivery now，后续分别为 Reconciliation 与 Workspace hygiene。
- 只有双方都具有 current session/evidence，且 lifecycle 为 active／review-pending 的 Direct finding 才计入当前 blocker。
- stale session、历史 overlap、过期 review 与未登记 Candidate 进入 Reconciliation；legacy-unmanaged、no-session、retained、estimated reclaim 与 absent-session Unknown 进入 Workspace hygiene。
- Primary root 保持 `Protected canonical root`；Unknown 完整保留，不被表达成零风险或确定冲突。
- 36-worktree-like 合成 fixture 证明：37 个历史 Direct 不再形成当前 blocker，唯一 current Direct 仍被保留为 1 个当前 blocker。

## W5B 图形化验收与边界

- 同一 Observatory 增加 Team sibling page，可图形化完成 Personal → Team → Enable → Start → heartbeat/sharing → capture/sync → request accept/reject → Stop → Disable。
- 动态入口是 root-only `scripts/docsite/serve_team_observatory.py`，固定绑定 `127.0.0.1`；默认静态／动态 docsite、managed-tool 白名单、Skill 模板与公开 v0.2.0 不变。
- 状态改变要求合法 Host、精确 Origin、随机 HttpOnly／SameSite control cookie、16 KiB body 和 exact-field 校验；错误响应不回显私有路径、credential 或 Team 内容。
- 页面没有任意命令、路径、URL、shell 参数、源码正文、Prompt／回答／transcript 或未 push diff 输入；中央 request-only，本机 accept／reject receipt 始终 `execution_performed=false`。
- UI 关闭时只停止其拥有的 loopback Coordinator，保留 Git-private Team config 与本地项目事实。
- 自动发现、真实其他设备、真实 LAN、Host 迁移／选主、云 relay、多设备和远程 shell／Agent／merge／delete 均未实现。

## 本地证据

### 功能 Agent checkpoint

- W4 health／component：14/14 PASS；
- W5A／W5B：16/16 PASS；
- frozen adjacent checkpoint：33/33 PASS，206.129s；
- Chromium 1280px 与 390×844：完整点击路径通过，无横向溢出；结束后 Team disabled、runtime absent。

完整命令、fixture 和浏览器步骤见 [W4 health／W5B Worktree Validation](2026-08-27-w4-health-w5b-team-observatory.md)。

### 中央 Candidate 门

- integrated structure：PASS；
- 隔离静态站：1,576 KB、121 docs；
- Markdown：343 files／886 local links，只有 D1 冻结 positive fixture 的预期 missing target；
- forbidden tracked artifacts：0；
- 首轮动态全仓：320 项，314 PASS + 3 个既有 Windows symlink privilege skips + 3 个失败；三项失败全部是协作 CLI 测试仍冻结 Core 0.1.8，而候选真实输出为 Core 0.1.9，不是产品行为失败；
- 将三条冻结期望更新为 0.1.9 后，原失败用例定向重跑 3/3 PASS；最终 exact SHA 仍必须由远端 Windows／Ubuntu 全矩阵重新证明。

## Promotion 边界

- 该分支必须先推送非 `main` exact SHA，并取得 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)` 双 PASS；
- 双 PASS 只证明该 exact SHA 达到 self-host promotion gate，不证明真实多机 Team Mode 或公开 Release；
- 即使双 PASS，也必须等待维护者亲自体验 Personal／Team 页面并明确确认；在此之前不得合并 `main`。
