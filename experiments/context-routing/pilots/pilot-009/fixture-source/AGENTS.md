# Orrery Fixture Agent 入口

任何维护任务依次读取：`docs/HANDOFF.md`、`docs/PROGRESS.md`、`docs/core/principles.md`、相关
`docs/state/*.md`；只有需要理解长期理由时才读相关 ADR，最后读取代码和测试。

- 实现和测试是行为事实；State 只写当前事实，ADR 保留决定原因。
- 局部修复不新建 ADR，不重写历史 ADR。
- 实现或验证后更新受影响的 State 与 PROGRESS；只有停止点或风险变化时更新 HANDOFF。
- 不修改任务未授权的路径，不访问网络、真实用户数据、凭据或 Git 历史。
