# 项目结构 State

Updated: 2026-08-28
Governing ADRs: [ADR-0001](../decisions/0001-project-orrery-self-hosting.md), [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0007](../decisions/0007-multi-worktree-collaboration-and-branch-fact-scopes.md), [ADR-0008](../decisions/0008-local-first-team-coordination-and-cross-machine-metadata.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md), [ADR-0014](../decisions/0014-dynamic-workstream-succession-contract.md)

## 当前事实

- 单一 Git 仓库根：`D:\coding warehouse\project-orrery`。
- 并发协作当前人工采用“一个 Workstream = 一个分支 + 一个独立 linked worktree 或 clone”；一个平台会话可以在该 Workstream 中完成多个相关 Change Set。主 worktree 只供维护者集成。2026-08-20 已用独立 integration worktree 恢复并拆分三个共享工作目录任务，随后为 context-routing、platform／adapters 和 docsite／broker 分配三个干净 linked worktree，证明人工隔离与干净集成路径可行。
- 已发布 v0.2.0 产品源仍是 `skills/project-orrery/`；当前工作树包含未发布的 `packages/project-orrery-{core,cli,observatory}/` 源码边界、`adapters/codex/` 薄平台 Adapter，以及候选 `adapters/harness-json/` subprocess JSON 参考 Adapter。
- Core 持有 schema、manifest／兼容判定和 canonical 作者模板；CLI 组合 Core 与 Observatory；Observatory 持有 managed-tool 清单与模板投影规则。
- 项目文档权威根：`AGENTS.md` 与 `docs/`。
- `docs/state/authority-meta-model.md` 现作为 authority-semantics 子系统事实地图；它只报告规范与实现缺口，不是新的作者文档角色或机器 Meta Model 实现。
- 自托管观测台：根 `scripts/docsite/` 与 `start-docsite.bat`。
- 非权威研究控制面：`experiments/context-routing/`。
- 本地大型原始运行根：`D:\coding warehouse\project-orrery-benchmark`，不属于 Git 仓库。
- 原始运行由仓库内 `experiments/context-routing/harness/raw-evidence-retention-policy.json` 与 `seal_raw_evidence.py` 管理 manifest、校验和、分类和到期状态；工具不自动删除。
- 发布打包与 CI：旧 Skill 使用 `scripts/package_release.py`；未发布 Codex Adapter 使用 `scripts/package_codex_adapter.py`；CI1 Worktree Candidate 的 `.github/workflows/fast-validation.yml` 负责普通 push／PR 快速反馈，`.github/workflows/validate.yml` 负责冻结 ref／exact-SHA 的 Windows／Ubuntu 分片 Promotion；尚未发布多组件产物。
- self-host GitHub 的 main 推广采用 Candidate-first：exact SHA 必须先在非 main 分支通过 Windows／Ubuntu smoke checks，随后才允许快进 main。服务端 branch protection 对管理员生效，不要求 PR；workflow 排除普通 main push，避免同一 SHA 重复矩阵。该外部规则不是通用 Orrery 产品能力。
- Codex Adapter 当前源码版本为 0.1.1，发行支持状态仍为 `experimental`／未发布；其 runtime manifest 中的历史证据只对 Adapter 0.1.0、Windows 11 build 26200、Codex Desktop 26.818.2441.0／`codex-cli 0.148.0-alpha.21`、Core／CLI 0.1.0 与已记录模型／审批组合标记 `verified`，不自动覆盖 0.1.1。
- 当前 W6 Worktree Candidate 从 W5C `6dd508f` 吸收 `main@673e252` 后，把未发布 Core／CLI／Observatory 推进到 0.1.10／0.1.14／0.1.6：W1–W3 提供 Personal Scope/review/cleanup，W4 health 将交付、对账与工作区卫生分层，W5A–W5C 提供 Team foundation 与 root-only UI，W6 Phase 0–2 增加本机 workspace maintenance。Core API 仍为 1；这些只属于 `codex/w6-workspace-maintenance` Candidate／Worktree scope，公开 v0.2.0 不变。
- 当前 W5D Worktree Candidate 从 `codex/w6-workspace-maintenance@db78a7f` 建立，把未发布 Core／CLI／Observatory 推进到 0.1.11／0.1.15／0.1.7。它新增显式启动／停止的最小 LAN discovery、Host-confirmed join、单 active Coordinator generation／手工 Host switch、双 clone acceptance Harness，并修正 stacked Workstream lineage；这些仍只属于 `codex/w5d-lan-collaboration-harness` Candidate，不构成真实双机 LAN、Canonical 或 Release 事实。
- 当前 W5E Worktree Candidate 从 `CI1-tiered-parallel-validation@67a2fe9` 建立并吸收组合式接口／Brownfield Migration 文档提交，把 Observatory 推进到 0.1.8；Core 0.1.11、CLI 0.1.15 与 Core API 1 不变。它只收口 Team 信息架构和本机设置弹窗，不改变 LAN、Team authority、CI、公开模板或 Release 行为。
- 当前 W7A Worktree Candidate 从 `W5E-team-observatory-ui-closeout@692d19b` 建立；中央验收拒绝初始 `b6be68e` 后，correction checkpoint 把未发布 Core／CLI 推进到 0.1.13／0.1.17，Observatory 维持 0.1.8、Core API 维持 1。它新增 versioned `derived_from`／`depends_on`／`absorbs` record／graph／plan、独立 Session/lifecycle/runtime/evidence/Scope/subsystem/visibility/observability node 轴、exact Git evidence、deterministic active-tip、completed-takeover fail-closed 与只读 legacy lineage projection；该事实只属于当前 Candidate。
- 当前 W7B Worktree Candidate 精确从修正后的 `codex/w7a-dynamic-workstream-succession-contract@52e88b8` 建立，把未发布 Core／CLI 推进到 0.1.14／0.1.18，Observatory 0.1.8 与 Core API 1 不变。它在 W7A graph/record 上增加 exact local discovery、legacy materialization proposal、hash-bound execution/undo plan、one-time local-human confirmation、write-ahead journal、deterministic receipt、append-only compensation 与 recovery inspection；真实项目只执行了只读 dry-run，全部 apply/undo 证据来自隔离临时 Git fixture。
- 当前 W7C-A Worktree Candidate 从 `W5E-team-observatory-ui-closeout@692d19b` 建立，只在 `experiments/workstream-graph-visual-prototype/` 提供 dependency-free 静态视觉原型与显式 `provisional/non-authoritative` synthetic fixture。它探索 Succession／Dependency／Conflict、active tip、历史折叠、sibling、多前驱、Unknown／proposed、证据 inspector、筛选和移动端 list fallback；未读取真实 Workstream Session、未接入 Core relation、Team server、默认 docsite、Skill template 或 release manifest。
- 当前 W7C-B Worktree Candidate 精确以 corrected W7A `52e88b8` 为 parent/task base，并吸收 W7C-A `a39f6a7` 的实验资产；Observatory 0.1.9 新增 root-only／default-off `build_workstream_relation_graph.py` 与 sibling page。生产 provider 只消费 Core `workstream-relation-graph`／`workstream-succession-plan` v1，前端不扫描 Git、Session、branch 或路径相似度；provider/schema/root/evidence 失败时整体 Unavailable。W7C-A fixture 继续留在 `experiments/` 且保持 provisional/non-authoritative，默认 docsite、managed tools、Skill template、release manifest 与公开 v0.2.0 不变。
- 当前 W7D Integration Candidate 精确从 CI2 `8b635b1` 建立，并只加法合入 W7C-B `d411fd6`；W7A→W7B→CI2 祖先链和两输入 clean worktree 已在写前复核，W7C-A experiment/Validation 与 W7C-B 对应树字节一致，因此没有再次单独合入。组合组件事实为 Core 0.1.14／CLI 0.1.18／Observatory 0.1.9／Core API 1；它仍是非 `main` Candidate，不是 Canonical 或 Release。
- 本机 worktree 已于 2026-08-27 经维护者授权从 38 个清理为 2 个，只保留 primary 与当前 W5C。31 个 clean legacy worktree 直接移除；3 个 stale-session worktree 先把 Git-private `orrery/` 元数据按 SHA-256 归档再移除；最后移除可由保留 branch 重建的 recovery 与 final W4/W5 candidate worktree。所有 branch／commit 保留；该人工操作不是自动 cleanup 产品能力。
- `adapters/claude-code/` 与 `adapters/deepseek-harness/` 当前源码版本为 0.1.1、`experimental`／未发布的薄平台 Adapter；两者均只依赖平台中立 CLI，不拥有项目作者文档。现有真实 runtime evidence 仍精确绑定 Adapter 0.1.0：Claude Code 只证明 Plugin／Skill 发现后在认证前失败关闭；DeepSeek Harness 只有 manifest 所列 rc.8／Windows／Core 0.1.0／CLI 0.1.1 wheel／模型与生命周期范围为 `verified`。

## 当前边界

- canonical 作者模板位于 Core 包；`skills/project-orrery/assets/project-template/` 是 v0.2 兼容投影，并由测试要求与 canonical 内容一致。
- Observatory 实现源码仍位于根 `scripts/docsite/`，组件包负责清点与版本化；Skill 模板通过显式标题 token 投影保持目标项目可定制。
- 旧 Skill 三个脚本路径现在是薄 wrapper；源码仓库调用新 CLI，单独分发 Skill 时回退到冻结的 v0.2 兼容实现。wrapper 保留至 `0.3.x`，最早在 `0.4.0` 移除。
- `adapters/codex/` 只包含 Codex 发现／调用元数据和 Adapter 生命周期安装器；它通过 manifest 引用 Core／CLI，不复制 canonical 作者模板、schema、兼容规则或项目状态。平台安装器只管理目标 skills 根下的 `project-orrery` Adapter 目录。
- `adapters/harness-json/` 不包含 `SKILL.md` 或平台发现文件；它拥有 versioned request／response schema、参数白名单、subprocess 边界和 timeout 分类，只调用 CLI 的 opt-in JSON，不读取作者文档来重新判定事实。
- `adapters/claude-code/` 使用原生 Plugin discovery；`adapters/deepseek-harness/` 使用 profile Cordis Plugin Bundle。两者有独立 manifest、打包器、生命周期和 runtime evidence，不共享对第三方平台兼容性的推断。
- `docs/_site/`、缓存、凭据和 benchmark 原始输出不是作者文档或发布资产。
- 自托管、实验和测试资产已进入 `main`；v0.2.0 tag／Release 指向发布提交 `20fc95b`，后续当前事实由 main 上的发布后文档继续维护。
- linked worktree 共享 Git 对象库和普通 refs，但拥有独立 HEAD、索引与工作目录。未提交文件仍只属于所在 Worktree scope。W5A Candidate 只有用户本机显式 enable 后才能启动 Coordinator；中央只接受标注为 Local-only 的版本化元数据，不接收源码正文或未 push diff，也不把 telemetry 升级为代码证据。未启用、未分享、过期或证据不足继续投影 Unknown／Unavailable。
- Phase 0 配置固定在 `.project-orrery.json` 的 `collaboration.integration_ref`、`collaboration.primary_worktree` 和 `collaboration.project_mode`；integration ref 缺省为 `refs/heads/main`，只按本地 branch ref 解析精确 commit OID，不 fetch 或回退远端。主 worktree 缺省取 `git worktree list --porcelain` 的 main worktree，维护者覆盖必须是同一仓库已列出的绝对 worktree 路径。
- worktree 路径比较先收敛现有路径的真实绝对形式，再应用平台大小写规则；这让 Windows runner 的 8.3／长路径别名指向同一已列出 worktree，同时不允许不存在或跨仓库的 override 绕过检查。
- Phase 1 通过 `git rev-parse --git-path orrery/worktree.json` 定位每个 linked worktree／clone 的 Git 私有 session；原子写入不改变作者工作树。session 绑定 worktree ID、branch、HEAD、integration ref／OID、merge base 和 dirty fingerprint；只读 status 在绑定事实漂移后报告稳定 stale reason，不自动重写。
- `worktree create` 固定本地 integration OID 后建立 branch + linked worktree 与 `created` session；branch／path 碰撞预先拒绝，session failure／integration drift 只回滚本操作创建的 clean 对象。`worktree guard` 允许隔离 worktree，并对 clean／dirty primary 失败关闭且不自动迁移。
- lifecycle phase、runtime condition、evidence freshness 与 closure reason 独立保存；Git／review evidence 漂移会撤销有效 Review Ready。W3 Candidate 的 review／closure 操作会在关键绑定漂移时失败关闭，并只更新 Git-private session；它不自动把 Candidate 合入 main。
- Adapter capability contract 分离 launch／attach／rebind／message。Codex、Claude、DeepSeek 当前只声明 caller-provided attach，Harness JSON 全关闭；Adapter Skill 要求先走 route/guard，但不能拦截绕过 Adapter 的任意宿主写入，也不证明 platform runtime launch／rebind 支持。
- 根 `AGENTS.md` 的七个 subsystem 入口已有显式稳定 ID；Core registry 只投影这些入口链接的既有 State Docs，缺失 State 时失败关闭，`unmapped` 与 `project-wide` 只是 Scope 保留表达，不自动创建作者文档。
- W2 的 legacy session 仍从 merge base→HEAD 生成 committed scope 并标为 lineage Legacy／Unknown；显式 stacked session 记录 versioned `base_workstream_id`＋精确 `task_base_oid`，创建时要求 task base 是当前 HEAD 的祖先，并在本机父 session 可见时绑定其精确 HEAD。stacked committed delta 改为 task base→HEAD，staged／unstaged／untracked／expected 仍属于当前任务。Overlap 只在显式 lineage、scope HEAD 和本地 Git ancestor proof 都当前时排除 inherited committed provenance；parent fork 后新提交、siblings、legacy／proof unavailable 继续正常产生 finding，且不会生成“已解决的继承冲突”。
- Direct／Authority／Semantic／Unknown finding 与 Open／Acknowledged／Resolved／Stale 生命周期存放于 Git-private session。fingerprint 绑定 Scope revision、HEAD、integration OID、路径、验证面和对端；跨成员 L2 保存 required members 与逐成员确认，整体 `n/m` 未完成时阻止 Review Ready。
- Personal Mode 的 W2 collector、overlap、scope refresh 与 acknowledgement 都只执行本地 Git／文件系统操作；没有新增 listener、discovery、Coordinator、heartbeat 或 Team transport。凭据、release、schema migration 的默认独占路径可由项目配置收紧／替换，Direct／L3 以及未本机确认的 L2 已接入 Adapter route 并失败关闭。
- W3 Candidate 的 `integrate --dry-run` 固定 target OID 与 candidate HEAD，在新建、干净、一次性 integration worktree 中执行 merge／rebase 推测和声明验证；无论成功、冲突或验证失败都不更新 target ref，并核对作者 worktree 的 HEAD／status 前后不变。只有该工具创建的临时 worktree 会在运行后移除。
- review package 与 decision 保存在 common Git private `orrery/reviews/`，closure record 保存在 `orrery/closures/`。package 绑定 target OID、candidate HEAD、Scope revision/fingerprint、finding set、collaboration schema version/byte hash、validation set 与内容 hash；原始证据／结构化事实先于可选 AI 派生摘要，摘要没有 Authority。Approve／Request Changes／Hold／Reject 明确记录人类 actor、capability、reason、evidence、timestamp 与失效条件，AI actor 永不计入人审。
- integration eligibility 只计算当前 package、验证、风险策略和人类 decision 是否满足。workspace inventory 只枚举 Git 已登记 worktree、Git-private session／closure、`.project-orrery.json` 可选允许根与用户显式候选，不扫描磁盘或同前缀目录；输出七类分类、Unknown、保护原因和预计空间。无 session／closure 的历史 worktree／clone 维持 Legacy unmanaged／Unknown，未显式 adopt/classify 前只报告。
- cleanup eligibility 对选中目录验证允许根内的真实绝对路径、symlink/reparse escape、Git identity/common-dir、非 active、clean、未知 untracked／ignored、独有 commit、canonical ancestry／closure reason、review／Validation／closure 与新鲜 target OID。benchmark/raw evidence、recovery/immutable 与 credential/cache 通过显式策略或 Unknown fail-closed 保留；不按名称或时间自动删除。remove worktree、delete local branch、delete remote branch 与 remove ordinary directory 是四个独立授权，全部 `performed: false`；显式 Git-private action receipt 只记录调用者自述的外部动作。现有本机目录没有被本 Candidate 自动审计为可删。
- W4 Worktree Candidate 的 root-only `build_personal_observatory.py` 与 Observatory 内部 Personal projection 逐 worktree 调用 W1/W2 status／Scope／finding／lifecycle Core 合约，并正式消费 Canonical W3 的 review package freshness、risk、人类 approval、integration eligibility、bounded workspace inventory、cleanup eligibility、closure 与 action receipt bundle。W4 不复制这些判定：review／integration 只调用 W3 Core，inventory 七类、protection、Unknown 与预计空间来自 W3 bundle，只有 Core 标为 `evaluate-cleanup-eligibility` 的条目才继续调用 cleanup gate；四个 action 始终分别投影且自动采集保持 `authorized=false`、`performed=false`、`implies_actions=[]`。receipt 只显示 caller-attested evidence，不能证明删除已发生。
- W3 provider 缺失、失败或 schema 不兼容时，W4 整体页面仍保留 W1/W2 的 W4A 投影，W3 区域单独退回 Unavailable／Unknown；它不从目录名、前缀、年龄或页面状态自行推断 review、integration 或 cleanup 结论。
- 该 W4 Candidate 只生成显式 opt-in 的本地 HTML／可选 JSON 快照；默认 `build_docsite.py`、现有 loopback service、Authority projection、AI Q&A、发布模板与 v0.2.0 行为均未切换。投影声明 `read_only=true`、`writes_performed=false`、`network_performed=false`、`team_runtime_enabled=false`，没有 LAN／Coordinator／Member 同步或页面执行动作。
- W4 health Candidate 在不改变 W1–W3 Core finding／inventory／cleanup 事实的前提下生成 `derived-read-only` 健康路由。只有双方均为 current session/evidence 且 lifecycle 为 active／review-pending 的 Direct finding 进入 Delivery now blocker；stale session／finding、过期 review 和当前未登记 Candidate 进入 Reconciliation；legacy-unmanaged、no-session、retained、Unknown 与 estimated reclaim 进入 Workspace hygiene。Primary worktree 永远投影为 protected canonical root，不算普通 Agent Workstream；Unknown 按三层记账而不丢弃。
- W5B Candidate 的 `scripts/docsite/serve_team_observatory.py` 是独立 root-only 动态入口：UI 只绑定 `127.0.0.1`，默认页面在 Team disabled 时显示 Personal zero-network onboarding；enable 只写 Git-private 配置，start 才创建 UI 进程拥有的 loopback Coordinator，关闭 UI 会通过 Core-owned server object 停止该 runtime。Host／Origin、每次启动随机 HttpOnly control cookie、16 KiB body gate、固定 POST 动作与错误脱敏由本机 UI server 执行；页面／JSON 不包含 member credential、API key 或 runtime control token。
- Team sibling page 只消费 Core `team-read-only-projection` 和 Git-private Team config，显示 mode／Host／Member／sharing／heartbeat／last-seen、Member → Workstream、presence、request inbox 与本机 receipt。页面不复制 revision／TTL／permission／review 规则，不提供任意命令／路径／URL／shell 参数；中央 request 与 accept／reject 始终 `execution_performed=false`，不会把 Agent 自报或最后快照升级为 Review Ready／Integrated／实时在线。
- W5C 只改写上述页面的层次和语言：当前人话结论与建议操作置顶，成员／任务与 pending request 居中，已处理 request 折叠，Host／Coordinator／heartbeat／revision／测试入口下沉诊断。检测到其他本机 runtime registration 时禁用重复 start 并解释恢复路径；没有获得该 runtime 的 server object、PID 控制或越权停机能力。
- W5E 在 W5C 之上删除重复的共享边界 pill 与“现在的情况”摘要，把连接／成员／待处理／待同步四项状态上移；Team Mode、团队连接、在线状态与退出始终位于非折叠控制层。Host、内部 ID、last-seen、revision、测试／维护请求与隐私说明只通过齿轮弹窗按需展开；页面仍复用原固定 POST 和 Core projection，不增加权限或执行面。
- W7A 的 native relation event 位于 `$GIT_COMMON_DIR/orrery/workstream-relations/<relation-id>/`，以连续 revision 的独立 JSON 文件 append-only 保存；只读加载在目录不存在时零写入，worktree 删除后记录仍存续。关系 lifecycle 不删除 session、worktree、branch、commit、Validation 或作者文档；W6 maintenance 继续独占删除授权。
- W7A active-tip 只接受 Session/evidence/Scope current、runtime `active`、未结束 lifecycle 的节点；`review-ready` 映射为 `review-pending`，waiting/paused/blocked/failed/offline/stale-unknown 全部排除。active succession 还要求 predecessor 有显式 `paused` takeover marker；completed succession 要求 predecessor exact `closed/superseded`，否则 graph 失败关闭并保持 compare。Git `task_base_oid` 与 ownership `ownership_transfer_oid` 分字段验证；parent post-fork 独有提交、sibling、`depends_on`、stale／Unknown、pair L2/L3／exclusive constraint 继续进入 compare pairs。
- W7B 的执行控制面位于 `$GIT_COMMON_DIR/orrery/workstream-relation-transactions/{confirmations,journals,receipts}/`。plan 绑定本机 project hash、W7A graph/discovery、候选 record、source/target 完整 Session 字节 hash、HEAD、Scope hash、actor 与 expiry；apply/undo 必须同时匹配 exact plan ID/hash、一次性 token 与 `human-local` actor。全部输入在 journal 可写前预检；journal 非 terminal 时普通 graph/plan 读取失败关闭，恢复只会还原 exact Session 或追加 cancelled/stale 补偿 event，不删除历史。
- W7B active takeover 在同一 journal 中写 predecessor `paused` Session 与 active event；completed takeover 要么断言 predecessor 已 exact `closed/superseded`，要么同事务写入该状态。receipt 嵌入 W7A evidence，并保存实际 event hash、原/新 Session hash、HEAD、lifecycle/runtime/evidence/Scope/closure、actor、confirmation 与 resulting graph hash。graph/Session/HEAD/Scope 漂移、伪造/重放/过期/跨项目 confirmation、重复 history 或 pending recovery 都非零失败关闭。
- W7C-A 图只消费 versioned synthetic fixture；fixture 的 `confirmed` 只表示合成场景内部有显式 evidence marker，不证明真实项目 relation。所有图、edge label、cluster 和 inspector 都是派生呈现，不能创造 succession／dependency／conflict；生产 consumer contract 与 provider fail-closed 行为仍由 W7A／后续 W7C-B 冻结和接线。
- W7C-B 页面保留独立 lifecycle/runtime/evidence/Scope/subsystem/visibility/observability 轴，以 Core active-tip 列表为唯一 active 来源；waiting/paused/blocked/failed 不得获得 active-tip 样式。桌面为 inline SVG＋inspector＋可访问 ledger，390px 为单列 ledger；页面只读、zero-network，source link 只投影 Core 白名单内的仓库文档锚点，Git-private／opaque evidence 只显示不可导航标签。
- W6 Phase 0–2 复用 W3 bounded inventory／cleanup eligibility，新增严格 versioned maintenance policy、scan／queue／authorization／receipt、Git-private `orrery/maintenance/`、integration／closed event scan、24h Observatory catch-up、single-flight／debounce／hard timeout／interrupted 记录与 evidence-bound 建议队列。唯一执行面是本机人类确认后、只接受 authorization ID 的固定 `git worktree remove -- <registered-path>`；执行前重新验证 exact workspace/path/HEAD/branch/integration/closure/review/Validation/dirty/ignored evidence，执行后验证目录、registry、branch、commit 与 receipt。branch 与 remote branch 不删除，Team 中央只发送 `cleanup` request；默认 Personal 保持 zero-network、无后台进程、无 OS scheduler、无自动删除。

## 实现证据

- `.project-orrery.json`
- `skills/project-orrery/release-manifest.json`
- `scripts/package_release.py`
- `.github/workflows/validate.yml`, `.github/workflows/release.yml`
- `packages/component-versions.json`
- `packages/project-orrery-core/`
- `packages/project-orrery-cli/`
- `packages/project-orrery-observatory/`
- `adapters/codex/`
- `scripts/package_codex_adapter.py`
- `tests/test_codex_adapter.py`
- `adapters/harness-json/`
- `tests/test_harness_json_adapter.py`
- `adapters/claude-code/`
- `adapters/deepseek-harness/`
- `tests/test_claude_code_adapter.py`
- `tests/test_deepseek_harness_adapter.py`
- `packages/project-orrery-core/src/project_orrery_core/collaboration.py`
- `packages/project-orrery-core/src/project_orrery_core/review.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/collaboration-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/collaboration_contract.py`
- `packages/project-orrery-cli/src/project_orrery_cli/integration.py`
- `packages/project-orrery-cli/src/project_orrery_cli/review.py`
- `packages/project-orrery-cli/src/project_orrery_cli/worktree.py`
- `tests/fixtures/collaboration/git_fixture.py`
- `tests/test_collaboration_contract.py`
- `tests/test_collaboration_w3.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/personal_observatory.py`（W4 Worktree Candidate）
- `scripts/docsite/build_personal_observatory.py`（root-only W4 opt-in entry）
- `tests/test_personal_observatory.py`
- `packages/project-orrery-core/src/project_orrery_core/team.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/team-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/team.py`
- `tests/test_collaboration_team.py`
- `packages/project-orrery-observatory/src/project_orrery_observatory/team_observatory.py`
- `scripts/docsite/serve_team_observatory.py`
- `tests/test_team_observatory.py`
- `packages/project-orrery-core/src/project_orrery_core/maintenance.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/maintenance-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/maintenance.py`
- `tests/test_workspace_maintenance.py`
- `tests/test_collaboration_lineage.py`
- `tests/test_lan_collaboration_harness.py`
- `packages/project-orrery-core/src/project_orrery_core/workstream_relations.py`
- `packages/project-orrery-core/src/project_orrery_core/workstream_relation_execution.py`
- `packages/project-orrery-core/src/project_orrery_core/schema/workstream-relations-v1.json`
- `packages/project-orrery-core/src/project_orrery_core/schema/workstream-relation-execution-v1.json`
- `packages/project-orrery-cli/src/project_orrery_cli/workstream_relations.py`
- `tests/fixtures/workstream-relations/v1/succession-chain.json`
- `tests/test_workstream_relations.py`
- `tests/test_workstream_relation_execution.py`
- `scripts/ci/`
- `tests/test_ci_validation.py`
- `scripts/acceptance/run_lan_collaboration_acceptance.py`
- `docs/operations/lan-team-preflight.md`
- `experiments/workstream-graph-visual-prototype/index.html`
- `experiments/workstream-graph-visual-prototype/prototype.js`
- `experiments/workstream-graph-visual-prototype/fixtures/workstream-graph.provisional.v1.json`
- `tests/test_workstream_graph_visual_prototype.py`

## 已知缺口

- 已定义 R0 受限原始层、R1 脱敏可移植层和 R2 权威结论层；尚未实现自动 R1 导出器。
- H2／Harness／retention 研究资产已随 `bb2c768` 与 `96bfd21` 进入本地 `main`；远端 `origin/main` 尚未包含本轮提交。
- Pilot 005–009 的版本化控制包位于 `experiments/context-routing/pilots/`；已启动的控制包不可改写，
  修正使用新 Pilot。R0 原始运行只位于仓库外 `project-orrery-benchmark`，仓库内只保存 R2 结论与
  可复现控制面。
- 三个 Core／CLI／Observatory 组件目前只是未发布源码包，尚未形成独立 wheel 或多组件发布流水线。Codex Adapter 已能独立归档并完成一个精确 runtime 范围的 E2E，但尚未进入 release workflow；其他 runtime／OS 范围仍未验证。Harness JSON 已在同一候选提交通过 Windows／Ubuntu CI，但仍是 `experimental`／`unreleased` 参考 Adapter，尚未作为独立产物发布，也不构成第三方 Agent runtime 兼容证据。
- W3 source 已实现 review／integration／cleanup；当前 W5D Worktree Candidate 还包含健康分层的 Personal Observatory、opt-in Team Core／CLI／root-only UI、LAN candidate discovery、Host-confirmed join、手工 Coordinator Host switch、W6 maintenance 和 stacked lineage。Phase 3 自动 worktree removal 与 Phase 4 OS scheduler Adapter 未实现；仍没有真实双机／真实 LAN、自动 Coordinator 选主、云 relay、多设备迁移或远程 shell／Agent／merge／delete。真实 W5C／W6 legacy session 未由 W5D 自动改写，整合者仍需显式 rebind／retire；动态 UI 未进入默认 docsite、公开模板或 Release。
- W7B 已在 Worktree Candidate 实现真实本机 discovery／plan／confirmation／apply／undo／recovery，但没有对 self-host 真实 Session 或 relation store 执行 apply，也没有 retention/compaction、默认 Observatory 执行入口或真实跨平台 Promotion。任何真实项目 apply 仍需维护者在成员本机对 exact plan 单次确认，并由中央整合流程另行授权。
- W7C-A 仍不是生产 relation provider 或 Observatory 功能；其 provisional fixture 只作为 W7C-B browser acceptance 输入。W7C-B 已从 W7A 冻结的 node／edge identity、relation direction/kind、certainty/provenance、multi-predecessor、evidence link、status axes、active tip、visibility、ordering/version 与 fail-closed contract 生成真实 Core projection和安全链接；Personal／Team 默认入口、managed/public release 接线仍未启用。
- Claude Code／DeepSeek Harness Adapter 尚未公开发布；DeepSeek 的精确 manifest 范围不得外推到当前源码 Adapter 0.1.1／CLI 0.1.13、其他版本、OS、Provider、模型或未来发行物。
