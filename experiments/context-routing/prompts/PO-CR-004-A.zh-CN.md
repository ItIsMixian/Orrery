# PO-CR-004-A 新对话首条消息

你正在一个专门用于 Project Orrery 基准实验的隔离 Git 仓库中。请完成下面的任务，不要只给建议。

## 共同任务

改善这个仓库的公开 `README.md`，让第一次接触 Project Orrery 的用户能够从 GitHub 获得一条清晰、可复制的 Codex Skill 安装指令。保持现有文档风格和已有的安全采纳边界；不要修改 Skill、脚本、测试或其他产品行为。

完成后运行适合本次文档修改的验证。不要提交、推送或访问互联网，也不要查看当前 HEAD 以外的 Git 历史、分支、标签、reflog 或对象。

## A：固定阅读链

修改前依次全文阅读：

1. `README.md`
2. `skills/project-orrery/SKILL.md`
3. `skills/project-orrery/references/architecture.md`
4. `skills/project-orrery/references/migration-contract.md`
5. `skills/project-orrery/assets/project-template/AGENTS.md`
6. `skills/project-orrery/scripts/install_project_orrery.py`
7. `skills/project-orrery/scripts/validate_installation.py`

完成固定阅读链后，可以按普通方式搜索仓库并完成任务。

## 最终回复格式

先说明结果和验证，然后附上：

```text
BENCHMARK REPORT
variant: A
enumerated_paths_or_patterns:
search_queries:
content_reads: 逐项写路径以及 full/partial
writes:
commands:
scope_expansions:
validation:
uncertainty:
```

访问清单属于 Agent 自述，不要声称它是 Harness 独立审计结果。
