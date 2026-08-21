# Validation：平台中立 Phase 3 Harness JSON 候选实现

Date: 2026-08-21
Scope: ADR-0004 Implementation Plan Phase 3 的统一 CLI JSON 合约、稳定退出码与不依赖 Codex 的最小 Harness Adapter；不含第二平台、模型调用、组件发布、多人协作或 Authority Meta Model
Result: PASS（Windows 仓库实现检查点）— 跨 Windows／Ubuntu CI 尚未对该未 push 提交运行，因此 Phase 3 仍是 `experimental`／`unreleased` candidate
Source: branch `codex/harness-json-phase3`，baseline `main@14af26a879eb2f6e4242031719f675c50e5cb27a`

## 权威链

- 决策：[ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md)。
- Approved Design：[平台中立 Core 与 Adapter 架构](../design/platform-neutral-core-and-adapter-architecture.md)。
- 活动 Plan：[平台中立 Core 与 Agent／Harness Adapter](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)。
- 前置实现：[Phase 1 Core／CLI](2026-08-19-platform-neutral-phase-1-core-cli.md)与
  [Phase 2 Codex Runtime E2E](2026-08-21-codex-runtime-e2e-completion.md)。

本阶段不依赖当前 Codex runtime 行为，没有查询或修改 Codex 配置，也没有启动模型 turn。

## 环境与组件

| 维度 | 值 |
|---|---|
| OS | Windows 11 `10.0.26200`，x64 |
| Python | 3.13.5，Anaconda build，MSC v.1929 64 bit |
| Core | 0.1.0，API 1，未发布 |
| CLI | 0.1.1，JSON schema 1，未发布 |
| Harness Adapter | `project-orrery-harness-json-adapter` 0.1.0，API 1，`experimental`／未发布 |
| Transport | 直接 Python subprocess，stdin/file request 与 stdout response JSON |
| Agent runtime | 未加载、未调用 |

Codex Adapter 的历史 `verified` 证据继续精确绑定 CLI 0.1.0；本次 CLI 0.1.1 没有回写或外推该
runtime 证据。

## JSON 合约

三个命令都使用相同 response envelope：

- `schema_version`、`command`、`status`、`exit_code`；
- `versions.core`、`versions.core_api`、`versions.cli`；
- command-specific `data`；
- 结构化 `warnings[]` 与 `errors[]`，每项至少有稳定 `code` 和人类可读 `message`。

JSON 模式稳定退出码为：

| exit | 类别 | 本轮证据 |
|---:|---|---|
| 0 | success／structured warning | dry-run、安装、validate、compatible result、mixed toolchain |
| 2 | invalid request | 未知 Harness 参数失败关闭 |
| 3 | operation／protocol failure | manifest 与 response schema 固定；异常 subprocess 输出由 Adapter 分类 |
| 4 | validation failed | document schema 99 被 validator 拒绝 |
| 5 | compatibility failed | update checker 对 schema 99 返回 migration required |
| 6 | update unavailable | unique URL 的 offline／no-cache 路径，不访问网络 |
| 7 | timeout | manifest／response schema 与 Adapter timeout 分类固定；本轮不通过真实长任务制造超时 |

既有人类输出和旧 Skill wrapper 的成功路径回归保持不变；稳定退出码只由 opt-in JSON／Harness 路径
消费。

## 隔离验证矩阵

| 路径 | 结果 |
|---|---|
| scaffold dry-run | PASS — 两次 response 完全相同，报告 create/write 预测动作，目标目录不存在 |
| 临时实际安装 | PASS — 只写 `TemporaryDirectory` 目标，返回 `changed=true` |
| validate | PASS — 已安装结构有效，migration pending 被结构化为 warning 而非正式采纳 |
| mixed toolchain | PASS — 自定义 `scripts/docsite/serve.py` 保留，返回 `mixed_toolchain` warning |
| upgrade dry-run | PASS — 同时报告独立 `backup`／`upgrade` 动作；不创建备份、不改自定义工具 |
| schema 不兼容 | PASS — validate exit 4；check-update exit 5；error code 稳定 |
| offline update | PASS — 随机唯一 URL、无 cache，exit 6／source `offline`，没有网络请求 |
| 作者文件保留 | PASS — 修改后的 `AGENTS.md` 保持逐字不变并进入 `preserved_authored_paths` |
| Agent 隔离 | PASS — Adapter 树没有 `SKILL.md`；测试注入的假 Codex config／Skill／API Key 未改变且不出现在 response |
| 第三方平台声明 | PASS — manifest、README 与 State 只称参考 Harness 为 `experimental`，其他 Agent 继续为 `target` |

Harness request 只能使用 schema 白名单参数，不能注入任意 CLI argv。子进程环境移除
`CODEX_HOME`、`CODEX_CONFIG`、`AGENTS_HOME` 和常见 Provider API Key；调用的是指定 Python
解释器的 `project_orrery_cli` module，不搜索 `codex` binary。

## 验证命令

| 命令／检查 | 结果 |
|---|---|
| `python -X utf8 -m unittest tests.test_harness_json_adapter tests.test_project_orrery -v` | PASS — 20 passed，2 expected skips |
| `python -X utf8 -m unittest discover -s tests -v` | PASS — 66 passed，2 expected skips |
| `ORRERY_TEST_BUILD=1` + 全仓 unittest discover | PASS — 68/68 |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — 最终结构为 `integrated candidate` |
| `python -X utf8 -m json.tool packages/component-versions.json` | PASS |
| 隔离 docsite build | PASS — 61 docs；输出位于 ignored `dist/validation/phase3-harness-json/` |
| Markdown 本地链接扫描 | PASS — 247 files，497 local links，0 missing |
| `git diff --check` | PASS |

隔离 build 没有修改 `docs/_site/index.html`。

## 边界与待完成项

- 现有 `.github/workflows/validate.yml` 会在 Windows／Ubuntu 运行完整测试，但本分支尚未 push，因而
  当前没有该提交的双 OS CI run。跨 OS 验收门仍未通过。
- Harness 证明请求／subprocess／CLI response 的机器合约，不证明模型读取、理解或第三方 Agent
  平台发现／调用。
- 未生成 wheel、多组件 release、tag 或公开 Adapter 包；顶层组件状态继续为 `unreleased`。
- 未修改 `docs/_site/index.html`、用户目录、Codex 配置、登录态或凭据；没有产生模型调用。
- Phase 4 第二平台保持未开始。
