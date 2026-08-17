# Variant A：固定阅读链

在第一次产品写入前，依次全文阅读：

1. `README.md`
2. `skills/project-orrery/SKILL.md`
3. `skills/project-orrery/references/architecture.md`
4. `skills/project-orrery/references/migration-contract.md`
5. `skills/project-orrery/assets/project-template/AGENTS.md`
6. `skills/project-orrery/scripts/install_project_orrery.py`
7. `skills/project-orrery/scripts/validate_installation.py`

完成固定链后，可以在当前隔离仓库内按普通方式枚举、搜索和读取完成具体任务所需的文件。无需输出 Context Manifest；回执中的 `prewrite.context_manifest` 与 `prewrite.selected_evidence` 必须为 `null`。共同协议中的外部上下文禁令始终有效。

