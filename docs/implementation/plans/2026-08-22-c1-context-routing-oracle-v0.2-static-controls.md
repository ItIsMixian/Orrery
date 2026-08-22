# 实施计划：Context-routing Oracle v0.2 无模型静态 Controls

Status: Completed — static readiness only; Pilot 010 not created
Date: 2026-08-22
Development task: `C1`（开发任务编号，不是 R0／R1／R2 evidence layer）
Governing ADRs: [ADR-0002](../../decisions/0002-real-development-benchmark-portfolio.md),
[ADR-0005](../../decisions/0005-prewrite-scope-acquisition-input.md)
Approved Design: [真实开发上下文路由基准](../../design/real-development-context-routing-benchmark.md)
Research Design: [真实开发任务与 Oracle v0.2](../../../experiments/context-routing/designs/real-development-task-oracle-v0.2.zh-CN.md)

## 目标

不调用模型地证明下一轮任务 Oracle 能区分形式有效性、候选语义质量、结构化 State／未来版本遗漏与
apparatus contamination，并阻断 Pilot 008／009 已观察到的隐藏索引名和单一措辞假阴性。

## 工作包

- [x] 建立四层 versioned verdict；装置污染与候选质量独立保留。
- [x] 建立公开 State JSON schema、7 文件脱敏合成 fixture 与逐文件 SHA-256 manifest。
- [x] 用公共 API／真实 SQLite 终态验证 behavior、data safety 与未来版本写前拒绝，不检查 helper／索引名。
- [x] 为三项叙事事实各建立三种 positive paraphrase 与两种 contradiction controls；未知措辞进入
  `manual_review_required`。
- [x] 增加 guard、索引列顺序、写后拒绝、helper bypass、State omission、scope 与 formal mutation。
- [x] 保持 Pilot 004–009 文件和仓库外 raw evidence 只读；不创建 `pilot-010`。
- [x] 同步研究 State、Design、Validation、DEVLOG 与结果索引；根 PROGRESS／HANDOFF 留给唯一整合者。

## 完成出口

C1 Oracle self-test 20/20 controls 通过且显式报告 `model_calls: 0`、`pilot_created: false`。静态结论为：
Oracle 层已具备申请 Pilot 010 设计的条件；正式实验仍未 ready，因为尚无任务包，任务级 Prompt 等长、
嵌套隔离、目标 runtime 握手与 formal transport preflight 也没有为 Pilot 010 冻结。
