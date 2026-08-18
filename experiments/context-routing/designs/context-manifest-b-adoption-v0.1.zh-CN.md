# Context Manifest B 采纳候选 v0.1

Status: frozen research candidate; not accepted product policy
Updated: 2026-08-18

## 候选定义

本候选把历史实验中多次漂移的 “B” 固定为一个可检验协议：

1. 在第一次读取仓库正文前，Agent 输出简明但完整的 `CONTEXT MANIFEST`，列明任务分类、首批路径及理由、预期写入、验证和允许扩张的条件。
2. 每次读取 Manifest 之外的新路径或扩大既有行范围前，Agent 先输出 `SCOPE EXPANSION`，包含路径、标准 reason code 和一句理由。
3. 最终答复包含 `ACCESS SUMMARY`，汇总实际正文读取和发生过的扩张。
4. 不创建 Agent receipt、Manifest 文件或其他证明文档；访问事实仍以 Harness 的代理日志和完整 CLI JSONL 为准。

该协议只帮助 Agent 显式规划和向人类解释边界。它不构成文件系统安全边界，也不证明模型注意、理解或因果使用了已读取内容。

## 对照定义

Pilot 007 的 `P` 对照代表当前 Project Orrery v0.2 行为：从任务和仓库入口定位事实，按需读取和验证，不要求模型输出 Manifest、扩张声明或访问摘要。`P` 与 `B` 使用完全相同的受控读取代理、JSONL 审计、独立 Oracle、模型、推理强度和运行预算。

代理从第三个不同正文路径起要求命令携带 reason code，这是共同实验装置，不是 `P` 产品协议。`P` 不需要把该参数复述成额外的模型消息。

## 采纳质量门

只有以下条件同时满足，B 才能进入 ADR 讨论：

1. 三个新任务全部通过独立 Oracle；总通过数不得低于 P，且高风险任务不得出现 P 通过、B 失败。
2. 必要依赖召回不低于 P；B 不得出现未声明扩张、意外写入或无效访问证明。
3. B 总 input token 不高于 P 的 110%，总 output token 不高于 115%，Agent 墙钟时间不高于 115%。
4. B 必须证明实际收益：代理返回正文总字节至少低于 P 15%，或在成本门内补回一个经独立 Oracle 证实、P 遗漏的必要依赖。
5. 两组都不得生成 receipt／Manifest 文档；六个 run 的原始 manifest 必须可验证。
6. 任何共同装置缺陷、外部上下文、未知工具或隐藏重试都会污染整轮；修复必须进入新 Pilot，不能改写 Pilot 007。

通过实验不等于自动采纳。实验完成后仍需维护者明确接受，才新增 ADR 并安排发布版 Skill 的实施与迁移。

## 样本与限制

- 基线：`f9cd508696280e41c933680f3b8c5090fe71cd9d`。
- 模型：`gpt-5.6-terra`，reasoning `medium`。
- 三个全新任务：跨平台可重复打包、R1 脱敏导出、安全的 Windows CLI 安装文档。
- 每项任务同时运行 P/B，一共六次调用；任务顺序由种子 `7007` 固定。
- 这是直接采纳实验，但仍是小样本。即使通过，也只能支持当前 Project Orrery / 当前执行配置下的受限决定。
