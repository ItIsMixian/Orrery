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

## 2026-08-18 — v0.2.0 首次公开发布

- 将产品修复、上下文路由研究、自托管文档和发布准备拆分提交并快进 `main`。
- 首轮 CI 暴露 shallow checkout 无法读取历史 benchmark commit；为验证与发布 workflow 增加 `fetch-depth: 0` 后，分支和 main 的 Windows／Ubuntu 全部通过。
- 创建 annotated tag `v0.2.0`，Release workflow `32057644595` 发布 zip 与 SHA-256；重新下载校验一致。
- 发现 Windows／Ubuntu 重建 zip 会受行尾和权限元数据影响，未达到跨平台 byte-for-byte 可重复性；保留 v0.2.0，并把修复列入下一补丁。

## 2026-08-18 — Context Aperture H2 与独立读取证据装置

- 设计 H2：删除 Agent 生成的完整 Manifest、Selected Evidence、Receipt 与重复正式验收叙述，让 Harness 从任务配置和代理事件机械生成审计结构。
- 实现受限 UTF-8 读取代理、reason-coded 扩张、Hook Pre/Post 语义、`codex exec --json` 独立事件审计，以及 seal/verify/status 原始证据工具。
- 运行 10 轮一次性 Windows CLI smoke 并逐轮封存；确认 Codex CLI 0.147.0 非交互运行未产出 Hook 事件，因此采用 JSONL 事后作废作为兼容基线，Hook 仅保留为增强层。
- 7 项专项测试通过；十份 raw manifest 10/10 可验证，既有第九轮可由新 validator 只读证明 1/1 合法代理读取。
- 建立 R0 受限原始、R1 脱敏可移植、R2 权威结论三层证据与四档保留期；不自动删除，也不把原始 JSONL 复制进文档仓库。

## 2026-08-18 — Pilot 005 / 006 B/H2 决策轮

- 冻结 PO-CR-025／026 两个新高风险任务、B/H2 Prompt、独立 Oracle、Terra medium 执行配置和成本门。
- Pilot 005 暴露 Windows 命令包装、绝对写路径、隔离 Git 历史、契约键名和失败快速验证分类等共同装置问题；四个原始 run 全部保留为 `contaminated`。
- Pilot 006 修正共同 Harness 后，B 与 H2 均通过 2/2 独立任务验收；四份 raw manifest 均保持有效。
- 修复代理 Windows TextIO 的 CRLF→CRCRLF 翻译，并以同时核对代理 SHA-256 的 v3 validator 只读复核两个假阴性；不回写、不重分类原始 run。
- H2 非缓存 input 低 31.9%，但总 input 高 18.5%、output 高 22.5%、代理正文高 23.7%、Agent 时间高 7.2%，未通过采纳门；不新增 ADR、不修改发布 Skill。
- 完成研究设施、Pilot 控制包、专项测试、Validation 与 R2 报告的分层审阅；确认发布产品目录和 R0 原始输出均未进入 diff，并形成研究层提交 `bb2c768`。
- 形成自托管权威状态提交 `96bfd21`，随后以 `--ff-only` 将研究分支快进到本地 `main`；没有创建合并提交、远端推送或新 Release。

## 2026-08-18 — 全量推送与 Pilot 007 B 采纳实验准备

- 将 H2 研究提交 `bb2c768`、自托管状态提交 `96bfd21` 和整合状态提交 `f9cd508` 推送到公开 `origin/main`；未创建新版本或 Release。
- 冻结历史 B 的精确定义：首次正文读取前 Context Manifest、扩张前 reason-coded Scope Expansion、最终 Access Summary，不生成 receipt 文件。
- 建立 Pilot 007，以当前发布流程 P 为直接对照，固定 Terra medium、提交基线、三项新任务、成本／正确性／最小收益门和独立 Oracle。
- Oracle 自测、三项 baseline negative control、Prompt 生成与控制哈希 dry-run 通过；正式六次模型调用尚未启动，B 没有被采纳，也没有新增 ADR。

## 2026-08-18 — Pilot 007 P/B 直接采纳实验

- 使用 `gpt-5.6-terra` / medium 完成 PO-CR-027／028／029 三项任务的 P/B 成对运行；六个 CLI 最终 exit 0，六份 R0 manifest 全部有效，没有人为补跑。
- 发现外层隔离分支 `benchmark` 与嵌套 Pilot 006 dry-run 分支冲突，导致六边 formal validation 共同失败；`PO-CR-028-B` 另有 failed proxy read 与协议检查假阴性。本轮不能作为干净因果对照。
- 冻结 Oracle 原始结果为 P 0/3、B 0/3；R2 语义复核将 029 固定词形假阴性修正后，P/B 质量同为 2/3，027 两边仍真实遗漏跨平台大小写排序。
- B 相对 P 聚合 input +25.68%、output +23.56%、Agent 时间 +16.89%、代理正文 -6.95%；正确性无收益且四项成本／收益门均失败。B 不采纳，不新增 ADR，不修改发布 Skill。
