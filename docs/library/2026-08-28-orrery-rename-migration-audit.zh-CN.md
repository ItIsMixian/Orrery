# Orrery 命名面审计与兼容迁移输入（current-main refresh）

Date: 2026-08-28

Status: Non-authoritative Library audit; no rename implementation authorization

Current baseline: `main@2037cab7a46ae048147115c3c317f8d542a8cee9`（clean）

Provenance: R1 `codex/r1-orrery-rename-migration-audit@f991befb3854bc7603b85e243c24cc4b2fb7a0e9`，
其审计基线为旧 W5E `692d19b3945f0a950548399d67eadd76b4587688`。

## 1. 权威边界与刷新方法

R1 只存在于未合入 `main` 的研究分支，不能通过 cherry-pick 覆盖当前 Library 索引，也不能把旧 W5E
State 或计数写成当前事实。本稿采用加法迁移：保留 R1 的四类处置法（保留／迁移／alias／禁止改写）、
历史边界与风险分类，同时在精确 current-main baseline 上重新机械统计，并把差异明确归因于后续进入
main 的 W7／CI 源码、schema、测试和文档。

统计只读取 `git ls-files` 返回的 tracked paths；内容计数使用 `git grep -I -F -o` 的大小写敏感 exact
substring。standalone `Orrery` 使用 `(?<!Project )(?<!Project-)Orrery`，因此有意与其他模式独立、可能重叠。
冻结根为 `docs/decisions`、`docs/validation`、`docs/snapshots`、`experiments/context-routing`。未读取
Git-private session 正文、API Key、keyring、cache、生成站点或仓库外 benchmark 原始数据。

## 2. current-main 计数与 R1 差异

| 模式 | current-main 次数／文件 | R1 次数／文件 | 差异 |
|---|---:|---:|---:|
| tracked paths | 655 | 622 | +33 paths |
| `Project Orrery` | 399／223 | 394／218 | +5／+5 |
| `Project-Orrery` | 2／2 | 2／2 | 0／0 |
| `project-orrery` | 1,372／298 | 1,322／288 | +50／+10 |
| `project_orrery` | 462／147 | 426／140 | +36／+7 |
| standalone `Orrery` | 242／79 | 222／69 | +20／+10 |
| `ORRERY_` | 194／67 | 185／61 | +9／+6 |
| `.project-orrery` | 171／75 | 169／74 | +2／+1 |

路径计数也增长：含 `project-orrery` 的 tracked paths 从 116 增至 122，新增六条全部位于
`packages/`；含 `project_orrery` 的路径从 74 增至 80，新增六条也全部位于 `packages/`。当前分布为：

| 路径模式 | 总数 | 分布 |
|---|---:|---|
| `project-orrery` | 122 | packages 79；skills 40；adapters 1；docs 1；根 manifest 1 |
| `project_orrery` | 80 | packages 75；skills 4；tests 1 |
| exact `.project-orrery.json` | 1 | repository root |

冻结根没有随品牌文案同步而被批量改写：

| 模式 | current-main 次数／文件 | R1 次数／文件 | 差异 |
|---|---:|---:|---:|
| `Project Orrery` | 163／92 | 163／92 | 0／0 |
| `project-orrery` | 528／136 | 525／134 | +3／+2 |
| `project_orrery` | 104／53 | 103／52 | +1／+1 |

新增旧技术标识主要来自 W7 relation contract，而非品牌倒退：含旧 slug 的 JSON schema `$id` 从 R1
的 12 个增至 14 个，新增 `workstream-relations-v1` 与 `workstream-relation-execution-v1`。current-main
还机械枚举到 72 个 `contract_type` 出现、22 个文件、46 个 distinct values。它们是 versioned protocol
identity，不能被 brand-only replace。

复现命令：

```powershell
git ls-files
git grep -I -F -o -- 'Project Orrery' 2037cab7 --
git grep -I -F -o -- 'project-orrery' 2037cab7 --
git grep -I -F -o -- 'project_orrery' 2037cab7 --
git grep -I -P -o -- '(?<!Project )(?<!Project-)Orrery' 2037cab7 --
git grep -I -E '"\$id"[[:space:]]*:[[:space:]]*"[^"]*project-orrery' 2037cab7 -- '*.json'
```

## 3. 当前品牌、技术标识、协议和冻结面

### 3.1 已经是 Orrery 的活跃品牌事实

- 根 README 中英文标题、公开仓库名和当前 clone/install 链接已使用 `Orrery`。
- `.project-orrery.json` 明确分离 `title: Orrery` 与 `name: project-orrery`。
- 环境变量和 HTTP headers 已使用 `ORRERY_*`／`X-Orrery-*`。
- Git remote 为 `https://github.com/ItIsMixian/Orrery.git`；旧仓库 URL 当前返回 301 redirect。

仍待 brand-only 收口的活跃展示面包括 self-host Observatory 默认标题
`Project Orrery · Documentation`、Broker/CLI/Adapter display text、Skill 正文和部分当前 State／Design／Plan
叙述。目标项目模板的 project-title Python replacement token 不是品牌漂移，必须继续按目标项目 title 投影。

### 3.2 当前稳定技术标识

- Skill/plugin name 与目录：`project-orrery`、`skills/project-orrery/`；
- CLI distribution/entrypoints：`project-orrery-cli`、`project-orrery` 及十二个
  `project-orrery-*` entrypoints；
- Python distributions/imports：`project-orrery-{core,cli,observatory}` 与
  `project_orrery_{core,cli,observatory}`；
- Adapter distributions/IDs：`project-orrery-{codex,claude-code,deepseek-harness,harness-json}-adapter`；
- project manifest：`.project-orrery.json`、`name=project-orrery`；
- backup/credential namespaces：`.project-orrery-backup`、Adapter backup/trash、
  `project-orrery/provider`、`project-orrery-broker/provider` 等既有槽位。

这些标识已有代码、fixture、runtime evidence 或用户安装依赖。品牌改名不授权改变它们。

### 3.3 稳定协议标识

14 个旧 slug schema `$id`、现有 `contract_type`、receipt/fingerprint/hash domain、Authority Model 1、
Core/CLI/Adapter API version、Workstream/review/closure/receipt IDs 与 Git-private `orrery/` 控制路径分别拥有
独立兼容权威。内容相同而仅换品牌不能创建 v2；未来真实语义变化若引入 v2，仍必须保留 v1 reader。

### 3.4 历史不可改写面

以下名称是历史事实：ADR、Validation、Snapshot、DEVLOG 历史段、完成/停止的 Plan、Pilot/benchmark
fixture、v0.2.0 tag/Release/ZIP/checksum/release notes、冻结 manifest/bridge/baseline、旧 CLI golden、已签发
receipt/hash/Workstream ID。新文档可以加当前名称说明，但不得重写原证据或重算旧 hash。

## 4. 外部只读核验（2026-08-28）

- [GitHub repository](https://github.com/ItIsMixian/Orrery) 返回 `ItIsMixian/Orrery`、default branch
  `main`，description 为 “A portable skill for traceable Markdown project documentation, local observability,
  and safe migration.”。
- 旧 `https://github.com/yw9299-stack/project-orrery` 返回 301 到当前仓库；它是外部 redirect alias，不是
  修改历史内容的授权。
- [v0.2.0 Release](https://github.com/ItIsMixian/Orrery/releases/tag/v0.2.0) 仍关联 tag commit
  `20fc95be7b9616fa2de90fc1ffe33b35d5c3f3fd`。API 列出的自定义资产仍为
  `project-orrery-v0.2.0.zip`（82,550 bytes，SHA-256
  `13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`）和
  `project-orrery-v0.2.0.sha256`（92 bytes）。GitHub 页面另将自动 source archives 计入四项 Assets；
  这些均保持历史名称。
- [PyPI `orrery`](https://pypi.org/project/orrery/) 当前为无关的 Code Choreography 项目 0.1.1，summary
  为 “A framework for supporting MVC and observer patterns in Python”，并提供 `import orrery`。因此本项目
  不得发布 `orrery` distribution 或占用顶层 `orrery` import。

以上核验均为匿名只读 GET/HEAD；没有修改 GitHub、PyPI、tag、Release、assets 或 repository settings。

## 5. 四类处置结论

| 类别 | 当前范围 |
|---|---|
| 保留 | `project-orrery*` distribution/Skill/Adapter IDs；`project_orrery_*` imports；`.project-orrery.json`；`ORRERY_*`；既有 config/keyring/cache/backup namespaces；v1 protocol readers |
| 迁移 | 活跃 README/中英文文案、self-host Observatory/Broker/Adapter display text、未来 workflow display label、未来 release display metadata |
| alias | 旧 GitHub redirect；未来经冲突和宿主验证的 CLI/Skill user-facing route；future manifest 的 versioned alias capability |
| 禁止改写 | v0.2.0 与冻结 manifest/assets/checksum；历史 ADR/Validation/Snapshot/Plan/DEVLOG/Pilot；schema `$id`、contract_type、hash domain、Authority Model 和既有 Workstream/receipt IDs |

## 6. 决策输入与停止条件

R2 应把品牌、stable ID、完整 0.3.x 兼容窗口、最早 0.4.0 removal review、历史冻结面和 PyPI 冲突写入
ADR；Design 再定义 alias resolver、warning、rollback、brownfield mixed-state 和 privacy；Plan 拆成 R3
Brand-only、R4 compatible aliases、R5 optional package/CLI transition。任何阶段遇到 v0.2 hash drift、两个
完整 Skill 同时被发现、JSON stdout/exit drift、old/new config divergence、真实 secret 复制、缺少 rollback
或 exact-SHA 双平台门未通过时必须停止。

本审计仍是 Library 输入，不证明 ADR 已接受、Design 已批准或任何改名实现已完成。
