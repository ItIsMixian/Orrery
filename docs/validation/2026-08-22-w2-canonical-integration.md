# Validation：W2 Canonical 集成

Date: 2026-08-22
Scope: 基于最新受保护 main 吸收 W2 Scope/Finding Candidate，同步 State 并形成 exact integration SHA；不启动 W3/W4/W5，不创建 tag 或 Release
Status: Local PASS；Candidate-first Windows／Ubuntu CI 尚待推送

## 输入

- Canonical base：`main@6e1f9cb`，包含 Candidate-first main protection 与 workflow main 去重。
- W2 source：`codex/w2-scope-finding@3f098e3`，起点为旧 `main@193b3ba`；实现与当前 main 无路径冲突，共享文档按 additive merge 处理。
- Implementation：`de5152e`；原 Candidate Validation：`3f098e3`。

## 本地验收

- W2/W1 collaboration：27/27 PASS；
- 默认全仓：278 项，273 PASS + 5 existing skips；
- W2 原 Candidate 动态全仓：275 PASS + 3 Windows privilege skips；exact integration SHA 的动态跨平台门由 Candidate-first GitHub checks执行；
- integrated structure：PASS；隔离静态站构建到 `D:\coding warehouse\project-orrery-validation-w2-20260822\index.html`：PASS；
- Markdown：335 files／855 links；D1 positive fixture 1 个预期 missing target，0 unexpected missing；
- high-confidence secret scan、forbidden tracked artifacts 与 `git diff --check`：PASS；
- Personal Mode zero-network 与本机 L2/L3 门保持不变。

## 边界

- W2 进入 Canonical source 不等于 W3 已实现；review package、speculative integration、cleanup、closure archive 均不存在。
- W4 Observatory、W5 Team Mode、平台 launch/rebind/message 与宿主级写入拦截仍未实现。
- Core 0.1.5／CLI 0.1.10／Adapter 0.1.1 仍未发布，旧 Adapter 0.1.0 runtime evidence不外推。
- exact SHA 必须先在非 main 分支取得 Windows／Ubuntu双 PASS，才能由 branch protection 允许推广 main。
