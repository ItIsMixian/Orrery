# Authority Model migration apply

Date: 2026-08-21

Status: Candidate checkpoint

## 范围

验证 ADR-0011 的显式语义迁移 apply 路径。该路径只改变兼容 project manifest 的
`authority_model_version`，不改变 `authority_status`、`manifest_format`、`document_schema`、作者文档、
release 默认值、installer 或 managed Observatory。

## 安全合约

- dry-run 产生的 receipt 绑定源 manifest SHA-256、目标模型和规范化提议 manifest SHA-256；
  apply 必须显式提供 receipt，不能只凭一个旧 source hash 换目标执行。
- 过期／不匹配 receipt、非法目标、unsupported 模型、正交版本不兼容和不存在的离散迁移路径
  全部在任何备份或写入前失败关闭。
- apply 先将原始 manifest bytes 写入
  `.project-orrery-backup/authority-model/<UTC>-<hash>/` 并 flush，再在项目根同目录写临时文件，
  flush 后使用 `os.replace` 原子替换。
- no-op 不创建备份、不重写 manifest。注入 replace failure 时原 manifest bytes 不变、精确备份保留、
  临时文件被清理。
- Core planner/materializer 仍是内部 API；CLI 候选版本为 0.1.3。Harness JSON Adapter 尚未开放该命令。

## 验证

```powershell
python -X utf8 -m unittest tests.test_authority_model_migration -v
python -X utf8 -m unittest discover -s tests
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out "$env:TEMP\project-orrery-authority-migration-apply-20260821.html"
```

migration 专项 20/20，连同 compatibility／CLI capability 的定向组合 32/32。全仓 151 项中
149 通过、2 项动态依赖按设计跳过。integrated validator 通过，Authority Model 1 报告
supported／strict evaluation eligible；静态站生成 1044 KB，包含 11 个 ADR、6 个 State、12 个
Plan 与 74 份 docs。PowerShell 扫描 263 份 Markdown、574 个本地链接／图片，0 missing target；
`git diff --check` 通过，仅报告两个既有候选组件文件的 LF→CRLF 工作树提示。

## 未验证／未实现

- 没有公开 restore command；当前恢复能力来自逐字节备份与失败前原文件保持。
- 没有真实修改 self-host manifest；self-host 已是 model 1，真实命令只应得到 no-op。
- 没有 release／installer／new scaffold projection，也没有独立 CLI 发布。
- 没有 Harness JSON Adapter schema／白名单、managed Observatory 或 consumer production switch。
