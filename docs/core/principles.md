# Seed：Project Orrery 核心原则

这些原则是 **Project Orrery Product Seed**：约束这个产品的目标与决策，但不冒充当前实现状态，也不等同于所有项目通用的 Authority Meta Model。通用角色、claim、scope 与 evidence 解释以 [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md)和[Approved Design](../design/authority-meta-model.md)为准；文字重叠不改变两者职责。

1. **维护者必须保持控制感。** Agent 生成更多文件不能以牺牲项目可理解性、作者意图或决策历史为代价。
2. **不同读者可以有不同入口，但只能共享一套事实。** Agent 导航与人类总览最终必须回到同一组 Seed、有效 ADR、实现、State 和 Validation。
3. **设想、决定、计划、实现与证据不可混写。** `accepted` 不等于 `implemented`，计划清单也不能证明完成。
4. **当前事实必须可定位到真实实现。** State Docs 只描述现在是什么，并明确记录偏差、缺口和发布态／工作树态的区别。
5. **重要决定保留原因和历史。** 有意改变长期约束时新增 `amends` 或 `supersedes` ADR，不重写已接受历史。
6. **派生视图没有决策权。** 仪表盘、AI 问答、摘要、索引和趋势雷达都必须可回到原始文档，不能自行产生事实。
7. **研究先于采纳。** Library、Backlog 和 `experiments/` 可以提出并验证方向；只有通过预先定义的质量门并形成 ADR，才可约束发布版 Skill。
8. **可审计性不能只靠 Agent 自述。** Git 证明写入而非读取；精确内容访问若需强证明，必须由 Harness 或受控工具边界提供。
9. **文档收益必须覆盖维护成本。** 新文档、协议或回执应证明其导航、决策或验证价值，避免为了“完整”制造新的文档债务。
10. **迁移、升级与秘密处理默认保守。** 不覆盖作者文档；工具升级先预演并备份；凭据只进入受保护存储；安装、迁移、采纳和发布必须分开表达。
