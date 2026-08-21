# 测试覆盖 State

Updated: 2026-08-21

## 当前事实

- `tests/test_project_orrery.py` 保护安装、非覆盖升级、发布包、更新兼容和凭据配置边界。
- `tests/test_context_routing_benchmark.py` 保护历史语料、Pilot 装置、回执规则、未跟踪文件采集、安全 Oracle 和恢复行为。
- `.github/workflows/validate.yml` 在 Windows／Ubuntu 上运行验证；动态文档站测试需要额外依赖和 `ORRERY_TEST_BUILD=1`。
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
- ADR-0007／ADR-0008 的 Phase 0–4 自动化矩阵尚未实现；目前没有机器可执行的主 worktree 写入守卫、私有 session、重叠／review／cleanup、Personal 指挥台或 Team Mode 网络测试。
- ADR-0009/0010/0011 已有 Candidate fixture corpus、experimental Core evaluator、Accepted ADR 的 CLI shadow、Observatory lifecycle/explicit-relation harness、内部 Gate B capability judgment、receipt-gated 显式迁移／恢复和 future-release projection contract，但仍没有完整 CLI claims、Observatory production projection、实际下一 release 默认字段、production-switch 或 release 证据。
