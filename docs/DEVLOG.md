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

## 2026-08-19 — 真实开发基准政策采纳

- 复核 Marglo／NextStep Seed_2 的双入口、ADR／State 演化、SQLite 迁移、安全门、UI、测试与发布文档，确认它能提供比纯文档维护更真实的开发任务模式。
- 用户接受 ADR-0002：未来上下文路由采纳实验采用真实产品开发、安全／迁移／跨模块和文档治理的滚动任务组合；三任务 Pilot 至少两项以可运行代码为主要交付物。
- 建立 Approved Design，固定代码优先的 Oracle 层级、隔离／脱敏要求和首批候选任务族。真实 fixture、Implementation Plan 和 Pilot 008 尚未创建，发布 Skill 保持不变。

## 2026-08-19 — docsite AI 设置入口优化

- 将动态 docsite 的 AI 服务设置入口从“问文档”面板移到顶栏主题按钮左侧；静态 HTML 继续不注入设置 UI。
- 统一设置与主题按钮尺寸，并在窄屏收起副标题和搜索框，使 390px 视口保留两个工具按钮且不产生横向滚动。
- 同步根观测台和发布模板，增加入口唯一性／顺序断言，并让动态测试使用空 keyring backend，避免读取维护者真实凭据。
- 1280px 与 390px 浏览器交互验证通过；启用动态 reader 后全仓 40/40、集成结构验证、静态站生成和 `git diff --check` 通过。该变更未新增 ADR，也尚未提交、推送或发布。

## 2026-08-19 — Pilot 008 Skill Entry Router 准备

- 停止继续叠加 Agent Manifest／Receipt 协议，提出直接缩短必读 Skill 入口、按操作加载低频 references 的 R 候选；发布 Skill 保持不变。
- 建立人工脱敏的真实开发 fixture，覆盖反馈状态 Bug、SQLite v1→v2 幂等迁移和实现／State／Handoff 对齐；不复制 Marglo 代码、数据库、凭据、缓存或未提交改动。
- 建立独立行为 Oracle，完成 3/3 baseline negative 与 3/3 positive controls；首次自测发现并修正 `__pycache__` 越界噪音和 Windows SQLite 未关闭句柄问题。
- 修正 Pilot 007 的同名分支盲点，在外层 `pilot-008-outer` 与内层 `pilot-008-fixture` 中完成真正嵌套 preflight；Pilot 008 dry-run 与专项 13/13 通过。
- 将 P 冻结为 Pilot 内 9,109-byte 快照，消除活动发布源并行写入造成的基线漂移；R 为 2,386 bytes，三项完整 Prompt 的 R/P 字节比为 44.48%–44.67%。没有启动模型，没有 R0/token/质量结论，也没有采纳 R。

## 2026-08-19 — Pilot 008 Scope Acquisition 重构

- 用户通过 ADR-0005 明确效率目标：统计 Agent 从任务 Prompt 到首次允许产品写入前，为确认实现范围累计消耗的 input；由 Harness 被动派生，不要求 Agent 生成 Manifest、Receipt、Selected Evidence、访问总结或 reason code。
- Pilot 008 treatment 从 P/R 不同 Skill 改为 P/S 相同完整 Skill：P 保留 598-byte 线性入口，S 使用 1,638-byte 任务优先入口；三项完整 Prompt 在 P/S 间逐项等长为 11,708、11,705、11,666 bytes。
- 新增 app-server Scope analyzer，校验首次 `fileChange`、边界前最后累计 usage、单调性、thread／turn、允许写路径和写前代理 proof；4-case self-test 包含旧 `codex exec` 整轮聚合流的明确拒绝。
- 读取代理增加 passive 模式；P/S 外层／内层 preflight、Pilot dry-run、上下文专项 17/17、默认全仓 51 项中的 49 passed + 2 expected skips、24 项 corpus、6 份既有 run record、integrated static build、195 份 Markdown 本地链接和 diff 检查通过。
- 本机 schema 只证明事件字段存在，不证明真实 ordering；配置保持 `scope_usage_ordering_verified: false`，正式路径在创建输出根或调用模型前失败关闭。本轮没有模型运行、仓库外输出根、R0、Scope Lock token 或采纳结论。

## 2026-08-19 — App-server Scope Ordering Smoke 001

- 维护者授权一次隔离兼容性 smoke，不授权三对 P/S 正式样本。PATH 中的 Store alias 从工作区终端执行被 Windows 拒绝；复制桌面包二进制后确认实际版本为 `codex-cli 0.148.0-alpha.15` 并生成精确 schema。
- 在仓库外一次性 Git 仓库启动一个 `gpt-5.6-terra` / medium turn；89 个服务端消息包含 3 次同 turn 单调累计 usage，最终整轮 input 为 58,541，但没有命令、`fileChange` 或产品改动。
- 根因是临时目录只复制了 `codex.exe`，遗漏同版本 `codex-code-mode-host.exe`；模型两次工具启动失败后结束。该运行不能判断 usage／首次写入顺序，最终 usage 不能冒充 Scope Lock 指标。
- 原始根 `appserver-scope-smoke-20260819-130447` 按 contaminated 封存；manifest 36/36 验证有效。runner 已新增 code-mode host、command runner、sandbox setup 与 `rg` sibling 前置检查和 2-case ordering self-test。
- 同版本 runtime 已补齐，但没有自动发起第二个模型 turn。配置保持未验证、Pilot 008 正式路径保持失败关闭；修正后 smoke 自测 2/2、上下文专项 18/18、默认全仓 52 项中的 50 passed + 2 expected skips、benchmark、integrated static build、202 份 Markdown 链接与 diff 检查通过。修正 smoke 与正式样本分别等待维护者确认。

## 2026-08-19 — 平台中立 Core 与 Adapter 架构采纳

- 审计确认权威模型、Python CLI 和观测台具备平台中立基础，但唯一发布单元、版本命名、入口元数据和测试仍围绕 Codex Skill。
- 用户通过 ADR-0004 接受单仓库分包、canonical `AGENTS.md`、独立组件版本和真实 runtime E2E 才能标记 `verified` 的边界。
- 建立 Approved Design 与分阶段 Implementation Plan，明确 Core／CLI／Observatory／Agent Adapter／Harness Adapter／平台安装器的职责和迁移回滚路径。
- 完成权威索引、本地链接、尾随空白、`git diff --check` 和 integrated structure 的文档级验证；没有把该结果扩展为实现或 runtime 兼容证据。
- 本轮没有抽取代码、修改发布资产、运行 Pilot 008、选择第二平台或生成平台兼容证据；当前发布实现仍是 v0.2.0 Codex Skill。

## 2026-08-19 — docsite Provider 凭据加固与可选 Broker

- 用户接受凭据端点绑定、失败关闭、错误脱敏、本地 HTTP 防护和可选 Broker，但否决“必须先测试连接再启用”的两步体验；实现保留一次“保存并启用”，成功后可直接触发正常仪表盘生成。
- 新增 ADR-0003、Approved Design 和完成态 Implementation Plan。直接模式先解析非秘密 Provider 配置，再读取对应环境变量或 Provider／Base URL 指纹绑定的 keyring 槽；旧共享槽不在启动时读取或自动迁移。
- OpenAI／DeepSeek 固定官方 HTTPS 主机，自定义远程端点强制 HTTPS，本地 Broker 只允许环回；SDK 与 Broker 均拒绝跟随重定向。设置、问答和仪表盘刷新改为同源 POST，并补充 Host、请求体、安全响应头和错误脱敏防护。
- 增加确定性 `llm_broker.py`：独立凭据 namespace、固定上游、Bearer client token、模型白名单、SQLite 内容寻址缓存、并发 single-flight、每日请求和保守 token 预算。只有独立 OS 身份或等价外层隔离才可称为 Provider-Key 隔离。
- 根观测台、发布模板、installer managed tools、validator、README、Skill 和自动化测试已同步。测试使用空 keyring、非环回网络禁用和环回假上游，不接触真实 Provider Key。
- 本轮完成专项动态测试、全仓动态回归、integrated static build、根／模板 diff、本地链接和 `git diff --check`；精确结果见 `docs/validation/2026-08-19-docsite-credential-hardening.md`。改动尚未提交、推送或发布。

## 2026-08-19 — 平台中立 Phase 0 发布基线

- 以 v0.2.0 tag 和已发布 checksum 为边界，固化 36 个 Skill 归档路径、8 个 managed tools、三个 CLI 入口以及 release／project manifest 必需字段。
- 新增两项回归，保护 installer／validator／update checker 的人类输出、既有发布契约子集和 canonical `AGENTS.md`；当前并行新增工具不被倒写为 v0.2.0 事实。
- 将模板入口标题从 `Codex state index` 改为 `Agent state index`，保持文件路径与权威职责不变。
- 中英文 README 明确 CLI 尚未独立打包、Codex 为 `experimental`、其他平台为 `target`；没有新增平台兼容声明。
- Project Orrery 产品专项 9 项通过、2 项动态依赖按设计跳过；integrated structure、链接与 diff 检查通过。未运行任何 Pilot、模型调用或 context-routing 测试。

## 2026-08-19 — 平台中立 Phase 1 Core／CLI 抽取

- 建立 Core、CLI、Observatory 三个 `packages/*/src` 源码包，初始版本均为未发布的 0.1.0，Core API 为 1。
- Core 接管 authority／project-manifest schema、release bridge、兼容判定和 canonical 作者模板；Observatory 独立清点 9 个 managed tools，并显式记录自托管源码到目标模板的标题投影。
- CLI 组合 Core 与 Observatory，提供统一 `scaffold`、`validate`、`check-update` 源码入口；现有 Skill 三个脚本改为薄 wrapper。
- 单独复制或解压 Skill 时，wrapper 回退到冻结的 v0.2 实现；兼容路径承诺保留至 0.3.x，最早 0.4.0 移除。
- 三项 Phase 1 回归和完整产品专项通过：新旧入口输出／manifest／文件逐项一致，作者 `AGENTS.md` 不覆盖，发布 ZIP fallback 可独立安装验证；结果为 12 passed + 2 expected skips。
- 这些组件尚未独立发布，也没有 Codex runtime E2E、第二平台实现或 `verified` 状态；未运行任何 Pilot 或 context-routing 测试。

## 2026-08-19 — 平台中立 Phase 2 Codex Adapter 仓库实现

- 建立 `adapters/codex/` 独立薄 Adapter 0.1.0，只包含 Codex `SKILL.md`、`agents/openai.yaml`、安装说明、Adapter manifest 与生命周期安装器；不复制 canonical 模板、schema、兼容规则或项目事实。
- manifest 分别声明 Adapter/API 版本、Core API 1、CLI `>=0.1.0,<0.2.0`、`experimental` 支持状态和空 runtime evidence；`packages/component-versions.json` 同步该投影。
- 新增确定性 `scripts/package_codex_adapter.py`，生成独立 ZIP 与 SHA-256；归档解压后可直接使用自身安装器。
- 平台安装器默认未知目录失败关闭；新装和 dry-run 不触碰目标项目，旧 Skill／已识别 Adapter 仅在显式 `--upgrade` 下先整目录备份，卸载移入可恢复回收目录。备份／回收均位于 skills discovery 根之外，避免旧 `SKILL.md` 被重复发现。
- Adapter 专项 5/5、当前既有产品专项 13 passed + 2 expected skips；合计 18 passed + 2 expected skips。没有运行 Pilot、context-routing 或真实 Codex runtime，也没有写入维护者用户技能目录。
- Phase 2 只完成前三项仓库实现清单；真实发现、调用、失败、更新和卸载 E2E 仍待明确授权，Codex 继续为 `experimental`，v0.2.0 发布事实不变。

## 2026-08-19 — Broker 成为 docsite 唯一 API 网关

- 用户要求不再把 Local Broker 与 OpenAI／DeepSeek／Custom 并列；通过 ADR-0006 将后三者改为 Broker 上游注册预设，动态 docsite 的有效 Provider 恒为 `broker`。
- 默认本机托管模式在 docsite 进程内启动环回 Broker，自动分配端口，使用独立 Provider namespace 和 client token，并为所有请求提供缓存、single-flight、模型白名单和预算门。
- 外部隔离模式只接收 Broker URL 和 client token；从本机模式切换时删除同用户托管 Provider Key 与 Broker token，但不把“同用户托管”误述为隔离。
- `set_key.py` 已改为 Broker 注册器；`serve.py` 重载与测试、`docsite_qa.py` 默认和 CLI 入口都要求 Broker。旧直接配置只报迁移错误，不读凭据或后台直连。
- 根观测台、Skill 发布模板、中英文 README 和权威文档已同步。动态产品专项 16/16，默认全仓 59 项中 57 通过、2 项按设计跳过；integrated static build、语法、投影与 diff 检查通过。本改动未提交、推送或发布。

## 2026-08-19 — App-server Scope Ordering Smoke 002

- 维护者重新授权一次修正后的隔离兼容性 turn，不授权 Pilot 008 三对 P/S 正式样本。临时运行目录补齐 `codex.exe`、code-mode host、command runner、sandbox setup 与 `rg`，并逐项确认其 SHA-256 与当前桌面包一致；实际版本为 `codex-cli 0.148.0-alpha.15`。
- 真实事件流中，冻结指令读取命令在事件 59 完成，累计 usage 在事件 60 到达，首次产品 `fileChange` 在事件 62 启动；仓库最终只把 `marker.txt` 从 `BEFORE` 改为 `AFTER`。
- 独立 analyzer 判定 `measurement_valid: true`、`precision: exact`，写前 input 19,361、cached input 9,984、non-cached input 9,377、output 99；最终整轮 input 为 58,481。
- Smoke policy 的 `minimum_prewrite_content_reads` 为 0，所以该结果只证明 usage／首次写入的真实事件顺序，不证明代理正文交付，也不是 P/S 成本样本。无关 MCP startup 产生 HTTP 502 噪音但未进入任务调用链，正式 transport 仍需隔离或明确分类。
- 原始根 `appserver-scope-smoke-002-20260819-132227` 按 `decision_supporting` 封存，manifest 39/39 有效，保留至 2027-08-19。Pilot 配置已改为 ordering verified；正式 app-server transport、proxy proof、R0 封存与汇总仍未实现，runner 继续在模型调用前失败关闭。
- 权威链同步后，Scope analyzer 4/4、ordering 2/2、上下文专项 18/18、默认全仓 59 项中的 57 passed + 2 expected skips、24 项 corpus、6 份 run record、integrated structure、docsite build、205 份 Markdown 本地链接与 diff 检查通过；没有启动额外模型 turn 或正式 P/S 样本。

## 2026-08-19 — Pilot 008 正式装置停止与 Pilot 009 修正

- 为 Pilot 008 接入 app-server 正式 transport、完整事件生命周期审计、真实 proxy proof、exact Scope
  analyzer、独立 Oracle、正式验证、成对失败关闭、R0 seal/verify 和聚合汇总。
- 首对 `PO-CR-031` 的 P/S Scope measurement 均有效；P 额外直接读取用户目录已安装 Skill，因此
  contaminated。两侧实现与测试满足迁移行为，但冻结 Oracle 暗中要求固定索引名和文档词形。
- runner 正确停止后续两项；P 85/85、S 88/88 manifest 有效。原始证据保持只读，修正进入 Pilot 009。
- Pilot 009 使用新 task ID，Prompt 明确排除已安装 Skill，app-server 关闭 `skill_search`；迁移 Oracle
  改为索引列顺序和可观察行为，并放宽第一轮已知词形假设。Oracle 自测与 synthetic formal pipeline 通过。

## 2026-08-19 — Pilot 009 P/S Scope Acquisition 正式运行

- 运行前通过上下文专项 20/20、默认全仓 61 项中的 59 passed + 2 expected skips、24 项 corpus、6 份
  run record、integrated static build、227 份 Markdown 本地链接与 diff 检查。
- 使用 `gpt-5.6-terra` / medium 和 `codex-cli 0.148.0-alpha.15` 完成 3 项 × P/S 六次运行；6/6 access
  audit、exact Scope、formal validation 和 R0 有效，未发生仓库外读取或隐藏重试。
- P/S 聚合写前 input 为 540,105／446,904，S/P 0.8274；non-cached input、唯一 slice bytes、完整
  input、output 和 Agent seconds 比分别为 0.8711、0.8126、0.9059、0.9453、0.9595，成本门全过。
- 冻结 Oracle 0/3 对 0/3 中，033 与 035 是自然语言固定词形假阴性；只读复核为 P/S 各 2/3。034
  两侧行为与数据安全通过，但 PROGRESS 都遗漏未来版本写前拒绝，维持失败；S 不采纳。
- 形成 R2、Validation 和任务／Oracle v0.2 研究候选。下一轮先分离 behavior／data safety／scope／
  structured State／narrative verdict，并通过 paraphrase、contradiction 与 mutation controls；不自动补跑模型。

## 2026-08-19 — sivtr 外部工作记忆层观察

- 固定读取 `Ariestar/sivtr@4fae091`，核对 README、Agent 指令、Skill／MCP、WorkRecord／WorkRef／WorkSet、
  provider registry、BM25／eval、remote／privacy、Roadmap、known issues 与发布状态。
- 结论是 `sivtr` 更适合作为终端与 Agent transcript 的情境证据层，Orrery 继续负责 ADR／State／实现／
  Validation 的权威事实层；二者互补，但历史 memory 不能自动升级为当前事实。
- 记录可研究模式：类型化 provider-neutral record、稳定 ref、`records + anchors` 渐进披露、只读 MCP 与
  Skill 分层、冻结 corpus／逐查询检索指标、显式 opt-in 的 remote origin。
- 同时保留反向证据：Agent 入口／架构／Roadmap 与代码漂移，公开 retrieval snapshot 缺失，regex redaction
  不是安全边界，WorkSet／parse cache 扩大敏感副本与 lifecycle 负担，MCP contract 尚未稳定。
- 两次 `cargo test --workspace --locked` 都在依赖 build script 启动时被本机 Windows `os error 5` 阻断，
  没有进入项目测试；静态 659 个 `#[test]` 不冒充通过数。未安装 sivtr、未读取真实 transcript、未改发布
  Skill／Observatory／路由 treatment，也未创建或运行新 Pilot。
- Orrery `--build --require-integrated` 结构／静态站验证通过，231 份 Markdown 的 395 个本地链接无缺失，
  相关文件 `git diff --check` 通过。

## 2026-08-20 — 共享工作树恢复与多 worktree 协作采纳

- 三个并发 Agent 曾共享 `main@96eee5a` 和同一工作目录；先建立 `codex/recovery-shared-main-20260820@a87c5a4`，完整封存 198 个路径的交错改动，没有 reset、覆盖、推送或删除原证据。
- 在独立 integration worktree 中将恢复提交拆分为 context-routing 研究、平台 Core／Codex Adapter + Broker docsite、sivtr Library 和权威状态四组提交，再合入协作协议分支。
- 临时决策 `PO-DEC-WT-001` 在最新集成历史上获得正式 ADR-0007；Approved Design 与活动 Plan 明确 Canonical／Candidate／Worktree 作用域、主 worktree 集成专用和临时 ADR 编号规则。
- 首次默认回归发现通用 EOF 空行清理改变 Pilot 008／009 冻结输入哈希；没有修改冻结哈希，而是从恢复提交逐字节还原 27 个文件。定向 apparatus 2/2、默认 59 passed + 2 expected skips、动态 61/61、integrated structure、691 KB 静态站和 235 份 Markdown／420 个本地链接随后通过。
- 本轮只采纳并验证人工工作法；私有 session、自动重叠检测、主 worktree 守卫、integration CLI 和观测台作用域投影仍未实现。没有推送 `origin/main`，也没有发布版本。
- 已从本地集成点建立 `codex/agent-context-routing`、`codex/agent-platform-adapters` 与 `codex/agent-docsite` 三个 clean linked worktree；它们共享对象库但拥有独立 Git 管理目录、索引和工作目录。

## 2026-08-20 — ADR-0008 与多 Workstream 产品 Design 收敛

- 在独立 `codex/agent-context-routing` worktree 中完成安全并行、指挥台、冲突预警和多人多 Agent 的产品层讨论，并以单一候选提交交给 integration worktree 审阅。
- 最终审计发现 Team Mode 的未 push 元数据同步超出了 ADR-0007 仅认 pushed／PR／CI 输入的边界；没有改写历史，而是把临时 `PO-DEC-WT-002` 在集成时分配为 ADR-0008，正式修订跨机器可见性。
- Approved Design 现固定默认 zero-network Personal Mode、显式 Team Mode、Agent-first／Orrery-first 混合入口、Workstream／Scope／subsystem、L0–L3 finding、双维度状态、风险审查、人工合流、保守清理和渐进式 Observatory。
- Implementation Plan 改为 Personal foundation → 本地 review loop → opt-in Team extension → self-host／release，并把新实现目标指向平台中立 Core／CLI／Observatory／Adapter；发布 Skill 继续只是兼容投影。
- 本轮只更新决策与文档，没有实现协作 CLI／UI／网络能力、改变支持状态或创建发布；精确集成检查见 `docs/validation/2026-08-20-adr-0008-collaboration-design-integration.md`。

## 2026-08-21 — ADR-0009 Authority Meta Model 规范落地

- 把维护者网页讨论先保存为非权威 Library，再提炼为临时 `PO-DEC-AUTH-001`；逐项审计 ADR-0001～0008 后，接受 AUTH-2／3／5／6／7／8 的限定版本，AUTH-1／4 继续 pending。
- 外部复核纠正了早期“状态转换”表述：各 authority object 拥有自己的 lifecycle，Decision／Implementation／Validation 是独立但相关的 claim dimensions，不能压缩为 `planned → implemented → validated` 单一状态机。
- 正式分配 ADR-0009，并建立 Authority Meta Model Approved Design／State：规范角色、非线性 Authority Graph、Canonical／Candidate／Worktree／Local-only／Historical／Unknown、provider-neutral evidence 和 derived-view semantic constraints。
- `docs/core/principles.md` 明确为 Project Orrery Product Seed，不再与通用 Meta Model 职责混写；平台中立 Design 同时保留 AUTH-4 单一 implementation owner 未决定的边界。
- 本轮没有创建 Implementation Plan、修改产品代码、拆分 Observatory、增加 `authority_model_version` 字段或改变发布状态；这些留到下一次对话。

## 2026-08-21 — Codex Adapter Runtime E2E 集成

- 将 `codex/agent-platform-adapters` 的两个已验证提交以 `--ff-only` 集成到本地 `main`；功能分支和 main 在合流前均 clean，merge base 为 `117acac9825b0ee93f0a98a8a64c8b82d13f56f6`。
- 使用 Codex 官方 `skills.config` per-run 禁用项隔离真实登录态中的同名旧 Skill；精确 `codex-cli 0.148.0-alpha.21` Windows runtime 实测需要指向旧 `SKILL.md` 文件，模型可见目录才只剩 repo Adapter。
- `gpt-5.6-terra`／medium 真实 turn 完成显式／隐式 Adapter 路由、CLI 0.1.0 preflight／validate、distribution 缺失和 0.2.0 不兼容失败关闭；旧 v0.2 Skill 显式升级、完整备份、可恢复卸载、重新发现和作者文件保留也有复现证据。
- manifest 只把精确 Windows／Codex／Adapter／Core／CLI／模型／审批 runtime compatibility 标记为 `verified`；Adapter distribution 与组件顶层继续为 `experimental`／`unreleased`，没有发布、第二平台或 Phase 3 实现。
- 真实用户旧 Skill／Codex 配置未修改，凭据未读取、复制或输出；repo Adapter 已从隔离 fixture 可恢复卸载。完整矩阵见 `docs/validation/2026-08-21-codex-runtime-e2e-completion.md`。

## 2026-08-21 — Phase 3 Harness JSON 候选实现

- 从本地 `main@14af26a` 建立 `codex/harness-json-phase3` 独立 clone；沙箱禁止写主仓库 `.git`，因此没有在主 worktree 注册 linked worktree，也没有污染 main。
- CLI 提升到未发布 0.1.1，为 scaffold／validate／check-update 增加 schema v1 opt-in JSON envelope 与稳定退出码，同时保留既有人类输出和旧 Skill wrapper。
- 新增未发布 Harness JSON Adapter 0.1.0：白名单 request schema、response schema、subprocess timeout／protocol failure 分类，以及 Codex／Agent／Provider 环境变量清理；Adapter 不包含或加载 `SKILL.md`。
- Windows 隔离测试覆盖确定性 dry-run、临时实际安装、mixed toolchain、备份升级预演、schema 失败关闭、offline no-cache、非法请求和作者文件保留；默认全仓 66 passed + 2 expected skips，动态 68/68。
- 当前只形成 Windows candidate；该提交尚未运行 Windows／Ubuntu CI，仍为 `experimental`／`unreleased`，没有模型调用、第二平台、push、tag 或 Release。

## 2026-08-21 — Authority Meta Model M1 本地 Canonical 集成

- 从 `main@2989582` 审阅 `codex/authority-meta-model-fixtures` 的 20 个提交；Candidate 与 main merge base 一致，功能 worktree 和主 worktree 均 clean，随后以 `--ff-only` 集成到本地 main。
- ADR-0010 指定平台中立 Core 为唯一确定性 evaluator owner；ADR-0011 固定项目模型选择、release 默认值 + 离散支持集、legacy／unsupported 失败关闭和显式语义迁移边界。AUTH-1 仍未决定。
- 集成 `amm-fixture-v1`、experimental Core evaluator、CLI／Observatory shadow、模型 capability、receipt-gated migrate／restore、future release projection、AI non-escalation receipt 和默认关闭的诊断面板；默认 legacy 页面、退出码和公开 v0.2.0 资产不切换。
- 合并前完整发现 196 项测试并全部成功，Authority 专项 120/120；integrated structure、1096 KB 静态站、269 份 Markdown／586 个本地链接／0 缺失和 `git diff --check` 通过。迁移／恢复安全审阅确认写入仅限项目 manifest、项目内备份和原子替换，拒绝外部路径及 symlink 逃逸。
- 本轮只完成本地 Canonical 集成，没有 push、tag、Release、稳定 API、standalone installer 模型声明或 production consumer switch。

## 2026-08-21 — Authority Meta Model M2 本地 Canonical 集成

- 从 clean `main@65ef774` 建立独立 integration worktree；M2.1 `db81691` 与 M2.2 `06ee3eb` 顺序快进，M2.3 `cfd76e4` 作为从 M2.1 分叉的独立发布门通过 merge commit `bb03040` 接入。
- 三处冲突均为 Implementation／State／Validation 索引中的并行追加，人工保留双方事实；产品代码没有语义冲突。
- 本地 Canonical baseline 现包含完整内部 CLI Authority bundle、root-only opt-in Observatory projection 和 provider-neutral release-candidate gate；legacy CLI、默认文档站、公开 v0.2.0 历史资产和发布状态不变。
- 合并后 Authority 163 项中 160 通过、3 项环境跳过；全仓 231 项中 226 通过、5 项环境／可选依赖跳过。结构、默认与显式 projection、release gate、277 份 Markdown／639 个本地链接／0 缺失和 diff 由独立 M2 integration Validation 记录。
- 本轮没有 push、tag、Release、实际 SemVer／manifest 选择、稳定 API 或 managed consumer production switch；M2.3 `release_ready` 继续为 false。

## 2026-08-21 — 当前状态入口职责压缩

- 审计发现根 PROGRESS 已累计早期 Pilot、平台阶段和实现史，Authority State 也保存了逐检查点实现与 Validation 文件目录；两者虽然内容大多正确，但不再适合作为 Agent／维护者的快速当前入口。
- 将 PROGRESS 从 146 行压缩为 55 行，只保留四条当前线路、当前结论、活动计划、阻塞、最近完成与下一里程碑；完整历史继续由本 DEVLOG、Validation 和 Git 记录承担。
- 将 Authority State 从 147 行压缩为 60 行，以规范事实和 Core／CLI／Observatory／migration／release gate 分层能力表替代逐检查点叙述，并把实现／验证证据收敛为少量权威入口。
- Documentation System State 明确 PROGRESS／HANDOFF 是集成入口而不是历史总账。本轮没有改变 ADR、Design、Plan、代码、发布契约或公开支持状态。
- 首次把本 Validation 写成精确 `Result: Passed` 时，完整回归捕获 strict role collector 会将其升级为结构化 Validation success；改用非权威 `Status:` 表述后，相关 32 项专项和最终全仓回归通过，没有削弱 collector 或测试。
- 全仓 231 项中 226 通过、5 项按既有环境／可选依赖跳过；integrated build、默认／显式 Authority projection 回滚、278 份 Markdown／655 个本地链接与 diff 检查通过。

## 2026-08-21 — 文档治理与信息生命周期采纳

- 维护者确认当前入口还需要长期治理规则；ADR-0012 正式修订 ADR-0001 的维护职责，同时保持 ADR-0009 Authority Meta Model 只定义事实语义，不吞入文档编辑工作流。
- Approved Design 把 AGENTS、HANDOFF、PROGRESS、State、ADR、Design、Plan、Validation、DEVLOG、Snapshot 和非权威材料分别映射到当前／历史职责、更新事件和保留规则。
- 治理采用事件驱动同步、链接而非复制证据、按职责拆分和 soft review budget。未来 CLI／Harness／Observatory 只能生成 non-authoritative finding，不得自动改写作者文档或创造事实。
- 活动 Plan 将只读 contract／fixture、CLI、Observatory 和公开模板／发布拆成后续阶段；本轮只完成自托管规范，没有实现 audit runtime、改动产品代码、切换模板或发布版本。
- HANDOFF 因包含大量安全接续信息被标为首个专项 review candidate；本轮只增加治理接续入口，没有未经人工复核删除既有风险。
- 首轮全仓回归正确捕获仓库级 amend 关系冻结集合缺少 ADR-0012；只补充 `ADR-0012 → ADR-0001` 的精确预期，未放宽 Authority evaluator 或测试。
- 修正后全仓 231 项中 226 通过、5 项按既有环境／可选依赖跳过；integrated build、默认／显式 Authority projection 回滚、282 份 Markdown／686 个本地链接和 diff 检查完成。
- 候选提交 `15e0071` 在 clean `main@3e4847b` 上通过 `--ff-only` 进入本地 Canonical；没有 push、tag、Release 或公开模板迁移。

## 2026-08-21 — Harness JSON State 漂移修正

- `docs/state/project-structure.md` 仍保留 Phase 3 候选早期的“尚未经过 Windows／Ubuntu CI”描述，与平台 Plan、Release State、Test Coverage State 和既有 Phase 3 Validation 冲突。
- 依据同一候选提交 Windows／Ubuntu 双 PASS 的既有证据，将当前事实修正为“CI 已完成，但仍为 `experimental`／`unreleased`，不证明第三方 Agent runtime 兼容”。
- 本轮只修复 State 漂移并追加历史记录，没有修改实现、测试、Adapter、组件版本、PROGRESS、HANDOFF 或发布状态。

## 2026-08-21 — main 验收、跨平台夹具修正与公开同步

- 对相对公开 `origin/main@117acac` 的 38 个本地提交执行动态全仓 231 项、integrated build、Authority 显式投影／默认回滚、Markdown 链接、发布排除与 diff 验收；本地检查全部通过。
- 首次推送 `95fa4e3` 后，GitHub Actions `32492265629` 的 Windows job 通过，Ubuntu job 发现 `test_cli_preserves_candidate_manifest_lexical_path` 把 `C:/...` 错当作所有平台的绝对路径。
- 在独立 `codex/fix-release-gate-posix-lexical-path` worktree 中把夹具改为平台原生绝对词法路径；产品安全门未改动，symlink identity 不得提前 resolve 的约束保持不变。
- 修正后 Windows focused 10 passed + 2 privilege skips、Ubuntu WSL focused 12/12；提交 `42aebae` 快进进入 `main`。最终 GitHub Actions `32492830151` 在 Windows／Ubuntu 双 PASS。
- `main` 已同步至公开 GitHub；v0.2.0 仍是当前公开 Release，没有 tag、Release、实际 SemVer／manifest 选择、稳定 API 或 managed Authority production switch。

## 2026-08-22 — W1 Personal Core／CLI Phase 0 Candidate

- 在独立 linked worktree 和 `codex/w1-personal-core-contract` 分支完成协作 Phase 0；实现提交为 `4ae4f0a`，没有写入主 worktree、push、merge、tag 或 Release。
- Core 0.1.1 新增 provider-neutral collaboration schema、dependency-free validation、integration ref／OID 和主 worktree 解析、显式 subsystem registry、Scope 特殊表达、Member capability／credential epoch 与 zero-network project mode contract；CLI 0.1.6 新增只读 `collaboration-contract`。
- 合成 Git fixture 实际建立 clean main、两个 linked worktree、独立 clone、文件级 untracked 和未 push commit。首次实现后测试暴露 CLI fixture 缺 Observatory source path 及 Git untracked 目录折叠，均收紧 fixture 后修复。
- 最终专项 10/10、受影响组合 67 passed + 2 expected skips、全仓 236 passed + 5 existing skips；integrated structure、隔离静态站、284 份 Markdown／696 个本地链接和 diff 检查通过。证据见 [Phase 0 Validation](validation/2026-08-22-personal-collaboration-phase-0.md)。
- 本轮没有实现持久 session、主目录写入守卫、Scope/path collector、finding 计算、review／integration／cleanup、Observatory 或 Team 网络层；根 PROGRESS／HANDOFF 留给唯一整合者同步。
