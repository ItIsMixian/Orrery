# Changelog / 更新日志

Project Orrery follows Semantic Versioning for the distributed Skill. Compatibility with an installed project is determined by the machine-readable release manifest, not by version numbers alone.

Project Orrery 的 Skill 发布遵循语义化版本；与既有项目能否直接兼容，以机器可读的发布清单为准，而不能只看版本号。

## 0.2.0 — 2026-08-18

- Add a stable release manifest with separate Skill, target toolchain, project-manifest, and document-schema versions.
- Add cached, offline-tolerant update checks with explicit compatible, migration-required, newer-than-stable, and unknown states.
- Preserve authored project documents during upgrades and retain the previous toolchain version when a target remains mixed.
- Add reproducible Skill packaging, SHA-256 checksums, and tag-driven GitHub Releases.

- 新增稳定发布清单，分别记录 Skill、目标工具链、项目清单格式和文档架构版本。
- 新增带缓存、可容忍离线环境的更新检查，并明确区分可直接升级、需要迁移、安装版更新以及状态未知。
- 升级时继续保护项目作者文档；若目标工具链仍为混合状态，则保留旧工具链版本，避免误报完成升级。
- 新增可重复的 Skill 打包、SHA-256 校验和与由 Git 标签触发的 GitHub Release。
