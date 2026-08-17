# 测试覆盖 State

Updated: 2026-08-18

## 当前事实

- `tests/test_project_orrery.py` 保护安装、非覆盖升级、发布包、更新兼容和凭据配置边界。
- `tests/test_context_routing_benchmark.py` 保护历史语料、Pilot 装置、回执规则、未跟踪文件采集、安全 Oracle 和恢复行为。
- `.github/workflows/validate.yml` 在 Windows／Ubuntu 上运行验证；动态文档站测试需要额外依赖和 `ORRERY_TEST_BUILD=1`。
- 自托管补全新增 installer 排除模板 Python 缓存的回归断言。
- 2026-08-18 基线结果：默认套件 28 项中 27 项通过、动态 reader 测试按设计跳过；设置 `ORRERY_TEST_BUILD=1` 后完整 28/28 通过。24 项 benchmark 语料与工作树中的 6 份 run record 也通过验证。

## 验证证据

- [2026-08-18 自托管基线](../validation/2026-08-18-self-hosting-baseline.md)
- `python -m unittest discover -s tests -v`
- `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`
- `python -X utf8 scripts/docsite/build_docsite.py`

## 已知缺口

- 动态图形化 AI 设置测试默认跳过，除非安装 reader 依赖。
- 没有 Harness 独立证明模型接收文件字节的端到端测试。
- 外部 benchmark 原始数据的长期完整性目前依赖本机目录和报告内 hash。
