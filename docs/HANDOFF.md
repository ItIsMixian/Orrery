# 跨会话交接

Updated: 2026-08-19

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
- `codex/b-adoption-pilot` 已完成 Pilot 007 六次运行。仓库外原始根为 `D:\coding warehouse\project-orrery-benchmark\pilot-007-20260818-143450`；六份 manifest 有效，不得回写、重分类或复制进 Git。
- Pilot 007 的共同 nested-branch formal-validation 缺陷使原 raw 0/3 对 0/3 不能直接解释；R2 语义复核为 P/B 均 2/3。B 的成本／收益门仍全部失败，因此不采纳、不新增 ADR。
- ADR-0002 已接受：未来上下文路由采纳实验必须含隔离的真实应用开发任务。Approved Design 已完成，真实 fixture、Oracle 和 Pilot 008 尚未开始。
- Marglo／NextStep Seed_2 是首批素材来源；只可提炼模式或从固定提交构造脱敏 fixture，不能在真实工作树运行，也不能复制用户数据、凭据、缓存或未提交改动。

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
- Pilot 007 已冻结；共同装置问题必须进入 Pilot 008。不要修复 raw summary、frozen Oracle、协议检查或候选仓库后再冒充同一轮结果。
- 未来 runner 的外层隔离分支不能再命名为 `benchmark`，否则既有 Pilot 006 dry-run 会在嵌套 clone 中创建同名分支失败。
- 不要把 ADR-0002 的“政策已接受”写成“Pilot 008 已准备”或“真实开发任务已通过”；当前没有新的控制包或运行证据。

## 安全接续点

1. 阅读 `docs/PROGRESS.md` 和 `docs/state/context-routing-research.md`。
2. 运行自托管结构验证和完整测试，确认 Validation 仍匹配。
3. 阅读 [H2 装置验证](validation/2026-08-18-h2-read-proof-apparatus.md)、[Pilot 005 / 006 验证](validation/2026-08-18-pilot-005-006-bh2.md)和活动 Implementation Plan。
4. Pilot 007 准备后的专项测试为 12/12；全仓默认 39/40（1 skip），动态 reader 开启后 40/40；benchmark、integrated build、文档站、本地链接与 diff 检查通过。若涉及既有 raw run，只可执行 verify／只读派生。
5. 阅读 [Pilot 007 R2 结果](../experiments/context-routing/results/2026-08-18-pilot-007-pb-adoption-terra-medium.md)和 [运行验证](validation/2026-08-18-pilot-007-pb-adoption.md)；不要只看 frozen raw 的 0/3。
6. 当前没有活动采纳实验。若用户要求继续，先写 Pilot 008 Design／Plan／Oracle 并完成真正嵌套的 preflight；不得直接重跑 Pilot 007。
7. 下一轮先读取 [ADR-0002](decisions/0002-real-development-benchmark-portfolio.md)与[真实开发基准 Design](design/real-development-context-routing-benchmark.md)，再为 fixture 构建创建独立 Implementation Plan；正式模型运行仍需再次确认。
