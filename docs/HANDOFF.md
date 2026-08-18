# 跨会话交接

Updated: 2026-08-18

## 当前情况

- 根文档系统已依据 ADR-0001 完成自托管集成；`.project-orrery.json` 应保持 `authority_status: integrated`。
- Project Orrery v0.2.0 已公开发布：`main`、tag、Release、zip、checksum 和远端 manifest 均已核验。
- 自托管、实验、installer 缓存排除和 CI 完整历史修复已进入 Git 历史。
- 上下文路由证据集中在 `experiments/context-routing/`；大型原始输出位于 `D:\coding warehouse\project-orrery-benchmark`。
- Pilot 004 的 H1 未达到 token 采纳门，不能加入发布版 Skill。
- H2 候选、读取代理、JSONL 独立 validator、可选 Hook 和原始证据保留工具位于 `experiments/context-routing/`；研究层 `bb2c768`、权威状态层 `96bfd21` 和整合状态 `f9cd508` 已推送到公开 `origin/main`。没有新 Release。
- 10 份 CLI smoke 原始运行均在仓库外封存为 `contaminated`；manifest 10/10 可验证。既有 run `h2-hook-smoke-20260818-114907` 可被新 JSONL validator 只读判定为 1/1 内容读取证明，但不得回写或改分类。
- Pilot 005 四个 B/H2 run 因共同装置缺陷全部按 `contaminated` 封存；Pilot 006 修正共同 Harness 后完成相同两个任务。B/H2 均通过 2/2 任务验收。
- Pilot 006 的 PO-CR-026 两份冻结访问结果受 CRLF→CRCRLF 假阴性影响，原始分类仍为 `contaminated`；v3 只读复核证明四个 run 的访问均有效，且四份 manifest 始终有效。
- H2 相对 B 的总 input 高 18.5%，没有通过预设成本门，不采纳、不新增 ADR、不修改发布 Skill。R2 结论见 [Pilot 005 / 006 报告](../experiments/context-routing/results/2026-08-18-pilot-005-006-bh2-terra-medium.md)。
- `codex/b-adoption-pilot` 正在准备 Pilot 007：P 是当前发布流程，B 固定为 Context Manifest／Scope Expansion／Access Summary 且不生成 receipt 文件。三项新任务的 Oracle 与 dry-run 已通过，正式 6 个 run 尚未启动。

## 风险与常见陷阱

- 不要把 v1 Oracle 的正式 validator exit 1 解读为六个候选实现失败；详见 Pilot 004 结果报告和 v2 复核。
- 不要为了“同步文档”把 JSONL、隔离仓库或本机路径批量复制进 `docs/`。
- v0.2.0 资产 checksum 有效，但跨 Windows／Linux 重建尚非 byte-for-byte 相同；不要宣称跨平台可重复打包已经解决。
- 运行 `py_compile` 会在模板目录产生被忽略的 `__pycache__`；installer 必须继续排除它们。
- H2 新增文件已进入本地 `main`；不要误删 Pilot 控制包，也不要把仓库外 raw run 复制回仓库。
- 不要声称 Windows CLI Hook 已工作：0.147.0 下项目 Hooks、trusted 覆盖、绝对 `commandWindows` 和 CLI 内联 Hooks 都未产生日志。当前正式候选证据模式是 `codex-exec-jsonl-posthoc`。
- JSONL 模式是完整事件流上的事后作废，不是实时权限边界；任何 MCP／Hosted／未知 item、直接读取命令或输出哈希不匹配都必须使 run 失败。
- 原始 run sealing 后不得增补文件或“修正”分类；派生复核进入新 R1／Validation 文件并引用原 run。
- 读取代理已改为直接写 UTF-8 bytes；不要恢复为 Windows TextIO 输出，否则 CRLF 会再次变成 CRCRLF。兼容旧 run 的恢复形式仍必须命中代理独立 SHA-256，不能接受无哈希的换行宽松比较。
- Pilot 007 一旦首个模型 run 启动即冻结；共同装置问题必须进入 Pilot 008。不要把 dry-run 通过写成 B 已通过或已采纳。

## 安全接续点

1. 阅读 `docs/PROGRESS.md` 和 `docs/state/context-routing-research.md`。
2. 运行自托管结构验证和完整测试，确认 Validation 仍匹配。
3. 阅读 [H2 装置验证](validation/2026-08-18-h2-read-proof-apparatus.md)、[Pilot 005 / 006 验证](validation/2026-08-18-pilot-005-006-bh2.md)和活动 Implementation Plan。
4. Pilot 007 准备后的专项测试为 12/12；全仓默认 39/40（1 skip），动态 reader 开启后 40/40；benchmark、integrated build、文档站、本地链接与 diff 检查通过。若涉及既有 raw run，只可执行 verify／只读派生。
5. H2 研究轮已经关闭。Pilot 007 是新的直接采纳实验，基线固定为 `f9cd508696280e41c933680f3b8c5090fe71cd9d`；正式运行必须输出到仓库外新目录，并使用 Terra medium。
6. Pilot 007 运行前再次执行 `python experiments/context-routing/pilots/pilot-007/run_pilot.py --dry-run`。未得到维护者启动确认时只准备，不运行；通过自动门后仍先请求维护者决定，再考虑 ADR。
