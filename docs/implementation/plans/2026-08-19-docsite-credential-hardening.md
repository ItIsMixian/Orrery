# 实施计划：docsite 凭据安全加固

Status: Completed
Date: 2026-08-19
Governing ADR: [ADR-0003](../../decisions/0003-provider-bound-credentials-and-optional-local-broker.md)
Approved Design: [docsite 凭据隔离与本地 Broker](../../design/docsite-credential-isolation-and-broker.md)

## 实施映射

- [x] 将 `_llm.py` 改为先解析非秘密 Provider 配置，再读取对应环境变量或绑定 keyring 槽。
- [x] 在设置 API 中加入 Provider、显式端点、指纹与启用状态；保持单次保存即启用。
- [x] 禁止远程 HTTP、默认端点回退与配置漂移自动调用；旧共享凭据不自动读取或使用。
- [x] 为本地服务增加 Host／Origin、浏览器响应头、请求体、刷新方法和错误脱敏防护。
- [x] 让后台卡片仅在 Provider 可用时生成，并用语料／Provider 指纹验证缓存。
- [x] 增加可选 `llm_broker.py`，实现独立 namespace、固定端点代理、缓存、single-flight 与预算门。
- [x] 同步根观测台、发布模板、managed tool 白名单、Skill 使用说明和用户入口。
- [x] 增加无真实 keyring、无非环回网络、端点错配、状态 API 不回显、Broker 缓存／预算的测试。
- [x] 运行动态全仓、结构、静态站、链接、发布包与 diff 验证。
- [x] 用 Validation、State、PROGRESS、DEVLOG 与 HANDOFF 接管完成事实。

## 实现目标

- `scripts/docsite/_llm.py`, `serve.py`, `set_key.py`, `llm_broker.py`
- `skills/project-orrery/assets/project-template/scripts/docsite/**`
- `skills/project-orrery/scripts/install_project_orrery.py`
- `tests/test_project_orrery.py`
- `docs/**`, `README.md`, `README.zh-CN.md`

## 验收条件

1. 配置缺失、指纹漂移或 Provider／主机不匹配时没有任何模型请求。
2. 保存并启用不强制发出测试请求；成功后可自动刷新，重启后可安全自动恢复。
3. 一个 Provider 的 Key 不能被另一个 Provider 或 Base URL 读取。
4. 测试即使在维护者 keyring 已配置时也只能看到空测试后端，且非环回 socket 被拒绝。
5. Broker 上游请求不跟随重定向，Provider Key 不进入客户端响应、缓存、日志或项目文件。
6. 根副本与模板除项目占位符外保持一致，发布包不包含任何运行凭据或缓存。

## 验证命令

- `python -m unittest discover -s tests -v`
- `$env:ORRERY_TEST_BUILD='1'; python -m unittest discover -s tests -v`
- `python skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --build`
- `python -X utf8 scripts/docsite/build_docsite.py`
- `git diff --check`

完成结果由 `docs/validation/2026-08-19-docsite-credential-hardening.md` 接管；本清单本身不构成证据。
