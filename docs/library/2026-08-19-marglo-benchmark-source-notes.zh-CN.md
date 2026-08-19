# Marglo 作为真实开发基准素材源的观察

Date: 2026-08-19
Authority: Library；本文件记录素材，不证明任何任务或策略已被采纳

## 为什么参考它

Project Orrery 最初正是从 Marglo／NextStep Seed_2 的开发失控感中产生。该项目已经长期演化，既有真实应用代码，也有 Agent／Human 双入口、ADR、State、SQLite 数据、用户主权、安全门、UI、测试覆盖、发布同步和 deferred 工作，适合提供比纯文档维护更接近日常开发的任务模式。

## 可提炼的复杂度

- `AGENTS.md`、Handoff 与 State 对同一测试基线出现 122／123 的当前事实差异。
- 两份不同主题的 ADR 共用 0022 编号，后续引用必须识别语义目标而不能只匹配编号。
- ADR-0024.1 的早期“待实现”描述与后续 Phase 1–3 已实现记录并存，要求区分历史决定、追加状态和当前实现。
- 用户反馈、冷却、安全 rail、UI 和持久化之间存在跨模块行为闭环。
- SQLite schema 迁移必须保留长期数据并保持幂等。
- OS keychain、移除 `.env` fallback、敏感观察器默认关闭等构成可失败注入的安全任务。
- deferred 测试记录了触发条件，可用于判断 Agent 是应该实施还是克制。
- 用户文档、CHANGELOG、Release Intro 和镜像同步形成发布治理任务。
- 活跃工作树可能已经包含用户改动，适合构造“保留预置脏文件”的范围测试。

## 使用限制

- 只提炼模式，不直接在真实工作树执行实验。
- 不复制真实数据库、日志、凭据、缓存、私人记忆或未提交改动。
- 历史修复不能连同答案文档直接暴露给候选 Agent；必要时使用更早提交或重新注入等价缺陷。
- 任务必须有独立行为 Oracle，不能以“补齐文档”作为代码正确性的替代物。
- 对外发布 fixture 前需要再次检查许可、隐私和本机路径。

该素材已推动 [ADR-0002](../decisions/0002-real-development-benchmark-portfolio.md) 和对应 [Approved Design](../design/real-development-context-routing-benchmark.md)，但具体任务仍需未来 Implementation Plan 才会进入实施。
