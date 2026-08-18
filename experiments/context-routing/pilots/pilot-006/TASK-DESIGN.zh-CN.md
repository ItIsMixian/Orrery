# Pilot 006：修复后确认轮质量门

Status: frozen before model execution

Pilot 006 保留 Pilot 005 的局部链接安全任务和跨模块 managed-tools 任务，但使用新的 Prompt revision。Pilot 005 的四份 contaminated run 只作为装置缺陷证据。

质量门保持不变：独立正确性 H2 不低于 B；所有正文读取由代理+JSONL 证明；H2 必要依赖召回不低于 B；分别报告 input、cached input、non-cached input、output、代理字节和墙钟时间；H2 两项合计 input 不高于 B。

失败不隐藏重试。本轮新的四份运行仍按任务成对并行、任务按种子固定顺序执行并独立封存。
