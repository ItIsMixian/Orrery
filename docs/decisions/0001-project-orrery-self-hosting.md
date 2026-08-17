# ADR-0001：Project Orrery 使用自身权威模型管理开发

Status: Accepted
Date: 2026-08-18

## Context

Project Orrery 已经拥有可发布 Skill、迁移模板、文档观测台、兼容性工具和一组上下文路由实验，但仓库自身只有 README、Library 与分散的 `experiments/` 报告。它没有根级 Agent 入口、Progress、Handoff、State、Validation 或自身 ADR。

这造成了与产品目标相同的问题：实验虽然留下详细证据，人类却难以从 `docs/` 得知当前阶段、有效结论、发布态与工作树态差异，以及下一步为什么尚未采纳 Context Aperture。

## Decision

1. 在仓库根建立并正式采纳 Project Orrery 权威模型：`Product intent → Seed → effective ADR → approved Design → implementation → State Docs → Validation → Snapshot`。
2. `AGENTS.md`、`docs/HANDOFF.md` 和 `docs/PROGRESS.md` 作为读者入口；它们导航到事实，不复制另一套事实。
3. `skills/project-orrery/` 是可发布产品源；根 `scripts/docsite/` 是本仓库自托管的观测台工具；`docs/` 是本仓库文档权威根。
4. `experiments/` 保存非权威实验装置、可版本控制的证据和报告。大型隔离仓库、JSONL 与本地运行缓存保存在仓库外 `project-orrery-benchmark/`，不自动进入发布包或权威文档。
5. 每轮实验完成后必须同步研究 State、PROGRESS、DEVLOG、HANDOFF 和可复现 Validation；详细运行数据不重复复制到 Docs。
6. 实验结果只有在预先定义的质量门通过且用户明确接受后，才能通过新 ADR 约束发布版 Skill。负结果和 apparatus failure 仍需保留。
7. `.project-orrery.json` 的 `authority_status` 在入口、State、Validation 和本 ADR 完成后设置为 `integrated`。

## Consequences

- 项目将能用自身协议解释自己的演化，并暴露文档漂移。
- 维护一次实验需要同时维护实验报告与少量当前状态摘要，但不需要把原始日志复制进 Docs。
- 发布版 0.2.0、当前工作树和未来候选设计必须分别表达，不能把未提交代码写成已发布能力。
- 根观测台工具成为自托管工具链的一部分，但模板源仍以 `skills/project-orrery/assets/project-template/` 为准。
- Context Aperture H1 仍是未采纳研究；本 ADR 不接受任何具体路由策略。

## Alternatives considered

- **只使用 `experiments/`：** 保留了证据，却不能提供项目当前地图和交接入口。
- **把全部原始运行数据放入 Docs/Git：** 会放大仓库、暴露本机路径并降低可读性。
- **把实验结果直接写成架构 ADR：** 会混淆研究信号与产品决定，违反预先质量门。

## Validation

- `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`
- `python -X utf8 scripts/docsite/build_docsite.py`
- `python -m unittest discover -s tests -v`
- [自托管基线验证](../validation/2026-08-18-self-hosting-baseline.md)
