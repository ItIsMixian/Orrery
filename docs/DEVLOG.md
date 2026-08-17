# 开发日志

## 2026-08-17 — v0.2 发布候选与上下文路由研究启动

- 建立版本化发布、兼容性清单、更新检查、图形化 AI 设置和中英文公开 README。
- Pilot 001 暴露仓库身份缺失和外部 Skill 上下文污染；Pilot 002 修复装置并证明固定七文件链存在方向性开销。
- 建立任务上下文、证据来源和文档负担研究综述。
- 兼容协议已进入 `main`，但远端没有创建 tag 或 GitHub Release，因此此阶段是候选准备而非实际发布。

## 2026-08-18 — Pilot 003 与确认性 B/C 对照

- 完成多任务 A/B/C 真实运行、JSONL 捕获、回执、未跟踪文件采集和 operator-side 安全验收。
- 修复 Harness 对未跟踪产品文件的遗漏和安全 Oracle 的若干刚性假设。
- B/C 确认轮显示 C 虽减少自报读取，却增加约 75% input token 且未通过高风险质量门；不采纳 C。

## 2026-08-18 — Pilot 004 B/H holdout

- 使用 `gpt-5.6-terra` / medium 完成 3 个任务 × B/H，共 6 次一次性隔离运行。
- 冻结 v1 Oracle 出现跨 helper 与 AST 顺序假阳性；原结果保持不变，并由 checksummed v2 做只读复核。
- B/H 均通过 3/3 任务验收；H 自报读取更少，但总 input token 高 47%、平均耗时高约 15%，未进入 ADR。

## 2026-08-18 — Project Orrery 自托管补全

- 非破坏式安装本仓库观测台，保留已有 Library 和 `.gitignore`。
- 通过 ADR-0001 建立根级权威链、State、Progress、Handoff、Validation 和 Snapshot。
- 明确可版本控制实验与仓库外大型原始结果的证据边界。
- 修复 installer 会复制模板 Python 缓存的问题，并增加回归断言。
- 以 `authority_status: integrated` 完成结构、静态阅读器、动态设置边界、28 项默认测试、benchmark 语料／run record 和 Markdown 本地链接验证；结果记录在自托管基线 Validation。
