# Validation：DeepSeek Wheel／W1 Windows CI 修复

Date: 2026-08-22
Scope: 修复 DeepSeek wheel Canonical 集成首次 GitHub Actions 暴露的 Windows-only test-environment 与 worktree path alias 问题；不改变协作 contract、DeepSeek verified scope、tag 或 Release
Result: PASS — 本地专项／动态全仓通过，修复提交的 GitHub Actions Windows／Ubuntu matrix 双 PASS

## 触发证据

`main@afdbc3b` 已推送，GitHub Actions [32500503338](https://github.com/yw9299-stack/project-orrery/actions/runs/32500503338) 的 Ubuntu job 通过，Windows job 失败。两个失败均发生在仓库测试层：

1. GitHub Windows runner 的临时目录以 `RUNNER~1` 8.3 路径进入 Python，而 `git worktree list` 返回等价长路径；`collaboration.primary_worktree` 的绝对路径覆盖因此被误判为未列出。
2. 新 wheel 回归使用 `pip wheel --no-build-isolation`，Windows runner 没有预装 `wheel`，在 `bdist_wheel` 之前失败；Ubuntu runner 与本机因已有该测试依赖而通过。

失败 run 保留为真实历史，不重跑或改写原证据。

## 修复

- Core 的 worktree 路径比较在 `abspath` 后使用 `realpath`，再执行平台 `normcase`；Windows 会把 8.3／长路径别名收敛为同一现有路径，Linux 行为保持绝对真实路径比较。
- GitHub Actions 将 `wheel>=0.41,<1` 明确列为测试依赖；产品运行依赖、docsite requirements 和发布包不因此增加 `wheel`。
- 没有删除测试、增加 Windows skip、放宽“override 必须是已列出 worktree”规则，或修改 Team／网络边界。

## 本地验证

- `tests.test_collaboration_contract` + `tests.test_cli_wheel_installation`：11/11 PASS；
- `ORRERY_TEST_BUILD=1` 动态全仓：248 项，245 PASS + 3 Windows symlink privilege skips；
- integrated structure：PASS；隔离静态站构建到 `D:\coding warehouse\project-orrery-validation-deepseek-w1-ci-fix-20260822\index.html`：PASS；
- Markdown：298 files／782 local links／0 missing；高置信 token／private-key scan 与 `git diff --check`：PASS；

## 远端复验

修复提交 `000111d` 进入 `origin/main` 后，GitHub Actions [32554191374](https://github.com/yw9299-stack/project-orrery/actions/runs/32554191374) 完成：

- Windows `smoke-test`：PASS（2m39s）；
- Ubuntu `smoke-test`：PASS（50s）。

因此两个首轮失败点均已由独立远端环境复验关闭。该结论不创建新 Release，也不扩张 DeepSeek manifest 已记录的精确 runtime 范围。
