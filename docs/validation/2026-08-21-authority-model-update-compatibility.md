# Authority Model update compatibility

Date: 2026-08-21

Status: Candidate checkpoint

## 范围

验证未发布 neutral CLI 0.1.5 的 `check-update` 能只读消费 ADR-0011 的 future-release 默认模型与
离散支持集，同时不改变 v0.2.0 历史行为、不写 target manifest，也不扩展 Harness JSON schema v1。

## 合约

- release 没有声明 Authority Model 时保持既有 project manifest／document schema／runtime 判断；v0.2.0
  target 不会因本检查点突然要求语义迁移。
- future release 同时声明默认模型与离散支持集时，显式受支持 target 可以直接更新；legacy、invalid、
  unknown／unsupported target 返回既有 `update_available_migration_required` 或
  `current_incompatible`，并通过 `reasons` 指向显式维护动作。
- 没有 `--target` 的 Skill-only 查询不制造项目状态，也不阻止兼容更新。
- malformed future release 在形成 compatibility claim 前失败关闭；更新检查始终不执行 migration、restore
  或任何 target 写入。
- JSON 继续使用 schema v1 的既有字段和退出码；本检查点没有修改 Harness request/response schema。

## 验证

```powershell
python -X utf8 -m unittest tests.test_authority_update_compatibility -v
python -X utf8 -m unittest tests.test_authority_update_compatibility tests.test_authority_model_projection tests.test_authority_model_compatibility tests.test_project_orrery -v
python -X utf8 -m unittest discover -s tests
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out "$env:TEMP\project-orrery-authority-update-20260821.html"
```

专项 8/8；与 projection、compatibility 和产品测试组合 40 项中 38 通过、2 项动态依赖按设计跳过。
全仓 184 项中 182 通过、2 项动态依赖按设计跳过。integrated validator 通过并报告 model 1
supported／strict evaluation eligible；静态站生成 1071 KB，包含 11 个 ADR、6 个 State、12 个 Plan
与 77 份 docs。PowerShell 扫描 266 份 Markdown、580 个本地链接／图片，0 missing target；
`git diff --check` 通过，仅保留候选组件文件的 LF→CRLF 工作树提示。

## 未实现／未验证

- 没有创建实际下一 release manifest、tag、zip、checksum 或 GitHub Release。
- 没有自动执行语义迁移；维护者仍需显式 dry-run、receipt-gated apply 和必要时 restore。
- 没有改变 v0.2 standalone fallback、managed Observatory 或 Harness 命令白名单。
