# 项目结构 State

Updated: 2026-08-18
Governing ADR: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md)

## 当前事实

- 单一 Git 仓库根：`D:\coding warehouse\project-orrery`。
- 发布产品源：`skills/project-orrery/`。
- 项目文档权威根：`AGENTS.md` 与 `docs/`。
- 自托管观测台：根 `scripts/docsite/` 与 `start-docsite.bat`。
- 非权威研究控制面：`experiments/context-routing/`。
- 本地大型原始运行根：`D:\coding warehouse\project-orrery-benchmark`，不属于 Git 仓库。
- 原始运行由仓库内 `experiments/context-routing/harness/raw-evidence-retention-policy.json` 与 `seal_raw_evidence.py` 管理 manifest、校验和、分类和到期状态；工具不自动删除。
- 发布打包与 CI：`scripts/package_release.py`、`.github/workflows/`。

## 当前边界

- 模板源与本仓库安装副本是两个角色：模板位于 `skills/project-orrery/assets/project-template/`，根观测台用于本仓库阅读。
- `docs/_site/`、缓存、凭据和 benchmark 原始输出不是作者文档或发布资产。
- 自托管、实验和测试资产已进入 `main`；v0.2.0 tag／Release 指向发布提交 `20fc95b`，后续当前事实由 main 上的发布后文档继续维护。

## 实现证据

- `.project-orrery.json`
- `skills/project-orrery/release-manifest.json`
- `scripts/package_release.py`
- `.github/workflows/validate.yml`, `.github/workflows/release.yml`

## 已知缺口

- 已定义 R0 受限原始层、R1 脱敏可移植层和 R2 权威结论层；尚未实现自动 R1 导出器。
- H2／Harness／retention 研究资产已随 `bb2c768` 与 `96bfd21` 进入本地 `main`；远端 `origin/main` 尚未包含本轮提交。
- Pilot 005／006 的版本化控制包位于 `experiments/context-routing/pilots/`；R0 原始运行只位于仓库外 `project-orrery-benchmark`，仓库内只保存 R2 结论与可复现控制面。
