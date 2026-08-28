# ADR-0015: Orrery 品牌与兼容标识契约

Status: Proposed

Date: 2026-08-28

Amends: [ADR-0001](0001-project-orrery-self-hosting.md),
[ADR-0004](0004-platform-neutral-core-and-adapter-boundaries.md),
[ADR-0011](0011-authority-model-version-and-compatibility.md)

Research input: [current-main rename audit](../library/2026-08-28-orrery-rename-migration-audit.zh-CN.md)

## Context

公开仓库、根 README 和 project manifest title 已使用 `Orrery`，但发布 Skill、CLI、Python packages/imports、
Adapter IDs、schema、credential/backup namespaces 与历史证据仍广泛使用 `project-orrery`。这不是一个可用
全仓替换解决的文案问题：相同字符串同时承担产品品牌、机器 identity、协议 identity 和历史事实。

PyPI 已由无关项目占用 `orrery` distribution 与顶层 import。v0.2.0 的 tag、Release、ZIP、checksum 和
manifest 已公开且必须保持原样。已有用户、旧命令和 mixed-version project 需要先兼容，再决定是否切换
默认入口。

## Proposed decision

若本 ADR 被接受：

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
6. CLI 可在 R4 后增加 user-facing `orrery` alias，但只能在 PATH/third-party collision 检查、显式安装或
   宿主 capability 允许时启用。旧命令与 alias 必须产生相同 exit code、JSON envelope、写入计划和结果；
   warning 不得污染 JSON stdout。
7. Skill/plugin/adapter 的 display name 可变为 Orrery；canonical ID 继续为现值，直到各宿主分别证明 alias
   discovery、upgrade、uninstall 与 mixed-install 行为。一个平台的证据不外推到另一个平台。
8. GitHub current authority 为 `ItIsMixian/Orrery`；旧仓库 redirect 是兼容 alias。当前 README、badges、
   install links 使用新 URL；历史 release notes、Actions runs 和旧 URL 引用不重写。
9. v0.2.0 annotated tag、commit、Release、ZIP/checksum、frozen release manifest/bridge/baseline 以及所有历史
   ADR、Validation、Snapshot、Pilot/benchmark fixture 永久按原字节或原事实保留。
10. 本地 repository directory、Codex Saved Project 和 Codex data root 不属于 package identity。只有产品
    brand/compat rollout 验收后，才可在独立维护窗口按“关闭/保存 worktree → 重命名 root → 重新登记 Saved
    Project/重建 worktree → 验证 → 另行迁移 Codex 数据到 D 盘”的顺序处理；本 ADR 不授权这些操作。
11. 没有新增匿名 telemetry。兼容判断只使用本地、显式、无 secret 的 capability/receipt；不得同步
    prompt、answer、transcript、源码正文、未 push diff、凭据或 keyring 内容，也不得以“没有报告”推断
    用户已迁移。

## Authority by surface

| Surface | Migration authority under this proposal |
|---|---|
| README/中英文文案、Observatory title、repository description | R3 brand-only allowlist；当前内容和历史引用分开 |
| GitHub owner/repo、redirect、badges、install links | GitHub current state + maintainer remote authority；本地 docs 不能改远端 |
| Skill/plugin/adapter ID | host-specific R4 contract；ID 先保持，display name 可迁移 |
| CLI entrypoint | R4 alias capability；R5 才可评审默认入口，旧入口覆盖 0.3.x |
| Python distribution/import | 保持 `project-orrery-*`／`project_orrery_*`；本 ADR 不迁移 |
| project manifest/env/config | `.project-orrery.json` 与 `ORRERY_*` 保持；config names 不因品牌复制 |
| keyring/cache/backup | 既有 namespace 是恢复权威；默认不搬移、不复制 secret |
| schema/contract/hash/Authority/Workstream IDs | 各 versioned producer/reader；brand-only 禁止修改 |
| v0.2.0/frozen evidence | immutable tag/assets/checksum/fixture/hash；只能新增说明 |
| local directory/Saved Project/Codex data | 本机维护计划与用户确认；后于产品 rollout，彼此分离 |

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
- 本提案若被接受，Approved Design 才能从 candidate 状态提升为 Approved，R3 才能开始实现。

## Remaining review choices

以下选择不阻塞品牌原则，但需维护者在对应阶段确认：

- R4 的 `orrery` CLI alias 是显式 opt-in shim、独立 launcher，还是仅在无 PATH collision 的安装器投影；
- 各宿主是否支持单 canonical discovery + thin alias，若不支持则只迁移 display name；
- 首个新 release 是否改变新资产 display filename，或继续使用稳定 `project-orrery-*` archive name；
- 产品 rollout 后本地 root/Saved Project 维护窗口的确切时间。

## Mapping

- Approved Design candidate: [Orrery rename and compatibility contract](../design/orrery-rename-and-compatibility-contract.md)
- Implementation Plan: [R3–R5 phased plan](../implementation/plans/2026-08-28-orrery-rename-and-compatibility.md)
- Validation: [R2 decision contract](../validation/2026-08-28-orrery-rename-decision-contract.md)
