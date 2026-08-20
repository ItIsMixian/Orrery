# Pilot 009：P/S Scope Acquisition 对照

Date: 2026-08-19
Model: `gpt-5.6-terra` / medium
Baseline: `fd3fab27ca9da25aab4dbb781d11d69f3a1270b8`
Status: apparatus valid and cost gate passed; quality gate failed; S not adopted

## 结论

Pilot 009 首次得到一轮装置完整的写前 Scope 数据：六个 run 的 app-server 事件、读取代理 proof、首次
产品写入边界、正式验证和 R0 manifest 全部有效，没有仓库外读取或隐藏重试。相对线性入口 P，任务优先
入口 S 的聚合写前 input 为 `82.74%`，写前 non-cached input 为 `87.11%`，唯一代理正文为 `81.26%`；
总 input、output 和 Agent 时间也分别为 `90.59%`、`94.53%`、`95.95%`。所有预设成本门都通过。

但 S 不采纳。冻结 Oracle 原始报告为 P/S 均 0/3；只读语义复核确认其中两项是英文词形假阴性，真实任务
质量为 P/S 均 2/3。迁移任务的行为和数据约束通过，但两侧 PROGRESS 都没有完整记录未来版本写前拒绝，
是共同的真实事实链遗漏。冻结质量门要求 S 3/3，且不得出现质量回退；因此自动证据门和复核后的质量门
都不通过。当前结果支持“任务优先入口值得继续测试”，不支持把它写入发布 Skill 或模板。

## 聚合结果

| Variant | Apparatus | 语义复核质量 | 写前 input | 写前 non-cached | 写前 slice bytes | 完整 input | Output | Agent seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P | 3/3 | 2/3 | 540,105 | 63,689 | 13,831 | 1,083,673 | 8,908 | 703.863 |
| S | 3/3 | 2/3 | 446,904 | 55,480 | 11,239 | 981,705 | 8,421 | 675.391 |
| S/P | — | equal | 0.8274 | 0.8711 | 0.8126 | 0.9059 | 0.9453 | 0.9595 |

三项 P/S Prompt 逐项等长，聚合均为 36,129 bytes；两组共享相同 9,109-byte 冻结 Skill。S 的入口文件
本身比 P 长，因此观测到的写前 input 下降来自后续定位链，而不是缩短 Prompt。

## 按任务结果

| Task | P 写前 input | S 写前 input | S/P | 只读质量判断 |
|---|---:|---:|---:|---|
| PO-CR-033 feedback bug | 162,906 | 115,632 | 0.7098 | P/S 行为、测试、State 与 PROGRESS 均满足；Oracle 只识别 `auto-expiry`，没有识别等价的 `automatic expiry`，两侧改判 pass |
| PO-CR-034 SQLite migration | 163,743 | 140,158 | 0.8560 | P/S 迁移行为、旧行保留、幂等、未来版本写前拒绝和索引列顺序均通过；两侧 PROGRESS 未完整记录未来版本拒绝，维持 fail |
| PO-CR-035 fact alignment | 213,456 | 191,114 | 0.8953 | P/S 都准确写明 schema v1、4 tests 和自动过期风险；Oracle 暗中要求固定短语 `auto-expiry cooldown bug`，两侧改判 pass |

S 在三项任务中分别少读 2、1、1 个写前正文路径。033 的 P 额外读取 HANDOFF 与 principles；034 的 P
额外读取 HANDOFF 与 principles，而 S 按模块映射读取迁移 ADR；035 的 P 额外读取 principles。路径数和
代理 bytes 不能证明理解，但与 exact usage 的同方向变化一致。

## 装置结论

- 6/6 access audit、Scope analysis、formal validation 和协议检查通过。
- 首次写入均只覆盖任务允许路径；所有运行最终仓库测试通过。
- 6/6 R0 manifest 验证有效：P run 各 85 files，S run 各 88 files。
- `features.skill_search=false` 加上 Prompt 边界消除了 Pilot 008 的外部已安装 Skill 读取；完整事件 validator
  仍独立拒绝任何直接外部读取。
- Harness 成功直接统计首次允许产品写入前累计 input；Agent 没有生成 Manifest、Receipt、Selected
  Evidence、reason code 或实验访问总结。

## Oracle 与下一轮任务设计

本轮再次证明：行为 Oracle 可以稳定，但用少量 substring 验收自然语言事实会把同义改写误判为失败。
下一轮采用 [真实开发任务与 Oracle v0.2](../designs/real-development-task-oracle-v0.2.zh-CN.md)：把行为、数据／
安全、范围、结构化 State 和叙事一致性分开报告；只有任务或仓库公开规定的标识符才允许 exact match；
PROGRESS／HANDOFF 使用矛盾检测和同义改写 controls，不再要求隐藏词形。新任务还应加入跨模块小功能或
安全删除场景，避免长期只复用 feedback／migration 两类实现。

## 原始证据与不可改写边界

仓库外原始根：
`D:\coding warehouse\project-orrery-benchmark\pilot-009-scope-20260819-142948`

- `pilot-summary.json`: `2e1519ba7083390ada396833c5317ea8b8fd4da204f5bc6fb7c77f35196c1498`
- `pilot-summary.md`: `5abed0c9f1e2ce179f89baffdcb3cdbe96fa2848a7edaee216cc1989711968e3`
- `PO-CR-033-P`: `2eb6a0f5e3d68fe52745e40983a851c9de5e372d68a4ddfc6a9f6e1563cebacc`
- `PO-CR-033-S`: `d09f389ce958afc7e1982ecba5b62c052de0ad0e44452fbc9465a75691b15688`
- `PO-CR-034-P`: `36e1ab25b13f885cfa8b002699102034731390836fb15ade87bc4c6d5ffac4e0`
- `PO-CR-034-S`: `24e93d7a5d66329f0fc26bcc0c3fe0711f87a958a6743866903f42a78d7b4fbf`
- `PO-CR-035-P`: `aa676b90d7d122f8a8ce6a98ccc435fa5fb707edbe2df59d24679cfb136694c2`
- `PO-CR-035-S`: `564c5197aa5ce6f0e12a0ad84ac3c89eb025d258d0e6c476e7888d92f73c61f0`

原始仓库、事件和 manifest 不进入 Git、不回写、不重分类。本文是 R2 解释层，不改变冻结 Oracle 的
0/3 原始报告；任何装置或任务修正必须使用新 Pilot 和新输出根。

## 适用边界

样本只有三项、单一模型和单一 runtime，且写前 input 以 cached token 为主；结果不能外推到所有 Agent、
仓库或缓存状态。它证明当前装置能可靠测量并给出一个一致方向信号，不证明模型真正理解了返回正文，也
不证明 S 对正确性无风险。
