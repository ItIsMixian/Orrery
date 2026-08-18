# Pilot 006：修复装置后的 B/H2 确认轮

Pilot 005 v1 四份原始 run 已全部按 contaminated 封存。该轮暴露了 PowerShell 命令包装、绝对写入路径、隔离仓库 Git 历史和契约键名四项装置问题，不能用于判断 H2。

Pilot 006 保留相同两项任务目标和 B/H2 treatment，只修复共同 Harness：

- 完整 Git 历史随隔离仓库保留，但 Agent 仍禁止读取历史；
- JSONL validator 归一化 Windows shell 包装与仓库绝对写入路径；
- 失败的已批准验证命令属于候选结果，不再冒充访问装置失败；
- 代理读取必须顺序执行；`list` 不接受 reason，第三个正文路径必须在 `read` 命令携带 reason；
- managed-tools 契约字段名在 Prompt 中明确为 `schema_version`、`managed_tools` 和 `managed_tools_contract_format`。

Pilot 005 不重分类、不覆盖、不删除。
