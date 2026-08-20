# Validation：平台中立 Phase 2 Codex Adapter 仓库实现

Date: 2026-08-19
Scope: ADR-0004 Implementation Plan Phase 2 的仓库内产物、打包与生命周期检查点；不含真实 Codex runtime E2E
Environment: Microsoft Windows NT 10.0.26200.0，Python 3.13.5，工作树基于 `96eee5a`

## 预期行为

1. Codex Adapter 是可独立归档的薄 Skill，只包含 Codex 发现／调用提示、manifest、安装说明和平台安装器。
2. Adapter 通过 manifest 声明 Core API／CLI 依赖，不复制 canonical 模板、schema、兼容规则、State、ADR 或 Validation。
3. 独立归档具有固定条目顺序、时间和权限元数据，并生成对应 SHA-256。
4. 平台安装器支持无写入 dry-run；未知既有目录失败关闭；已识别 Adapter 或 v0.2 旧 Skill 先完整备份再升级。
5. 升级备份和卸载回收目录位于 skills discovery 根之外，避免旧 `SKILL.md` 被重复发现；操作不删除或修改目标项目文件。
6. 没有真实 runtime 证据时，Adapter 与 runtime 状态都保持 `experimental`，verified／evidence 数组为空。

## 合约依据

- 本地决策与设计：`docs/decisions/0004-platform-neutral-core-and-adapter-boundaries.md`、
  `docs/design/platform-neutral-core-and-adapter-architecture.md`。
- Codex Skill 发现格式参考 OpenAI 的 [Build skills](https://developers.openai.com/codex/skills/) 文档：
  目录以 `SKILL.md` 为必需入口，`agents/openai.yaml` 为可选 UI 元数据；用户级发现位置包括
  `$HOME/.agents/skills`。该外部文档只决定 Codex 薄层格式，不决定 Orrery 的项目事实。

## 检查与结果

| 检查 | 结果 |
|---|---|
| `python -X utf8 -m unittest tests.test_codex_adapter -v` | PASS — 5/5 |
| 薄层内容与版本投影 | PASS — 5 个声明文件；无 `assets/`、`references/`、release manifest 或 runtime verified 声明 |
| 两次独立打包与 SHA-256 | PASS — ZIP 字节一致，checksum 匹配，解压后的安装器可从归档安装 |
| 新装／相同版本 keep／本地差异升级 | PASS — dry-run 无写入；升级前完整备份，源文件恢复一致 |
| 未知目录与旧 Skill 迁移 | PASS — 未知目录 exit 2 且保留；v0.2 manifest 只有显式 `--upgrade` 才备份迁移 |
| 卸载 | PASS — dry-run 无写入；实际操作移入 discovery 根外的带时间戳回收目录并输出恢复路径 |
| `python -X utf8 -m unittest tests.test_project_orrery tests.test_codex_adapter -v` | PASS — 18 passed，2 个动态依赖测试按设计跳过 |
| integrated structure、定向本地链接、尾随空白与 `git diff --check` | PASS |

## 边界与已知缺口

- 本轮没有写入、升级或卸载 `C:\Users\1\.codex\skills`、`C:\Users\1\.agents\skills`
  或其他真实用户级 Codex 目录；生命周期测试全部位于临时目录。
- 没有运行真实 Codex Adapter 发现、显式／隐式调用、CLI 缺失失败、更新或卸载后的重新发现；
  因此 Phase 2 后两项清单未完成，状态不能改为 `verified`。
- Adapter 依赖未发布的 `project-orrery-cli >=0.1.0,<0.2.0`；它可以独立归档，但目前不是
  完整公共安装路径，也没有进入 `.github/workflows/release.yml`。
- v0.2.0 旧 Skill、tag、ZIP 和 checksum 未修改；旧 Skill 的迁移测试只使用最小临时 fixture。
- 未运行 context-routing、Pilot 001–008、模型调用或第二平台测试；不产生任何第二平台兼容声明。

## Result

PASS（仓库实现检查点）：Phase 2 的独立薄 Adapter、归档器和可恢复生命周期边界已实现并通过
隔离测试。Phase 2 整体仍未完成；下一步必须先获明确授权，再安装独立 CLI／Adapter 并在
真实 Codex runtime 上记录版本化 E2E 证据。
