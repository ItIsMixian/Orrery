# Authority Model restore

Date: 2026-08-21

Status: Candidate checkpoint

## 范围

验证 ADR-0011 显式 Authority Model 迁移的恢复路径。该路径恢复
`migrate-authority-model` 产生的精确 project manifest 备份；它不修改作者文档、release 默认值、
installer、managed Observatory、Harness JSON Adapter 或公开 v0.2.0 资产。

## 安全合约

- `--backup` 必须是当前项目下
  `.project-orrery-backup/authority-model/<generated>/.project-orrery.json` 的相对路径。绝对路径、
  `..`、文件 symlink、目录形状漂移和解析后逃出备份根的路径均失败关闭。
- 当前 manifest 必须选择本工具支持的模型；备份只能是 `legacy-unversioned` 或同一受支持模型，且
  `manifest_format`／`document_schema` 均兼容。移除 `authority_model_version` 后，当前与备份对象必须
  完全相同，避免旧备份或其他项目备份回滚无关元数据。
- dry-run receipt 绑定当前 manifest SHA-256、规范化项目内备份路径和备份 SHA-256。current 或 backup
  任一字节变化，都必须重新预演；不匹配在任何撤销备份或写入前失败。
- apply 先把当前 manifest 原始 bytes 保存到
  `.project-orrery-backup/authority-model-restore/<UTC>-<hash>/`，再以同目录临时文件、flush 和
  `os.replace` 原子恢复备份 bytes。no-op 不写入；注入 replace failure 时当前 bytes 不变、撤销备份
  保留且临时文件清理。
- Core restore planner 与 CLI 仍是 Candidate 内部边界；CLI 候选版本为 0.1.4，Harness JSON Adapter
  不开放迁移或恢复命令。

## 验证

```powershell
python -X utf8 -m unittest tests.test_authority_model_restore -v
python -X utf8 -m unittest tests.test_authority_model_restore tests.test_authority_model_migration tests.test_authority_model_compatibility tests.test_authority_cli_compatibility -v
python -X utf8 -m unittest discover -s tests
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out "$env:TEMP\project-orrery-authority-model-restore-20260821.html"
```

restore 专项 17/17；定向 migration／restore／compatibility 49/49。全仓 168 项中 166 通过、2 项动态
依赖按设计跳过。integrated validator 通过并报告 model 1 supported／strict evaluation eligible；静态站
生成 1053 KB，包含 11 个 ADR、6 个 State、12 个 Plan 与 75 份 docs。PowerShell 扫描 264 份
Markdown、576 个本地链接／图片，0 missing target；`git diff --check` 通过，仅保留既有候选组件文件的
LF→CRLF 工作树提示。

## 未验证／未实现

- 没有在 self-host 项目上执行真实 restore；测试只操作临时隔离项目。
- 没有向 Harness JSON Adapter 暴露命令，也没有 release／installer／new scaffold projection。
- 没有把 Core planner 导出为稳定公共 API，没有 consumer production switch 或新发布。
