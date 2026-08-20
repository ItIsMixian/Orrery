# docsite 凭据安全加固验证

Date: 2026-08-19
Status: local implementation validated; not committed or released
Governing ADR: [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md)
Approved Design: [docsite 凭据隔离与本地 Broker](../design/docsite-credential-isolation-and-broker.md)

## 范围

本记录验证当前工作树中的 Provider／Base URL 绑定、一键保存并启用、失败关闭、同源本地
HTTP 边界、卡片缓存签名，以及可选确定性 Broker 的端点固定、重定向拒绝、模型白名单、
缓存、并发 single-flight 和每日请求／token 预算。它不证明公开 v0.2.0 已包含这些改动。

## 隔离方法

- 动态 docsite 子进程使用 `keyring.backends.null.Keyring`，并清除所有受支持的 Key、Provider、
  Base URL 和模型环境变量。
- `ORRERY_TEST_NO_EXTERNAL_NETWORK=1` 在测试子进程中拒绝所有非环回 socket。
- Broker 使用临时 SQLite 和测试进程内的环回假上游；没有读取维护者 keyring，也没有访问
  真实 Provider。
- 测试 Key 是固定 sentinel；响应和 SQLite 均断言不包含 Provider sentinel。

## 结果

| 命令／检查 | 结果 |
|---|---|
| `python -X utf8 -m unittest discover -s tests -v` | PASS；当时快照 42 项，40 通过、动态 reader／Broker 2 项按设计跳过；随后并行加入的 Phase 0 两项由最终动态套件覆盖 |
| `$env:ORRERY_TEST_BUILD='1'; python -X utf8 -m unittest discover -s tests -v` | PASS；最终 44/44，包含 Pilot 008 dry-run、Phase 0 基线与全部 docsite 动态测试 |
| `$env:ORRERY_TEST_BUILD='1'; python -X utf8 -m unittest discover -s tests -p test_project_orrery.py -v` | PASS；11/11 |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --build` | PASS；integrated candidate + static build |
| `python -X utf8 -m py_compile ...`（根与模板四个 docsite 安全脚本） | PASS |
| 根／模板 `_llm.py`、`set_key.py`、`llm_broker.py` 内容 diff | PASS；无差异 |
| 根／模板 `serve.py`、`build_docsite.py` 内容 diff | PASS；只有预期项目标题占位符差异 |
| 本地 Markdown 链接扫描 | PASS；166 个 Markdown 文件没有缺失目标；冻结的 Pilot 008 `controls/P-SKILL.md` 独立 fixture 按设计排除 |
| `git diff --check` | PASS |

## 行为证据

- 未启用、端点无效、Provider 主机错配或指纹漂移时不构造可用 Provider；仅设置
  `DOCSITE_PROVIDER` 也不能绕过文件绑定指纹。
- 远程 HTTP 被拒绝；OpenAI／DeepSeek 固定官方主机；SDK 使用显式 Base URL 且禁用重定向。
- 设置、问答和手动刷新要求同源 POST；旧 `?refresh=1` GET 不再触发模型调用。
- 状态 API、错误响应、项目 JSON、Broker 响应和 Broker SQLite 不包含测试 Key。
- 两个并发相同 Broker 请求只产生一次假上游调用，随后命中同一缓存；single-flight 临时锁
  在完成后释放。
- docsite 卡片缓存由进程内锁保护并通过原子替换写入；Broker 状态目录在 POSIX 下收紧权限。
- 超出保守 token 预留或每日请求上限的请求在上游调用前返回 429；上游重定向返回 502。
- 发布包测试确认模板包含 `llm_broker.py`，且没有 `__pycache__`、`.pyc` 或 `.pyo`。

## 已知边界

- 标准系统凭据库只防项目明文与误提交，不能阻止同一 OS 用户的任意进程读取通用凭据。
- Broker 的 Provider-Key 隔离要求独立 OS 身份或等价外层边界；本轮只验证代码边界，没有把
  同用户测试进程宣称为 OS 隔离证据。
- Broker client token 是受预算约束的消费凭据；能读取它的进程仍可消耗允许额度。
- 没有使用真实 Provider Key 或真实上游做连接测试，因此不证明任何第三方账户、配额或网络
  当前可用。
- 此实现未提交、未推送、未打 tag、未发布；公开 v0.2.0 资产保持不变。
