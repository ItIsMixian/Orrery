# ADR-0015: Orrery 品牌与兼容标识契约

Status: Accepted

Date: 2026-08-28

Amends: [ADR-0001](0001-project-orrery-self-hosting.md), [ADR-0004](0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0011](0011-authority-model-version-and-compatibility.md)

Research input: [current-main rename audit](../library/2026-08-28-orrery-rename-migration-audit.zh-CN.md)

## Context

公开仓库、根 README 和 project manifest title 已使用 `Orrery`，但发布 Skill、CLI、Python packages/imports、
Adapter IDs、schema、credential/backup namespaces 与历史证据仍广泛使用 `project-orrery`。这不是一个可用
全仓替换解决的文案问题：相同字符串同时承担产品品牌、机器 identity、协议 identity 和历史事实。

PyPI 已由无关项目占用 `orrery` distribution 与顶层 import。v0.2.0 的 tag、Release、ZIP、checksum 和
manifest 已公开且必须保持原样。已有用户、旧命令和 mixed-version project 需要先兼容，再决定是否切换
默认入口。

## Decision

1. 面向人的当前产品品牌统一为 **Orrery**。自托管文档必须在首次出现时区分 current product brand、
   current technical identifier 和 historical name。
2. 品牌迁移不改变机器 identity。以下标识保持稳定且本 ADR 不弃用：
   - `.project-orrery.json` 与 `name=project-orrery`；
   - `project-orrery-{core,cli,observatory}` distributions 和 `project_orrery_*` imports；
   - 现有 Adapter distribution/ID、schema `$id`、`contract_type`、receipt/fingerprint/hash domain、Authority
     Model/API version、Workstream/review/closure/receipt IDs；
   - 现有 keyring/cache/backup/trash namespaces 和旧 backup reader。
3. 不发布名为 `orrery` 的 Python distribution，不引入顶层 `import orrery`。除非后续 ADR 证明 registry
   ownership、供应链安全、pickle/import identity 和 brownfield migration，不重命名 Python package/import。
4. `project-orrery` Skill、CLI 和 Adapter 用户入口至少在完整 0.3.x 系列保持可用。最早到 0.4.0 才能
   评审移除；版本号只是 review eligibility，不承诺移除。任何移除另需 ADR、usage/evidence review、
   rollback 和 release notes。
5. 路线固定为 `Brand-only → compatible identifiers/aliases → optional package/CLI transition → optional
   cleanup`。alias 必须路由到同一实现；一个宿主不得发现两个完整 Skill/Plugin 实现。
6. R4 的 user-facing `orrery` CLI alias 采用显式 opt-in、collision-checked 的 thin launcher，并路由到唯一
   canonical implementation；不得复制完整实现。旧命令与 alias 必须产生相同 exit code、JSON envelope、
   写入计划和结果；warning 不得污染 JSON stdout。
7. Skill/plugin/adapter 在各宿主的默认迁移只改变 display name，canonical ID 保持现值。只有宿主独立证明
   safe alias discovery、upgrade、uninstall 与 mixed-install 行为后，才可增加路由到同一 canonical
   implementation 的 thin alias；一个平台的证据不外推到另一个平台。
8. GitHub current authority 为 `ItIsMixian/Orrery`；旧仓库 redirect 是兼容 alias。当前 README、badges、
   install links 使用新 URL；历史 release notes、Actions runs 和旧 URL 引用不重写。
9. v0.2.0 annotated tag、commit、Release、ZIP/checksum、frozen release manifest/bridge/baseline 以及所有历史
   ADR、Validation、Snapshot、Pilot/benchmark fixture 永久按原字节或原事实保留。首个新的 Orrery Release
   继续使用稳定 `project-orrery-*` archive/asset filename，同时以 Orrery 作为品牌显示；未来改变 asset
   display filename 必须另行评审。
10. 本地 repository directory、Codex Saved Project 和 Codex data root 不属于 package identity。R3 Brand-only
    完成、exact Candidate SHA 通过规定门并进入 `main` 后，即可在独立本机维护 Workstream 中依次 freeze
    clean SHA、保存并关闭或重建 worktree、把 primary root 从 `project-orrery` 改为 `Orrery`、更新 Codex
    Saved Project、验证并保留旧路径回滚。随后才能另开 Codex application-data D 盘迁移。该本机维护不依赖
    R4/R5 公共兼容周期；本 ADR 本身不授权执行上述文件系统、Codex 设置或数据迁移操作。
11. 没有新增匿名 telemetry。兼容判断只使用本地、显式、无 secret 的 capability/receipt；不得同步
    prompt、answer、transcript、源码正文、未 push diff、凭据或 keyring 内容，也不得以“没有报告”推断
    用户已迁移。

## Authority by surface

| Surface | Migration authority under this proposal |
|---|---|
| README/中英文文案、Observatory title、repository description | R3 brand-only allowlist；当前内容和历史引用分开 |
| GitHub owner/repo、redirect、badges、install links | GitHub current state + maintainer remote authority；本地 docs 不能改远端 |
| Skill/plugin/adapter ID | 默认仅迁移 display name；host-specific 证据通过后才增加指向同一实现的 thin alias |
| CLI entrypoint | R4 显式 opt-in、collision-checked thin launcher；R5 才可评审默认入口，旧入口覆盖 0.3.x |
| Python distribution/import | 保持 `project-orrery-*`／`project_orrery_*`；本 ADR 不迁移 |
| project manifest/env/config | `.project-orrery.json` 与 `ORRERY_*` 保持；config names 不因品牌复制 |
| keyring/cache/backup | 既有 namespace 是恢复权威；默认不搬移、不复制 secret |
| schema/contract/hash/Authority/Workstream IDs | 各 versioned producer/reader；brand-only 禁止修改 |
| v0.2.0/frozen evidence | immutable tag/assets/checksum/fixture/hash；首个新 Release 仍用 `project-orrery-*` asset filename |
| local directory/Saved Project/Codex data | R3 exact-SHA 进入 main 后的独立本机维护；不依赖 R4/R5，Codex data 另立任务 |

## Reasons

- 品牌统一改善人的入口，但机器 identity 的稳定性和历史可验证性价值更高。
- 保留唯一 Python namespace 避免依赖混淆、typosquatting 与第三方 import 覆盖。
- alias-first 允许已安装用户、旧命令和 mixed-version project 渐进迁移，而不复制业务实现。
- 分阶段 Candidate-first promotion 让每个 alias、Adapter 和 release surface 有独立 rollback。

## Consequences

- 全仓 `Project Orrery`／`project-orrery` 计数不会归零，也不应成为验收目标。
- 新代码和文档必须按 display/technical/protocol/history 分类，而不是按字符串机械替换。
- R3 只改活跃品牌面；R4 才能增加 versioned aliases；R5 可以选择继续永久保留技术 ID。
- 0.4.0 之前不得删除旧入口；到达 0.4.0 也不构成删除授权。
- 本 ADR 已由维护者接受，配套 Design 已 Approved；R3 的决策／设计门已解除，但接受决定不等于 R3 已实现。

## Remaining review choices

以下选择不阻塞 R3，但只能在对应阶段凭新增证据确认：

- R3 进入 main 后，本机 root/Saved Project 维护窗口的具体时间、操作人和备份落点；
- R5 是否把 `orrery` 从显式 opt-in launcher 提升为 preferred/default CLI；证据不足时保持现状；
- 首个新 Release 之后是否改变未来 archive/asset display filename；需要独立发布兼容评审；
- 每个宿主是否有足够证据增加 thin alias；没有安全 discovery/upgrade/uninstall 证据的宿主只改 display name。

## Mapping

- Approved Design: [Orrery rename and compatibility contract](../design/orrery-rename-and-compatibility-contract.md)
- Implementation Plan: [R3–R5 phased plan](../implementation/plans/2026-08-28-orrery-rename-and-compatibility.md)
- Validation: [R2 decision contract](../validation/2026-08-28-orrery-rename-decision-contract.md)
