# Orrery Fixture Agent 任务路由

先按人类任务定位模块，只读取确认实现范围所需的入口；不要为了“完整”线性遍历所有 Orrery 文档。

## 模块入口

- **反馈状态、自动过期、snooze**：当前事实见 `docs/state/application.md`；实现与行为测试分别在
  `src/orrery_fixture/feedback.py`、`tests/test_feedback.py`。只有需要理解用户主动延期的长期理由时，
  才读 `docs/decisions/0001-user-controlled-deferral.md`。
- **SQLite schema、初始化、迁移**：当前事实见 `docs/state/application.md`；实现与迁移测试分别在
  `src/orrery_fixture/storage.py`、`tests/test_storage.py`。需要确认迁移幂等约束时读
  `docs/decisions/0002-idempotent-storage-migrations.md`。
- **事实链对齐**：先读任务点名的 State、PROGRESS 或 HANDOFF，再读取解决冲突所需的实现和测试；
  不修改历史 ADR 来迎合当前文档。

## 条件入口

- `docs/core/principles.md` 只在局部事实与长期边界冲突、任务涉及安全／隐私或准备改变规则时读取。
- `docs/PROGRESS.md` 在任务要求纠正进度或实现完成后同步当前里程碑时读取。
- `docs/HANDOFF.md` 只在任务点名、停止点变化或风险变化时读取。
- ADR 只在需要理解决定原因或判断长期规则是否改变时读取；局部修复不新建 ADR。

实现和测试是行为事实，State 只写当前事实。只修改任务授权路径，不访问网络、真实用户数据、凭据或
Git 历史。验证后同步真正受影响的 State 与 PROGRESS；HANDOFF 仍按上述条件更新。
