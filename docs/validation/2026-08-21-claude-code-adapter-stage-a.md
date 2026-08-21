# Validation：Claude Code Adapter Stage A

Date: 2026-08-21
Scope: ADR-0013／Phase 4A 的仓库实现、官方 Plugin 验证、隔离安装／升级／卸载和 CLI 依赖失败关闭；不含真实登录态、模型调用、发布或 `verified` 提升
Result: PASS — Adapter 0.1.0 已实现并通过无模型隔离生命周期；支持状态保持 `experimental`／`unreleased`
Source: branch `codex/claude-deepseek-adapters`，baseline `main@2989582d106e1bc36307a30427c8ba5f1dfb91c2`

## 权威链

- [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md)
- [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)
- [Approved Design](../design/platform-neutral-core-and-adapter-architecture.md)
- [Implementation Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)

实现与验证只依据 Claude Code 官方 Plugin、Plugin reference、CLI 和 environment variable 文档，以及
精确本机 binary 的 `--help`：

- [Plugins](https://code.claude.com/docs/en/plugins)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [CLI reference](https://code.claude.com/docs/en/cli-reference)
- [Environment variables](https://code.claude.com/docs/en/env-vars)

## 精确范围

| 维度 | 值 |
|---|---|
| OS | Windows 11 Pro x64 `10.0.26200`，build 26200 |
| Python | 3.13.5 |
| Claude Code | `2.1.87` |
| binary | `C:\Users\1\.local\bin\claude.exe` |
| binary SHA-256 | `c722ff8836e7a90b5c62fd5cb6549887dc314e7e8d9551c01df1718d9198ecdf` |
| Adapter | `project-orrery-claude-code` 0.1.0，API 1 |
| Core／CLI | Core 0.1.0／API 1；CLI 0.1.1，均未发布 |
| CLI 约束 | `project-orrery-cli >=0.1.1,<0.2.0`；entrypoint `project-orrery` |
| 模型调用 | 0 |

## 仓库实现

`adapters/claude-code/` 是原生 Plugin：`.claude-plugin/plugin.json` 声明身份，
`skills/project-orrery/SKILL.md` 提供薄路由，bundled local marketplace 只用于隔离生命周期。Adapter 不含
canonical 模板、schema、项目 State 或兼容实现；依赖预检缺失 distribution、缺失 entrypoint 和 0.2.0
不兼容时分别非零失败，不回退到旧 Skill。

两次确定性归档 byte-identical：

- ZIP SHA-256：`fcbdd1f4ca74d06e6f696eefa583adf4228d76cafa59adb716b39ddbc6457e56`
- 证据根：`D:\orrery-stage-ab-artifacts-final-20260821\claude-a` 与 `claude-b`

## 官方 runtime 生命周期

`claude plugin validate` 对 marketplace 与 plugin manifest 均无 warning 通过。随后
`scripts/validate_claude_code_adapter_stage_a.py` 创建全新的
`D:\orrery-stage-ab-final-20260821\claude-stage-a-003`：

1. `CLAUDE_CONFIG_DIR` 只指向该隔离根，并从进程环境移除 Anthropic API Key／OAuth token；没有复制
   真实配置、登录态或凭据。
2. native marketplace／plugin CLI 安装 fixture 0.0.9；`plugin list --json` 唯一返回 0.0.9。
3. marketplace 更新后，native `plugin update` 明确报告 `0.0.9 to 0.1.0`；安装列表唯一返回 0.1.0。
4. native `plugin uninstall --keep-data` 后安装列表为 `[]`；隔离 cache 保留 0.0.9 和 0.1.0，可通过
   重新安装恢复，但两者不再位于 installed plugin catalog。
5. fixture 作者 `AGENTS.md` 的 SHA-256 始终为
   `66ce61b9f504988bcc5d37c00c2dd0a4d389a3884aa6537c612ddff52417f6a0`。

结果文件：`...\claude-stage-a-003\result.json`。早先 `claude-current`／`claude-upgrade-001`／
`claude-upgrade-002` 目录保留前置 smoke 与较早 manifest 检查点，不作为最终产物的主证据。

## 仓库收尾验证

- `python -X utf8 -m unittest discover -s tests -v`：74 项中 72 passed、2 expected skips。
- `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`：
  PASS，`Authority status: integrated candidate`。
- 静态 docsite 使用绝对输入／输出路径构建到
  `D:\orrery-docsite-claude-deepseek-stage-ab-20260821-003\index.html`：PASS；未修改 `docs/_site/index.html`。
- Markdown 本地链接：256 份文件、552 个链接、0 missing；`git diff --check`：PASS。

## 结论与 Stage B 门

Stage A 证明 Plugin 结构、宿主安装目录、版本升级、卸载后 catalog 状态、可恢复 cache、作者文件保留和
CLI 失败关闭。它没有启动 Claude turn，因此没有证明 Skill 进入模型目录、显式／隐式调用、CLI 失败被
模型正确解释或真实权限行为。

`verified` 门未通过，manifest 的 `verified` 保持空数组。Stage B 若获明确授权，才可使用真实登录态和
最少 `claude -p` turn 补齐发现、显式／隐式调用与失败路径；在此之前不得写真实用户 Plugin／Skill
目录或修改真实 Claude 配置。
