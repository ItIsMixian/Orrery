# PO-CR-035：把事实链纠正到当前实现

代码和测试没有改变，但 State、PROGRESS 与 HANDOFF 对反馈缺陷、SQLite schema、迁移状态和
自动化测试数的描述互相冲突。以当前实现和实际测试发现结果为准纠正三份当前事实文档，同时保留
与托盘、导出、发布和数据边界有关的无关说明。

只修改 `docs/state/application.md`、`docs/PROGRESS.md` 和 `docs/HANDOFF.md`。不得修改代码、测试、
历史 ADR、Seed 或为了让文档好看而宣称未实现的 v2 迁移已经完成。
