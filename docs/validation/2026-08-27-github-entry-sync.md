# Validation：GitHub 当前入口同步

Date: 2026-08-27

Scope: 仅同步当前展示名和 `ItIsMixian/Orrery` 活跃链接；不修改历史文档、产品架构、技术 ID、tag、
Release asset 或 Git 历史。

## 结果

- 根 README 中英文标题、正文展示名、badge、clone、安装、Release 与 Watch 链接已同步；clone 后本地
  外层目录使用 `Orrery`，内部 `skills/project-orrery` 技术路径保持不变。
- self-host manifest、稳定 Skill manifest、Core 当前 release bridge 与两个 Adapter metadata 已同步新 URL；
  `project-orrery` Skill／CLI／package／schema ID 保持不变。
- 5 份受影响 JSON 均可解析；当前入口旧 URL 扫描为 0，根 README 旧展示名扫描为 0，diff additions
  私人身份标识扫描为 0。
- Project tests：16 项中 14 PASS、2 个既有可选依赖 skip；Claude／DeepSeek Adapter：6/6 PASS；
  integrated structure 与 `git diff --check` PASS。
- 6 个新公开入口经 HEAD 请求均返回 2xx，包括仓库、CI badge、tagged Skill、latest Release、Release ZIP
  和 raw manifest。

本 Candidate 未提交、未推送，也没有修改 GitHub 仓库设置。
