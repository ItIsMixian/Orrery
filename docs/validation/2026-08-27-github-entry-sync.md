# Validation：GitHub 当前入口同步

Date: 2026-08-27

Scope: 仅同步当前展示名和 `ItIsMixian/Orrery` 活跃链接；不修改历史文档、产品架构、技术 ID、tag、
Release asset 或 Git 历史。

## 结果

- 根 README 中英文标题、正文展示名、badge、clone、安装、Release 与 Watch 链接已同步；clone 后本地
  外层目录使用 `Orrery`，内部 `skills/project-orrery` 技术路径保持不变。
- self-host manifest 的更新入口与两个 Adapter metadata 已同步新 URL；`project-orrery`
  Skill／CLI／package／schema ID 保持不变。v0.2.0 Skill manifest 与 Core release bridge 是 release gate
  冻结的历史输入，保留发布时内容并依赖 GitHub redirect。
- 5 份受影响 JSON 均可解析；当前入口旧 URL 扫描为 0，根 README 旧展示名扫描为 0，diff additions
  私人身份标识扫描为 0。
- Project tests：16 项中 14 PASS、2 个既有可选依赖 skip；Claude／DeepSeek Adapter：6/6 PASS；
  integrated structure 与 `git diff --check` PASS。
- 6 个新公开入口经 HEAD 请求均返回 2xx，包括仓库、CI badge、tagged Skill、latest Release、Release ZIP
  和 raw manifest。

## Candidate-first CI

- 首次 Candidate `230a6ff` 错误修改了两份冻结 v0.2.0 输入；GitHub Actions `33107986476` 的
  Windows／Ubuntu 均按设计在同一 historical-input hash 门失败，`main` 未更新。
- 修正保留失败证据并恢复冻结文件，不更新冻结 hash；最终 Candidate 结果以随后 exact SHA 的 required
  checks 为准。
- 恢复后本地 Authority release gate：12 项中 10 PASS、2 个既有 Windows symlink privilege skip；两项
  原远端错误用例均 PASS。

当前只推送 Candidate 分支；`main`、tag、Release、Git 历史和 GitHub 仓库设置均未修改。
