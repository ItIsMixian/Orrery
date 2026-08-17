# PO-CR-004 pilot 002：共同任务包

你正在一个用于上下文路由基准实验的隔离 Git 仓库中。请完成任务，不要只给建议。

## 运行前检查

本轮只允许使用：

1. 这条用户消息本身；
2. 当前隔离仓库工作树中的文件；
3. 本任务明确允许的本地时间与验证命令。

隔离仓库含有由实验准备器生成并提交的 `.codex/config.toml`。它只用于让宿主禁用会污染对比的外部 Skill，是三个变体共有的测试夹具，不是历史产品文件。宿主可以把它作为配置加载，但 Agent 不得通过文件工具读取其正文；路径枚举中看到它不算污染，也不计入任务证据。

不要读取或调用全局安装的 Skill、系统文档、其他工作区文件、Git remote、`.git/config`、环境变量中的仓库信息或互联网内容。如果宿主或更高优先级规则迫使你读取了任何当前隔离仓库之外的文档内容，请在写入前停止，并只回复：

```text
RUN CONTAMINATED
external_context: <脱敏来源>
reason: repository-only 条件无法满足
```

不要尝试在已经发生外部读取后继续实验。

确认未发生外部内容读取后，先输出：

```text
EXTERNAL CONTEXT PREFLIGHT
status: clean
```

然后运行 `Get-Date -Format o`，把结果保留为 `started_at`。这一步不计入仓库内容读取。

## 共同任务

只修改公开的 `README.md`，让第一次接触这个仓库的用户获得一条清晰、可复制的 Codex Skill GitHub 安装指令。保持现有文档风格与安全采纳边界；不要修改 Skill、脚本、测试或其他产品行为。

本轮共同提供的规范事实如下，不需要自行发现或验证：

- 规范 Skill 地址是 `https://github.com/yw9299-stack/project-orrery/tree/main/skills/project-orrery`；
- 安装入口使用 `$skill-installer`；
- 安装 Skill 不等于目标项目已经搭建、迁移或正式采纳其文档权威链。

禁止联网，也不要查看当前 HEAD 以外的 Git 历史、分支、标签、reflog 或对象。

## 什么算“读取内容”

- `Get-Content`、打开文件、`rg`/`Select-String` 输出匹配正文、脚本打印文件片段，都算对应文件的全文或局部内容读取。
- `rg --files`、只返回文件名的 `rg -l` 和纯目录名枚举只算路径枚举，不算正文读取。
- 一条搜索若返回多个文件的匹配正文，就对每个文件分别记一次局部内容读取。
- 上下文预算只约束第一次写入前的证据读取；写入后的 diff 和测试输出单独记为验证命令。

## 共同范围边界

- 写入范围固定为 `README.md`。
- 任何仓库文件内容读取都必须遵守对应 A／B／C 策略。
- 外部文档内容不允许通过范围扩展纳入；发生后整次运行标记为污染。
- `git config`、`git remote`、直接读取 `.git/**` 或查询等价元数据均不属于路径枚举，且本轮禁止。
- `.codex/config.toml` 是不可读取、不可修改的共同测试夹具，不能通过范围扩展纳入。
- 若向操作者提问，三个变体必须收到相同答案；在最终报告中逐项记录问题与回答。

## 共同验证

完成修改后运行相同验证：

```text
git status --short
git diff --check
git diff -- README.md
git diff --name-only
python -m unittest discover -s tests -v
```

随后再次运行 `Get-Date -Format o`，把结果保留为 `ended_at`。不要提交、推送或合并。

## 最终回复

先说明结果和验证，再附上以下自述。未知值写 `null`，不要写成 0，也不要把自述称为 Harness 证据。

```text
BENCHMARK REPORT
pilot_id: pilot-002
prompt_revision: po-cr-004-pilot-002-v1
variant: <A|B|C>
started_at:
ended_at:
external_context_preflight: clean | contaminated
context_manifest: <不适用时写 null>
selected_evidence: <不适用时写 null>
enumerated_paths_or_patterns:
search_queries:
content_reads: 逐项写仓库相对路径、full/partial；partial 必须写行号或查询范围
writes:
commands:
metadata_queries:
scope_expansions: 逐项写声明发生在读取前还是读取后
operator_interventions:
validation:
uncertainty:
evidence_note: Agent self-report; not an independent Harness audit
```
