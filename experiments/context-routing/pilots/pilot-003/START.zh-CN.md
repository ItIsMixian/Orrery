# Project Orrery context-routing pilot 003：操作说明

pilot 003 不再只测试一个低风险 README 修改。它使用三项历史任务，每项各运行 A／B／C：

| 任务 | 类型 | 目的 |
|---|---|---|
| `PO-CR-006` | 中等风险、多文件文档 | 检查双语入口和跨文件语义一致性 |
| `PO-CR-010` | 高风险、跨模块实现 | 检查 HTTP 层与 LLM 配置层的依赖定位 |
| `PO-CR-011` | 高风险、安全实现 | 检查凭据、项目配置、原子写入与 Git 忽略边界 |

本轮仍是研究实验，不会自动形成 ADR 或修改发布版 Skill。

## 推荐：一条命令自动运行

自动运行器会准备九个隔离仓库、按每项任务并行启动 A／B／C、保存 Codex JSONL 与标准错误、记录操作者时间、独立采集受跟踪及未跟踪产品变更、执行操作者侧安全验收、封存并生成比较摘要。正常情况下不再需要手工新建九个任务、复制 Prompt 或逐次调用 `Start`／`Finish`。

### 一次性前置条件

PowerShell 必须能够直接调用**独立安装的 Codex CLI**：

```powershell
codex --version
```

Codex 桌面应用内部附带的可执行文件不一定允许由 PowerShell 启动；它不能替代上述检查。自动运行器不会安装 CLI，也不会在 `-DryRun` 中调用模型。

Codex CLI `0.147.0` 的自动运行使用 `--approve-for-me` 隐含的 `workspace-write` 沙箱，并以
`workspace-write; approval=automatic-review` 记录在实验档案中。不要把它改回放在 `exec`
之后的 `--ask-for-approval never`：该版本不接受该参数位置，而且 `approval=never` 会把需要
审批的 PowerShell 命令直接拒绝。

### 先做零模型预检，再正式运行

在 Project Orrery 源仓库执行。第一次先用一个尚不存在的输出目录运行 `-DryRun`：

```powershell
Set-Location -LiteralPath "D:\coding warehouse\project-orrery"

powershell -NoProfile -ExecutionPolicy Bypass `
  -File ".\experiments\context-routing\pilots\pilot-003\run_pilot_003.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Model "<九组共同使用的模型>" `
  -ReasoningEffort "<九组共同使用的 reasoning effort>" `
  -MaxParallel 3 `
  -DryRun
```

`-DryRun` 只检查 CLI 版本、生成和验证实验装置，不发送 Prompt，也不产生模型 token。预检通过后，保持所有执行设置不变，在同一输出目录续跑：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File ".\experiments\context-routing\pilots\pilot-003\run_pilot_003.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Model "<九组共同使用的模型>" `
  -ReasoningEffort "<九组共同使用的 reasoning effort>" `
  -MaxParallel 3 `
  -Resume
```

也可以对一个尚不存在的输出目录省略 `-DryRun` 和 `-Resume`，直接正式运行。`-MaxParallel 3` 只让同一任务的 A／B／C 同时执行；三项任务仍按顺序推进，避免一次启动九个 Agent。

需要做确认性子实验时，必须把选择写进 Harness，而不是准备九组后任意少跑。下面的例子只准备 `PO-CR-010/011` 的 B/C 四组；相同参数必须同时用于预检和 `-Resume`：

```powershell
& ".\experiments\context-routing\pilots\pilot-003\run_pilot_003.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003-bc-confirmatory" `
  -Model "gpt-5.6-terra" `
  -ReasoningEffort "medium" `
  -MaxParallel 2 `
  -TaskId @("PO-CR-010", "PO-CR-011") `
  -Variant @("B", "C") `
  -DryRun
```

所选 task/variant 矩阵会进入 checksummed `execution-profile.json` 与 `pilot-manifest.json`；恢复时改变选择会被拒绝。

### 关机或中断后

原样重跑正式命令并保留 `-Resume`。运行器会跳过已经完成的组；对关机时仍处于运行态的组标记 `contaminated`，且**绝不自动重试**，以免把第二次尝试伪装成第一次基准结果。剩余未启动组可以继续完成。已经封存的结果再次 `-Resume` 只会复核摘要，不会重复调用 Agent。

返回码：

- `0`：九组干净完成并通过验证；
- `1`：准备、封存或独立验证失败；
- `2`：流程完成但存在污染／不完整比较，或因 `-StopOnFailure` 提前停止。

主要证据位于：

```text
<OutputRoot>/_operator/
├─ automation-state.json
├─ automation-profile.json
├─ operator-run-log.json
├─ security-acceptance.py
├─ runs/<RunKey>/events.jsonl
├─ runs/<RunKey>/stderr.log
├─ runs/<RunKey>/final-message.txt
├─ runs/<RunKey>/product-changes.json
├─ automation-summary.json
└─ comparison.md
```

`product-changes.json` 由 Harness 通过 `git diff HEAD` 与 `git ls-files --others --exclude-standard` 的并集生成，记录路径、受跟踪状态、大小和 SHA-256；因此新建但尚未 `git add` 的产品文件也会进入允许路径检查。JSONL 能独立保存 Codex 暴露的命令、工具与用量事件，但它仍不能证明“模型具体看到了文件中的哪些字节”；比较摘要会保留这一证据边界。

## 手动备用流程

只有在独立 CLI 不可用、需要人为澄清，或需要复核自动化装置本身时，才使用下面的逐任务流程。

## 1. 先记录统一执行配置并生成九个隔离仓库

在 Project Orrery 源仓库运行。把尖括号内容替换为三组任务实际共同使用的设置；不要写猜测值：

```powershell
Set-Location -LiteralPath "D:\coding warehouse\project-orrery"

powershell -NoProfile -ExecutionPolicy Bypass `
  -File ".\experiments\context-routing\pilots\pilot-003\prepare_pilot.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Model "<相同模型>" `
  -ReasoningEffort "<相同 reasoning effort>" `
  -PermissionProfile "<相同权限配置>" `
  -Harness "Codex desktop" `
  -NetworkPolicy "disabled" `
  -TimeBudgetMinutes 30
```

`OutputRoot` 必须尚不存在，并位于源仓库之外。准备器会生成：

```text
pilot-003/
├─ _operator/
│  ├─ execution-profile.json
│  ├─ operator-run-log.json
│  ├─ pilot-manifest.json
│  ├─ agent-receipt.schema.json
│  └─ PROMPT-PO-CR-*-*.zh-CN.md
├─ PO-CR-006-A/ ... PO-CR-006-C/
├─ PO-CR-010-A/ ... PO-CR-010-C/
└─ PO-CR-011-A/ ... PO-CR-011-C/
```

Prompt、执行档案、回执 schema 与 Harness overlay 都有 SHA-256。先验证准备结果：

```powershell
python ".\experiments\context-routing\pilots\pilot-003\validate_pilot.py" `
  --output-root "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  --prepared-only
```

只有看到 `pilot-003 prepared apparatus OK` 才开始任务。

## 2. 每次启动任务时由操作者计时并复制 Prompt

不要从现有任务分叉。按同一任务的 A／B／C 为一组，分别建立全新 Codex 任务，并把工作目录设为对应隔离仓库。

每次发送前运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "D:\coding warehouse\project-orrery\experiments\context-routing\pilots\pilot-003\record_operator_run.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Action Start `
  -RunKey "PO-CR-006-A" `
  -CopyPrompt
```

该命令会记录操作者侧开始时间并把对应完整 Prompt 放入剪贴板。随后在匹配的全新任务中直接粘贴发送。把 `RunKey` 依次替换为：

```text
PO-CR-006-A  PO-CR-006-B  PO-CR-006-C
PO-CR-010-A  PO-CR-010-B  PO-CR-010-C
PO-CR-011-A  PO-CR-011-B  PO-CR-011-C
```

建议先同时完成 `PO-CR-006` 三组，再做 `010`，最后做 `011`。同一任务的 A／B／C 必须使用相同模型、reasoning、权限、联网状态和时间预算。

## 3. 澄清、污染与结束

若某一组提出必须回答的澄清问题，不要只回复这一组。先把统一答案写入三个变体的操作者日志：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "D:\coding warehouse\project-orrery\experiments\context-routing\pilots\pilot-003\record_operator_run.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Action Intervention `
  -TaskId "PO-CR-010" `
  -Message "<发送给三个变体的相同答案>"
```

再把同一句回复发送给该任务的 A／B／C。若没有澄清，不需要运行这一步。

若 Agent 返回 `RUN CONTAMINATED`，记录后停止该组：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "D:\coding warehouse\project-orrery\experiments\context-routing\pilots\pilot-003\record_operator_run.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Action Contaminate `
  -RunKey "PO-CR-010-A" `
  -Message "<脱敏污染来源>"
```

正常结束时，Agent 应已创建被本地 Git exclude 忽略的 `.benchmark/agent-receipt.json`。记录操作者结束时间：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "D:\coding warehouse\project-orrery\experiments\context-routing\pilots\pilot-003\record_operator_run.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Action Finish `
  -RunKey "PO-CR-006-A"
```

`Finish` 会拒绝没有 Agent 回执的运行。

## 4. 封存并独立复核

九组均完成或明确污染后，确认没有遗漏操作者干预并封存日志：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "D:\coding warehouse\project-orrery\experiments\context-routing\pilots\pilot-003\record_operator_run.ps1" `
  -OutputRoot "D:\coding warehouse\project-orrery-benchmark\pilot-003" `
  -Action Seal `
  -ConfirmSameExecutionSettings
```

随后运行完整复核：

```powershell
python "D:\coding warehouse\project-orrery\experiments\context-routing\pilots\pilot-003\validate_pilot.py" `
  --output-root "D:\coding warehouse\project-orrery-benchmark\pilot-003"
```

验证器会独立复核 Prompt、执行档案、overlay、仓库 HEAD、完整产品变更集、路径边界和验证命令；高风险任务还会从操作者侧检查环境变量 `hasKey`、凭据写入失败顺序、明文泄漏、异常脱敏与原子替换。自动流程要求存在带哈希的 `product-changes.json`；手动流程缺少该冻结产物时只进行现场重算并给出警告。Agent 回执中的读取事件仍然只是自述，验证通过也不等于已经获得 Harness 级访问审计。

完成后不要提交、推送、合并或删除九个隔离仓库。直接回到主评估任务说“pilot-003 已完成”，评估者可以从共享文件系统读取全部证据。
