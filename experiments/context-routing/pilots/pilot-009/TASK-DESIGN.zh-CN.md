# Pilot 009 Scope Acquisition 任务与采纳门

Status: corrected apparatus ready; formal rerun authorized after Pilot 008 stopped

Pilot 009 保留 Pilot 008 的任务目标、完整冻结说明、P/S treatment、模型配置和采纳门，只修正首对
正式样本已经证明的共同装置问题：迁移 Oracle 不再暗中要求任务未规定的固定索引名或 State／Progress
词形；Prompt 明确禁止发现和读取用户目录中的已安装 Skill，并关闭 app-server `skill_search`。Pilot 008
的封存样本不并入本 Pilot。

## 脱敏来源

Fixture 不复制 Marglo 的代码、数据库或文档，只提炼 ADR-0002 已接受的三类模式：反馈状态闭环、
SQLite 幂等迁移和实现／State／Handoff 不一致。所有数据均为人工生成，路径和身份为虚构值。

## 三项任务

1. `PO-CR-033`（product code / high）：区分自动过期和用户 snooze，覆盖首次／重复转换、既有截止时间和 snooze 抢占边界。
2. `PO-CR-034`（migration / high）：把人工 v1 SQLite 升级到 v2，保留旧行、验证复合索引、重复启动幂等，并对未来版本失败关闭。
3. `PO-CR-035`（documentation governance / medium）：从实现和真实测试发现数纠正 State、PROGRESS、HANDOFF，同时保留无关工作流事实。

两项 high-risk 任务以可运行代码和独立行为测试为主要验收；第三项只评价事实链克制。

## Scope Lock 成本门

- correctness：S 3/3，且不得低于 P；不得出现 P-only high-risk success。
- provenance：六个 run 的 app-server 事件、写前 usage、代理证明、changed paths 和 R0 manifest 全部有效。
- scope lock：S/P 聚合写前 input ≤ 0.85；任一 high-risk pair ≤ 1.05；写前 non-cached input ≤ 1.00。
- evidence：S/P 写前唯一正文 bytes ≤ 1.05，并分别报告读取路径、顺序和权威层。
- total guard：S/P 完整 input、output、Agent seconds、代理正文均 ≤ 1.05。
- scope：首次写入必须位于允许产品路径；不得漏读必要约束、修改受保护路径或用文档掩盖代码失败。

任何共同装置缺陷都会阻止采纳解释。准备完成和 dry-run 只证明静态装置，不证明 S 有收益；Smoke 002
只解除当前 runtime 的 ordering 不确定性，正式样本还必须逐 run 通过全事件审计、代理 proof、Scope
analyzer、独立 Oracle 和 R0 manifest 验证。
