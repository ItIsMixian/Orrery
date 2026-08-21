# Validation：DeepSeek Harness Adapter Stage A

Date: 2026-08-21
Scope: ADR-0013／Phase 4B 的仓库实现、精确官方 developer-preview runtime、profile Bundle composition、真实无模型 Skill registry discovery、隔离升级／移除和 CLI 依赖失败关闭；不含模型调用、真实凭据、发布或 `verified` 提升
Result: PASS — Adapter 0.1.0 已实现并通过干净 discovery scope 的无模型 runtime 生命周期；支持状态保持 `experimental`／`unreleased`
Source: branch `codex/claude-deepseek-adapters`，baseline `main@2989582d106e1bc36307a30427c8ba5f1dfb91c2`

## 权威链与官方资料

- [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md)
- [ADR-0013](../decisions/0013-claude-code-and-deepseek-harness-adapters.md)
- [Approved Design](../design/platform-neutral-core-and-adapter-architecture.md)
- [Implementation Plan](../implementation/plans/2026-08-19-platform-neutral-core-and-adapters.md)

扩展面只依据 DeepSeek 官方仓库固定提交 `141eb6fef83422698aef7a981029e843e8161534` 与官方 npm
distribution：

- [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
- [CLI behavior reference](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/reference/README.md)
- [Skill subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md)
- [Filesystem Skill provider](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md)
- [Packaged Skill example](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-badge/README.md)

## 精确范围

| 维度 | 值 |
|---|---|
| OS | Windows 11 Pro x64 `10.0.26200`，build 26200 |
| Node／npm／pnpm | Node 22.17.0；npm 10.9.2；pnpm 11.19.0 |
| DeepSeek Harness | `@deepseek-ai/dsh 0.1.0-rc.8`（npm `next`） |
| entrypoint | 隔离 runtime 的 `node_modules/@deepseek-ai/dsh/lib/bin.js` |
| entrypoint SHA-256 | `c0226687bb20f45c603ec6fe50f3de16d1c3510c3a803304ec575ef9bc366c62` |
| Adapter | `project-orrery-deepseek-harness-adapter` 0.1.0，API 1 |
| Core／CLI | Core 0.1.0／API 1；CLI 0.1.1，均未发布 |
| CLI 约束 | `project-orrery-cli >=0.1.1,<0.2.0`；entrypoint `project-orrery` |
| 模型调用 | 0 |

## 仓库实现与产物

`adapters/deepseek-harness/` 是原生 profile Plugin Bundle：`package.json` 声明
`dsh.bundle.patch`，`cordis.patch.yml` 挂载插件，`index.js` 向真实 `ctx.skills` 注册 packaged
`project-orrery` Skill。Adapter 不含 canonical 模板、schema、项目 State 或兼容实现。

两次确定性 npm-compatible `.tgz` byte-identical：

- SHA-256：`6cab195ea26cc5fab0ebeeb5b6974718a6385df1c21023b46b5d16c0eb5b152b`
- 证据根：`D:\orrery-stage-ab-artifacts-final-20260821\dsh-a` 与 `dsh-b`

## 隔离 runtime 与生命周期

官方 rc.8 使用 pnpm 安装到
`D:\coding warehouse\project-orrery-claude-deepseek-stage-a-20260821\dsh-runtime-rc8-pnpm`，content store
也位于同一 D 盘证据根。有效生命周期由
`scripts/validate_deepseek_harness_adapter_stage_a.py` 在无空格根
`D:\orrery-stage-ab-dsh-stage-a-007` 执行：

1. `DSH_HOME`、`DSH_AGENTS_HOME`、pnpm home／store、npm cache 全部指向隔离 D 盘路径；移除
   DeepSeek、OpenAI、Anthropic API Key 环境变量，并显式禁用 telemetry。
2. `dsh plugin` 安装 0.0.9 tarball，profile dependency 与 Bundle list 均识别 Adapter；
   `--dump-config` 含 `project-orrery-skill` row。
3. 一个仅用于验证、注入 `skills` service 的 Cordis probe 启动真实 profile，直接调用
   `ctx.skills.list()`／`get()`：目录中恰好一个 `project-orrery`，provider 为 `project-orrery`，两种
   invocation policy 均为 true，body 从安装 package 加载；没有建立 Agent 或模型 turn。
4. `dsh plugin add` 当前 tarball 把 dependency 从 0.0.9 切换到 0.1.0；随后官方 `plugin update` 报告
   already up to date。重启 profile 后 registry 仍恰好发现一个当前 Adapter。
5. `dsh plugin remove` 后 dependency 与 Bundle list 均无 Adapter；重启同一 probe 后 Skill 列表为 `[]`，
   `get('project-orrery')` 返回空。
6. 两个版本 tarball 与 pnpm store 位于 profile discovery 之外，可通过重新 `add` 恢复；fixture 作者
   `AGENTS.md` SHA-256 始终为
   `66ce61b9f504988bcc5d37c00c2dd0a4d389a3884aa6537c612ddff52417f6a0`。

主结果位于 `D:\orrery-stage-ab-dsh-stage-a-007\result.json`。

## 仓库收尾验证

- `python -X utf8 -m unittest discover -s tests -v`：74 项中 72 passed、2 expected skips。
- `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`：
  PASS，`Authority status: integrated candidate`。
- 静态 docsite 使用绝对输入／输出路径构建到
  `D:\orrery-docsite-claude-deepseek-stage-ab-20260821-003\index.html`：PASS；未修改 `docs/_site/index.html`。
- Markdown 本地链接：256 份文件、552 个链接、0 missing；`git diff --check`：PASS。

## 被拒绝的前置运行

- 隔离 npm install 因 rc.8 大型依赖图持续解析、未生成 binary 而被精确停止；未完成目录保留，随后
  改用官方 CLI 要求的 pnpm 在新目录成功安装。
- `dsh-lifecycle-001`／`002` 证明 rc.8 的 Windows `shell:true` pnpm 转发不能正确处理含空格 tarball
  路径／`%20` file URI；有效运行因此使用 D 盘无空格 fixture 根，未降低验证内容。
- `003` 和 `004` 虽完成 Adapter 生命周期，却因未正确设置官方变量 `DSH_AGENTS_HOME` 而同时列出
  真实 `C:\Users\1\.agents\skills` 的 Skill metadata。它们未写用户目录、未读取凭据、未调用模型，
  但按 discovery 污染废弃；`005` 是修正后的首个干净 PASS，最终 manifest 写入后又以 `006` 对最终
  Adapter 重跑通过；Stage B evidence manifest 写入后又以 `007` 对最终 Adapter 完整重跑，只有 `007`
  作为当前主证据。

## 结论与 Stage B 门

Stage A 已证明真实 DSH Skill registry discovery、body load、profile Bundle composition、升级、移除后重新
发现 0 项、作者文件保留和 CLI 失败关闭。它没有创建 Agent turn，因而没有证明显式／隐式 Skill 调用、
CLI 路由或模型对失败路径的解释。

`verified` 门未通过，manifest 的 `verified` 保持空数组。Stage B 若获明确授权，才可配置隔离 profile
所需真实凭据并执行最少 headless turn；不得复制用户 `.dsh` 凭据、写真实 profile 或把 Stage A discovery
冒充模型调用。
