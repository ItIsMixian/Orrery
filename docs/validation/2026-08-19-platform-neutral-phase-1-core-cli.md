# Validation：平台中立 Phase 1 Core／CLI 抽取

Date: 2026-08-19
Scope: ADR-0004 Implementation Plan Phase 1；未发布 Core／CLI／Observatory 源码边界和 v0.2 Skill 兼容入口

## 预期行为

1. Core 独立持有 schema、manifest 构造、兼容判定和 canonical 作者模板，不依赖 Codex runtime。
2. CLI 通过 Core 与 Observatory 完成 scaffold、validate、check-update；旧 Skill 三个路径只是兼容 wrapper。
3. Observatory 有独立版本和 managed-tool 清单；根自托管源码的标题通过显式投影生成目标模板。
4. 新 CLI 与旧路径在隔离目标上产生相同人类输出、manifest 和文件；既有作者文件不覆盖。
5. 单独打包的 Skill 不依赖仓库 `packages/`，能通过冻结 fallback 安装并验证。

## 组件基线

- Core／CLI／Observatory：`0.1.0`，状态 `unreleased`
- Core API：1
- 旧 Skill wrapper：保留至 `0.3.x`，最早 `0.4.0` 移除
- Observatory managed tools：9
- 发布 bridge：继续读取不可变 v0.2.0 契约，不修改既有 tag、ZIP 或 checksum

## 检查与结果

| 检查 | 结果 |
|---|---|
| Phase 1 三项定向回归 | PASS — 3/3 |
| 新 CLI 与旧 Skill 路径 scaffold／validate／check-update 等价 | PASS — 输出、manifest 与安装文件逐项一致 |
| 既有作者 `AGENTS.md` 保留 | PASS — 报告 `SKIP`，内容未覆盖 |
| 当前 Skill ZIP 解压后的 legacy fallback | PASS — 在仓库 packages 外完成安装与验证 |
| `python -m unittest tests.test_project_orrery -v` | PASS — 12 passed，2 个动态依赖测试按设计跳过 |
| integrated structure、定向本地链接、尾随空白与 `git diff --check` | PASS |

## 边界与已知缺口

- 三个 `pyproject.toml` 目前定义源码包边界，但尚未发布 wheel／归档，也未建立多组件 Release workflow。
- Observatory 的大文件实现源码仍位于根 `scripts/docsite/`；组件包拥有版本、清单和模板投影，Skill 目录仍保存兼容投影。测试防止两条输出路径漂移。
- 机器可读统一 JSON schema 与稳定退出码属于 Phase 3，当前继续保护人类输出。
- 未实施 Codex Adapter 安装器、更新、卸载或真实 runtime E2E；Codex 继续为 `experimental`。
- 未运行 context-routing、Pilot 001–008 或任何模型调用，也未声明第二平台兼容。

## Result

PASS：Phase 1 源码边界与兼容迁移入口已实现并通过等价验证。结果只说明工作树实现成立，
不表示组件已经发布、Codex runtime 已验证或第二平台已适配。
