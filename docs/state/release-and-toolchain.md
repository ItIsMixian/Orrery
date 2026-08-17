# 发布与工具链 State

Updated: 2026-08-18

## 当前事实

- GitHub 仓库当前没有 tag 或 Release。`origin/main` 已包含 Project Orrery v0.2.0 的候选 `release-manifest.json`、兼容协议和发布工作流，但它们尚未完成公开发布。
- Skill、目标工具链、项目 manifest 格式和文档 schema 分别版本化。
- 默认安装只创建缺失文件；`--upgrade-tools` 只处理白名单并先备份。
- 工作树新增了 installer 对 `__pycache__`、`.pyc`、`.pyo` 的排除规则；该修复尚未进入稳定发布。
- Pilot 004 中产生的共享 compatibility gate、凭据撤销和缓存实现都在隔离仓库中，不属于当前产品实现。

## 实现证据

- `skills/project-orrery/scripts/install_project_orrery.py`
- `skills/project-orrery/scripts/validate_installation.py`
- `skills/project-orrery/scripts/check_project_orrery_update.py`
- `skills/project-orrery/release-manifest.json`
- `scripts/package_release.py`

## 已知缺口

- 下一发布版本已决定为首次公开 `v0.2.0`；提交边界、门禁和发布后同步见活动发布计划。
- 架构维护工作区和公开发行面的长期组织方式仍在 Backlog，尚无 ADR。
