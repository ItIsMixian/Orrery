# Pilot 004：B/H holdout 结果（gpt-5.6-terra / medium）

> 日期：2026-08-18  
> 原始输出：`D:\coding warehouse\project-orrery-benchmark\pilot-004-bh-terra-medium-r1`  
> 结论：H 暂不进入 ADR／产品采纳；需要先降低 token 与运行时间成本

## 运行完整性

- 固定任务顺序：`PO-CR-014 → PO-CR-012 → PO-CR-013`，种子 `4004`。
- 每项 B/H 成对并行，任务之间顺序执行；六个 run 都只启动 1 次。
- 6/6 Agent 进程正常结束，6/6 回执存在，0 contaminated，0 operator intervention。
- 所有目标仓库均来自提交态基线 `ec0ec4a213275338ce34fe7219c5ad692bbcad81`，单提交、无远端；operator Oracle 未进入目标仓库。
- H 在 Oracle 完成前冻结；SHA-256：`2181e00c69ed9026cd3164479d6294eaa3a8b51c143eb56599462fc52b78be1d`。

## Oracle apparatus failure 与修正复核

冻结的 v1 Oracle 自测通过，但正式 validator 返回 `1`。只读审计确认四组失败均为 Oracle 假阳性：

1. v1 只在 `fetch_latest` 函数体内寻找原子替换，因候选把事务抽到 `write_cached` 而误报；
2. v1 使用 `ast.walk` 的广度顺序判断 `try/except` 调用先后，误报 provider reload；
3. v1 直接测试通用 `_safe_error`，没有验证 DELETE handler 实际返回的常量脱敏边界。

原始 `_operator/holdout-acceptance.py`、validator 输出和 exit code 保持不变。新增只读复核 Oracle `holdout_acceptance_v2.py`，改用词法调用顺序、跨 helper 的动态缓存失败注入，以及 DELETE 公开 handler 边界。v2 自测通过，SHA-256：`170e29e56d35e09dd160c52dd6b8f986492b4fce1543fb1dddd9f92e1aa7678b`。

v2 结果：

| 任务 | B | H |
|---|---|---|
| PO-CR-012 凭据撤销 | PASS | PASS |
| PO-CR-013 更新缓存 | PASS | PASS |
| PO-CR-014 共享兼容门 | PASS | PASS |

因此任务正确性为 B 3/3、H 3/3；v1 正式 validator 结果只能标记为 apparatus failure，不能解释为候选失败。

## 路由行为

- `PO-CR-014`：H 初始只读 installer/checker，随后在写入前以 `dependency-found`、`acceptance-gap`、`missing-authority` 扩张到 validator、测试和 release manifest；全部消费者被召回。
- `PO-CR-012`：H 初始两文件闭合，仅对 `serve.py` 的更大片段声明一次 `security-boundary` 扩张；B 自报 7 次正文读取，H 为 3 次。
- `PO-CR-013`：B/H 都只修改 checker；B 自报 3 次正文读取，H 为 2 次；没有仓库级无理由扩张。
- 回执 schema、写入范围、写入前扩张时机和产品 diff 均通过 formal validator；唯一 formal failure 来自 v1 Oracle。

## 成本

| 任务 | B input | H input | H 相对 B |
|---|---:|---:|---:|
| PO-CR-014 | 383,529 | 803,879 | +109.6% |
| PO-CR-012 | 375,039 | 512,729 | +36.7% |
| PO-CR-013 | 322,825 | 272,777 | -15.5% |
| **合计** | **1,081,393** | **1,589,385** | **+47.0%** |

H 平均 Agent 时间为 376.5 秒，B 为 326.7 秒；H 慢约 15.2%。H 的自报正文读取更少（平均 3.33 vs 5.33），但并未转化成较低的总输入 token。

## 决策门

H 满足：

- 正确性不低于 B，且无 high-risk 回归；
- 0 schema failure，0 未声明正文扩张；
- 014 必要依赖召回，013 保持局部；
- Oracle 正反 fixture 自测与 v2 行为复核通过。

H 不满足：

- 三项总 input token 不高于 B；实际高 47.0%；
- 012 高 36.7%，没有独立证明必须付出该增量；
- 014 虽有必要扩张收益，但 input 高 109.6%，远超可接受的解释成本。

所以当前结论不是“B 比 H 更正确”，而是：**H 的检索行为更克制、正确性持平，但推理／上下文组织成本过高，尚不能替代 B。** 下一轮应先拆解 H 的 token 来源（长 Manifest、Selected Evidence、重复验证或缓存命中统计口径），设计瘦身版 H2，再做更小的确认实验。
