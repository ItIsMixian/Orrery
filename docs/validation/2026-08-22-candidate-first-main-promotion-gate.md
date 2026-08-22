# Validation：Candidate-first main promotion gate

Date: 2026-08-22
Scope: 为 Project Orrery self-host GitHub 建立服务端 main 推广门，阻止未经 Windows／Ubuntu 矩阵验证的新 SHA 先进入 main；不强制 PR，不修改发布版本
Status: Candidate branch CI pending；main protection 尚未启用

## 问题

此前多次把 integration commit 先推到 main，再由 GitHub Actions 暴露 Windows／Ubuntu 差异。虽然失败被保留并修复，但 main 会短暂变红，且权威文档需要追加“失败→修复→复验”提交，进一步触发重复 CI。

本机全仓测试不能完全模拟 GitHub runner 的 8.3 路径、预装工具和跨 OS checkout。继续增加本地自述或重复测试不能消除这一分布式差异。

## 决定的运行方式

1. 唯一整合者在独立 integration worktree 形成 clean Candidate commit；
2. 推送 Candidate branch，等待 exact SHA 的 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`；
3. 两项均成功后，才把同一 SHA fast-forward 到 main；
4. GitHub branch protection 要求两个 context 且 `strict=true`，`enforce_admins=true`；
5. 不要求 PR，不允许 force push 或删除 main。

required checks 依赖 `.github/workflows/validate.yml` 的稳定 job name。规则只保护本仓库 main，不等于 Project Orrery 已实现 provider-neutral review/integration CLI。

## 验证计划

- 当前 main protection 读取结果为 404 `Branch not protected`；
- 本 Candidate commit 先在 `codex/main-promotion-gate` 运行双平台矩阵；
- 矩阵通过后写入保护规则并回读 exact contexts／strict／admin enforcement；
- 只把已验证 Candidate SHA 推到 main，再验证 main、origin/main 与 GitHub commit SHA 一致；
- 不创建 tag、Release 或 PR。
