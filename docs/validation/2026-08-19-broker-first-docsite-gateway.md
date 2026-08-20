# Broker-first docsite gateway 验证

Date: 2026-08-19
Status: local implementation validated; not committed or released
Governing ADR: [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md)
Approved Design: [Broker-first docsite Provider gateway](../design/broker-first-docsite-provider-gateway.md)

## 范围

本记录验证动态 docsite 的模型请求只能经过 Broker，OpenAI、DeepSeek 和
Custom 只是上游注册预设。覆盖默认本机托管、外部隔离、旧直接配置失败关闭、
凭据替换，以及 UI、HTTP、独立 Q&A CLI 和终端 Key 入口。

## 隔离方法

- 动态设置测试使用 `ORRERY_TEST_IN_MEMORY_KEYRING=1`，Broker 配置／SQLite 位于临时目录。
- `DOCSITE_MANAGED_BROKER_PORT=0` 由操作系统分配环回端口；`ORRERY_TEST_NO_EXTERNAL_NETWORK=1`
  拒绝非环回连接。
- Provider Key 和外部 Broker token 均为 sentinel；状态响应、错误、项目 JSON 和 Broker
  配置均断言不包含 sentinel。未读取维护者真实 keyring，也未调用真实 Provider。

## 结果

| 命令／检查 | 结果 |
|---|---|
| `$env:ORRERY_TEST_BUILD='1'; python -m unittest tests.test_project_orrery` | PASS；16/16，包含本机／外部 Broker 动态设置与独立 Broker HTTP 回归 |
| `python -m unittest discover -s tests -p "test*.py"` | PASS；59 项中 57 通过，2 项动态依赖按设计跳过 |
| `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated --build` | PASS；integrated candidate + static build |
| 根／模板五个 AI 脚本 `py_compile` | PASS |
| 根／模板 `_llm.py`、`docsite_qa.py`、`llm_broker.py`、`set_key.py` 内容比对 | PASS；完全一致 |
| 根／模板 `serve.py` 内容比对 | PASS；仅有预期项目标题占位符差异 |
| `python -m black --check` 新 `set_key.py` 与 `llm_broker.py` 的根／模板副本 | PASS |
| 本地 Markdown 链接扫描 | PASS；204 份 Markdown 无缺失目标，冻结 Pilot 008 `P-SKILL.md` fixture 按设计排除 |
| `git diff --check` | PASS；仅 Git 报告 requirements 行尾转换警告，exit 0 |

## 行为证据

- 设置页不再出现 `Local Broker` 同级 Provider 选项；上游选项只有 OpenAI、
  DeepSeek 和 Custom，并明确标记为 Broker 上游。
- 本机与外部模式保存后 `ai-config.json` 的 `provider` 恒为 `broker`；本机模式
  另保存非秘密上游元数据，外部模式只绑定 client token。
- `serve.py` 重载、可选连接测试、`docsite_qa.py` 独立 CLI 的默认构造和显式调用
  都要求 `provider == broker`。
- `set_key.py` 已从直接 Provider 凭据写入器改为 Broker 注册器；本机模式写入
  Broker Provider namespace 并绑定 client token，外部模式只接收 client token。
- 替换本机上游会删除上一个绑定 Provider Key；从本机切换到外部模式会删除
  同用户托管凭据，避免在“隔离”模式下留存上游 Key。
- 保存并启用不强制先测试；正常仪表盘生成可在 Broker 就绪后直接按需开始。

## 已知边界

- 本机托管模式的 docsite 与 Broker 位于同一 OS 用户，只证明统一路由、缓存和预算门，
  不证明 Provider-Key 身份隔离。
- 外部模式的真实隔离强度取决于 Broker 是否确实在独立 OS 身份或等价外层边界中运行。
- 没有使用真实 Provider Key，因此不证明第三方账户、配额或当前外网可用。
- 本实现未提交、未推送、未打 tag、未发布；公开 v0.2.0 资产保持不变。
