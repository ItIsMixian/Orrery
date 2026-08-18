# 当前进度

Updated: 2026-08-18

## 当前阶段

Project Orrery v0.2.0 已公开发布。Pilot 007 的六次 P/B 运行已经完成并封存：六份 R0 manifest 有效，但共同 formal-validation 分支冲突和一份 B 访问装置无效使本轮不能成为干净的因果对照。只读复核后 P/B 任务质量同为 2/3；B 的 input、output、时间和最小正文收益门全部失败。因此 B 不采纳，不新增 ADR，不修改发布 Skill。

## 已完成

- [x] 通过 ADR-0001 正式采纳 Project Orrery 自托管权威链。
- [x] 建立真实 Agent／维护者入口、State、Validation、Snapshot 与开发日志。
- [x] 明确 `docs`、`experiments`、发布 Skill 和仓库外 benchmark 的职责。
- [x] 完成 Pilot 003 全量、修复后的 B/C 确认轮和 Pilot 004 B/H holdout。
- [x] Pilot 004 v1 Oracle apparatus failure 已保留，v2 只读复核已记录。
- [x] 修复 installer 会复制模板 `__pycache__`／`.pyc` 的问题。
- [x] 完成本地集成验证：28 项默认测试（27 通过、1 项按设计跳过）、启用动态 reader 后完整 28/28 通过、24 项 benchmark 语料与 6 份 run record 通过、文档站与本地链接检查通过。
- [x] 形成 Context Aperture H2 候选：取消 Agent 自写完整 Manifest、Selected Evidence 与 Access Receipt，改由 Harness 从任务配置和代理事件生成。
- [x] 实现受限读取代理、JSONL 独立审计、可选 Hook 增强、原始证据 seal/verify/status 与 7 项专项测试。
- [x] 完成 10 轮真实 CLI 兼容性探测并逐轮封存；全部 manifest 可验证，确认 Windows Codex CLI 0.147.0 的非交互 Hook 未触发，当前采用 JSONL 事后作废模式。
- [x] 完成全仓回归：默认 35 项中 34 通过、1 项按设计跳过；动态 reader 开启后 35/35 通过；benchmark、integrated build、文档站、链接与 diff 检查通过。
- [x] 冻结 PO-CR-025／026 两个新高风险任务及 B/H2 Prompt、Oracle、模型、执行配置和成本口径。
- [x] 保留 Pilot 005 的四个装置失败 run，并以修正后的 Pilot 006 完成 4 个正式运行；四份 raw manifest 均可验证。
- [x] 以 v3 规则只读复核 Windows CRLF stdout 假阴性；Pilot 006 四个运行的内容读取证明均有效，原始分类没有被改写。
- [x] 完成研究轮最终回归：默认 39 项中 38 通过、1 项按设计跳过；动态 reader 开启后 39/39 通过；24 项 corpus、6 份 run record、integrated static build、文档站、本地链接和 diff 检查通过。
- [x] 将 `bb2c768`、`96bfd21`、`f9cd508` 全部推送到公开 `origin/main`。
- [x] 冻结 Pilot 007 的 P/B treatment、三项新任务、独立 Oracle、Terra medium 配置和采纳门；baseline negative control 与 dry-run 通过，未启动模型调用。
- [x] 完成 Pilot 007 准备回归：专项 12/12、默认 39/40（1 skip）、动态 reader 40/40，corpus／run records、文档站、本地链接与 diff 检查通过。
- [x] 完成 Pilot 007 六次 Terra medium P/B 运行；所有 CLI 最终 exit 0，六份 R0 manifest 6/6 校验有效，没有隐藏重试。
- [x] 完成 Pilot 007 R2 只读复核：记录共同装置缺陷，将 029 的固定词形 Oracle 假阴性与 027 的真实跨平台排序遗漏分离，并按冻结成本门停止 B 采纳。

## 当前结论

- Context Aperture H1 正确性与 B 持平、读取更克制，但总 input token 高 47%，未通过采纳门。
- 发布版 Skill 仍不强制 Context Manifest、Selected Evidence 或访问回执。
- H2 正确性与 B 持平，但总 input token 高 18.5%、output 高 22.5%、代理正文高 23.7%、墙钟高 7.2%；非缓存 input 低 31.9% 不足以抵消总成本，因此 H2 不采纳。
- 当前装置只证明受控命令输出与代理切片一致，不证明模型理解，也不提供实时阻断。
- Pilot 007 没有显示 B 的质量收益；B 相对 P 聚合 input +25.68%、output +23.56%、Agent 时间 +16.89%，代理正文仅 -6.95%，不满足采纳门。
- 共同装置缺陷意味着不能把本轮宣传为普遍“科学证伪 B”；项目层面的保守决定仍是不采纳、不继续给当前 B 增加协议。

## 待办

- [x] 人工审阅本次自托管、实验与产品修复 diff，并确定分层提交及首次发布方案。
- [x] 按发布计划形成产品修复、研究证据、自托管、发布准备提交，并补充浅克隆 CI 修复。
- [x] 分支与 `main` 双平台 CI 通过，首个 [`v0.2.0` GitHub Release](https://github.com/yw9299-stack/project-orrery/releases/tag/v0.2.0) 已创建并验证。
- [x] 设计 H2，优先削减 Agent 生成的 Manifest、Selected Evidence、Receipt 和重复验证叙述。
- [x] 设计并实现由 Harness 证明内容读取范围的最小代理／JSONL 实验。
- [x] 冻结两个全新任务、B/H2 Prompt、Oracle、执行配置与成本口径。
- [x] 运行小规模 B/H2 对照，并按正确性、必要依赖召回、input token、代理字节和墙钟时间决定是否继续；结论为不采纳 H2。
- [x] 审阅并提交 H2 研究设施、Pilot 005／006 控制包和 R2 结论；研究层提交为 `bb2c768`，仓库外 R0 原始输出未进入 Git。
- [x] 将研究分支以 `--ff-only` 快进合并到本地 `main`；`main` 已包含 `bb2c768` 与 `96bfd21`，本轮不发布新 Skill 版本。
- [x] 将本轮全部提交推送到 `origin/main`；远端 `main` 与本地推送点一致。
- [x] 准备 Pilot 007 B 采纳实验及独立 Oracle，不执行正式模型样本。
- [x] 运行 Pilot 007 的 3 对 P/B 样本并生成 R2；结论为装置受污染且 B 成本／收益门失败，不采纳。
- [ ] 跨平台 byte-for-byte 可重复打包暂不进入本阶段；v0.2.0 已发布资产的 checksum 仍有效。

## Blockers / risks

- 仓库外 benchmark 已有 manifest、保留分类和脱敏边界，但尚无自动 R1 导出器；到期只报告，不自动删除。
- Pilot 004 正式 validator 保留 exit 1，因为冻结的 v1 Oracle 存在假阳性；正确结论依赖 checksummed v2 只读复核。
- v0.2.0 的 GitHub 资产和 checksum 一致，但 Windows 与 Ubuntu 从同一 tag 本地打包得到的 zip 字节不同；已确认条目集合一致，差异来自行尾与权限元数据，列入下一补丁。
- Windows Codex CLI 0.147.0 的 `codex exec` 未执行项目或会话内联 Hook；当前 JSONL 模式只能事后判废，不能执行前阻断。
- Pilot 006 只有两个高风险任务，足以否决当前 H2 的预设成本门，不足以推导所有模型和任务的普遍规律。
- Pilot 007 的外层 `benchmark` 分支会使嵌套 Pilot 006 dry-run 创建同名分支失败；任何未来 Pilot 必须在启动前用不同外层分支名覆盖该路径。
- Pilot 007 frozen Oracle 对 029 过度要求英文精确词形 `ExecutionPolicy`；R2 已修正语义判断，但没有回写原始 Oracle 或 raw summary。

## 下一里程碑

上下文路由采纳实验暂时停止。下一里程碑回到发布产品 backlog；若维护者仍希望研究 Manifest，先提出明显更低成本的新候选并建立 Pilot 008，而不是补跑或改写 Pilot 007。
