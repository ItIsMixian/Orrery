# Skill Entry Router R v0.1

Status: proposed research candidate; not accepted product policy
Date: 2026-08-19
Governing research boundary: [ADR-0002](../../../docs/decisions/0002-real-development-benchmark-portfolio.md)

## 问题

Project Orrery 的 `SKILL.md` 是每次触发都必须完整读取的固定入口。当前入口同时包含操作选择、
release channel、安装、升级、权威链维护、观测台运行和交接验证。对已经集成 Orrery 的普通
代码维护任务而言，大部分安装／升级／viewer 说明不会参与实现，却仍进入 Agent 上下文。

Pilot 004–007 已表明，要求 Agent 额外生成 Manifest、Expansion 或 Receipt 不会自然降低总
input；本候选不再增加任何 Agent 输出协议，而是缩短固定 Skill 入口并把低频操作按需路由。

## 候选定义

`R` 保留在每次任务都必须出现的边界：

- 先服从目标仓库 `AGENTS.md` 与本地权威链；
- `accepted`、Plan、工作树、提交和发布状态必须分开；
- State 只写当前实现事实，ADR 保存长期决定与原因；
- 不覆盖作者文档，不把秘密、缓存或生成物带入发布；
- 实现或验证后按目标仓库规则同步 State、PROGRESS、DEVLOG 与 HANDOFF。

安装、release channel、viewer、架构解释和迁移契约移到独立 references。普通维护任务只读
主入口和目标仓库的本地入口，不读取这些 references，也不做与版本兼容无关的更新检查。

`P` 是当前发布源 `skills/project-orrery/SKILL.md` 的完整入口。P/R 不要求 Agent 输出
Manifest、Scope Expansion、Selected Evidence 或 Access Summary；读取事实仍由共同 Harness
的代理与完整 CLI JSONL 记录。

## Pilot 008 假设

在相同真实开发 fixture、Oracle、模型和工具边界下，R 应当：

1. 把固定 Skill 正文字节降到 P 的 45% 以下；
2. 把完整 Prompt 字节至少降低 15%；
3. 三项任务正确性、必要依赖召回和受保护范围不低于 P；
4. 总 input 不高于 P，output、墙钟和代理正文不高于 P 的 105%；
5. 不通过漏读安全／迁移约束或省略必要事实同步换取成本下降。

## 不作出的承诺

- 候选文件位于 `experiments/`，不修改发布 Skill。
- Prompt 字节下降不等于总 token 必然同比下降；正式结果必须分别报告总 input、cached input、
  non-cached input、output、墙钟、代理正文和固定 Prompt 字节。
- Pilot 008 的准备和 dry-run 不构成采纳证据。正式模型运行需维护者再次确认，结果通过后仍需
  R2 复核和明确接受，才能新增产品 ADR。
