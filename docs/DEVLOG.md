# 开发日志

## 2026-08-29 — SC1 Closed Worktree Removal

- 经维护者明确确认后，对 W5D、CI4、R1、R2、R3、W6 六个 `closed/superseded` worktree 逐项复核 registered／clean／allowed ignored／branch／commit／session 状态；完整 Git-private `orrery/` 先归档到 `.git/orrery/retired-worktree-sessions/2026-08-29/` 并复核 SHA-256。
- 使用 exact-path `git worktree remove --force` 只移除六个 worktree 目录及其可重建 generated ignored 内容；所有 local branch、remote ref、commit、作者文档、源码历史和发布事实保持。
- post-check 为 7 个 registered worktree：清理期间独立 `codex/github-front-door-redesign` worktree 被创建且不在本轮授权范围内，因此完整保留。maintenance 25 秒 bounded scan 先前失败关闭，没有生成自动 queue／authorization／receipt，本操作不冒充自动 cleanup 产品证据。

## 2026-08-29 — SC1 Canonical State Closeout

- 只读对账确认 `main = origin/main = 9ee831f`，主工作树 clean；CI5 Fast `33235942078` 与 Promotion `33235992711` 均成功，Promotion 为 25/25 jobs、双平台各 390 tests／27 shards、23.9 lane job-min 和约 40% derived overhead，同一 SHA 已进入 protected main。
- 从 clean main 建立独立 `codex/sc1-canonical-state-closeout` worktree；本轮只收口 AGENTS、PROGRESS、HANDOFF、四份 subsystem State、相关 Plan 状态、CI5 Validation、DEVLOG 与索引，不修改产品代码、组件版本、release manifest、branch protection、tag 或 Release。
- PROGRESS／HANDOFF 恢复为当前控制入口，逐次历史继续链接 DEVLOG／Validation；R3、W5C、W5E、W7D、CI3、CI5 不再以等待 Promotion 的 Candidate 表述，W6 明确为 Phase 0–2 Canonical／Phase 3–4 未实现。
- 本机旧 Workstream session 的 lifecycle 与 Git ancestry 不一致被保留为单独协调问题；Git-private retirement 不冒充 W3 integrated closure，物理 worktree／branch 删除不属于作者文档提交。

## 2026-08-29 — CI5 Promotion Throughput Optimization Candidate

- 在 CI4 exact `a4b0ed3` Fast 2/2、Promotion 59/59 双平台通过并 fast-forward `origin/main` 后，从该 Canonical 基线建立 D 盘独立 `codex/ci5-promotion-throughput` worktree，登记 Git-private `CI5-promotion-throughput-optimization`；不另开任务，不修改产品组件。
- 四次成功 Promotion 的 54 shard jobs 稳定只有约 15 分钟测试、约 24–26 分钟环境开销；CI5 保留 27 个逻辑 shard／全部测试／原预算与 required checks，新增十个 fail-closed physical lane，每个 shard 继续用独立 Python 子进程和独立 result，aggregate 另验十份 lane receipt。
- Windows／Ubuntu lane 与 repository gate 改为共同 preflight 后并行；Fast 只取消同分支 superseded feedback，并忽略已由普通分支 Fast 检查过的冻结 `promotion/**` push；Promotion 不复用／取消且完整执行。真实 `lane-05` 生成 3 shard＋1 lane receipt 并 3/3 PASS；本机波动保持原样，不作为放宽预算或重跑依据。
- CI4 Checkpoint baseline 78/78 assertion PASS 但 164.741828s 超 90s，其中单个最小 Git journey 为 120.961576s。该 journey 只移出 Checkpoint、仍完整存在于 W7B Promotion；阶段反馈随后为 80/80 41.697448s，最终 81/81 两次为 42.806990s／43.071302s，预算未调高。
- CI contract 17/17、inventory 390／27／10／57／81、最终 Fast 57/57 3.235952s、integrated validation、2,040 KB／157-doc 隔离站、repository gate（667／360／1010）、release dry build、workflow YAML、compile/diff 门通过；exact-SHA hosted Fast/Promotion 留给 Candidate closeout。

## 2026-08-29 — CI4 Opaque CLI Token Argument Reliability Candidate

- 精确从 R3 `439c40fe5347689d8616cc057812d9a6438ca116` 建立 `codex/ci4-opaque-cli-token-argument-reliability`，首次作者写入前注册 Git-private Workstream；primary 为 test-coverage，affected 为 release-and-toolchain、documentation-system、project-structure，并由本轮唯一整合者授权同步根 HANDOFF，不改 PROGRESS。
- 只在 `tests/test_workstream_relation_execution.py` 的 apply／undo CLI 调用中使用单 argv `--confirmation-token=<opaque-token>`；新增确定性 leading-dash apply→undo 回归，分别固定 `-leading-dash-apply-token` 与 `-leading-dash-undo-token`。没有把 token 正文拼入 shell 命令，也没有修改产品 Core／CLI parser、token 生成／entropy／hash／storage、schema、协议或 receipt 语义。
- 当前非历史代码／文档审计只发现产品 parser 声明与该测试的调用点；历史 Validation／DEVLOG／Pilot 命令保持原样。R3 brand contract 6/6 验证稳定 Python／CLI／Skill／Adapter ID、schema／历史 hash 与 brand allowlist 未漂移。
- 本机 leading-dash 1/1、原失败流 1/1、W7B 5/5（501.427s）、W7A 15/15（30.959s）、Fast 57/57（3.217789s／15s）、inventory 386／27／57／78、CI validator、integrated validation、repository gate（664／358／1002）和 diff gate通过。R3 baseline Fast `33231693802` 双 PASS；Promotion `33231693777` 的 Ubuntu `team-relations-execution` 因随机 `-` 开头 token 的分离 argv 失败。CI4 exact-SHA hosted Fast／Promotion 结果在最终任务回执报告，不为其追加 docs-only commit。

## 2026-08-28 — R3 Orrery Brand-only Closeout Worktree Candidate

- 精确从 clean `main@1e67d4ac7f18e11459417ff4e04eef0ce065b28b` 建立 `codex/r3-orrery-brand-only-closeout`，首次产品写入前注册同名 Git-private Workstream；primary 为 documentation-system，affected 为 project-structure、release-and-toolchain、test-coverage。普通功能分支未修改根 PROGRESS/HANDOFF。
- 新增 machine-readable brand contract，先将候选写入分类为 current brand、stable technical ID、protocol ID 或 historical fact，再只更新 allowlisted 当前 README／文档入口、默认 self-host surfaces、Broker 和安全的 Skill／Adapter display metadata。目标项目 title token 继续可定制；未增加 alias、复制实现或改变 discovery／upgrade／uninstall identity。
- 冻结并复核 8 份 schema、ADR-0015、Approved Design、phase-0 baseline、v0.2 manifest／Core data 和公开 ZIP hash；`project-orrery-*` distributions/assets、`project_orrery_*` imports、CLI／Skill／Adapter IDs、`.project-orrery.json`、环境变量／header／credential namespaces 均保持不变。历史页面保留原事实，不以旧字符串归零为目标。
- 浏览器在 1280px 与 390×844 验收默认站、Personal、Team 和 Graph：当前品牌均为 Orrery、零横向溢出、零 console warning/error；Personal／Team／Graph 的 zero-network、derived-read-only、synthetic-non-authoritative／无执行入口边界保持。专项组合 64 tests PASS + 2 expected skips，Fast 57/57，integrated installation、isolated docsite、repository／links／diff gates 通过。完整命令与限制见 [R3 Validation](validation/2026-08-28-r3-orrery-brand-only-closeout.md)。
- 本 Candidate 未 push、合并 main、修改 GitHub settings、tag／Release、选择 SemVer 或迁移本地 root／Codex Saved Project／Codex data root。R4/R5 未启动；exact-SHA 双平台 required checks 与 Promotion 留给唯一整合者。

## 2026-08-28 — R2 Orrery decision acceptance closeout

- 维护者接受 ADR-0015 并批准 Orrery Rename and Compatibility Design；R3 的 ADR/Design 门已解除，可另立 Workstream 启动，但本次仍未实现 R3，R4/R5 继续是后续独立 Workstream。
- 固化 R4 默认：`orrery` 为显式 opt-in、collision-checked thin launcher，路由到单一 canonical implementation；各宿主默认只改 display name，只有独立证明 safe discovery/upgrade/uninstall 后才增加 thin alias。首个新 Orrery Release 继续使用 `project-orrery-*` archive/asset filename。
- 本机 root/Saved Project 维护改为 R3 exact-SHA 进入 main 后即可另行授权，不依赖 R4/R5；随后 Codex application-data D 盘迁移仍须再开独立 Workstream。本次没有执行本机迁移、remote/package/schema/CLI/Skill/Adapter/tag/Release 变更，根 PROGRESS/HANDOFF 保持不变。
- acceptance closeout 通过 repository gate（660 paths／356 Markdown／998 links）、integrated installation validator、产品专项 16 run／14 pass／2 expected skips、Fast 51/51（2.681523s／15s）、diff 与 13-path docs-only boundary；未运行完整 Checkpoint/Promotion，R3 后续必须取得自身 exact-SHA 门。

## 2026-08-28 — R2 Orrery Rename Decision and Compatibility Contract

- 精确从 clean `main@2037cab7a46ae048147115c3c317f8d542a8cee9` 建立 `codex/r2-orrery-rename-decision-contract`，并在作者写入前注册 Git-private `R2-orrery-rename-decision-contract`；primary 为 project-structure，affected 为 release-and-toolchain、documentation-system、test-coverage。普通功能分支未修改根 PROGRESS/HANDOFF。
- 把未合入 R1 `f991bef` 作为 Library provenance，而非 cherry-pick 或 current State；在 current main 重算 655 tracked paths、品牌/技术/协议/冻结面，并只读核验 GitHub current repo/redirect/v0.2.0 assets 与 PyPI `orrery` 冲突。
- 新增 Proposed ADR-0015、Proposed-for-approval Design 和 blocked R3–R5 Plan：产品 brand 为 Orrery；Python distribution/import、project manifest、v1 schema/contract/hash/Authority/Workstream、credential/cache/backup namespaces 保持稳定；旧 Skill/CLI/config/Adapter 入口覆盖完整 0.3.x，最早 0.4.0 只评审而不承诺移除。
- 本任务没有执行 R3、全仓改名、本地目录/Saved Project/Codex 数据迁移，也未修改 package/schema/CLI/Skill/Adapter/GitHub settings/tag/Release。验证只覆盖 current-main inventory、文档权威链、索引/链接、repository gates 和 diff；R3 必须等待维护者接受 ADR 并批准 Design。

## 2026-08-28 — W7D W7 Integration Candidate

- 精确从 CI2 `8b635b1` 建立独立 `codex/w7d-w7-integration-candidate`，写入前注册 Git-private Workstream；复核 W7A→W7B→CI2 祖先链、两输入 clean worktree 与 W7C-A 对应树已被 W7C-B 字节级吸收，只加法合入 W7C-B `d411fd6`。
- 对 DEVLOG、Implementation/Validation 索引、四份 subsystem State、组件版本和 CI manifest 做语义整合。组合版本为 Core 0.1.14／CLI 0.1.18／Observatory 0.1.9；schema 2 保留 Fast 15 秒、Checkpoint 90 秒和独立 W7B Promotion 300 秒。preflight 与双平台 aggregate discovery dependency 顺序均纳入 workflow validator/回归，最终机械 inventory 为 377 IDs／27 shards／51 Fast／70 Checkpoint。
- W7B 的 discovery/plan/human confirmation/apply/recovery/receipt/undo 是已实现 Candidate 能力，但真实 self-host apply、默认 UI 执行入口和公开发布仍未发生；W7C 图继续只读且没有 apply/undo/close/delete 控件，中央 Team 视图没有执行权。
- Focused 13/13、初始 Fast 51/51 2.132432 秒、Checkpoint 68/68 81.201647 秒通过；preflight 修复后 CI contract 10/10、新增第 69 个 Checkpoint selector 独立通过，最终 hosted 修复后的 Fast 51/51 为 2.328416 秒，未机械重跑完整 Checkpoint。1280×900 与 390×844 in-app Chromium 覆盖三 lens、筛选、历史、节点/边 inspector、键盘、安全链接、零横向溢出与零 console warning/error。唯一一次 W7B Promotion 的 4/4 测试断言成功，但 311.803221 秒超过 300 秒预算而由 runner 正确判 FAIL；未放宽预算或重跑，逐测试对照、结构门与 hosted exact-SHA 结果进入独立 W7D Validation。
- 修复后的 hosted run `33192808364` 进入完整矩阵，W7B 在 Windows 2m36s／Ubuntu 20s 双 PASS；required checks 仍因 W7C 测试读取 self-host Git-private session、Authority lazy `_llm`/ADR-0014 expected map 与 Windows workspace 字符串路径比较失败。对应修复后本地 workspace 3/3、Team UI 16/16、Authority 127/127 通过；没有改预算、产品关系执行权、图形按钮或发布边界。
- 第三轮 hosted run `33193955085` 的 54 个跨平台 Promotion shard 与两侧 repository gate 全部通过，W7B 为 Windows 2m32s／Ubuntu 31s；两个 required aggregate 在下载完整 27 份 artifact 后因自身未安装 `mistune` 而失败。现已在 Windows/Ubuntu aggregate 清点前安装相同 discovery requirements，并新增双平台顺序门；这是 CI 聚合装置修复，不改变测试选择或产品边界。
- exact Candidate `28f5fad24f8589e146ce56c5507b3e76d81c2bfe` 在 hosted run `33194655256` 取得 59/59 jobs PASS；Windows required job `98929761747`、Ubuntu required job `98929961709` 双 PASS，W7B 分别 164 秒／23 秒低于原 300 秒预算。Candidate 已 ready for maintainer-authorized main fast-forward；本任务没有推动 main、tag、Release、branch protection 或删除任何历史对象。

## 2026-08-28 — CI2 Tiered Test Performance Candidate

- 从干净 W7B `1160df4` 建立独立 `codex/ci2-tiered-test-performance`，注册 Git-private session 并声明测试、CI manifest/runner、test/release State、Validation、Plan 与 DEVLOG 范围；未改 W7B、main、PROGRESS 或 HANDOFF。
- W7B 的九套完整 fixture 重建收敛为一个 dependency-light Fast、一个 minimal-Git Checkpoint 和两个完整 Promotion journey；完整拓扑只构造两次，W1 生产 `create_worktree` acceptance 不再被 W7B fixture 重复调用。
- CI manifest schema 2 新增显式 Checkpoint 与 hard budget；Fast 为 15 秒、Checkpoint 为 90 秒，W7B 独立 `team-relations-execution` Promotion shard 为 300 秒。最终 inventory 为 362 IDs／27 shards／49 Fast／66 Checkpoint，0 missing／duplicate／dead selector。
- 本机 Windows Worktree：最终 Fast 49/49 2.117s、Checkpoint 66/66 83.629s、W7B Promotion 4/4 264.738s，较原 921.066s 缩短约 71%。没有完整全仓、hosted exact-SHA、push、main merge、tag 或 Release；远端证据留给唯一整合者。

## 2026-08-28 — W7B Succession Apply／Undo／Legacy Inference Candidate

- 精确从修正后的 `codex/w7a-dynamic-workstream-succession-contract@52e88b8` 建立独立分支，并在首次产品写入前注册 Git-private `W7B-succession-apply-undo-legacy-inference` session；primary 为 multi-worktree collaboration，声明 project-structure、documentation-system、release/toolchain、test-coverage、预计写入与验证面。
- Core 0.1.14 新增 execution schema、exact Session/HEAD/Scope/project/graph binding、legacy/explicit discovery、one-time local-human confirmation、write-ahead journal、apply/undo receipt 与 append-only recovery。非 terminal journal 阻断 graph；恢复只还原 exact Session 或追加 cancelled/stale compensation，W6 删除授权保持独立。
- CLI 0.1.18 新增 `relations discover|plan|inspect|apply|undo|receipt`；Unknown/blocked 稳定非零失败关闭，伪造/重放/过期/跨项目 token、actor/plan mismatch、graph/Session/HEAD/Scope drift 与重复 history 均拒绝。没有 shell/path/URL 执行面、网络调用、merge/push/delete/tag/Release。
- 隔离 W5C→W6→W5D→CI1/W5E fixture 完成 late CI、多 predecessor、active/completed takeover、故障注入/recovery、receipt/undo 与 CLI 全闭环；CI1 inventory 为 366 IDs／26 shards／49 Fast。self-host 真实项目只运行 dry-run：8 proposed／2 Unknown／exit 5，relation store 仍不存在、作者树不变。
- 受影响 subsystem State、W7B Validation、DEVLOG 与索引同行；根 PROGRESS/HANDOFF 留给唯一整合者。任何真实项目 apply 仍需维护者本机 exact confirmation 和中央另行授权。

## 2026-08-28 — W7C-B Production Workstream Relation Graph Observatory

- 从 corrected W7A `52e88b8` 建立独立 Workstream，并精确吸收 W7C-A `a39f6a7`；共享 project/documentation/test State、Validation index 与 DEVLOG 只做加法合并，W7C-A fixture 继续保持 provisional/non-authoritative。
- Observatory 0.1.9 新增 root-only／default-off sibling page；provider 只接受 Core `workstream-relation-graph`／`workstream-succession-plan` v1，三 lens、history folding、filters、SVG/ledger/inspector 不扫描 Git/Session/branch/path，也不提供 apply/undo/close/delete/merge/remote execution。
- provider/schema/root/node/evidence/legacy Unknown/Core failure 整体失败关闭；safe source links 只投影白名单仓库文档锚点，Git-private/opaque evidence 不导航。默认 docsite、managed tools、Skill template、release manifest 与公开 v0.2.0 未改变。
- Focused 13/13、Fast 50/50、W7A/W7C-A/Personal/Team 45/45 以及 CI/structure/install/isolated-site gates 通过；真实 in-app Chromium 在 1280px 与 390×844 完成三 lens、过滤、历史、点击、Enter/Space、inspector、safe link、zero-overflow 与截图。未运行 Promotion，未 push、合 main、改 protection、tag 或 Release；W7B 的执行层当时已在 sibling Candidate 实现，本页面未接入 apply/undo。

## 2026-08-28 — W7A Dynamic Workstream Succession Contract

- 中央只读验收拒绝初始 `b6be68e`：旧 node summary 把 waiting/paused/blocked/failed 误判 active，且 apply/undo 无法原子标记/恢复 predecessor Session。本 correction 在同一 ADR-0014 下修正，不改写 peer Session 或 W7C-A。
- Core 0.1.13／CLI 0.1.17 保留独立 lifecycle/runtime/evidence/Scope/subsystem/visibility/observability 轴，以严格 active eligibility 和 completed predecessor `closed/superseded` 失败关闭修复 active-tip；apply/receipt/undo 冻结 exact graph/Session/HEAD/no-drift 与无删除原子 I/O，执行仍留给 W7B。
- 新增 synthetic-non-authoritative W7C consumer compatibility fixture；只读对照 `w7c-a@a39f6a7` 的字段需求，不复制 provisional schema、页面、布局或 UI 权威。Focused 15/15，CI1 inventory 357 IDs／26 shards／48 Fast。
- 从 `W5E-team-observatory-ui-closeout@692d19b` 注册独立 Git-private W7A session，并以 ADR-0014／Approved Design／Candidate Plan 正式接受增量关系方向。
- 新增 provider-neutral `derived_from`／`depends_on`／`absorbs` event、五态 lifecycle、graph／active-tip／discovery／apply／undo／legacy projection contract，以及 `$GIT_COMMON_DIR/orrery/workstream-relations/` append-only 边界。
- Core 0.1.12 与 CLI 0.1.16 提供 dependency-free exact OID/ancestor、cycle/multi-parent、post-fork/sibling/Unknown/L2-L3 保守判定和 `relations graph|succession-plan|propose`；Observatory 与公开 v0.2.0 未改变。
- 脱敏 W5C→W6→W5D→CI1→W5E＋late CI fixture 与 12 项 focused 测试全部通过；CI1 为 354 IDs／26 shards／45 Fast。邻接版本断言已同步；W5D 双 clone runner 两次并发 loopback timeout 后独占 PASS，未修改其 transport。
- W7B 保留真实自动发现、一次本机确认批量 apply、transition/undo 和 legacy migration；W7C 保留三类图形派生与可访问列表。W7A 未 push、未合 main、未改 branch protection、未 tag 或 Release。

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

## 2026-08-22 — DeepSeek Harness Adapter 真实模型 Stage B

- 使用用户明确授权且已配置的真实 DeepSeek credential；Key 仅进入隔离 headless 子进程内存，未复制到测试根或 Git，真实 GUI profile／settings／launcher 和运行进程保持不变。
- `@deepseek-ai/dsh 0.1.0-rc.8`、`deepseek-official`／`deepseek-v4-flash` 完成显式 `/project-orrery`、隐式 `skill({name: project-orrery})`、CLI distribution 缺失 exit 3 和 0.2.0 不兼容 exit 4；失败路径均无 fallback。
- editable source CLI 0.1.1 的 preflight／validate 通过；普通 wheel CLI 同版本在 `validate` 前因无法定位 source-owned Observatory assets 失败，证明 version preflight 不能替代可执行兼容证据。
- 六个模型 turn 后，隔离 Adapter remove／restore／final remove 的 runtime discovery 为 0→1→0，424 个作者 fixture 文件逐字节一致。由于 wheel blocker，支持状态继续为 `experimental`／`unreleased`，`verified` 不提升。

## 2026-08-22 — W1 与第二平台 Adapter 干净整合

- 从 clean `main@8df974f` 建立独立 integration worktree，先 no-ff 合入 W1，再重放 Claude／DeepSeek 两个逻辑提交；两个来源没有共享工作目录，原分支与 worktree 均保留。
- 旧平台分支的 Phase 4 `ADR-0010` 与主线 Authority ADR 编号冲突，整合时分配为 ADR-0013，并保留 0010–0012 的既有含义。
- 全局 State／PROGRESS／HANDOFF 由唯一整合者合并：W1 只提升到本地 Canonical Phase 0，Adapter 仍是未发布 experimental source；没有推送、tag、Release 或支持状态提升。
- 联合专项首次暴露 Authority amendment 期望未包含 ADR-0013；补齐冻结关系后 31/31 通过，最终全仓与结构验收见[整合 Validation](validation/2026-08-22-w1-and-second-platform-adapters-integration.md)。

## 2026-08-22 — CLI Wheel Observatory Assets 修复

- Observatory wheel 构建现在依据版本化 `component.json` 的固定白名单嵌入九个 managed tools；CLI 优先使用安装包内 assets，只有 source／editable checkout 才回退 monorepo。
- 新增隔离 wheel 回归，在全新 venv 中完成 Core／Observatory／CLI wheel 安装、scaffold 与 validate；普通非 editable wheel 不再依赖源码仓库。
- 同一普通 wheel 又通过真实 DeepSeek Harness 显式 Adapter turn，preflight／validate 均 exit 0；作者 fixture、credential 与 GUI profile 保持不变，隔离插件最终卸载并恢复 0 项 discovery。
- 功能分支证据与修复见 [CLI Wheel Validation](validation/2026-08-22-cli-wheel-observatory-assets.md)；是否写入最终 `verified` compatibility entry 由干净整合与联合回归决定。

## 2026-08-22 — DeepSeek Wheel Runtime Canonical 集成验收

- 从 `main@56d44fb` 建立独立 integration worktree，只重放 P1 在旧 Stage B 检查点后的 `77811f9`；功能代码无冲突，四份共享文档按当前 W1／Authority 事实增量合并。
- 联合回归首次捕获两组 Authority CLI 测试缺少新声明的 Observatory source 依赖；显式补齐测试 path 后相关 10/10 通过，没有删除测试或增加 skip。
- 默认全仓 243 PASS + 5 expected skips，动态全仓 245 PASS + 3 Windows symlink privilege skips；结构、隔离静态站、297 份 Markdown／779 个本地链接、secret scan 与 diff 检查通过。
- 只有 rc.8／Windows build 26200／Adapter 0.1.0／Core 0.1.0／CLI 0.1.1 wheel／指定 DeepSeek provider-model 与记录范围进入 `verified`；Adapter 发行仍为 `experimental`／`unreleased`，没有 tag 或 Release。

## 2026-08-22 — DeepSeek／W1 首次远端 Windows CI 修复

- `afdbc3b` 推送后的 GitHub Actions `32500503338` 在 Ubuntu 通过、Windows 失败；失败不是模型或 Adapter 行为，而是 Windows `RUNNER~1`／长路径别名比较和 runner 未安装 `wheel` 两项测试基础设施问题。
- Core 路径规范化改为 realpath + normcase，仍只接受 Git 列出的 worktree；workflow 显式安装 wheel 测试依赖，不把它加入产品运行依赖。
- 本地受影响专项 11/11、动态全仓 245 PASS + 3 Windows symlink privilege skips；原失败 run 保留。修复提交 `000111d` 的 GitHub Actions `32554191374` 随后取得 Windows／Ubuntu 双 PASS，跨平台修复完成。

## 2026-08-22 — W1.1 Personal Phase 1A Candidate

- 延续已完成的 W1 Phase 0，在独立 `codex/w1-1-personal-phase-1a` worktree 完成只读 worktree status 与 Git-private Workstream session；实现提交为 `6c5570d`，没有占用 W2 Scope/Finding 编号。
- Core 0.1.2 派生 branch／HEAD、integration ref／OID、merge base、ahead／behind、dirty fingerprint 与计数；CLI 0.1.7 提供稳定 JSON `worktree status`，只有显式 `worktree session write` 才原子写入 `git rev-parse --git-path orrery/worktree.json`。
- session 绑定 worktree ID、branch、HEAD、integration ref／OID 与 dirty fingerprint；status 以稳定原因码报告 stale，不自动重写。linked worktree 与独立 clone 均验证私有路径、scope 字段和作者工作树不变。
- 专项 13/13、默认全仓 246 PASS + 5 existing skips、动态全仓 248 PASS + 3 Windows symlink privilege skips；integrated structure、隔离静态站、本地 Markdown links、secret scan 与 diff 检查通过。证据见 [W1.1 Validation](validation/2026-08-22-w1-1-personal-phase-1a.md)。
- 本轮没有实现 worktree create、主目录写入守卫、完整 lifecycle／attach／rebind、Scope/Finding、review／integration／cleanup、Observatory、Team Mode、push、tag 或 Release；根 PROGRESS／HANDOFF 留给唯一整合者同步。

## 2026-08-22 — W1.2 Personal Phase 1B Candidate

- 在 W1.1 Candidate 之上建立 stacked `codex/w1-2-personal-phase-1b`；实现提交 `ebf9b75` 将 Core／CLI 提升到 0.1.3／0.1.8，没有重写既有 W1／W1.1 历史，也没有占用 W2。
- `worktree create` 固定配置的本地 integration OID，创建 branch + linked worktree 并初始化 Git-private `created` session；branch／path 碰撞预先拒绝，session failure／integration drift 回滚本操作创建的 clean 对象。dirty primary 的作者改动原样保留，新 worktree clean。
- `worktree guard` 作为平台中立只读 preflight：隔离 worktree allow；clean／dirty primary 均 block，dirty 只给人工恢复边界，不自动迁移。当前 Adapter 尚未强制调用，因此不宣称全局写入拦截。
- 专项 18/18、默认全仓 251 PASS + 5 existing skips、动态全仓 253 PASS + 3 Windows symlink privilege skips；其余结构／站点／链接／secret／diff 证据见 [W1.2 Validation](validation/2026-08-22-w1-2-personal-phase-1b.md)。
- 本轮没有实现 lifecycle transitions、launch／attach／rebind／message、Scope/Finding、review／integration／cleanup、Observatory、Team Mode、push、merge、tag 或 Release；根 PROGRESS／HANDOFF 留给唯一整合者同步。

## 2026-08-22 — W1.3 Personal Phase 1C Candidate

- 在 W1.2 Candidate 之上建立 stacked `codex/w1-3-personal-phase-1c`；实现提交 `8874f1a` 将 Core／CLI 提升到 0.1.4／0.1.9，并完成 Phase 1 最后两项，没有改写 W1／W1.1／W1.2 历史或占用 W2。
- session schema 新增独立 evidence freshness、closure reason、lifecycle revision 与 transition reason；Core／CLI 只允许显式合法转换。Git／evidence 漂移会把有效 Review Ready 退回 `validating` 并保留原因；尚无 executable gate 时进入 Review Ready／Integrated 失败关闭。
- 四个 Adapter Candidate 提升到 0.1.1 并声明 launch／attach／rebind／message matrix；Codex、Claude Code、DeepSeek Harness 当前只支持 caller-provided attach，Harness JSON 全关闭。三个 Agent Adapter Skill 强制先走只读 route；attach 只写 Git 私有 session，no-rebind 返回新 Workstream／新会话 continuation brief，dirty primary 不自动迁移。
- 专项 22/22、默认全仓 255 PASS + 5 existing skips、动态全仓 257 PASS + 3 Windows symlink privilege skips；既有真实 Adapter runtime evidence 继续精确绑定 0.1.0，没有提升 0.1.1 支持状态。其余结构／站点／链接／secret／diff 证据见 [W1.3 Validation](validation/2026-08-22-w1-3-personal-phase-1c.md)。
- W2 Scope/Finding、review／integration／cleanup、closure archive、Observatory、Team Mode、实际 platform launch／rebind／message、宿主级任意写入拦截、push、merge、tag 和 Release 均未实现；根 PROGRESS／HANDOFF 留给唯一整合者同步。

## 2026-08-22 — D1 文档治理 Phase 1 finding contract

- 在独立 `codex/document-governance-finding-contract` worktree 中冻结 Core 内部 `documentation-governance-finding-v1` schema、11 条规则 registry 与 dependency-free validator；没有增加 scanner、CLI、Observatory 或公开 API。
- finding 显式携带 source／scope／evidence、category／severity、uncertainty、人工 review status／ack 和五项 `must_not_infer`；schema 拒绝 patch、Authority、Validation 写入字段，Authority／作者文档 effect 恒为 `none`。
- 11 组正负合成 fixture 覆盖 soft budget、入口密度、重复事实、当前／历史、断链、State／Plan／Validation 职责、失活 Plan、metadata 和功能分支全局入口 ownership；golden evidence 绑定文件 SHA-256 与行区间。
- 所有 D1 规则默认 exit 0；soft budget 仅 advisory，断链只标记为未来 `eligible-not-enabled`。真实项目配置位置／阈值、ack storage 和任何硬门仍待 Phase 2 之后另行决定。
- 专项 11/11 已通过；完整仓库、integrated structure、隔离静态站、Markdown links 与 diff 结果进入对应 Validation。根 PROGRESS／HANDOFF 按普通功能分支规则保持不动。

## 2026-08-22 — C1 Context-routing Oracle v0.2 无模型静态 Controls

- `C1` 是开发任务编号，不是 R0／R1／R2 evidence layer。在独立 `codex/context-routing-oracle-v0-2-static` worktree 建立研究专用 Oracle 包；未调用任何模型，未创建 Pilot 010，未触碰发布 Skill、冻结 Pilot 004–009 或仓库外 raw evidence。
- 四层 verdict 分开保留形式有效性、语义质量、结构化 State／未来版本遗漏和 apparatus contamination；checksummed 7 文件 fixture 公开 versioned State 字段、枚举与四项可发现测试。
- 20 个 self-test cases 覆盖三组英／中 paraphrase、每项事实两组 contradiction、索引改名、关键 behavior/data/scope/State/formal mutations、未知措辞人工复核与外部读取污染；全部只走临时 Git、Python 公共调用链与 SQLite，结果明确为 `model_calls: 0`。
- 静态结论只允许申请 Pilot 010 设计；任务包、Prompt 等长、嵌套隔离、目标 runtime handshake 和 formal transport 尚未冻结，因此不得运行新样本或采纳 S。

## 2026-08-22 — W1／D1／C1 本地 Canonical 集成

- 从 clean `main@606e2c8` 建立独立 integration worktree，按 W1→D1→C1 顺序吸收；W1 六个 stacked commits fast-forward，D1/C1 只在共享文档追加处冲突并按当前事实增量合并。
- 首轮联合专项捕获 C1 fixture 从 C 盘重放到 D 盘后的 CRLF hash mismatch；新增 fixture-source 专属 LF 属性，保持原 manifest hash，Pilot 004–009 冻结目录不变。
- 修复后联合专项 35/35、默认全仓 268 PASS + 5 existing skips、动态全仓 270 PASS + 3 Windows privilege skips。
- W1 Phase 1、D1 contract/fixture 与 C1 static controls 进入 Canonical source；W2/D2/C2、Pilot 010、发布和模型运行均未自动启动，远端 CI 尚待推送。
- 首次远端矩阵 `32564000587` 为 Ubuntu PASS／Windows FAIL；Windows 失败来自测试对 `RUNNER~1` 与 Git 长路径做字面比较。产品 containment 逻辑未改，测试改用 realpath/normcase 后 collaboration 22/22，最终 `32564334514` Windows／Ubuntu 双 PASS。

## 2026-08-22 — Candidate-first main promotion gate 候选

- 多次“先推 main、再由远端发现平台差异”说明本地全仓无法替代 GitHub runner；问题是推广顺序，不只是缺少更多测试。
- self-host 流程改为先推 Candidate exact SHA 并等待 Windows／Ubuntu 双 PASS，再快进 main；服务端 required checks 对管理员生效，但不强制 PR。
- 本记录先随 Candidate branch 运行自身矩阵，保护规则和 main 推广结果由同一 Validation 在外部状态完成后补全。
- Candidate `e4e4442` 的 `32566445483` Windows／Ubuntu 双 PASS 后，main protection 已以 strict/admin enforcement 启用并接受同一 SHA；workflow 随后排除普通 main push，避免重复矩阵。

## 2026-08-22 — W2 Scope / Finding Candidate

- 从 `origin/main@193b3ba` 在独立 `codex/w2-scope-finding` worktree 实现正式 W2；实现提交为 `de5152e`，没有启动或编号 W3/W4/W5，没有修改用户级 Skill、push、merge、tag 或 Release。
- Core 0.1.5／CLI 0.1.10 复用 collaboration-v1、Git-private session、subsystem registry 和 W1 route/guard，采集 committed／staged／unstaged／untracked／expected 五类路径来源，并提供 `worktree overlap`、`scope inspect/refresh` 与 `finding acknowledge`。
- Scope observation 识别 Seed／ADR／Design／Plan／State／Validation／AGENTS／PROGRESS／HANDOFF／DEVLOG，按 registry Truth 路径映射 subsystem；Unmapped／project-wide 保持显式，共享 subsystem 只提高 Semantic 检查优先级，不自动判冲突。
- Direct／Authority／Semantic／Unknown 与 Open／Acknowledged／Resolved／Stale 绑定 Scope／baseline fingerprint；L2 只接受本机 Member 理由确认，跨成员保存 `n/m`，单方确认只解锁本地工作。Direct／L3、凭据／release／schema 独占面和未本机确认 L2 已接入 Adapter route 并失败关闭。
- collaboration 专项扩展到 27/27；实现提交后的默认全仓 278 项中 273 PASS + 5 existing skips。完整动态、结构、隔离站点、链接、secret／forbidden 与 diff 结果见 [W2 Validation](validation/2026-08-22-w2-scope-finding.md)。
- W2 只把 Acknowledged L2 与处置历史保存为未来 W3 审查包输入，不生成审查包；review／integration／cleanup、Observatory、Coordinator／LAN／Team transport、自动合流和自动修复均未实现。

## 2026-08-22 — W2 本地 Canonical 集成

- 从受保护 `main@6e1f9cb` 建立独立 integration worktree，重放 W2 两个提交；实现无冲突，共享 DEVLOG／State／Validation 索引与 promotion-gate 事实增量合并。
- collaboration 27/27、默认全仓 273 PASS + 5 existing skips；结构、站点、链接与安全门完成后，exact SHA `21a2e1c` 先推 Candidate 分支，并在 GitHub Actions `32570545138` 取得 Windows／Ubuntu required checks 双 PASS。
- branch protection 随后允许同一 SHA fast-forward 进入 `origin/main`；没有 PR、tag、Release 或重复 main matrix。W2 进入 Canonical source 后下一任务为 W3，公开 v0.2.0 与发布状态不变。

## 2026-08-22 — W3 Review / Integration / Cleanup Candidate

- 从本地 `main@ef488715` 建立独立 `codex/w3-review-integration-cleanup` worktree；远端 fetch 因本机 `127.0.0.1:7897` proxy 无法连接而未刷新，但开始时本地 `main` 与本地 tracking `origin/main` 指向同一 OID。工作树保持未提交、未推送，根 PROGRESS／HANDOFF 留给唯一整合者。
- Core 0.1.7／CLI 0.1.12 Candidate 复用 W1/W2 collaboration-v1、Git-private session、Scope、finding、acknowledgement 与 route gate，新增 `integrate --dry-run`、证据优先 review package、Approve／Request Changes／Hold／Reject、integration eligibility、Git-private closure record，以及 bounded workspace inventory/advisory-only cleanup eligibility。
- 推测性 merge／rebase 只在工具新建的干净临时 integration worktree 中运行；package 精确绑定 target OID、candidate HEAD、Scope revision/fingerprint、finding set、schema version/byte hash、validation set 与内容 hash。输入漂移、冲突、验证／State／ADR 失败、缺少足够非作者人审都会失败关闭；AI 摘要明确非权威且不计 reviewer。
- 2026-08-23 在同一 W3 范围内补充 cleanup contract：inventory 只从 Git metadata、private session/closure、项目允许根和显式候选取数，分类七类；历史无 session/closure 目录必须显式采纳，保留策略与 Unknown 失败关闭。remove worktree、local branch、remote branch、ordinary directory 是四个互不隐含的授权，工具全部不执行；closure v2 引用 Git-private caller-attested action log。没有把本机截图、历史 clone、临时输出或仓库外 benchmark 声称为已审计可删。
- 实现不 fetch、不更新 main、不 push、不建 PR/tag/release、不删除用户 branch/worktree/ordinary directory，也不实现 W4 Observatory、W5 Team Mode、平台 launch/rebind/message 或任何网络 transport。W3 focused 13/13；按更新后的验证策略，当前增量只以专项/checkpoint 交付，全仓动态、docsite、全链接与 exact-SHA 双平台矩阵由中央在 W3+W4 干净联合 Candidate 上统一执行。证据见 [W3 Validation](validation/2026-08-22-w3-review-integration-cleanup.md)。

## 2026-08-23 — W3 Canonical integration candidate

- 冻结 W3 实现 `e807f4c` 与 Candidate 文档 `1aa3f32`，在 W2 base `ef48871` 上按原顺序吸收；没有包含 W4、分级验证文档分支、用户级 Skill、历史目录或仓库外 benchmark。
- 本地 integration candidate `c758827` 运行唯一一套动态全仓：291 项中 288 PASS + 3 个既有 Windows symlink privilege skips；integrated structure、1,471 KB 隔离站点、337 份 Markdown／862 个本地链接／0 unexpected missing、secret／forbidden 与 diff 门通过。
- W3 仍不执行真实 main update 或清理动作；Promotion 必须先把包含最终集成记录的 exact SHA 推到非 main branch，并取得 Windows／Ubuntu required checks。公开 v0.2.0、W4/W5 和 Release 均不改变。
- 首次远端 `32583193534` 为 Ubuntu PASS／Windows FAIL；Windows 失败来自 `RUNNER~1` 与等价长路径的测试字面比较，而非产品 cleanup 放行。测试统一使用与 Core 相同的 filesystem identity 后，两个原失败用例本地 2/2 PASS；保留首次失败并要求新 exact SHA 重跑双平台门。

## 2026-08-22 — 分级验证原则

- 用户接受 `Fast → Checkpoint → Candidate → Promotion` 作为跨阶段验证原则：日常迭代使用受影响专项，完整动态全仓与双平台证据留给冻结后的联合 integration candidate。
- W3／W4 已通过任务控制消息人工采用该策略；被中断且无明确终态的长测试不计为证据，不再在编辑循环盲目整轮重跑。
- Candidate-first exact-SHA Windows／Ubuntu 门保持不变。本轮只记录原则、Plan 与当前人工状态；未实现持久 runner、自动影响分析、缓存、跨 SHA 复用或 CI 跳过规则，也未创建 ADR。

## 2026-08-22 — W4 Personal Observatory Worktree Candidate

- 从最新 `main@ef488715` 建立独立 `codex/w4-personal-observatory` worktree；与并行 W3 保持隔离，只消费已经 Canonical 的 W1/W2 Core／CLI contract。真实构建通过排除槽把 `codex/w3-review-integration-cleanup` 仅登记为 Unavailable，没有打开其工作目录或 Git-private session。
- Observatory 0.1.1 Candidate 新增只读 Personal projection 与 root-only opt-in builder。投影按本机 worktree 聚合 branch／HEAD／integration／merge base／ahead-behind／dirty-untracked、Scope、subsystem、Direct／Authority／Semantic／Unknown、Scope Revision、ack `n/m`、lifecycle／runtime／freshness；规则均委托 Core 0.1.5，不在 UI 重算。
- 首页采用项目状态、需要关注、活动 Workstream、subsystem 四区；路径、finding 与 Git 细节使用原生 details 按需展开。W3 review queue／integration eligibility／cleanup eligibility 没有 contract 时稳定显示 `Unavailable / W3 not integrated`；无本机 finding 仍提示 remote/unreported Unknown。
- 页面无表单或执行按钮，声明 read-only／zero-external-network／Team runtime off；没有 Team Mode、Member、LAN、Coordinator、heartbeat、请求传输、平台 launch/rebind/message、merge、cleanup、acknowledge 或作者事实写回。默认 build／serve、Authority projection、AI Q&A、Skill template、managed assets 和 v0.2.0 发布契约未切换。
- 浏览器在 1440×1000 与 390×844 实测：四区、W3 fallback、三维状态、details 展开和空状态有效；窄屏最终 `scrollWidth=375 < 390`，主题按钮保留且搜索框折叠。完整回归、结构、站点、链接与安全证据见 [W4 Validation](validation/2026-08-22-w4-personal-observatory.md)。根 PROGRESS／HANDOFF 按普通功能分支规则保持不动。
- 用户审阅后，Personal Observatory 从总览内嵌面板改为侧栏独立 sibling page；总览 DOM 保持原内容。原先“31 个活动 Workstream”实际混入全部 `git worktree list` 结果，现按 Canonical session／phase 数据分为 2 个未 integrated／closed 的活动 Workstream、28 个无 session 的 worktree 与 1 个隔离 unavailable worktree。活动主行只显示身份、三维状态、Scope／working tree／finding 摘要，29 个非活动项默认折叠，Git OID、路径、finding 与 acknowledgement 留在 details。
- 第二轮用户审阅指出页面仍按机器 schema 而非人的问题组织。页面随后改为编辑式项目简报：首屏用一句确定性当前焦点和“未结束／推进／暂停阻塞／直接重叠”四个信号回答项目现状，关注区把 Direct、暂停、stale、W3 unavailable 与 Unknown 分开解释，Workstream 改成可扫描状态行，subsystem 说明影响范围；W3 slots、Git、OID、路径和 inventory 统一进入底部技术证据。趋势因没有历史快照保持 Unknown，不由 UI 生成项目事实。

## 2026-08-23 — W4B Canonical W3 read-only projection

- 先把已验证 W4A 冻结为本地 `335f10a`，再把 Canonical `main@7932a9c` 精确合入为 `9ab8522`；语义冲突同时保留 W3 Canonical 与 W4A Candidate 事实，根 PROGRESS／HANDOFF 只继承 main 内容且相对 main 无 W4 diff。没有读取旧 W3 worktree。
- W4B 实现提交 `2b9b556` 将 Observatory 推进到 0.1.2。Personal provider 从 session-bound `review_package_id` 调用 W3 Core package freshness 与 integration eligibility，投影 risk、human approval、blockers、target／candidate／Scope binding；七类 workspace inventory、protection、Unknown、estimated size 与 cleanup candidate 也直接来自 W3 Core。
- 只有 Core `recommended_action=evaluate-cleanup-eligibility` 的条目继续调用 cleanup gate；remove worktree、delete local branch、delete remote branch、remove ordinary directory 四个动作分别显示且自动投影要求 `authorized=false`、`performed=false`、`implies_actions=[]`。closure 与 caller-attested action receipt 只作为 Git-private evidence，页面明确不推断删除已发生。
- provider 缺失、失败或 schema 不兼容时只把 W3 区域降为 Unavailable／Unknown，W1/W2 的 W4A 页面继续工作。界面仍按人的项目问题组织，raw OID／hash／path 下沉技术证据；没有执行按钮、Team Mode、LAN、telemetry、请求、外部网络、merge 或 cleanup。
- 隔离修复后的 Fast focused 为 12/12 PASS（99.481 s），包含真实 W3 Core review package→W4 consumer；组件版本一致性 1/1 PASS。实现代理误启动的 collaboration 组合运行在约十分钟后停止并记录为 interrupted，没有重跑或算作通过；默认／动态全仓与 exact-SHA 双平台矩阵留给中央联合 Candidate。
- 首次 W4B diagnostic build 暴露 W1/W2 exclusion 尚未阻止新 W3 provider 间接读取被排除 worktree；该产物立即判废并覆盖。修复提交 `e5a198e` 在显式 exclusion 下完全跳过自动 W3 provider，回退 `IsolationBoundary / Unavailable`；回归测试断言 provider 未被调用。修复后的真实隔离页、稳定 W3 代表页与 provider fallback 页均完成桌面／390×844 浏览器验证，无表单、产品动作按钮、外链或横向溢出。

## 2026-08-23 — W5A opt-in Team Mode foundation Candidate

- 从 `main@7932a9c01efb2e5125da1962873e67383982d98c` 建立独立 `codex/w5-team-foundation` worktree；实现提交 `ac0f4eb` 将 Core／CLI 推进到 0.1.8／0.1.13，没有修改 W4 Observatory／docsite、用户级 Skill、PROGRESS／HANDOFF、tag 或 Release。
- 复用 W1–W3 Member／Host／Workstream／Scope／finding／review contract，新增 Git-private Team config／credential／Coordinator／outbox／inbox、64 KiB exact-field metadata envelope、Member → Workstream 只读 projection、monotonic revision、手工 active Host switch、heartbeat／TTL 与 request-only 本机确认。
- Personal 默认保持零监听；Team enable 本身不打开网络，显式 serve 默认只绑定 loopback，LAN bind 要求本机开关。disable 停止已登记 runtime 并保留本地 Git／Workstream／Validation／文档。
- 手工 invite／join 已实现项目 fingerprint、指定成员、Host-local Admin 确认和非成员拒绝；自动发现、跨 Coordinator 迁移／选主、云 relay、多设备迁移、完整 credential re-issue UX 与 W5 UI 留给后续。
- focused 13/13 PASS；adjacent checkpoint 的 24 个实际产品用例全部通过。首次 checkpoint 误写两个 unittest class 名，只产生 loader selection error，已用正确 class 名 2/2 补跑；没有把该命令错误重分类为产品通过或失败。完整证据见 [W5A Validation](validation/2026-08-23-w5a-team-mode-foundation.md)。

## 2026-08-23 — W4／W5A non-main integration candidate

- 从 `main@7932a9c` 建立独立 integration worktree，按分级验证原则→W4A/W4B→W5A 顺序吸收；共享 Plan／State／DEVLOG／Validation index 加法合并，代码零冲突，根 PROGRESS／HANDOFF 保持 Canonical main 内容。
- 联合源码版本为 Core 0.1.8／CLI 0.1.13／Observatory 0.1.2；W4 只读投影 W1–W3，W5A 提供显式 opt-in、metadata-only、request-only Team foundation，公开 v0.2.0 与发布入口不变。
- W4+W5 focused 26/26、动态全仓 313 PASS + 3 privilege skips；结构、legacy/W4 站点、340 Markdown／874 links／0 unexpected missing、安全、schema 与 diff 门通过。
- 本轮只准备非 main Candidate；必须先取得 exact-SHA Windows／Ubuntu checks，并由维护者明早确认，才能决定是否合并 main。没有 tag、Release、真实远程执行或目录清理。
- 实现 candidate `2bc6207` 的 Ubuntu PASS；Windows attempt 1 仅既有图形化 AI 设置本机 HTTP timeout，W3/W4/W5 均通过，随后同 SHA attempt 2 PASS。首次失败保留；在根入口和状态同步后，最终纯文档 SHA 仍须重新过 required checks，且继续等待维护者确认。
- 状态同步 SHA `43678f6` 的 Windows 再次在同一图形化设置本机 HTTP 请求超时，Ubuntu 通过，W3/W4/W5 仍全部通过。连续复现后停止 rerun 策略：测试用进程内 loopback 503 假上游替换 `127.0.0.1:9` 关闭端口，定向动态 1/1 PASS；产品行为和网络安全边界未改，最终新 SHA 重新走 required checks。

## 2026-08-27 — W4 health semantics / W5B Team Observatory Candidate

- 从 W4／W5A non-main candidate base `31f04ff` 在独立 `codex/w4-health-w5-ui` worktree 开始；没有触碰主 worktree、根 PROGRESS／HANDOFF、push、PR、main、tag 或 Release。
- Phase A `a900087` 把 Personal 健康页固定为 Delivery now／Reconciliation／Workspace hygiene：current Direct blocker 只计算双方 current session/evidence 的 active／review-pending Workstream；stale source session、历史 finding、过期 review 和未登记 Candidate 进入对账；legacy／no-session／retained／estimated reclaim 与 absent-session Unknown 进入卫生。Primary root 单独保护，Unknown 不丢弃。Observatory 推进到 0.1.3。
- Phase B `b31e1d1` 增加 Core 0.1.9 owned Coordinator stop 与 Observatory 0.1.4 Team sibling page；新 root-only UI 固定 loopback、同源／Host、随机 HttpOnly cookie、16 KiB body、脱敏错误和固定 POST，复用 W5A projection／permission／revision／TTL／receipt，不增加任意命令／路径／URL 或远程执行面。
- focused／adjacent checkpoint 最终 33/33 PASS，206.129s；真实 Chromium 在 1280 与 390×844 点击 Personal↔Team、enable、start/stop、heartbeat、sharing、capture/sync、request accept/reject、disable，无横向溢出。浏览器首次发现 Team 第 4 个概览入口被旧 CSS 隐藏，随后把概览组设为 expanded 并重建复验。
- 浏览器结束后 Team disabled、runtime registration absent、network features empty，UI server 与测试页均关闭。完整证据和仍未实现的自动发现／真实多机／LAN／云 relay 边界见 [Validation](validation/2026-08-27-w4-health-w5b-team-observatory.md)。

## 2026-08-27 — W4 health／W5B final non-main integration candidate

- 在既有非 `main` W4／W5A integration branch 上以 `--ff-only` 吸收 `a900087`、`b31e1d1` 与 `31b12f7`；候选推进到 Core 0.1.9／CLI 0.1.13／Observatory 0.1.4，`main@7932a9c`、v0.2.0、tag 与 Release 保持不变。
- W4 首屏正式拆成 current delivery blocker、reconciliation 与 workspace hygiene；截图中的历史 Direct、无 session Unknown 和 legacy worktree 不再共同组成一个危急总数，但它们仍作为对账或卫生债务保留，不被隐藏或自动清理。
- W5B 提供 root-only loopback Team 图形流程，延续 W5A metadata-only／request-only／zero-remote-execution 边界；默认 docsite、发布模板与真实多机支持没有被扩大。
- 中央 Candidate 的结构、隔离站、链接与 forbidden 门通过。动态全仓首次 320 项仅有 3 条 Core 0.1.8 冻结版本断言失败；期望同步到 0.1.9 后原失败定向 3/3 PASS。最终 exact-SHA Windows／Ubuntu required checks 和维护者体验确认仍待完成，未经确认不合并 `main`。

## 2026-08-27 — W5C Team Observatory information architecture Candidate

- 从已通过双平台 required checks 的 W4 health／W5B 候选 `6266a44` 建立独立 `codex/w5c-team-observatory-ux` worktree；没有改动已冻结候选、`main@7932a9c`、tag、Release 或公开 v0.2.0。
- Observatory 0.1.5 把 Team 页面从协议调试面板改为人类指挥台：动态当前结论与建议操作置顶，成员／任务与 pending request 为主，handled request 和 Coordinator／Host／heartbeat／revision／测试入口默认折叠。
- 实际浏览器发现并修正 Host 竖排与 Local-only 独占列；同时识别另一个本机 runtime registration／失效登记，不再误写“尚未启动”或只报英文 operation-failed，也不绕过 Core ownership 强停进程。
- 最终 W5A／W5C／component adjacent checkpoint 17/17 PASS，111.523s；1280px 与 390×844 无横向溢出。首次真实页面生成在 37+ worktree 环境约需 2 分钟，缓存／渐进加载留作独立性能任务。根 PROGRESS／HANDOFF 未由本功能分支改写。

## 2026-08-27 — Local worktree cleanup and stale-session retirement

- 维护者要求先清理本机工作区。只读审计确认 31 个 legacy 目标 tracked/untracked 为 0，ignored 只有 `__pycache__`／`docs/_site`，无可疑本机文件或占用进程；使用 `git worktree remove --force` 移除目录但保留所有 branch／commit，回收约 117.1 MB。
- 三个 protected stale session 不被伪造为正常 closed：先把各自 Git-private `orrery/` 复制到 `.git/orrery/retired-worktree-sessions/2026-08-27/` 并验证 `worktree.json` SHA-256，再移除 worktree。恢复证据不进入作者文档或发布包。
- 最终从 38 降至 2 个 worktree；recovery 与最终 integration candidate 目录在确认 clean 后也被移除，但对应 branch／commit 保留。当前 W5C 正式登记为 validating／waiting-for-user；Personal Observatory 从 41 reconciliation／34 hygiene 变为 0／0。remote、源码和 benchmark 未删除。

## 2026-08-27 — Workspace Maintenance / scheduled cleanup Plan

- 维护者接受“定时盘点不等于定时删除”的方向，并要求建立正式 Implementation Plan。新 Plan 复用 ADR-0007／0008 和既有 W3 eligibility，不新增 ADR，也不把人工 38→2 清理写成产品能力。
- 推荐顺序为 contract／fixture → 事件与启动补查＋建议队列 → 本机确认执行 → 显式 opt-in 自动 worktree removal → 跨平台 OS scheduler Adapter。默认阈值为 24h 补查、8 worktrees、500 MB、7 天 worktree 缓冲与 30 天 branch 提醒；所有 branch 动作继续独立且默认不执行。
- 本轮只新增 Plan、索引和历史记录，没有实现 scheduler、executor、maintenance queue、配置字段或 Observatory 新页面；根 PROGRESS／HANDOFF 继续留给后续唯一整合者。

## 2026-08-27 — GitHub 当前入口同步 Candidate

- 根 README 中英文展示名与公开链接同步到 Orrery／`ItIsMixian/Orrery`；self-host 更新入口和 Adapter
  metadata 同步新 URL，`project-orrery` 技术 ID与冻结 v0.2.0 manifest/bridge 保持不变。
- 受影响 JSON、Project 16 项、Adapter 6 项、结构、diff、入口零残留扫描及 6 个公开 URL 验证通过；
  本 Candidate 未提交、未推送，也未修改 tag、Release、Git 历史或 GitHub 设置。
- 首次 Candidate `230a6ff` 误改冻结 v0.2.0 manifest/bridge，远端 run `33107986476` 在 Windows／Ubuntu
  以同一 historical-input hash 门失败，main 未更新；修正恢复冻结文件而不更新冻结 hash，并要求新 exact
  SHA 重跑双平台门。

## 2026-08-27 — W6 Workspace Maintenance Phase 0–2 Candidate

- 从 W5C `6dd508f` 建立 `codex/w6-workspace-maintenance`，在首次产品写入前合入 `main@673e252`；只解决 DEVLOG 加法冲突，未改写 W5C、main、PROGRESS 或 HANDOFF。随后注册 Git-private `W6-workspace-maintenance` session，声明 multi-worktree primary、四个受影响 subsystem、预期写入与验证面。
- Core 0.1.10 新增 strict maintenance v1 policy／scan／queue／authorization／receipt 与 11-scenario corpus，复用 W3 inventory／cleanup eligibility；integration／closed 事件、Observatory 24h catch-up、single-flight／debounce／hard timeout／interrupted recovery 和 evidence-bound suggestion queue 只写 common Git private `orrery/maintenance/`，不扫描整盘、不联网、不自动删除。
- CLI 0.1.14 新增 `orrery maintenance policy|scan|queue|inspect|authorize|execute|receipt|schedule|status`。唯一 destructive path 只接受本机 human authorization ID，固定执行 `git worktree remove -- <已登记路径>`，并在前置漂移／lock／Unknown 时 Stale；成功后验证 path、registry、branch、commit 与 receipt。local／remote branch 不删除，scheduler 固定 unsupported，Phase 3／4 未实现。
- Observatory 0.1.6 增加独立“工作区维护”页：静态输出只读，root-only loopback 动态页提供只读扫描、逐项／批量授权与逐项执行；worktree／local branch／remote branch 三类动作明确分栏。Team 中央新增 `cleanup` request，但 request／accept 均保持 `execution_performed=false`，不会调用 execute。
- W6 focused 7/7、W3 + Personal 27/27、Team + component 4/4、version／W1-W2 compatibility 64/64 PASS；结构门通过。真实 in-app Chromium 在 1280×720 点击维护导航和只读扫描，在 390×844 点击历史 details；两种 viewport 均无横向溢出，移动布局为单列。浏览器扫描后当前仓库仍为 3 个 worktree、0 suggestion、0 receipt、branch 未变；完整隔离站、链接、diff 与命令证据记录在 [W6 Validation](validation/2026-08-27-workspace-maintenance-phase-0-2.md)。
- 本分支不 push、不合并 main、不建 tag／Release；Candidate／Promotion 全仓与 exact-SHA Windows／Ubuntu checks 留给唯一整合者。

## 2026-08-27 — W5D LAN Collaboration Harness and stacked lineage Candidate

- 从 `codex/w6-workspace-maintenance@db78a7f` 建立独立 `codex/w5d-lan-collaboration-harness`，注册 Git-private `W5D-lan-collaboration-harness` session；首次写入前本地 `main@673e252` 未超出基线，远端 fetch 因本机代理不可用未能复核。本分支未改写 W5C／W6 session、main、根 PROGRESS／HANDOFF、tag 或 Release。
- Core 0.1.11／CLI 0.1.15／Observatory 0.1.7 完成默认关闭的最小 LAN discovery、完整 invite／join／Host-local Admin 确认、单 active Host／手工 switch、旧 Host revision 拒绝、断线／TTL／单调重连、request-only 与 capability revoke；Personal Mode 继续 zero-network，Team enable 不会自动广播或启动 Host。
- 单机双身份 acceptance runner 只使用独立临时 clone／credential／runtime、受控 discovery 与 loopback HTTP，7 stages PASS；脱敏 manifest 和阶段结果经独立 validator 校验，未使用真实凭据、外网、DNS 或真实 LAN。真实双机、防火墙／多网卡、睡眠恢复和 exact-SHA Ubuntu required check 仍是后续验收边界。
- collaboration v1 新增显式版本化 `base_workstream_id`＋`task_base_oid` lineage；current lineage 的 committed scope 改为 `task_base_oid..HEAD`，只在可验证祖先链中排除精确 base 已包含的 inherited committed provenance。parent post-fork、siblings、legacy／Unknown、staged／unstaged／untracked／expected 与 L2／L3、exclusive resource、ack／Review Ready 门保持保守语义。
- Synthetic W5C→W6→W5D fixture 的祖先两两计算由修正前 4 Direct／3 Authority 降为纯继承 0／0；child 新增仍可见，parent fork 后同路径重新形成冲突，非法／不存在／非祖先／漂移 base 失败关闭或 Unknown。Personal Observatory 按显式 stacked chain 折叠并显示 base OID、inherited path 和 chain 内 unique current finding；真实 W5C／W6 legacy session 留给中央显式 rebind／retire。
- LAN／Team／Review Ready 定向回归 22/22、lineage／schema／Personal 17/17、结构、隔离 docsite、作者 Markdown 链接、JSON／compile／diff 检查和真实 in-app Chromium 1280px／390px 点击验收通过；完整命令、校验和与平台限制记录在 [W5D Validation](validation/2026-08-27-w5d-lan-collaboration-harness.md)。

## 2026-08-27 — CI1 tiered parallel validation Worktree Candidate

- 从 `codex/w5d-lan-collaboration-harness@ae6913e` 建立独立 `codex/ci1-tiered-parallel-validation`；首次写入前确认本地 `main@673e252` 已是基线祖先，并注册 Git-private `CI1-tiered-parallel-validation` session。未改 W5D／W6／W5C／main、PROGRESS、HANDOFF、branch protection、tag 或 Release。
- 新增 dependency-free final unittest inventory、26-shard manifest、逐 test timing JSON runner、fail-closed aggregate、repository gate 与独立 workflow validator。当前 342 个 discovery ID 全部恰好分配一次；W6 七个方法逐项拆分，Personal Observatory 拆为三片。
- 普通 push／PR 只运行 40-test Fast 并标注非 Promotion；完整 Windows／Ubuntu Promotion 只由显式 ref＋SHA dispatch 或 `promotion/**` 冻结分支触发。preflight 后所有 job checkout exact SHA，最终 required-check 名仍为 `smoke-test (windows-latest)`／`smoke-test (ubuntu-latest)`。
- CI1 回归 8/8、最终 Fast 40/40（runner 3.897s／wall 4.639s）、最终 `workspace-remove` 1/1（runner 148.990s／wall 149.805s）、inventory／YAML／static contract、结构、隔离站、332 Markdown／911 links、forbidden artifact 与 diff 通过。hosted Fast ≤90s 与 Windows Promotion ≤4m 只作投影，留给中央冻结 exact-SHA run 验证。

## 2026-08-27 — W5E Team Observatory UI closeout Candidate

- 从 `CI1-tiered-parallel-validation@67a2fe9` 建立独立 W5E Worktree，并吸收 `0235116` 的组合式接口 Library 草案与 Brownfield Migration HANDOFF 接续；二者没有升级为 ADR、公共 API 或实现事实。
- Observatory 0.1.8 删除重复的 Team 边界 pill 和“现在的情况”摘要，把四项关键状态上移；Team Mode、连接、在线状态与退出常驻外层，低频协议字段、测试／维护请求和隐私说明进入齿轮设置 dialog。Core／CLI／Team server 与安全契约未改。
- Team／component 18/18、CI contract／inventory／repository gate、结构、隔离站、链接、compile 和 diff 通过。真实 in-app Chromium 在 1280px 与 390×844 完成 enable、连接、heartbeat、dialog、退出和响应式验收，最终恢复 Personal Mode；远端 Promotion 与 main 合流仍待中央执行。

## 2026-08-28 — W7C-A Workstream Graph visual prototype Candidate

- 从 `W5E-team-observatory-ui-closeout@692d19b` 建立独立 `codex/w7c-a-workstream-graph-visual-prototype`，首次产品写入前注册 Git-private `W7C-A-workstream-graph-visual-prototype` session，并绑定 W5E parent／task base、expected writes 和 Fast／browser validation surface。没有改 W5E、W7A、main、PROGRESS、HANDOFF、Core、Team server、默认 docsite、Skill 或 release manifest。
- `experiments/workstream-graph-visual-prototype/` 新增 versioned `provisional/non-authoritative` synthetic fixture 与 dependency-free HTML／CSS／JS。Succession 默认折叠三节点历史并保留 active tip／主链／一层 sibling；Dependency 覆盖双前驱与 Unknown；Conflict 覆盖 synthetic confirmed Direct 与 proposed Semantic。所有 node／edge／cluster 选择共用 evidence inspector，桌面 inline SVG 与移动 HTML ledger 共用同一 fixture。
- Design exploration 明确 fixture 字段不构成公共 schema，并把 stable identity、relation/provenance、multi-predecessor、evidence、status、tip、visibility、cluster、ordering/version 与 fail-closed 交给 W7A 冻结；真实 Core/Observatory consumer、安全链接、Personal/Team 投影与 release 接线留给 W7C-B。
- W7A Git-private status 的只读对账确认两个 sibling 都声明修改三份 subsystem State、Validation index 与 DEVLOG，并共享 diff 验证面；该真实整合重叠不写入 synthetic fixture、不触碰 W7A 工作树，留给唯一整合者做加法合并。
- 专项 6/6、JS／JSON、repository gate 与 diff 通过。真实 in-app Chromium 在 1280×720 与 390×844 点击三 lens、edge evidence、history、filter、keyboard/mobile ledger；两端无横向溢出，console 无 warning/error，页面资产只来自 loopback。没有 push、main 合流、tag 或 Release。

## 2026-08-28 — CI3 Fast Validation Dependency Fix Candidate

- 精确从 `codex/w7d-w7-integration-candidate@e2c049e` 建立 `codex/ci3-fast-validation-dependency-fix`，首次产品写入前注册 Git-private Workstream。基线 Promotion `33195264226` 双 required checks PASS；独立 Fast `33195264316` 双平台在 final discovery 因缺 `mistune` 失败，Fast 未启动且无条件 artifact 上传形成次生错误。
- Fast 复用 Promotion 已验证的 wheel＋版本化 docsite requirements 安装和 pip cache，并在 `validate_ci.py --all` 前执行；validator 与 mutation regression 机械保护命令和顺序。结果文件先由跨平台 setup Python 检测，存在才上传；真实 Fast failure 仍保持红色且结果存在时继续上传。
- CI focused 13/13、inventory 379／27／51／72、validator 与 Fast 51/51（2.324s／15s）通过。Checkpoint 两次均为 72/72 assertion PASS，但以 95.382s、98.320s 超 90s 保持 FAIL；预算、selector、W7B/W7C 和 Promotion 未修改，本地 Promotion 未运行。最终 hosted Fast＋Promotion 将绑定一个 clean exact SHA，并只在任务回执报告以避免 docs-only SHA 循环。
## 2026-08-29 — U1 acceptance and U2 integration baseline

- 维护者接受 Unified Observatory 架构与 production docsite inheritance boundary；唯一整合者把临时 U1 proposal 晋级为 ADR-0016，把 Design 晋级为 Approved，同时继续明确 `accepted != implemented`。
- 一个独立 integration baseline 合并 W6.1／CI6、A3 与 U1。A3 与 CI6 只在 `scripts/ci/test-shards.json` 发生预期冲突；整合保留 CI6 schema-5/data-only registry，并登记 A3 七个低成本 Authority consumer tests，CI contract 与 A3 7/7 专项通过。
- U1 synthetic prototype 仍只是 architecture interaction study。U2 必须优先适配现有 `build_docsite.py`／`serve.py` 文档、搜索、AI、作者信息架构和可识别视觉体验；全面视觉重设计没有获得授权。
- 本节点只建立 Candidate baseline，不宣称 `origin/main`、production Unified Shell、默认 launcher、public template、managed tools、tag 或 Release 已改变。

## 2026-08-29 — U2 Unified Observatory Production Integration Candidate

- 从 `codex/u1-u2-integration-baseline@12f3bf53dfc768067a5a4048de63437313ed633a` 建立独立
  `codex/u2-unified-observatory-production-integration`，首次作者写入前注册 Git-private U2 Workstream 并绑定
  exact task base；parent lineage 保持 `parent-unverified-unknown`，没有表述成 origin/main Canonical。
- Observatory 0.1.11 新增 versioned consumer registration/capability discovery、静态 root-only builder、单
  loopback supervisor 和 headless `Start Orrery.vbs`／one-console debug 入口。生产 HTML 直接适配现有 docsite
  reader/search/AI/信息架构与视觉壳；Authority 消费 A3，Maintenance 消费 W6.1，Team/Graph/Personal 复用现有
  provider。route/privilege collision 失败关闭，optional consumer 独立 quarantine，required consumer 触发
  whole-shell rollback。
- 动态模式只公开一个 URL。Host／Origin／cookie／settings token 与 JSON/body gate 在统一入口收口；Team 仍
  项目 opt-in/request-only，Authority/AI 不自行启用，Quick Remove 仍由 provider 要求本机 action-specific
  confirmation＋fresh preflight。最终 diff/browser review 修正 Maintenance legacy action suffix 和旧 Team 页面
  rebuild 阻塞；Unified 使用 ADR-0016 route 并直接轮询 provider status，不复制 cache/eligibility。ready
  identity 与 helper ownership 在正常 stop、console interrupt 和 stale recovery 后释放；`start-docsite.bat` 未改。
- focused 11/11、CI6 Fast 49/49 与最终 Checkpoint 54/54 PASS；静态 artifact 无 Unified dynamic control/Team fetch。真实 in-app
  Chromium 在 1280x720 验证搜索、Maintenance、AI provider 未启用与 Graph Unavailable，在 390x844 验证导航抽屉；两端无横向
  溢出或 console error。Candidate／Promotion、non-main push、main、
  public template、managed tools、installer、tag 与 Release 留给后续唯一整合者。
## 2026-08-29 — U2／W7.1 local integrated experience Candidate

- 唯一整合分支在 W6.1／CI6／A3／U1 baseline 上合入 U2 `a0e5dbc` 与 W7.1 `903d4ac`。U2 提供真实 root-only 单 URL shell、静态 builder、headless/debug launcher 与版本化 consumer registry；W7.1 恢复 relation 已引用 archived endpoint 的 closed/offline/current/superseded 轴。
- W7.1 推进 Core 到 0.1.16；CLI 因精确 Core package 依赖同步推进到 0.1.20；U2 Observatory 为 0.1.11。四个 archive 安全回归登记为 `team-lan-core` Promotion-only medium evidence，不进入 Fast／Checkpoint。
- 当前节点只形成供维护者本机体验的 integrated Candidate。`origin/main`、public template、managed-tool inventory、installer、release manifest、v0.2.0、tag 与 Release 均未改变。

## 2026-08-29 — U2.1 Unified Observatory UX Acceptance Fixes Candidate

- 维护者实际体验 `codex/u1-u2-integration-baseline@4e2b5436d1744d8034011a34986df1eb6a04c9a4` 后拒绝 U2 UX；从该 exact SHA 建立独立 U2.1 worktree，并在首次作者写入前登记 Git-private Session。原 U2 Validation 只保留历史实现／安全证据，不再单独代表 UX acceptance。
- Core 0.1.17 将不兼容的 `last-run.json` 保持原字节并降级为历史 warning，current run 改写独立 `last-run-v2.json`；旧证据不再使 refresh/background/cache 整体失败，也不参与当前 removal eligibility。CLI 因精确 Core 依赖推进到 0.1.21。
- Observatory 0.1.12 只保留一组中文 app 导航与作者文档树，集中主视图词汇，新增全页 `关闭 Orrery 服务`；Team discovery 解释 fingerprint／untrusted／目标 Host 确认边界并标注 loopback self。Personal 改用待确认任务／历史状态与工作区清理建议；Quick Remove 对 0／有 eligible 两种状态均可发现且仍需 fresh preflight＋本机确认。
- Workstream provider gate 接受完整、只读、validation-valid、hash-bound 的 native 或 legacy/archive evidence，native root 只作来源事实；空 evidence 保持 Unavailable，archive 无执行权。动态 endpoint 复用启动缓存；真实 self-host 恢复 W7.1 引用节点／边与 closed 轴，不创建 relation root。
- fixture／内存／loopback 回归与真实 in-app Chromium 覆盖 1280x800、390x844 的 Overview／Personal／Team／Workstreams／Maintenance；无页面级横向溢出和 console error。未读取 Provider key、未访问外网、未真实 join Team、未执行删除。正式 CI6 Fast／Checkpoint 与 clean Candidate SHA 记录在 U2.1 Validation；本分支不修改根 PROGRESS/HANDOFF、不 push main、不发布。

## 2026-08-29 — W7.2 Workstream Graph Readability & Progressive Disclosure Candidate

- 维护者拒绝 integrated Graph 的卡片比例、长 ID、箭头层级和伪展开体验；U2.1 worktree 从 clean `02efa41` 以 `--ff-only` 接续唯一中央 baseline `ad9f094`，并在首次 W7.2 作者写入前登记 Git-private Workstream。根 PROGRESS/HANDOFF 未修改。
- Observatory 0.1.13 将 Graph 改为固定 248×104px 卡片、单一从左到右 rank lane、正交高对比箭头与不透明关系标签；每条链拥有自己的更早历史 cluster，Reset 恢复默认折叠／100%／关闭 inspector。桌面 inspector 为 overlay，390px 用同一事实集合的任务关系列表，桌面重复 ledger 只保留 screen-reader 语义。
- succession／dependency／conflict 三 lens 不再共享 active-tip 填充：dependency 无 edge 时为 0 节点中文空态，单边 fixture 为 2 端点＋1 箭头；conflict 只显示真实 pair 端点。Core relation schema／facts、W7.1 archive hash/source evidence 与零执行权均未改。
- focused Graph＋Unified 18/18、JS syntax、真实 self-host 1280×800／1440×900／390×844 交互与 frontend visual checks 通过；无页面横向溢出或 console warning/error。CI6 Fast／Checkpoint 与 exact clean Candidate 记录在 W7.2 Validation；不运行完整 Promotion、不 push main、不发布。

## 2026-08-30 — W7.2.1 Workstream Graph Interaction Correction

- 维护者在真实网页复查中指出画布缺少 `Ctrl + 滚轮`、SVG 边焦点出现巨大黑框、线路标签压在线上、折叠无法按链收回，以及依赖空态缺乏解释。修正从 exact W7.2 Candidate `5523e6d` 登记 Git-private `W7.2.1-workstream-graph-interaction-correction` 后写入，根 PROGRESS/HANDOFF 未修改。
- Observatory 0.1.14 去掉线路标签盒，以实线青／虚线黄／复合红线和明显箭头编码关系；焦点沿真实路径显示，画布支持 55%–160% 锚点式 `Ctrl + 滚轮`，Reset 恢复 100% 和原点。connected component 使用稳定水平行，展开后的每条上游链可独立收起，技术详情为画布内可关闭 drawer。
- dependency 继续严格消费真实 `depends_on`：self-host 无显式依赖边时显示“当前没有已登记的依赖关系”与 0 节点，不复制接续边或填充孤立任务。Core relation schema/facts、archive 只读与所有执行安全边界均未改变。
- focused Graph＋Unified 18/18、JS syntax、CI6 Fast 38/38 和真实浏览器三档验收通过。CI6 Checkpoint 路由为 44 tests／0 unknown path，但本机固定 90 秒外层预算在既有 Maintenance 增量 fixture 尚运行时超时；该 slow test 独立 1/1 通过（约 68–71 秒），因此本修正不伪称 evidence-eligible Checkpoint PASS，发布与中央整合仍需补齐该门。

## 2026-08-30 — W7.2.2 Graph Arrow & Scrollbar Visual Integration

- 维护者在真实深色页面指出冲突箭头比例失衡、页面／作者侧栏／图画布原生白色滚动条突兀；从 exact clean `bff8ce6` 登记 Git-private `W7.2.2-graph-arrow-scrollbar-visual-integration` 后写入，根 PROGRESS/HANDOFF 未修改。
- Observatory 0.1.15 将 SVG marker 从隐式 `strokeWidth` 倍增改为固定 10×10 `userSpaceOnUse`，默认／冲突路线收敛为 3px／4px；关系事实、lens、方向、折叠语义和执行边界均未改变。
- docsite 根 CSS 新增深浅主题 scrollbar token：页面、侧栏、图画布和技术详情共享 10px 低对比圆角轨道／滑块，去掉原生按钮；390px ledger 和屏幕阅读语义保持。focused 18/18、JS syntax、CI6 Fast 38/38 与三档真实浏览器验收通过，详情见 W7.2 Validation。

## 2026-08-30 — W7.2.3 Workstream Graph Density Correction

- 维护者在真实浅色页面指出少量节点仍被 disconnected component 的整行空白过度拉开；从 exact clean `4e62dba` 登记 Git-private `W7.2.3-workstream-graph-density-correction` 后写入，根 PROGRESS/HANDOFF 未修改。
- Observatory 0.1.16 保持 248×104px 卡片与可读字号，将 rank 通道从 112px 收至 88px，并用 44px 显式 component gap 替代额外 138px synthetic row；canvas 高度改由最后一个真实节点决定。
- 真实 self-host 14 节点／7 边桌面测量为 component gap 44px、rank gap 88px、0 node overlap、0 route/card crossing；390px 继续显示同事实 ledger，console 为空。Core facts、折叠语义、只读与所有执行安全边界未改变。
