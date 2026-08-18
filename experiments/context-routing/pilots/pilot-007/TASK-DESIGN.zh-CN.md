# Pilot 007 任务与采纳门

Status: frozen before model execution

## 三个新任务

1. `PO-CR-027`（high / release）：让 release zip 在行尾、mtime 和可执行位不同的工作副本中 byte-for-byte 一致。
2. `PO-CR-028`（high / research security）：建立只输出聚合元数据、不会泄露 Provider 正文、源码、绝对路径或 secret 的 R1 导出器。
3. `PO-CR-029`（medium / public docs）：为 Windows 用户提供不降低 ExecutionPolicy 的中英文 Codex CLI 安装说明，并把 npm prefix/cache 放到非系统盘示例。

三项任务都来自当前真实 backlog，但不与 PO-CR-001..026 重复。独立 Oracle 在 baseline 上必须失败，在正例 fixture 上必须通过。

## 决策门

- correctness：B 3/3，且不得低于 P；两项 high risk 不允许 P-only success。
- provenance：六个 run 的 JSONL、代理证明、原始 manifest 和 changed paths 都有效。
- cost：B/P 的 input ≤ 1.10、output ≤ 1.15、Agent seconds ≤ 1.15。
- benefit：B 代理正文总字节至少下降 15%，或独立补回 P 遗漏的必要依赖且仍满足成本门。
- protocol：B 的 Manifest、Expansion、Summary 顺序有效；P 不输出这些协议文字；两者都不创建 receipt 文件。

任何 apparatus error 都使对应任务对污染；若错误来自共同装置，Pilot 007 整轮不支持决策。
