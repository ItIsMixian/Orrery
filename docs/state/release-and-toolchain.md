# 发布与工具链 State

Updated: 2026-08-18

## 当前事实

- Project Orrery v0.2.0 已通过 annotated tag 和 [GitHub Release](https://github.com/yw9299-stack/project-orrery/releases/tag/v0.2.0)公开发布；tag 指向 `20fc95b`。
- 正式 zip SHA-256 为 `13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`，发布资产中的 checksum 已通过重新下载复核。
- Skill、目标工具链、项目 manifest 格式和文档 schema 分别版本化。
- 默认安装只创建缺失文件；`--upgrade-tools` 只处理白名单并先备份。
- installer 对 `__pycache__`、`.pyc`、`.pyo` 的排除，以及模板 `.venv/`／`venv/` 忽略规则已进入 v0.2.0。
- Pilot 004 中产生的共享 compatibility gate、凭据撤销和缓存实现都在隔离仓库中，不属于当前产品实现。

## 实现证据

- `skills/project-orrery/scripts/install_project_orrery.py`
- `skills/project-orrery/scripts/validate_installation.py`
- `skills/project-orrery/scripts/check_project_orrery_update.py`
- `skills/project-orrery/release-manifest.json`
- `scripts/package_release.py`

## 已知缺口

- v0.2.0 已发布；下一补丁需要修复 Windows／Linux ZIP 行尾和权限元数据差异，才能宣称跨平台 byte-for-byte 可重复打包。
- 架构维护工作区和公开发行面的长期组织方式仍在 Backlog，尚无 ADR。
