# Validation：平台中立 Phase 0 发布基线

Date: 2026-08-19
Scope: ADR-0004 Implementation Plan 的 Phase 0；不包含 Core 抽取、Adapter 分包或 runtime 兼容声明

## 预期行为

1. v0.2.0 已发布 Skill 的 36 个归档路径、8 个 managed tools、发布 checksum、CLI 入口和 manifest 必需字段有固定基线。
2. installer、validator、update checker 的既有人类可读输出由回归测试保护；当前新增工具可以扩展清单，但不能删除既有契约。
3. 新安装目标仍使用 canonical `AGENTS.md`，入口标题从 Codex 专属名称改为中立的 `Agent state index`。
4. 中英文 README 必须区分可直接运行的 CLI、`experimental` Codex 发布集成和只有目标定位的其他平台。
5. Phase 0 不改变 v0.2.0 发布归档结构，不宣称存在独立 Core／CLI 包或 `verified` runtime。

## 固化基线

- 机器可读 fixture：[platform_neutral_phase0_baseline.json](../../tests/fixtures/platform_neutral_phase0_baseline.json)
- 发布版本／tag：`0.2.0`／`v0.2.0`
- 已发布 ZIP SHA-256：`13b71c8be0af16b5bb51edcab2c979a14625b773bad1b901fd449c20797b6394`
- tag 内 Skill 文件：36；已发布 managed tools：8
- 现有 CLI 入口：installer、validator、update checker
- 兼容策略：基线字段和路径是当前实现的必需子集，允许未发布工作树增加工具，不把新增内容倒写成 v0.2.0 事实。

## 检查与结果

| 检查 | 结果 |
|---|---|
| `git ls-tree -r --name-only v0.2.0 skills/project-orrery` 与 fixture 清单复核 | PASS — tag 内 36 个 Skill 路径已固化 |
| 两项 Phase 0 定向回归 | PASS — 2/2 |
| `python -m unittest tests.test_project_orrery -v` | PASS — 9 passed，2 个动态依赖测试按设计跳过 |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated` | PASS — scaffold valid；authority 为 integrated candidate |
| 新增／修改文档本地链接、尾随空白与 `git diff --check` | PASS |

## 边界与已知缺口

- fixture 的 checksum 对应既有 GitHub v0.2.0 发布资产；本阶段没有重建、覆盖或重新发布该 ZIP。
- 测试保护人类可读输出和既有字段／路径存在性，不把当前 CLI 冻结为最终机器 API；统一 JSON schema 与退出码属于 Phase 3。
- 当前 CLI 脚本仍物理位于 Codex Skill 发布目录，Core／CLI 尚未独立打包。
- Codex 项保持 `experimental`，因为本阶段没有真实 runtime 的发现、调用、更新和卸载 E2E；其他平台保持 `target`。
- 未运行 context-routing 测试、Pilot 001–008 或任何模型调用。

## Result

PASS：Phase 0 已完成。v0.2.0 契约获得可执行基线，模板入口与公开支持状态完成中立化；
发布结构、平台兼容声明和 runtime 验证范围没有被扩大。
