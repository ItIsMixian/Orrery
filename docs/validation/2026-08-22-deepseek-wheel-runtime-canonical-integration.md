# Validation：DeepSeek Wheel Runtime Canonical 集成

Date: 2026-08-22
Scope: 将 P1 的普通 wheel Observatory assets 修复与真实 DeepSeek Harness 复验证据吸收到当前 Canonical source，并决定精确 runtime compatibility；不创建 tag、Release 或独立 Adapter 发行物
Result: PASS — wheel 阻塞关闭，精确 runtime 范围进入 `verified`，Adapter 发行仍为 `experimental`／`unreleased`

## 输入与整合

- Canonical base：`main@56d44fb`；已包含 W1、ADR-0013、Claude／DeepSeek Adapter 与此前 Stage B 证据。
- P1 source：`codex/claude-deepseek-adapters@77811f9`；相对既有 Stage B 检查点 `b72daeb` 只有一个新逻辑提交。
- 独立整合目录：`D:\coding warehouse\project-orrery-integration-deepseek-full-20260822`，分支 `codex/integrate-deepseek-full-20260822`。
- 功能代码可直接重放；冲突仅在 DEVLOG、Release State、Test State 与 Validation 索引的并行追加。整合保留当前 main 的 W1／Authority 事实，并增量加入 wheel 修复证据。

## 兼容性决定

- Adapter 发行支持状态保持 `experimental`，组件仍未发布。
- `runtime_compatibility.status` 只对下列精确组合标记 `verified`：Adapter 0.1.0、`@deepseek-ai/dsh 0.1.0-rc.8`、Windows 11 build 26200、Core 0.1.0、CLI 0.1.1 普通 wheel、`deepseek-official`／`deepseek-v4-flash`，以及 manifest 列出的发现、显式／隐式调用、依赖失败关闭、卸载恢复与作者文件保留范围。
- 当前 Canonical CLI 0.1.6、其他 DSH／OS／Provider／模型、未来发布包和跨版本范围不继承该结论。
- 真实模型与隔离生命周期的原始证据仍由 [Stage B Runtime](2026-08-22-deepseek-harness-adapter-stage-b-runtime.md)和 [CLI Wheel Observatory Assets](2026-08-22-cli-wheel-observatory-assets.md)共同提供；本记录只证明干净集成和联合回归。

## 联合回归发现与修复

首次默认全仓发现 240 项，其中 233 通过、5 项按环境／可选依赖跳过，2 个模块在收集阶段失败。原因是主线的两组 Authority CLI 测试只把 Core／CLI source 加入 `sys.path`，而 wheel 修复后 `repository_context()` 正式依赖已在 CLI package metadata 声明的 Observatory package。

修复仅让这两组 source-layout 测试显式注入 Observatory source；没有放宽产品依赖、删除测试或增加 skip。定向复跑 10/10 通过。

## 最终验证

- DeepSeek Adapter + wheel 专项：4/4 PASS；
- Authority CLI source-layout 回归：10/10 PASS；
- 默认全仓：248 项，243 PASS + 5 expected skips；
- `ORRERY_TEST_BUILD=1` 动态全仓：248 项，245 PASS + 3 Windows symlink privilege skips；
- integrated structure：PASS，Authority model 1 为 supported／strict-evaluation eligible；
- 隔离静态站：`D:\coding warehouse\project-orrery-validation-deepseek-full-20260822\index.html`，1,361,966 bytes；
- Markdown：297 files／779 local links／0 missing；
- 高置信 token／private-key scan：0 matches；
- `git diff --check`：PASS，仅有既有 JSON LF→CRLF 工作树警告。

## 边界

- Git 与仓库测试证明代码、manifest 与整合回归；真实模型调用事实仍以 P1 的隔离 runtime Validation 为证据。
- 本次没有再次调用真实模型，也没有读取或复制 credential、GUI profile、Prompt／回答或用户 Skill 根。
- 本次不创建 tag、Release 或新公开版本；v0.2.0 继续是当前公开 Release。
