# Validation：W1／D1／C1 Canonical 集成

Date: 2026-08-22
Scope: 在独立 integration worktree 中按 W1→D1→C1 顺序吸收 Personal Phase 1、文档治理 finding contract 与 Oracle v0.2 静态 controls；同步当前 State，但不启动 W2/D2/C2、Pilot 010、tag 或 Release
Result: PASS — 本地联合验收通过；首次远端 Ubuntu PASS／Windows FAIL，路径断言修复后 Windows／Ubuntu 双 PASS

## 输入与整合顺序

- Canonical base：`main@606e2c8dad0b32da009c369402a8d0b56ecbb333`；开始时 main、origin/main 和四个参与 worktree 均 clean。
- W1：`codex/w1-3-personal-phase-1c@1882002`，包含 W1.1／W1.2／W1.3 六个 stacked commits；因直接后继 main 而 fast-forward 吸收。
- D1：`codex/document-governance-finding-contract@d1e2775`；实现路径无冲突，DEVLOG、Documentation State 与 Validation 索引按当前事实增量合并。
- C1：`codex/context-routing-oracle-v0-2-static@30deb0a`；研究实现无冲突，DEVLOG 与 Validation 索引增量合并。

共享文档冲突没有使用整文件覆盖。W1 当前事实、D1 非权威 finding 边界和 C1 只具备设计申请 readiness 的限制均被保留。

## 整合期发现

首次联合专项中，W1 与 D1 的 33 项通过，C1 两项因 `application.facts.json` hash mismatch 失败。原因是 C1 manifest 冻结 LF 工作树字节，但新 D 盘 integration worktree 按全局 `text=auto` checkout 为 CRLF。

修复是在 `.gitattributes` 为 `experiments/context-routing/oracles/oracle-v0.2/fixture-source/**` 明确 `eol=lf`，并恢复原始 LF bytes；manifest 继续使用原 SHA-256，没有更新哈希迁就当前机器。Pilot 004–009 冻结目录未修改。修复后联合专项 35/35 PASS。

## 本地验证

- W1／D1／C1 联合专项：35/35 PASS；
- 默认全仓：273 项，268 PASS + 5 existing environment／optional-dependency skips；
- `ORRERY_TEST_BUILD=1` 动态全仓：273 项，270 PASS + 3 Windows symlink privilege skips；
- Oracle fixture 原 hash、`model_calls: 0` 与 `pilot_created: false` 保持不变；
- Oracle direct verify/self-test：7/7 fixture files、20/20 controls，`model_calls: 0`、`pilot_created: false`；
- Benchmark：24 corpus tasks + 6 checked-in run records；Pilot 004–009 frozen subdirectory diff：0；
- integrated structure：PASS，Authority Model 1 supported／strict-evaluation eligible；
- 隔离静态站构建到 `D:\coding warehouse\project-orrery-validation-w1-d1-c1-20260822\index.html`：PASS；
- Markdown：332 files／843 local links；只有 D1 `broken-link-positive.md` 的 1 个预期 synthetic missing target，0 unexpected missing；
- 高置信 secret scan：0；forbidden tracked artifacts：0；`git diff --check`：PASS。

## 权威与发布边界

- W1 Personal Phase 1、D1 contract/fixture 与 C1 static controls 进入 Canonical source，不等于相应能力已发布。
- W2 Scope/Finding、D2 scanner/CLI、C2 Pilot 010 design 都未自动启动；Pilot 010 未创建且无模型运行授权。
- Adapter 0.1.1／CLI 0.1.9 没有继承旧 Adapter 0.1.0 runtime evidence；公开 v0.2.0、tag、Release 和用户级 Skill 均不变。

## 首次远端矩阵

`main@7e194b5` 的 GitHub Actions [32564000587](https://github.com/yw9299-stack/project-orrery/actions/runs/32564000587) 为 Ubuntu PASS／Windows FAIL。Windows runner 的 `TEMP` 使用 `RUNNER~1`，Git 返回同一 session 的长路径；测试对两种等价路径做 `Path` 字面相等比较，导致 independent clone 子案例提前退出，随后又产生派生的 session-list IndexError。

产品的 Git-private containment 检查和返回路径均正确。修复只把测试断言收敛为 `abspath + realpath + normcase`，不放宽 session 必须位于当前 worktree Git dir 的安全边界。单项复跑 1/1、完整 collaboration 专项 22/22 PASS；新的远端矩阵通过前不宣称跨平台验收完成。

修复提交 `481f452` 进入 `origin/main` 后，GitHub Actions [32564334514](https://github.com/yw9299-stack/project-orrery/actions/runs/32564334514) 完成：Ubuntu PASS（48s），Windows PASS（4m20s）。因此 W1／D1／C1 Canonical source 的本轮跨平台门关闭；这仍不构成 tag、Release、Adapter 0.1.1 runtime verification 或 Pilot 010 授权。
