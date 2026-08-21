# 2026-08-21 文档治理采纳验证

Status: Completed documentation-level adoption review

## Scope

验证 ADR-0012、Approved Design 与活动 Plan 已形成可追溯的文档治理权威链，并且没有把本轮文档工作误写成审计 CLI、Observatory finding、模板迁移或公开发布实现。

本轮只证明：

- Authority Meta Model、Documentation Governance 和未来 Tooling 的职责分开；
- 当前控制面与历史／证据面有明确角色和同步事件；
- soft budget 只产生人工 review signal；
- 工具只能提出 non-authoritative finding，不能自动改写作者文档；
- Project Orrery 自托管 State 和入口已链接该治理规则。

## Documentation review

人工逐项检查：

1. ADR-0012 以 Accepted 记录维护者决定，并明确 amends ADR-0001、clarifies ADR-0009。
2. Approved Design 覆盖文档角色、更新事件、压缩／拆分标准、finding contract、人工闭环和安全边界。
3. Implementation Plan 把规范采纳、只读 contract、CLI、Observatory、模板／发布分成独立阶段。
4. AGENTS／Documentation State／PROGRESS／HANDOFF／DEVLOG 和四类索引能够定位新权威链。
5. 本轮没有产品代码、Skill 模板、组件版本、release manifest、tag 或远端状态变化；只同步一条仓库级精确测试预期，使 ADR-0012 的 `amends ADR-0001` 关系进入既有冻结集合，没有放宽 evaluator 或断言。

## Reproducible checks

首轮 full regression 发现 231 项中的 1 项失败：既有 `test_repository_amendments_have_explicit_core_relations` 精确冻结仓库全部 amend 关系，新增 ADR-0012 后预期集合尚未包含 `ADR-0012 → ADR-0001`。测试保持精确，只补充该关系后重新执行完整验收。

最终检查：

1. `python -X utf8 -m unittest discover -s tests`

   修正精确 relation 预期后，231 项中 226 项通过、5 项因既有 Windows symlink 权限／可选依赖跳过、0 项失败。

2. `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --build`

   结构与静态站构建完成；Authority status 保持 `integrated candidate`，模型 1 为 supported 且可执行 strict evaluation。

3. 默认／Authority projection／关闭开关回滚

   默认输出 SHA-256 为 `58E62A6AF73F3CE0BEF78895DD3897127B10A8AC57B51B1E3E6B94A6615B1F86`；显式 projection 为 `4A0CD164DB46383C512A4E33FDDB6F3253F7FB2FCF0B9838D50F99627D8DD2D0`；关闭开关后重新得到默认 SHA，证明回滚逐字节一致。Projection 报告 ready，包含 12 ADR、6 State、7 subsystem、2 Snapshot、92 docs、16 Plans 和 6 Library 文档。

4. Markdown 本地链接扫描

   282 份 Markdown、686 个本地链接／图片、0 个缺失目标。

5. `git diff --check`

   最终文档同步后执行；没有 whitespace error。

## Current boundary

Phase 0 只完成治理规范与 Project Orrery 自托管对齐。`docs audit`、finding schema、soft budget 配置、acknowledge storage、Observatory projection、公开模板和 release 仍是活动 Plan 中的未实现工作，不得由本记录推断为 present 或 validated。
