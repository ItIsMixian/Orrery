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

- 尚未为仓库外 benchmark 定义长期保留和可移植导出格式。
- 当前大量研究资产尚未进入 Git 历史。
