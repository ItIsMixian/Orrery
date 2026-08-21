# Authority Model migration dry-run

Date: 2026-08-21

Status: Candidate checkpoint

## 范围

验证 ADR-0011 解锁后的第一个迁移检查点：平台中立 Core 只生成迁移计划，neutral CLI 只在显式
`--dry-run` 下报告计划。此记录不验证 migration apply、installer 默认值、release manifest、Harness
Adapter 命令、managed Observatory 或任何发布资产。

## 实现边界

- `project_orrery_core.authority_migration` 是内部、纯计算 planner，没有文件 I/O，也未从 Core 顶层导出。
- 兼容的 `manifest_format = 1`／`document_schema = 1` 上，legacy-unversioned → model 1 只预测写入 `.project-orrery.json` 的
  `authority_model_version`；`manifest_format` 与 `document_schema` 原样保留。
- 已选择 model 1 返回 no-op；invalid／unsupported source、unsupported target 和缺少显式跨版本路径
  均失败关闭。
- CLI 命令为 `migrate-authority-model --to 1 --dry-run`。省略 `--dry-run` 会以非法请求退出；
  当前源码没有 apply 分支。
- CLI 从同一份 manifest bytes 解析计划并计算 SHA-256，报告 `writes_performed: false`、预测变更、
  备份范围与后续所需动作。
- self-host 项目实际 dry-run 返回 `already-selected`／no-op；命令前后 manifest SHA-256 一致。
- 候选 CLI 版本由 0.1.1 提升到 0.1.2；Harness JSON Adapter v1 的三命令白名单和 0.1.1
  minimum 不变，因此它尚不暴露迁移命令。

## 定向验证

```powershell
python -X utf8 -m unittest tests.test_authority_model_migration -v
python -X utf8 -m unittest tests.test_authority_model_compatibility tests.test_authority_cli_compatibility -v
python -X utf8 -m unittest tests.test_project_orrery tests.test_harness_json_adapter -v
```

结果：migration 专项 13/13；compatibility／CLI capability 12/12；产品与 Harness 专项 20 项通过，
2 项动态依赖按设计跳过。

## 全仓与文档验证

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
python -X utf8 scripts/docsite/build_docsite.py --out "$env:TEMP\project-orrery-authority-migration-20260821.html"
```

最终回归为 144 项中 142 通过、2 项动态依赖按设计跳过。integrated validator 通过，Authority
Model 1 报告 supported／strict evaluation eligible；静态站生成 1037 KB，包含 11 个 ADR、6 个
State、12 个 Plan 与 73 份 docs。PowerShell 扫描 262 份 Markdown、572 个本地链接／图片，
0 missing target；`git diff --check` 通过，仅报告两个既有候选组件文件的 LF→CRLF 工作树提示。

## 未验证／未实现

- 没有 apply、自动备份、恢复或真实 manifest 写入。
- 没有把 model 1 投影进新 scaffold、release manifest 或发布 Skill。
- 没有把新命令加入 Harness JSON Adapter request schema／白名单。
- 没有稳定 public Core API、production consumer switch 或新发布兼容声明。
