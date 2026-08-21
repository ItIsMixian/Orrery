# Authority Model release/project projection

Date: 2026-08-21

Status: Candidate checkpoint

## 范围

验证 ADR-0011 从内部 compatibility/migration 能力走向 future release 与 project manifest 投影时的
最小契约，同时避免把当前源码中的 v0.2.0 release manifest 改写成从未发布过的能力。

## 合约

- future release 若声明 Authority Model，必须同时提供正整数顶层默认值与离散 `supported` 数组；默认值
  必须位于支持集，非法／重复／缺失配对均失败关闭。
- project manifest v1 schema 允许但不要求正整数 `authority_model_version`；这不提升
  `manifest_format` 或 `document_schema`。
- 只有没有既有 manifest 内容的新项目，才从 future release contract 选择默认模型；已有 manifest 的
  字段存在／缺失状态均保留。普通 scaffold 和 `--upgrade-tools` 不能代替显式语义迁移。
- `skills/project-orrery/release-manifest.json` 与 Core bundled `release-v0.2.0.json` 继续保持模型字段缺失，
  从而保留 tag／zip／checksum 与 v0.2.0 历史事实。Candidate fixture 不构成实际 release manifest。

## 验证

```powershell
python -X utf8 -m unittest tests.test_authority_model_projection -v
python -X utf8 -m unittest tests.test_authority_model_projection tests.test_authority_model_compatibility tests.test_authority_model_migration tests.test_authority_model_restore tests.test_project_orrery -v
python -X utf8 -m unittest discover -s tests
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out "$env:TEMP\project-orrery-authority-model-projection-20260821.html"
```

projection 专项 8/8；与 compatibility、migration/restore 和产品测试组合为 69 项，其中 67 通过、
2 项动态依赖按设计跳过。全仓 176 项中 174 通过、2 项动态依赖按设计跳过。integrated validator
通过并报告 model 1 supported／strict evaluation eligible；静态站生成 1063 KB，包含 11 个 ADR、
6 个 State、12 个 Plan 与 76 份 docs。PowerShell 扫描 265 份 Markdown、578 个本地链接／图片，
0 missing target；`git diff --check` 通过，仅保留既有候选组件文件的 LF→CRLF 工作树提示。

## 未实现／未验证

- 没有创建或修改实际下一 release manifest、版本号、tag、zip、checksum、GitHub Release 或安装说明。
- standalone v0.2 fallback 仍不会为新项目选择 model 1；只有未来带有有效声明的 release contract 才会。
- 没有把 migration/restore 暴露给 Harness JSON Adapter，没有 managed Observatory production switch。
