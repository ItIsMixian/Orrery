# Pilot 008 Scope Acquisition 重构验证

Date: 2026-08-19
Result: deterministic apparatus ready; first real app-server smoke later contaminated; ordering still pending

> 后续状态：修正运行时后，单独授权的 [Smoke 002](2026-08-19-app-server-scope-ordering-smoke-002.md)
> 已在当前 CLI 上验证 usage／首次写入顺序。下文保留重构完成时和 Smoke 001 后的历史快照。

## 权威与实验边界

- ADR-0005 已接受：主成本指标是首次允许产品写入前累计 input，Agent 不生成实验 Manifest 或回执。
- ADR-0002 的三项真实开发 fixture、独立 Oracle、脱敏边界和验收层级保持不变。
- 旧 Skill Entry Router R 没有运行模型，已退出 Pilot 008 treatment；其准备记录保留为历史。
- 新对照 P/S 使用同一份冻结完整 Skill、任务、模型、推理强度、Oracle 和代理。唯一 treatment 是目标
  仓库的线性 `AGENTS.md` 与任务优先 `AGENTS.md`。

## 静态对照

| 项目 | P | S |
|---|---:|---:|
| 共同 Skill bytes | 9,109 | 9,109 |
| Agent 入口 bytes | 598 | 1,638 |
| PO-CR-030 Prompt bytes | 11,708 | 11,708 |
| PO-CR-031 Prompt bytes | 11,705 | 11,705 |
| PO-CR-032 Prompt bytes | 11,666 | 11,666 |

Prompt 完全等长；S 的入口本身更长，但提供模块到 State／实现／测试的直接映射。实验要回答的是它能否
减少后续无关读取和累计写前 input，而不是把入口字节下降预设成结果。

## Harness 验证

- 新增 `analyze_scope_acquisition.py`，从 app-server `thread/tokenUsage/updated` 与首个
  `item/started:fileChange` 派生 Scope Lock 前累计 usage。
- 分析器要求同 thread／turn、累计 usage 单调、首次写入位于允许产品路径、写前代理 proof 有效，并
  分别报告写前 input、cached/non-cached input、output、唯一路径与唯一切片 bytes。
- 合成 self-test 通过 4 类场景：有效边界、非单调 usage 拒绝、越界首次写入拒绝、旧
  `codex exec` 整轮聚合 usage 拒绝。
- 读取代理新增 passive 模式：仍记录第三路径和范围扩大，但 Pilot 008 不要求 Agent 提供 reason code；
  历史 Pilot 默认行为保持不变。
- P/S overlay 均在真实外层／内层 Git 路径中 preflight；S 入口在运行仓库内形成独立 treatment commit，
  模型启动前工作树保持干净。
- `scope_usage_ordering_verified` 当前为 `false`。不带 `--dry-run` 的 Pilot 命令在创建输出根或调用模型前
  失败关闭。

## 复现结果

| 检查 | 结果 |
|---|---|
| `python -X utf8 experiments/context-routing/harness/analyze_scope_acquisition.py --self-test` | PASS，4 cases |
| Pilot 008 `--dry-run` | PASS；P/S、共享 Skill、入口 overlay、analyzer、fixture、Oracle 与 Harness 均进入控制哈希 |
| Pilot 008 formal-path guard | PASS；兼容性 smoke 前返回非零且没有模型调用 |
| `python -X utf8 -m unittest tests.test_context_routing_h2 -v` | PASS，17/17 |
| 默认全仓 | PASS，51 项中 49 passed + 2 expected skips |
| benchmark validator | PASS，24 项 corpus、6 份既有 run record |
| integrated structure + static build | PASS |
| Markdown 本地链接 | PASS，195 份 Markdown |
| `git diff --check` | PASS；仅有两份并行工作中既存 `requirements.txt` 的 LF→CRLF 提示 |

## 观测能力边界

- 重构时本机 `codex-cli 0.147.0` 生成的 app-server schema包含逐响应累计 usage 与 `fileChange` 生命周期字段；
  schema 存在不证明真实运行顺序。随后当前桌面包的 0.148.0-alpha.15 首次 smoke 因缺少同目录 code-mode
  host 而污染，详见 [Smoke 001](2026-08-19-app-server-scope-ordering-smoke-001.md)。
- 对既有 Pilot 007 `codex exec --json` 的只读事件审计显示：首次 file change 位于整轮中段，唯一 usage
  只在 `turn.completed` 出现。因此旧流不能精确分段，分析器会报告 `unavailable`。
- 未运行 app-server 模型 smoke，没有 Scope Lock token、R0、仓库外 Pilot 008 输出根或候选收益结论。
- 下一步必须先单独确认一次隔离兼容性 smoke。若 usage 更新不能可靠先于对应首次写入事件，项目只报告
  不可用，不用 Prompt bytes、代理 bytes 或最终 token 估算精确写前 input。
