# 测试覆盖 State

Updated: 2026-08-28

## 当前事实

- `tests/test_project_orrery.py` 保护安装、非覆盖升级、发布包、更新兼容和凭据配置边界。
- `tests/test_context_routing_benchmark.py` 保护历史语料、Pilot 装置、回执规则、未跟踪文件采集、安全 Oracle 和恢复行为。
- CI1 Worktree Candidate 将 self-host CI 分为 `.github/workflows/fast-validation.yml` 与 `.github/workflows/validate.yml`。Fast 对每次 push／PR 运行 40 项结构、schema／contract、纯单元与最小高风险路径，明确标为 `non-promotion-feedback`，不启用动态 build，也不使用 required-check 名称。
- Promotion 只由显式 workflow dispatch 的 candidate ref＋SHA，或冻结 `promotion/**` branch push 启动。preflight 将 ref 绑定 exact SHA，Windows／Ubuntu 随后对 342 个最终 discovery ID 运行同一 26-shard inventory，并设置 `ORRERY_TEST_BUILD=1`；结构、隔离站、链接／forbidden artifact、发布打包与 diff 是独立 gate。
- self-host main promotion gate 的最终显示名仍精确为 `smoke-test (windows-latest)` 与 `smoke-test (ubuntu-latest)`。聚合器对取消／跳过／失败 matrix 或 gate、缺失／多余 artifact、manifest／inventory／SHA／OS 漂移、漏跑／重复 test ID 与非通过结果失败关闭；合法 unittest skip／expected failure 仍保留原语义并计为已执行。
- 分级原则仍为 `Fast → Checkpoint → Candidate → Promotion`。CI1 Candidate 实现 dependency-free inventory、timing runner/result 与静态／聚合 validator，但没有自动影响分析、跨 SHA 缓存或可复用 Promotion 证据；只有 containing ref 为 main 且远端 exact-SHA checks 通过后才是 Canonical promotion path。
- 自托管补全新增 installer 排除模板 Python 缓存的回归断言。
- 2026-08-18 基线结果：默认套件 28 项中 27 项通过、动态 reader 测试按设计跳过；设置 `ORRERY_TEST_BUILD=1` 后完整 28/28 通过。24 项 benchmark 语料与工作树中的 6 份 run record 也通过验证。
- 发布分支 CI `32057247222` 与 main CI `32057443759` 均在 Windows／Ubuntu 通过；最初失败轮 `32057075492` 暴露浅克隆缺少历史 commit，workflow 已改为 `fetch-depth: 0`。
- `tests/test_context_routing_h2.py` 当前 12 项专项测试，保护读取预算、路径边界、哈希／换行规范、Windows CRLF stdout 恢复且拒绝正文篡改、Hook 语义、CLI JSONL 独立审计、命令／写路径归一化、未知工具拒绝、原始证据篡改检测及 Pilot 005／006／007 冻结控制包 dry-run；2026-08-18 本地为 12/12 通过。
- Pilot 005／006 与 CRLF 修复集成后的全仓结果：默认 39 项中 38 通过、1 项按设计跳过；设置 `ORRERY_TEST_BUILD=1` 后 39/39 通过。24 项 corpus、6 份既有 run record、integrated static build、文档站生成、本地 Markdown 链接和 `git diff --check` 均通过。
- 十份仓库外 Hook smoke manifest 已全部重新 verify；真实 Windows CLI 0.147.0 未产出 Hook 日志，因此正式 B/H2 前只允许使用经 validator 证明的 JSONL 事后模式。
- Pilot 007 六份 R0 manifest 为 6/6 有效；正式候选测试暴露外层 `benchmark` 分支与嵌套 Pilot 006 dry-run 冲突，因此 frozen formal validation 不能作为产品回归失败证据，详见 R2 与运行 Validation。
- Pilot 007 R2 与项目文档同步后的仓库回归：专项 12/12、默认套件 39 passed + 1 expected skip、24 项 corpus、6 份 run record、文档站生成和 `git diff --check` 全部通过。
- 2026-08-19 动态 reader 回归断言 AI 设置入口只出现一次且位于主题按钮之前；测试进程使用空 keyring backend，避免读取或调用维护者的真实系统凭据。启用 `ORRERY_TEST_BUILD=1` 后全仓 40/40 通过，集成结构验证、静态站生成和 `git diff --check` 通过。
- 顶栏入口已在 1280px 与 390px 视口实测：桌面按钮顺序和尺寸正确；移动端齿轮与主题按钮同时可见、无横向滚动，设置弹窗可完整滚动使用。
- ADR-0003 回归覆盖 Provider／端点错配、指纹漂移、空测试 keyring、非环回网络禁用、状态／错误不回显 Key、64 KiB 请求体限制、同源写操作、刷新 POST、Broker 不跟随重定向、模型白名单、并发 single-flight、缓存和每日请求／token 预算。
- 最终安全版本启用动态依赖后，Project Orrery 专项 9/9 通过；全仓动态回归包含并行新增的 Pilot 008 装置测试，最终结果与精确命令见 2026-08-19 docsite credential hardening Validation。
- Pilot 008 新增 dry-run 回归后，上下文读取／封存／Pilot 专项为 13/13；Oracle 自测覆盖三项 baseline negative、三项 positive control 和真实外层／内层 Git preflight。
- 2026-08-19 Pilot 008 准备快照：上下文专项 13/13；文件稳定后的默认全仓 44 项中 42 通过、2 项动态依赖按设计跳过。较早的动态检查点为 41/42，唯一失败来自当时并行未完成的 docsite Broker HTTP 400 断言；新增并行测试后未重跑动态模式。benchmark、integrated static build、169 份 Markdown 本地链接与 diff 检查通过。
- 平台中立 Phase 0 新增 v0.2.0 发布清单 fixture 和两项回归，保护既有归档路径、managed tools、manifest 必需字段、人类 CLI 输出、模板入口与公开支持状态；`tests.test_project_orrery` 为 9 passed + 2 个动态依赖按设计跳过，未运行 context-routing 或任何 Pilot。
- 平台中立 Phase 1 新增三项回归：组件版本／模板投影一致性、新 CLI 与旧路径逐文件等价及作者文件保留、解压 Skill 的独立 fallback。产品专项为 12 passed + 2 个动态依赖按设计跳过；未运行 context-routing 或任何 Pilot。
- 平台中立 Phase 2 的 `tests/test_codex_adapter.py` 现有六项回归：薄 Adapter 内容与精确 runtime evidence 投影、确定性独立归档／checksum／解压安装、dry-run／升级备份／可恢复卸载、未知目录拒绝／旧 Skill 备份迁移和版本错配失败，以及 CLI distribution／entrypoint 缺失与版本范围的失败关闭。
- 2026-08-21 真实 `codex-cli 0.148.0-alpha.21` E2E 在 Windows 11 build 26200 上验证：唯一 repo Adapter 发现、显式／隐式模型调用、CLI 0.1.0 路由、distribution 缺失和 0.2.0 不兼容失败关闭、完整 v0.2 Skill 只经显式升级迁移、升级前完整备份、可恢复卸载、backup／trash 不重复发现、作者 tree 不变及卸载后 Adapter 消失。真实登录态中的旧用户 Skill 通过 per-run `skills.config` 禁用，没有复制凭据或写入用户 Skill 目录。
- Phase 3 新增 `tests/test_harness_json_adapter.py` 六项回归，保护 manifest／schema／组件版本投影、确定性 scaffold dry-run、临时安装与 validate、作者入口保留、mixed toolchain 和升级备份预演、schema 不兼容、离线无缓存更新、非法参数拒绝，以及不加载 `SKILL.md`／Codex 配置／Agent runtime 的隔离声明。
- Phase 4 新增 `tests/test_claude_code_adapter.py` 与 `tests/test_deepseek_harness_adapter.py`，保护 manifest／组件版本投影、薄 Adapter 内容、确定性 ZIP／npm-compatible TGZ、checksum、隔离生命周期与 CLI 缺失／不兼容失败关闭；真实 runtime 证据与单元测试证据分开记录。
- 2026-08-22 DeepSeek Stage B 使用真实 `deepseek-official`／`deepseek-v4-flash` 完成 6 个模型 turn：显式 editable route、隐式 `skill` route、CLI distribution 缺失、不兼容以及普通 wheel source-assets 失败；生命周期 probe 为 0→1→0，作者 fixture 424/424 字节一致。
- W1／第二平台干净整合首次全仓 247 项中仅 ADR-0013 amendment 冻结期望未同步而失败；补入 `ADR-0013 amends ADR-0004` 后联合专项 31/31、最终全仓 242 PASS + 5 expected skips。integrated structure、隔离静态站、295 份 Markdown／765 个本地链接和 diff 检查通过。
- CLI wheel 专项在临时 monorepo 构建 Core／Observatory／CLI wheel，断言九个 managed assets 被嵌入，并在无源码仓库的新 venv 中完成 scaffold／validate；普通 wheel 还通过真实 DeepSeek Harness 显式 Adapter turn。功能分支结果为专项 1/1、定向组合 18 passed + 2 expected skips、默认全仓 73 passed + 2 expected skips。
- DeepSeek wheel 修复进入当前整合基线后，首次默认全仓在收集阶段捕获两组 Authority CLI source-layout 测试未注入已声明的 Observatory 依赖；补齐测试 source path 后，相关 10/10、DeepSeek／wheel 4/4、默认全仓 243 PASS + 5 expected skips，动态全仓 245 PASS + 3 Windows symlink privilege skips。integrated structure、1,361,966-byte 隔离静态站、297 份 Markdown／779 个本地链接、secret scan 与 diff 检查通过。
- 首次远端 matrix `32500503338` 为 Ubuntu PASS／Windows FAIL：Windows 同时暴露临时目录 8.3／长路径 worktree alias 和缺少 `wheel` 测试依赖。修复保留已列出 worktree 硬门、使用 `realpath` 规范化别名，并在 workflow 显式安装 `wheel>=0.41,<1`；本地受影响专项 11/11、动态全仓 245 PASS + 3 privilege skips，后续 GitHub Actions `32554191374` Windows／Ubuntu 双 PASS。
- W1.1 为 `tests/test_collaboration_contract.py` 增加 linked worktree／独立 clone 私有 session、稳定 status JSON、author tree 不变、zero-network 和 branch／HEAD／integration OID／dirty fingerprint stale reason 回归；专项 13/13，通过默认全仓 246 PASS + 5 existing skips 和动态全仓 248 PASS + 3 Windows symlink privilege skips。该证据是 Windows Candidate 本地验证，不构成 W1.1 跨平台 CI 或发布支持声明。
- W1.2 将同一专项扩展到 18/18：覆盖 dirty primary 创建 clean linked worktree、精确 integration OID、Git-private created session、clean／dirty primary guard、隔离 worktree allow、branch／path 碰撞、session failure 与 integration drift 回滚、CLI JSON／exit code 和 zero-network Core 路径。默认全仓为 251 PASS + 5 existing skips，动态全仓为 253 PASS + 3 Windows symlink privilege skips；这是 stacked Windows Candidate 本地证据，不构成 W1.2 跨平台 CI 或发布支持声明。
- W1.3 将同一专项扩展到 22/22：覆盖 lifecycle 合法／非法转换、phase／runtime／evidence／closure 独立性、Review Ready stale 撤销、未来 review／integration gate 失败关闭、四 Adapter capability contract、只读 route、Git-private attach、caller-provided Agent-first attach、no-rebind 新 Workstream 回退、dirty／clean primary 阻断和稳定 CLI JSON／exit code。默认全仓为 255 PASS + 5 existing skips，动态全仓为 257 PASS + 3 Windows symlink privilege skips；这是 stacked Windows Candidate 本地证据，不构成 W1.3 跨平台 CI、当前 Adapter runtime 验证或发布支持声明。
- W1／D1／C1 干净整合先暴露 C1 CRLF hash mismatch；专属 `eol=lf` 修复后，联合专项 35/35、默认全仓 268 PASS + 5 skips、动态全仓 270 PASS + 3 privilege skips及其余本地门通过。首次远端 `32564000587` 为 Ubuntu PASS／Windows FAIL：W1 session-path 测试误把 `RUNNER~1` 与等价长路径判为不同；改用 realpath/normcase 后单项 1/1、collaboration 22/22，最终 `32564334514` Windows／Ubuntu 双 PASS。
- W2 将 collaboration 专项扩展到 27/27：覆盖五类路径来源、四类 finding、registry mapping、独占门、L1/L2/L3、route gate、lifecycle、ack 失效和跨成员 `1/2 → 2/2`。集成树默认全仓 278 项中 273 PASS + 5 existing skips；integrated structure、隔离静态站、335 份 Markdown／855 个链接／0 unexpected missing、secret／forbidden 与 diff 门通过。exact SHA `21a2e1c` 在 GitHub Actions `32570545138` 取得 Windows／Ubuntu 双 PASS 后由受保护 main 接受。
- W3 的 `tests/test_collaboration_w3.py` 已扩展到 13 项：除 review/integration 原有安全面外，还覆盖 bounded inventory、Legacy unmanaged／Unknown 显式采纳、active task、benchmark/evidence retained、recovery retained、path escape/reparse、独有 commit、未知 untracked／ignored、敏感 ignored 不可 allowlist、四动作分离授权、Git-private external-action receipt、stable JSON 和 zero-delete／zero-network。W3 focused 13/13；W1/W2 collaboration + W3 + 邻接 schema migration/restore + Codex adapter checkpoint 为 83/83。本地 integration candidate `c758827` 的动态全仓为 291 项中 288 PASS + 3 个既有 Windows symlink privilege skips；结构、隔离站点、337 份 Markdown／862 个本地链接／0 unexpected missing、安全与 diff 门通过。最终 Canonical 状态仍由包含集成记录的 exact SHA 双平台 required checks 决定。
- W3 首次远端 matrix `32583193534` 为 Ubuntu PASS／Windows FAIL：Windows runner 同时暴露 closure 原路径和 active inventory 查找的 8.3／长路径字面比较缺陷。Core workspace identity 未变；测试改为 `abspath/realpath/normcase` 等价比较后两个原失败用例 2/2 PASS，仍需新 exact SHA 双平台矩阵。
- W4／W5A 联合 non-main Candidate 的 W4+W5 focused 为 26/26，动态全仓为 316 项中 313 PASS + 3 个既有 Windows symlink privilege skips；结构、legacy/W4 站点、340 Markdown／874 links／0 unexpected missing、schema、安全与 diff 门通过。Candidate `2bc6207` 的 GitHub run `32603440758`：Ubuntu 1m16s PASS；Windows attempt 1 仅既有图形化 AI 设置本机 HTTP 请求 timeout，attempt 2 在同一 SHA 8m44s PASS。该证据不证明真实多机 LAN 或 Team UI，维护者确认仍待完成。
- 状态同步 SHA `43678f6` 的 run `33095474987` 再次只在 Windows 的相同本机 HTTP 测试超时，证明 `127.0.0.1:9` 关闭端口不是稳定失败装置。测试改用进程内 loopback 503 假上游，保留错误脱敏／500 失败关闭断言；定向动态 1/1 PASS（4.767s），产品代码未改，最终 SHA 仍须双平台 checks。
- W5A Candidate 新增 `tests/test_collaboration_team.py` 13 项：覆盖 Personal 零监听、显式 enable／disable、loopback runtime 与 LAN 双重开关、项目身份／邀请／Host 本机确认、非成员拒绝、递归 forbidden-field／64 KiB 门、event coalescing／sync-now、revision rollback、手工 active Host 切换、heartbeat off/on、TTL Unknown／Stale／Unavailable、request-only 本机 receipt／zero execution、capability revoke、DNS／公网失败关闭和稳定 CLI JSON。网络测试只绑定 loopback，不调用外部服务；自动发现明确保持 `unsupported-next-phase`。
- 2026-08-27 W4 health 增加 36-worktree-like 合成 fixture：4 registered-active、1 review-pending、31 legacy-unmanaged，并组合 stale source sessions、37 个历史 Direct、1 个 current Direct、32 个 absent-session Unknown、Primary root、未登记 Candidate 与 retained evidence。断言 current blocker 仅为 1，历史 Direct 进入 reconciliation，Unknown／legacy/no-session／estimated reclaim 进入 hygiene 且不丢弃。
- W5B 新增 `tests/test_team_observatory.py` 3 项，覆盖 Team sibling/onboarding、root-only、默认不暴露 LAN 输入、loopback-only UI、Host／Origin／随机 HttpOnly cookie、16 KiB body／未知字段拒绝、错误脱敏、enable/start/stop/disable、heartbeat/sharing、capture/sync、Member → Workstream、request accept/reject receipt、UI-owned runtime close 和 member/runtime secret 不回显。W4/W5B + W5A + Personal + 邻接 W1/W3/component checkpoint 最终 33/33 PASS，206.129s；未运行默认／动态全仓。
- 真实 in-app Chromium 在 1280px 与 390×844 验证 Personal↔Team、disabled onboarding、全部上述按钮、状态变化和 request 两条决定路径；桌面 `scrollWidth=1265 < 1280`，移动 `scrollWidth=375 < 390`。真实本机健康快照只作为本机验证：37 worktrees、0 current Direct blocker、60 reconciliation（4 stale session + 55 historical overlap + 1 unregistered Candidate）、32 hygiene debt、33 Unknown 全部进入 hygiene；这些数字没有提交为项目 fixture 或 canonical 事实。
- W4 health／W5B 中央 integration candidate 的结构、1,576 KB／121 docs 隔离站、343 份 Markdown／886 个本地链接和 forbidden-artifact 门通过。首轮动态全仓 320 项中 314 PASS + 3 个既有 Windows symlink privilege skips，另 3 项只因测试仍冻结 Core 0.1.8 而候选输出 0.1.9；更新三条版本期望后原失败用例定向 3/3 PASS。该局部修复尚不能替代最终 exact-SHA Windows／Ubuntu 全矩阵，Promotion 证据仍待完成。
- W5C Worktree Candidate 的最终 W5A／W5C／component adjacent checkpoint 为 17/17 PASS，111.523s；它保留 W5B server/security 全路径并增加人话摘要、中文操作、pending/history request 分层、诊断折叠和外部／stale runtime registration 说明。真实 Chromium 在 1280px 与 390×844 均无横向溢出；integrated structure、1,594 KB／123 docs 隔离站、345 Markdown／892 local links 和 diff 门通过。完整全仓与 exact-SHA 双平台门留给后续中央 integration candidate。
- W6 Worktree Candidate 新增 `tests/test_workspace_maintenance.py` 与 11-scenario synthetic corpus，覆盖 strict contract／policy／host preference、zero-network bounded scan、24h catch-up、single-flight／debounce／hard timeout／interrupted、integration／closed event、evidence drift、worktree lock/process-use、执行中断、action surface 拒绝与真实临时 linked-worktree removal 后 branch／commit／registry／path／receipt 验证。W6 focused 7/7 PASS（463.055s），W3 + Personal 27/27 PASS（798.195s），Team + component 4/4 PASS（45.301s），version／W1-W2 compatibility 64/64 PASS（306.162s）；1280×720 与 390×844 root-only 页面真实点击、只读扫描、折叠交互、单列布局和零横向溢出通过。结构、站点、链接与 diff 结果见对应 Validation；全仓动态与 exact-SHA 双平台门留给中央 Candidate。
- W5D Worktree Candidate 新增 `tests/test_lan_collaboration_harness.py`、`tests/test_collaboration_lineage.py` 和一键 acceptance runner。双 clone Harness 的 7 阶段覆盖隔离身份／credential/runtime、最小 discovery 泄漏门、spoof／replay／cross-project／expiry、Host-local join、disconnect／TTL／reconnect、monotonic revision、manual Host switch、request-only 与 revoke；脱敏 manifest 明确 `external_network=false`、`real_credentials=false`、`real_lan_validated=false`。lineage synthetic 的 legacy fixture 为 Direct 4／Authority 3，显式 W5C→W6→W5D 后为 0／0；child delta、parent post-fork、sibling L3、非法／非祖先 base、drift Unknown、ack 与 Review Ready 门均有回归。
- CI1 dependency-free 回归为 8/8 PASS；完整 inventory 342 unique IDs／26 shards／0 missing／0 duplicate／0 dead selector。最终 Fast 本机 Windows 40/40，runner 3.897s／端到端 4.639s；最终最慢选择性检查 `workspace-remove` 1/1，runner 148.990s／端到端 149.805s。hosted Windows ≤90s／完整 Promotion ≤4m 仍是待中央验证的目标，不是本机已达成事实。
- W5E Team／component adjacent checkpoint 18/18 PASS（217.750s），覆盖 root-only server、Host／Origin／cookie／body／secret、Personal zero-network、Team enable/start/stop/disable、sharing／heartbeat、request receipt、revision／TTL 和 Observatory 0.1.8 投影。CI contract、342-ID／26-shard inventory、repository gate（335 Markdown／919 links）、integrated structure、1,781,677-byte 隔离站、compile 与 diff 均通过。真实 in-app Chromium 在 1280px 与 390×844 验证状态上移、常驻连接／在线／退出控制、齿轮弹窗、连接和 heartbeat 状态切换、无旧摘要／pill 以及零横向溢出；测试后恢复 Personal Mode。
- W7A correction 将 `tests/test_workstream_relations.py` 扩为 15 项，并新增标记 `synthetic-non-authoritative` 的 W7C consumer compatibility fixture。除原三种关系、五态 lifecycle、single Git parent、多 predecessor、cycle/self/duplicate、exact Git、post-fork/sibling、Unknown/L3、append-only/no-network、deterministic CLI 与 legacy projection 外，新增六种非 active runtime 排除、active/review-pending 正对照、独立 node 轴、completed predecessor closure、atomic Session transition/apply receipt/exact undo no-drift 和 W7C-B 字段完整性。Focused 15/15 PASS；CI1 inventory 更新为 357 unique IDs／26 shards／48 Fast，0 missing／duplicate／dead selector。
- 初始 W7A 邻接记录仍保留：W1/W2 版本断言同步、W3/Authority、CI1/component、W5D lineage 与 LAN contract 均通过；double-clone runner 曾在并发负载下两次 loopback timeout 后独占 PASS。本 correction 将 Core/CLI 期望同步到 0.1.13/0.1.17；最终定向邻接与 loopback 结果见同一 W7A Validation，不把既有波动写成 relation 修复。
- Windows focused/checkpoint 已通过：W1/W2 27 项中 26 PASS＋1 个新增 schema 期望失败，期望同步后定向 PASS；lineage＋Personal 17/17、LAN／Team／UI／W3 gate 22/22 PASS。真实 in-app Chromium 在 1280px 与 390×844 显示 explicit chain、task-base OID、inherited path 与 chain 内 unique finding；两端均无横向溢出。当前主机没有可用 WSL distro，Docker Linux engine 未运行，因此本分支没有本地 Ubuntu 动态 PASS；`.github/workflows/validate.yml` 的 `unittest discover` 会在 Windows／Ubuntu exact SHA 上发现新增测试，Promotion 证据仍待中央执行。
- 本机 cleanup 验证对 36 个移除目标逐项检查 registered path、允许根、tracked/untracked、ignored allowlist 与进程引用；第一批 31 个目标只含 1,377 个 `__pycache__` 和 5 个 `docs/_site`，约 117.1 MB。三个 stale session 在删除前复制到 Git-private archive 并逐项通过 SHA-256 一致性；最后两个 recovery/final candidate worktree 由保留 branch 精确重建。最终 2 worktrees、0 reconciliation、0 hygiene；branch／commit 未删除。
- Phase 3 Windows 候选专项与产品回归为 20 passed + 2 expected skips；默认全仓为 68 项中 66 通过、2 项动态依赖按设计跳过，设置 `ORRERY_TEST_BUILD=1` 后完整 68/68 通过。CI run 28 的 Windows 通过、Ubuntu 因测试夹具错误失败；`c30acab` 改用平台原生命令名后，同一专项在 Windows 与 Ubuntu WSL 通过。run 29 保留 Ubuntu 成功与无关 Windows 本机 HTTP 超时的历史；run 30 在同一 `4a006fe` 提交取得 Windows／Ubuntu 双 PASS，Phase 3 跨平台门通过。
- Pilot 008 Scope Acquisition 重构后，上下文专项为 17/17：新增 passive proxy、4-case Scope analyzer、legacy aggregate-only 拒绝、P/S dry-run 和 formal fail-closed。文件稳定后的默认全仓为 51 项中 49 通过、2 项动态依赖按设计跳过；24 项 corpus、6 份 run record、integrated static build、195 份 Markdown 本地链接与 diff 检查通过。
- Smoke 001 装置修正增加 2-case app-server ordering self-test，并把 smoke runner 纳入 Pilot 008 控制哈希；上下文专项 18/18，默认全仓 52 项中 50 通过、2 项动态依赖按设计跳过，24 项 corpus、6 份 run record、integrated static build、202 份 Markdown 本地链接与 diff 检查通过。
- Smoke 002 使用同版本哈希一致的完整 CLI runtime，真实验证 usage 更新位于首次产品 `fileChange` 之前；独立 analyzer 判定 ordering 测量有效。原始根按 `decision_supporting` 封存且 manifest 39/39 有效。该 smoke 允许 0 次写前代理读取，不提供正式 P/S 或内容交付证据。
- Smoke 002 权威链同步后的最终回归：Scope analyzer 4/4、ordering self-test 2/2、上下文专项 18/18；默认全仓 59 项中 57 通过、2 项动态依赖按设计跳过；Pilot 008 dry-run 通过且正式路径继续失败关闭；Smoke 001／002 manifest 分别 36/36、39/39 有效；24 项 corpus、6 份 run record、integrated structure、docsite build、205 份 Markdown 本地链接与 diff 检查通过。
- ADR-0006 新增 Broker-only 回归：保护 UI 不再显示 Local Broker 同级入口、所有 docsite 构造要求 Broker、本机／外部保存后 `provider=broker`、上游替换删除旧 Key、内存 keyring 和 sentinel 不回显。动态产品专项 16/16 通过；默认全仓 59 项中 57 通过、2 项动态依赖按设计跳过；integrated static build、根／模板投影、204 份 Markdown 链接、语法与 diff 检查通过。
- Pilot 008 正式 transport 新增完整 app-server item lifecycle validator 及 3-case self-test，并在 synthetic
  formal pipeline 中串联代理 proof、Scope analysis、Oracle、正式验证和 R0 seal/verify。首对实际运行的
  fail-stop 生效，两份 manifest 为 85/85、88/88 有效。
- Pilot 009 dry-run 已加入 `tests/test_context_routing_h2.py`；上下文专项为 20/20。正式运行前默认全仓
  61 项中 59 通过、2 项动态依赖按设计跳过；24 项 corpus、6 份 run record、integrated static build、
  227 份 Markdown 本地链接和 diff 检查通过。正式六份 manifest 全部有效：P 各 85/85、S 各 88/88。
- 2026-08-20 多 worktree 恢复验证已证明：共享脏工作树可先封存为不可变恢复提交，再在独立干净 integration worktree 中按研究、产品和权威状态拆分提交并合入协议分支；恢复分支保持不变。默认全仓为 59 passed + 2 expected skips，启用动态依赖后为 61/61；integrated structure、静态站和 235 份 Markdown／420 个本地链接通过。此证据只覆盖人工流程，不覆盖尚未实现的 session、untracked overlap、Authority／Semantic／Unknown 自动分类或 integration CLI。
- 2026-08-20 协作 Design 收敛验证审计了 ADR-0007 与 Team Mode telemetry 的冲突，并通过正式 ADR-0008 amendment、Workstream 术语、session 示例、平台中立实现目标和 Personal-before-Team 交付顺序完成文档级闭环。该证据不包含任何协作 runtime 或网络测试。
- 2026-08-21 ADR-0009 文档级采纳区分了 role lifecycle 与独立 claim dimensions，并固定 Authority scope、provider-neutral evidence 与 derived-view conformance 边界；尚未建立可执行 fixture 或跨消费者一致性测试。
- 2026-08-21 Authority Meta Model Candidate fixture checkpoint 新增 `amm-fixture-v1`：21 个 versioned cases 与 2 个 comparison contracts 覆盖 accepted≠implemented≠validated、失败验证、历史/current、supersede/amend、Draft/Approved、Plan/State、六类 fact scope、Snapshot、五类 evidence、AI non-escalation 与 scope≠Coordinator；专项为 9/9 通过。它只验证 golden contract 的结构与不变量，尚未验证任何生产 evaluator 或 consumer conformance。
- 2026-08-21 ADR-0010 Core shadow evaluator 将 fixture cases 扩展为 normalized observations，新增 deterministic evaluation、all-case expected comparison、显式 extra-output 分类、visibility-sensitive output、unsupported version/scope/evidence/observation fail-closed 和非顶层 API 断言；Authority 专项为 14/14。CLI/docsite 尚未双轨运行，不能据此声称 consumer 已一致。
- 2026-08-21 CLI 第一处 shadow comparison 新增 6 项专项：保护 legacy integrated heuristic、真实 Accepted ADR 匹配、authority-visible input hash、`parser-gap` 分类，以及 mismatch／evaluator failure 时 warning-only、旧退出码不变。既有产品专项共运行 16 项，其中 14 通过、2 项动态依赖按设计跳过；默认全仓 81 项中 79 通过、2 项按设计跳过，integrated structure、静态站和 250 份 Markdown 本地链接均通过。Observatory 尚未双轨，CLI 也尚未切换生产语义。
- 2026-08-21 Observatory parser shadow 新增 8 项专项：保护未导出内部 adapter、七类 legacy lifecycle、真实 `parse_adrs` 双轨、当前仓库 ADR、精确输入 hash／过滤、`parser-gap` 与 graph/reference legacy-only 边界。Authority 三组专项合计 28/28；默认全仓 89 项中 87 通过、2 项按设计跳过，integrated structure、905 KB 静态站和 251 份 Markdown 本地链接均通过。该 harness 未接入 build/serve，不能表述为 Observatory 生产迁移。
- 2026-08-21 Observatory relation shadow 将专项扩展为 15 项：覆盖显式 `Amends`／`Supersedes`、`Superseded by` 方向反转、effective decision、amend 保留 base effect、真实仓库 6 条 amendment、非关系引用隔离、缺失目标保持 `Unknown` 与 malformed metadata 失败关闭。Authority 三组专项为 35/35；默认全仓 96 项中 94 通过、2 项按设计跳过，integrated structure、913 KB 静态站和 252 份 Markdown／513 个本地链接均通过。旧 build/serve graph、公开 API 与发布契约仍未切换。
- 2026-08-21 Observatory role shadow 新增 9 项专项：覆盖 Design Draft／Approved／Deprecated 与 Unknown、Plan/State 不生成 implementation claim、Validation 文档存在／Status／自由文本不等于通过、精确 Passed/Failed、隐藏 executable evidence 回退 Unknown、冲突元数据失败关闭、输入快照与真实仓库 7/12/6/29 角色盘点。Authority 四组专项为 44/44；默认全仓 105 项中 103 通过、2 项按设计跳过。该 adapter 未导出且未接入 build/serve，29 个现有 Validation 结果在严格 collector 中全部保持 Unknown。
- 2026-08-21 Observatory runtime shadow 新增 5 项专项：真实 legacy `render_site()` 双轨时 HTML/stats 完全相同，ADR/role report 组合、显式 scope 与 evaluator failure 隔离均受保护。Authority 五组专项为 49/49；默认全仓 110 项中 108 通过、2 项按设计跳过，integrated structure、930 KB 静态站和 254 份 Markdown／525 个本地链接均通过。该 bridge 未导出、未接入 managed build/serve，也未修改模板或发布契约。
- 2026-08-21 Gate B Candidate compatibility 新增 8 项专项与 9-case fixture：保护 public model 1／internal fixture ID 分离、缺失与显式 null 分离、离散 support gap、known/unknown/newer/invalid 分类、downgrade 不兼容、非法 capability 声明失败关闭和非顶层 API 边界。Authority 六组专项为 57/57；全仓 118 项中 116 通过、2 项按设计跳过。该检查点没有修改 project/release manifest、schema、installer、managed docsite 或发布状态。
- 2026-08-21 ADR-0011 integration 新增 4 项 CLI capability 回归与 2 项 Observatory status 回归，并更新新增 ADR 的 explicit-amendment golden：supported 只报告 eligible、legacy relaxed/strict 分流、unknown/invalid 失败关闭、JSON warning 结构、read-only shadow suppression 和 legacy render 不变均被覆盖。Authority 专项现为 63/63；全仓 131 项中 129 通过、2 项按设计跳过。self-host manifest 已显式选择模型 1；release manifest、installer、schema、managed docsite 与发布状态未变。
- 2026-08-21 Authority migration dry-run 新增 13 项回归：保护 legacy→model 1 的单字段计划、no-op、非法／unsupported source、unsupported target、正交 manifest/schema 版本失败关闭、离散支持集不产生隐式路径、非顶层 Core API、CLI 同字节 snapshot hash、统一 CLI 路由、`--dry-run` 强制要求、非法 target、缺失 manifest 和全路径零写入。全仓 144 项中 142 通过、2 项动态依赖按设计跳过；262 份 Markdown／572 个本地链接无缺失。Harness JSON Adapter 仍只暴露原三条白名单命令；apply、release projection 与发布状态未变。
- 2026-08-21 Authority migration apply 把专项扩展到 20 项：新增纯 materializer、receipt 必填、receipt 分别绑定源／目标／提议、stale manifest 拒绝、精确备份、原子替换、no-op 不写入，以及注入 replace failure 后原文件不变／备份保留／临时文件清理。全仓 151 项中 149 通过、2 项动态依赖按设计跳过；263 份 Markdown／574 个本地链接无缺失。Harness JSON Adapter、release projection 与发布状态仍未改变，restore command 尚未实现。
- 2026-08-21 Authority restore 新增 17 项专项：覆盖 pure restore planner、非顶层 Core API、统一 CLI 路由、当前／备份 receipt 绑定、绝对路径／穿越／文件 symlink 拒绝、生成目录形状、无关字段与非法／unsupported／正交版本失败关闭、精确恢复与撤销备份、current／backup 过期、no-op 以及 replace failure。定向 migration/restore/compatibility 共 49/49；全仓 168 项中 166 通过、2 项动态依赖按设计跳过。Harness JSON Adapter、release projection 与发布状态仍未改变。
- 2026-08-21 Authority release/project projection 新增 8 项专项：冻结 future release 默认值 + 离散支持集、配对／类型／重复校验、optional project schema、新项目默认选择、已有 legacy／explicit 选择保持、真实 `--upgrade-tools` 不迁移，以及 source/bundled v0.2.0 历史 contract 不改写。投影 + compatibility + migration/restore + 产品组合 69 项中 67 通过、2 项动态依赖按设计跳过；全仓 176 项中 174 通过、2 项动态依赖按设计跳过。实际下一 release、standalone installer projection 与发布状态仍未改变。
- 2026-08-21 Authority update compatibility 新增 8 项专项：future release 的 supported／legacy／invalid／unsupported target、无 target Skill-only 查询、malformed release 失败关闭、v0.2.0 历史行为和既有 JSON schema v1 均受保护。与 projection、compatibility 和产品组合 40 项中 38 通过、2 项动态依赖按设计跳过；全仓 184 项中 182 通过、2 项动态依赖按设计跳过。266 份 Markdown／580 个本地链接无缺失；没有实际下一 release 或 target 写入。
- 2026-08-21 managed Observatory shadow 新增 3 项专项：默认 build runtime 精确等于 legacy path，显式 sidecar 在 Candidate scope 下保持 HTML/stats 字节一致，非法 Coordinator-like scope 对 evaluator 失败关闭而不影响页面。与既有 runtime shadow、产品投影组合 26 项中 24 通过、2 项动态依赖按设计跳过；全仓 187 项中 185 通过、2 项动态依赖按设计跳过。
- 2026-08-21 Authority AI derived-view 新增 6 项专项：覆盖无 report 的 Unknown、Local-only shadow 不升级、预构造 context／模型回执伪造、虚构引用过滤、成功／失败输出 receipt、根／模板投影与 managed serve context/header 接线。专项 6/6；全仓 193 项中 191 通过、2 项动态依赖按设计跳过；最终 268 份 Markdown／582 个本地链接无缺失，integrated scaffold 与 1088 KB 静态站通过。此证据证明系统不会把 AI 结果升级为项目权威，不证明模型自然语言绝对正确。
- 2026-08-21 Authority shadow diagnostic 将 managed-entrypoint 专项从 3 项扩展到 6 项：新增显式 view-only 面板、bounded insights projection、根／模板一致性；默认与 report-only HTML 继续等于 legacy，面板标明非权威／未切换，effective claims 不进入 insights。全仓 196 项中 194 通过、2 项动态依赖按设计跳过；269 份 Markdown／584 个本地链接无缺失，integrated scaffold 与 1096 KB 静态站通过。
- 2026-08-21 M1 本地 Canonical integration 在 Candidate 与 `main@2989582` 同 merge base、两处 worktree clean 的前提下审阅 20 个提交并 `--ff-only` 合入；合并后全仓仍为 196 项中 194 通过、2 项按设计跳过，Authority 定向 120/120，integrated scaffold、1107 KB 静态站、270 份 Markdown／590 个本地链接／0 缺失和 `git diff --check` 通过。该证据只证明本地 Canonical baseline，不证明 push、发布或 production switch。
- 2026-08-21 M2.1 CLI claims Worktree Candidate 新增 versioned internal observation contract、完整 role/source hash、显式 decision graph、assertion／validation evidence 分离和 symlink／metadata／missing-target 失败关闭。Authority 专项为 139 项通过、1 项 Windows symlink privilege skip；最终全仓、站点与链接结果见对应 Validation。本证据不证明 Canonical integration、公共 API、Observatory production projection 或 release。
- 2026-08-21 M2.2 Observatory projection Worktree Candidate 新增 12 项专项，覆盖独立包导入、完整 M2.1
  reconciliation、effective decision／role/source 投影、determinism、默认无变化／关闭回滚、legacy model、
  collector／visibility／snapshot drift 失败关闭、source provenance 防篡改和 HTML escaping。Authority 专项当前
  为 151 项、1 项 Windows symlink privilege skip。首次全仓 219 项暴露 1 项 root/release builder 字节一致性
  失败，随后把 Candidate runtime 移到独立 root-only entry，并由含原失败用例的 19 项 focused rerun 证明修复；
  最终全仓、结构、站点、链接与 diff 见对应 Validation。
- 2026-08-21 M2.3 release／installer gate Worktree Candidate 新增 12 项门禁专项：覆盖 candidate manifest 配对／版本／secret 失败关闭、v0.2 历史 hash、确定性离线 archive／checksum、new／legacy standalone、invalid／unsupported 与非普通 target 零写入、receipt-gated migration／restore、self-host、环境凭据隔离／timeout，以及 traversal／大小写碰撞／symlink／forbidden／plaintext-secret 二次解包检查。Gate 专项 12 项中 10 通过、2 项因 Windows symlink privilege 跳过；Authority 专项 151 项中 148 通过、3 项跳过；全仓 219 项中 214 通过、5 项按环境或可选依赖跳过。该证据不选择实际 SemVer，不证明 M2.2 consumer production switch、公开发布或稳定 Core API。
- 2026-08-21 M2 本地 Canonical integration 把 M2.1／M2.2／M2.3 合并后的 Authority 专项扩展到 163 项，160 通过、3 项 Windows symlink privilege 跳过；全仓扩展到 231 项，226 通过、5 项按环境或可选依赖跳过。结构、默认 legacy build、显式 projection、链接与 diff 见 integration Validation；该证据不证明 managed production switch 或 release。
- 2026-08-21 `main` 推送验收先在本机启用动态依赖执行 231 项并全部通过，3 项 Windows symlink privilege 跳过；integrated build、默认／显式 Authority projection 精确回滚、282 份 Markdown／686 个本地链接／0 缺失和发布排除边界通过。首次远端 run `32492265629` 的 Ubuntu job 发现 release-gate 测试硬编码 Windows 绝对路径；`42aebae` 改用平台原生绝对词法路径后，Windows focused 为 10 passed + 2 privilege skips、Ubuntu WSL focused 12/12，最终 GitHub Actions `32492830151` 在 Windows／Ubuntu 双 PASS。该证据只验收公开 source `main`，不构成 Release。
- 2026-08-22 W1 Personal Core／CLI Phase 0 Candidate 新增 10 项专项，使用运行时合成 Git fixture 覆盖 clean main、两个 linked worktree、独立 clone、文件级 untracked 和未 push commit；同时覆盖 schema bundle、integration ref/OID、主 worktree 覆盖、subsystem registry、Scope 特殊表达、Member capability/credential epoch、Personal zero-network 与只读 CLI。专项 10/10，受影响组合 67 passed + 2 expected skips；最终全仓 241 项中 236 通过、5 项按既有 symlink privilege／动态依赖门跳过。
- 2026-08-22 D1 文档治理 Phase 1 Candidate 新增 11 项专项，保护 v1 finding schema／规则 registry、11 组正负 synthetic corpus、source hash／line range、status／acknowledge／defer／resolve、soft budget 默认 exit 0、结构门未启用、Authority／作者文档零影响、零网络与确定性零写入。最终全仓、结构、隔离站点与链接结果见对应 Validation。
- 2026-08-22 W4 Personal Observatory Worktree Candidate 新增 9 项专项，保护 W1/W2 Core contract 复用、排除 worktree 不读取、zero-network／read-only、Unknown／Unavailable、W3 三槽 fallback、总览内容不变而 Personal 以独立 sibling page 注入、active session 与 worktree-only／unavailable 分组、面向人的四问题信息架构、lifecycle／runtime／freshness 分离、HTML escaping、legacy 精确回退和窄屏 CSS；受影响组合为 42 PASS + 2 expected dynamic-dependency skips。默认全仓 287 项中 282 PASS + 5 skips，启用 `ORRERY_TEST_BUILD=1` 后 284 PASS + 3 Windows symlink privilege skips；integrated scaffold、legacy 隔离站、Authority + Personal 显式组合站、336 份 Markdown／863 个本地链接（仅 1 个 D1 冻结 synthetic missing target）、secret／forbidden 与 diff 门通过。真实 Chromium 覆盖 1440×1000、390×844、首屏 briefing、独立导航、Workstream／技术证据 details、折叠 inventory 与无 Workstream／无 finding 空状态；这是未提交 Windows Worktree Candidate 证据，不构成 Canonical integration、跨平台 CI 或 Release。
- 2026-08-23 W4B 将专项扩展到 12 项：除保留 W4A 边界外，覆盖真实 W3 Core review package→W4 freshness／risk／human approvals／eligibility／binding、无 review package 的七类 bounded inventory、cleanup candidate 只由 Core `recommended_action` 进入、四动作独立且 `authorized=false`／`performed=false`、closure／caller-attested receipt 非删除推断，以及 provider failure／旧 schema 的 W4A fallback。隔离修复后 12/12 PASS（99.481 s），组件版本一致性 1/1 PASS；根据 Fast／Checkpoint 策略未重跑默认或动态全仓，中央将在 W3+W4 干净联合 Candidate 统一执行全仓、全链接、安全全集与 exact-SHA 双平台矩阵。一条实现代理误启动的 collaboration 组合测试在约十分钟后被停止并记为 interrupted，未重跑、未计入通过证据。

## 验证证据

- [2026-08-18 自托管基线](../validation/2026-08-18-self-hosting-baseline.md)
- [2026-08-18 H2 读取证明装置](../validation/2026-08-18-h2-read-proof-apparatus.md)
- [2026-08-18 Pilot 005 / 006 B/H2](../validation/2026-08-18-pilot-005-006-bh2.md)
- [2026-08-18 Pilot 007 P/B 采纳实验](../validation/2026-08-18-pilot-007-pb-adoption.md)
- [2026-08-19 Pilot 008 Skill Entry Router 准备](../validation/2026-08-19-pilot-008-preparation.md)
- [2026-08-19 Pilot 008 Scope Acquisition 重构](../validation/2026-08-19-pilot-008-scope-acquisition-reframe.md)
- [2026-08-19 App-server Scope Ordering Smoke 001](../validation/2026-08-19-app-server-scope-ordering-smoke-001.md)
- [2026-08-19 App-server Scope Ordering Smoke 002](../validation/2026-08-19-app-server-scope-ordering-smoke-002.md)
- [2026-08-19 Pilot 008 formal apparatus stop](../validation/2026-08-19-pilot-008-formal-apparatus-stop.md)
- [2026-08-19 Pilot 009 P/S Scope run](../validation/2026-08-19-pilot-009-ps-scope-run.md)
- [2026-08-19 平台中立 Phase 0 发布基线](../validation/2026-08-19-platform-neutral-phase-0-baseline.md)
- [2026-08-19 平台中立 Phase 1 Core／CLI 抽取](../validation/2026-08-19-platform-neutral-phase-1-core-cli.md)
- [2026-08-19 平台中立 Phase 2 Codex Adapter 仓库实现](../validation/2026-08-19-platform-neutral-phase-2-codex-adapter.md)
- [2026-08-21 Codex Runtime E2E 安全停止](../validation/2026-08-21-codex-runtime-e2e.md)
- [2026-08-21 Codex Runtime E2E 完成](../validation/2026-08-21-codex-runtime-e2e-completion.md)
- [2026-08-21 平台中立 Phase 3 Harness JSON](../validation/2026-08-21-platform-neutral-phase-3-harness-json.md)
- [2026-08-19 Broker-first docsite gateway](../validation/2026-08-19-broker-first-docsite-gateway.md)
- [2026-08-20 多 worktree 恢复与人工采纳](../validation/2026-08-20-multi-worktree-recovery-and-manual-adoption.md)
- [2026-08-20 多 Workstream 协作 Design 收敛](../validation/2026-08-20-multi-worktree-collaboration-design-consolidation.md)
- [2026-08-20 ADR-0008 协作 Design 集成](../validation/2026-08-20-adr-0008-collaboration-design-integration.md)
- [2026-08-21 ADR-0009 Authority Meta Model 采纳](../validation/2026-08-21-authority-meta-model-adoption.md)
- [2026-08-21 Authority Meta Model fixture baseline](../validation/2026-08-21-authority-meta-model-fixture-baseline.md)
- [2026-08-21 Authority Meta Model M1 本地 Canonical 集成](../validation/2026-08-21-authority-meta-model-canonical-integration.md)
- [2026-08-21 M2.1 complete CLI Authority observations/claims](../validation/2026-08-21-m2-1-authority-cli-claims.md)
- [2026-08-21 M2.2 Observatory Authority Candidate projection](../validation/2026-08-21-m2-2-observatory-authority-projection.md)
- [2026-08-21 M2.3 Authority release／installer candidate gate](../validation/2026-08-21-m2-3-authority-release-candidate-gate.md)
- [2026-08-21 Authority Meta Model M2 本地 Canonical 集成](../validation/2026-08-21-authority-meta-model-m2-local-canonical-integration.md)
- [2026-08-21 Authority Meta Model Core shadow evaluator](../validation/2026-08-21-authority-meta-model-core-shadow-evaluator.md)
- [2026-08-21 Authority Meta Model CLI shadow comparison](../validation/2026-08-21-authority-meta-model-cli-shadow.md)
- [2026-08-21 Authority Meta Model Observatory parser shadow](../validation/2026-08-21-authority-meta-model-observatory-parser-shadow.md)
- [2026-08-21 Authority Meta Model Observatory relation shadow](../validation/2026-08-21-authority-meta-model-observatory-relation-shadow.md)
- [2026-08-21 Authority Meta Model Observatory role shadow](../validation/2026-08-21-authority-meta-model-observatory-role-shadow.md)
- [2026-08-21 Authority Meta Model Observatory runtime shadow](../validation/2026-08-21-authority-meta-model-observatory-runtime-shadow.md)
- [2026-08-21 Authority Model compatibility Candidate](../validation/2026-08-21-authority-model-compatibility-candidate.md)
- [2026-08-21 Authority Model migration dry-run](../validation/2026-08-21-authority-model-migration-dry-run.md)
- [2026-08-21 Authority Model migration apply](../validation/2026-08-21-authority-model-migration-apply.md)
- [2026-08-21 Authority Model restore](../validation/2026-08-21-authority-model-restore.md)
- [2026-08-21 Authority Model release/project projection](../validation/2026-08-21-authority-model-release-projection.md)
- [2026-08-21 Authority Model update compatibility](../validation/2026-08-21-authority-model-update-compatibility.md)
- [2026-08-21 Authority Model managed Observatory shadow](../validation/2026-08-21-authority-model-managed-observatory-shadow.md)
- [2026-08-21 Authority AI derived-view constraints](../validation/2026-08-21-authority-ai-derived-view-constraints.md)
- [2026-08-21 Authority shadow diagnostic projection](../validation/2026-08-21-authority-shadow-diagnostic-projection.md)
- [2026-08-22 Personal collaboration Phase 0](../validation/2026-08-22-personal-collaboration-phase-0.md)
- [2026-08-22 W1.3 Personal Phase 1C](../validation/2026-08-22-w1-3-personal-phase-1c.md)
- [2026-08-21 Claude Code Adapter Stage A](../validation/2026-08-21-claude-code-adapter-stage-a.md)
- [2026-08-21 DeepSeek Harness Adapter Stage A](../validation/2026-08-21-deepseek-harness-adapter-stage-a.md)
- [2026-08-21 Claude Code Adapter Stage B 认证阻塞](../validation/2026-08-21-claude-code-adapter-stage-b-auth-blocked.md)
- [2026-08-21 DeepSeek Harness Adapter Stage B 凭据边界](../validation/2026-08-21-deepseek-harness-adapter-stage-b-credential-blocked.md)
- [2026-08-22 DeepSeek Harness Adapter Stage B Runtime](../validation/2026-08-22-deepseek-harness-adapter-stage-b-runtime.md)
- [2026-08-22 W1 与第二平台 Adapter 本地集成](../validation/2026-08-22-w1-and-second-platform-adapters-integration.md)
- [2026-08-22 CLI Wheel Observatory Assets](../validation/2026-08-22-cli-wheel-observatory-assets.md)
- [2026-08-22 DeepSeek Wheel Runtime Canonical 集成](../validation/2026-08-22-deepseek-wheel-runtime-canonical-integration.md)
- [2026-08-22 DeepSeek Wheel／W1 Windows CI 修复](../validation/2026-08-22-deepseek-w1-windows-ci-fix.md)
- [2026-08-22 D1 文档治理 Phase 1 finding contract](../validation/2026-08-22-d1-document-governance-finding-contract.md)
- [2026-08-22 W2 Scope / Finding Candidate](../validation/2026-08-22-w2-scope-finding.md)
- [2026-08-22 W4 Personal Observatory Worktree Candidate](../validation/2026-08-22-w4-personal-observatory.md)
- [2026-08-23 W5A opt-in Team Mode foundation](../validation/2026-08-23-w5a-team-mode-foundation.md)
- [2026-08-27 W4 health / W5B Team Observatory](../validation/2026-08-27-w4-health-w5b-team-observatory.md)
- [2026-08-27 W4 health / W5B final integration candidate](../validation/2026-08-27-w4-health-w5b-integration-candidate.md)
- [2026-08-27 W5C Team Observatory information architecture](../validation/2026-08-27-w5c-team-observatory-ux.md)
- [2026-08-27 local worktree cleanup](../validation/2026-08-27-local-worktree-cleanup.md)
- [2026-08-27 W6 Workspace Maintenance Phase 0–2](../validation/2026-08-27-workspace-maintenance-phase-0-2.md)
- [2026-08-27 W5D LAN collaboration Harness and stacked lineage](../validation/2026-08-27-w5d-lan-collaboration-harness.md)
- [2026-08-27 W5E Team Observatory UI closeout](../validation/2026-08-27-w5e-team-observatory-ui-closeout.md)
- [2026-08-28 W7A Dynamic Workstream Succession Contract](../validation/2026-08-28-dynamic-workstream-succession-contract.md)
- `python -m unittest discover -s tests -v`
- `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`
- `python -X utf8 scripts/docsite/build_docsite.py`

## 已知缺口

- 动态图形化 AI 设置测试默认跳过，除非安装 reader 依赖。
- 当前端到端强度止于代理+完整 CLI JSONL 的事后交叉证明；没有可工作的实时 Hook 阻断。
- 外部原始数据已有 manifest 与保留策略，但仍依赖本机存储，且尚无自动脱敏导出器或异地备份。
- 发布打包测试验证包内安全边界，但尚未比较不同操作系统生成 archive 的 byte-for-byte 一致性。
- Codex Adapter 只有 Windows 11 build 26200、Codex Desktop 26.818.2441.0／`codex-cli 0.148.0-alpha.21`、Adapter／Core／CLI 0.1.0 与已记录模型／审批组合的 runtime compatibility 为 `verified`；Adapter 发行仍为 `experimental`，其他 OS、runtime、模型和权限模式也没有外推证据。
- Harness JSON 已有 Windows 本地、Ubuntu WSL 与同一提交的 Windows／Ubuntu CI 证据，Phase 3 跨平台验收完成。该 Adapter 证明 CLI subprocess 合约，不证明模型读取或任何第三方 Agent 平台兼容；发行状态仍为 `experimental`／`unreleased`。
- ADR-0007／ADR-0008 的当前 W5D Worktree Candidate 覆盖 W1–W3 Personal contract、W4 health、Team Core／CLI／root-only UI、W6 maintenance、显式 discovery/join/manual Host switch 与 stacked lineage。仍无 Phase 3 自动删除、Phase 4 scheduler、真实双机 LAN、自动选主或云 relay 证据；本分支只有 Windows 本机 focused/checkpoint/browser 和受控 transport 证据，Ubuntu／Promotion 仍要求中央 exact-SHA 双平台门。
- ADR-0014/W7A 当前只有 Windows 本机 Fast/Checkpoint 与隔离 Git fixture 证据；没有 W7B 真实 migration/apply/undo、W7C browser/UI、Ubuntu exact-SHA 或 Promotion 结果。双 clone runner 在并发负载下的两次本机 loopback timeout 说明该邻接面仍有既有波动，独占 PASS 不外推为 transport 稳定性修复。
- ADR-0009/0010/0011 的 fixture、experimental Core evaluator、M2.1 完整内部 CLI claims、M2.2 root-only opt-in projection、AI derived-view guard、receipt-gated 迁移／恢复与 M2.3 本地 candidate gate 已进入本地 Canonical baseline；仍没有默认 Observatory production projection、维护者选择的实际下一 release manifest、production-switch、稳定公共 API 或公开 release 证据。
- Claude Code 仍被认证阻断。DeepSeek Harness 已证明真实显式／隐式模型调用、模型侧 CLI 失败关闭和修复后的普通 wheel 路由；只有 manifest 中的精确 rc.8／Windows／Core 0.1.0／CLI 0.1.1／模型与生命周期范围进入 `verified`，其余范围不外推。
