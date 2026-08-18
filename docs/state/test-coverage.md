# 测试覆盖 State

Updated: 2026-08-18

## 当前事实

- `tests/test_project_orrery.py` 保护安装、非覆盖升级、发布包、更新兼容和凭据配置边界。
- `tests/test_context_routing_benchmark.py` 保护历史语料、Pilot 装置、回执规则、未跟踪文件采集、安全 Oracle 和恢复行为。
- `.github/workflows/validate.yml` 在 Windows／Ubuntu 上运行验证；动态文档站测试需要额外依赖和 `ORRERY_TEST_BUILD=1`。
- 自托管补全新增 installer 排除模板 Python 缓存的回归断言。
- 2026-08-18 基线结果：默认套件 28 项中 27 项通过、动态 reader 测试按设计跳过；设置 `ORRERY_TEST_BUILD=1` 后完整 28/28 通过。24 项 benchmark 语料与工作树中的 6 份 run record 也通过验证。
- 发布分支 CI `32057247222` 与 main CI `32057443759` 均在 Windows／Ubuntu 通过；最初失败轮 `32057075492` 暴露浅克隆缺少历史 commit，workflow 已改为 `fetch-depth: 0`。
- `tests/test_context_routing_h2.py` 当前 12 项专项测试，保护读取预算、路径边界、哈希／换行规范、Windows CRLF stdout 恢复且拒绝正文篡改、Hook 语义、CLI JSONL 独立审计、命令／写路径归一化、未知工具拒绝、原始证据篡改检测及 Pilot 005／006／007 冻结控制包 dry-run；2026-08-18 本地为 12/12 通过。
- Pilot 005／006 与 CRLF 修复集成后的全仓结果：默认 39 项中 38 通过、1 项按设计跳过；设置 `ORRERY_TEST_BUILD=1` 后 39/39 通过。24 项 corpus、6 份既有 run record、integrated static build、文档站生成、本地 Markdown 链接和 `git diff --check` 均通过。
- 十份仓库外 Hook smoke manifest 已全部重新 verify；真实 Windows CLI 0.147.0 未产出 Hook 日志，因此正式 B/H2 前只允许使用经 validator 证明的 JSONL 事后模式。
- Pilot 007 六份 R0 manifest 为 6/6 有效；正式候选测试暴露外层 `benchmark` 分支与嵌套 Pilot 006 dry-run 冲突，因此 frozen formal validation 不能作为产品回归失败证据，详见 R2 与运行 Validation。
- Pilot 007 R2 与项目文档同步后的仓库回归：专项 12/12、默认套件 39 passed + 1 expected skip、24 项 corpus、6 份 run record、文档站生成和 `git diff --check` 全部通过。

## 验证证据

- [2026-08-18 自托管基线](../validation/2026-08-18-self-hosting-baseline.md)
- [2026-08-18 H2 读取证明装置](../validation/2026-08-18-h2-read-proof-apparatus.md)
- [2026-08-18 Pilot 005 / 006 B/H2](../validation/2026-08-18-pilot-005-006-bh2.md)
- [2026-08-18 Pilot 007 P/B 采纳实验](../validation/2026-08-18-pilot-007-pb-adoption.md)
- `python -m unittest discover -s tests -v`
- `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`
- `python -X utf8 scripts/docsite/build_docsite.py`

## 已知缺口

- 动态图形化 AI 设置测试默认跳过，除非安装 reader 依赖。
- 当前端到端强度止于代理+完整 CLI JSONL 的事后交叉证明；没有可工作的实时 Hook 阻断。
- 外部原始数据已有 manifest 与保留策略，但仍依赖本机存储，且尚无自动脱敏导出器或异地备份。
- 发布打包测试验证包内安全边界，但尚未比较不同操作系统生成 archive 的 byte-for-byte 一致性。
