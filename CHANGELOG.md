# Changelog / 更新日志

Project Orrery follows Semantic Versioning for the distributed Skill. Compatibility with an installed project is determined by the machine-readable release manifest, not by version numbers alone.

Project Orrery 的 Skill 发布遵循语义化版本；与既有项目能否直接兼容，以机器可读的发布清单为准，而不能只看版本号。

## 0.3.1 — 2026-09-01

- Fix repeated Windows command-window flashes by applying the no-window child-process policy throughout the default headless runtime.
- Reuse an already healthy Orrery supervisor on repeated normal launch instead of starting a duplicate attempt.
- Preserve explicit `--console` behavior, all existing defaults, and the v0.3.0 compatibility contract.

- 修复 Windows 默认启动时反复闪现命令窗口的问题，为无界面运行链统一应用子进程隐藏策略。
- 重复正常启动时复用已经健康运行的 Orrery 服务，不再发起第二个 supervisor 尝试。
- 保持显式 `--console` 行为、现有默认值与 v0.3.0 兼容契约不变。

## 0.2.0 — 2026-08-18

- Add a stable release manifest with separate Skill, target toolchain, project-manifest, and document-schema versions.
- Add cached, offline-tolerant update checks with explicit compatible, migration-required, newer-than-stable, and unknown states.
- Preserve authored project documents during upgrades and retain the previous toolchain version when a target remains mixed.
- Add versioned Skill packaging with fixed archive timestamps, SHA-256 checksums, and tag-driven GitHub Releases. Cross-platform byte-for-byte reproducibility remains future work.

- 新增稳定发布清单，分别记录 Skill、目标工具链、项目清单格式和文档架构版本。
- 新增带缓存、可容忍离线环境的更新检查，并明确区分可直接升级、需要迁移、安装版更新以及状态未知。
- 升级时继续保护项目作者文档；若目标工具链仍为混合状态，则保留旧工具链版本，避免误报完成升级。
- 新增带固定归档时间戳的版本化 Skill 打包、SHA-256 校验和与由 Git 标签触发的 GitHub Release；跨平台逐字节可重复性仍待后续实现。
