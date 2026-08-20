# 实施计划：Broker-first docsite gateway

Status: Completed
Date: 2026-08-19
Governing ADR: [ADR-0006](../../decisions/0006-broker-only-docsite-provider-gateway.md)
Approved Design: [Broker-first docsite Provider gateway](../../design/broker-first-docsite-provider-gateway.md)

## 实施映射

- [x] 为 `llm_broker.py` 增加非交互注册、状态装载和 Provider Key 删除接口，CLI 复用同一路径。
- [x] 为 `_llm.py` 增加 Broker-only 构造门和 Broker 元数据持久化，不移除通用上游校验。
- [x] 将设置页改为“Broker 模式 + 上游 Provider”，删除 Local Broker 同级选项。
- [x] 实现默认本机 Broker 的保存、启动、重载、删除和启动恢复顺序。
- [x] 实现外部隔离 Broker 的 client-token-only 保存与连接测试。
- [x] 保证仪表盘、问答、趋势雷达和测试请求没有任何直接 Provider 路径。
- [x] 同步根观测台、发布模板、README、State、PROGRESS、DEVLOG 和 HANDOFF。
- [x] 增加迁移失败关闭、UI 入口、内存 keyring、Broker-only 请求和成本门回归。
- [x] 运行产品专项、默认全仓、integrated build、模板投影和 diff 验证；动态依赖覆盖产品专项，未重跑与本改动无关的完整研究动态组合。

## 验收条件

1. UI 中 OpenAI／DeepSeek／Custom 只作为上游注册项，Local Broker 不再是同级 Provider。
2. 成功保存后项目配置的 `provider` 恒为 `broker`，正常模型请求只命中环回 Broker。
3. 旧直接配置或直接环境变量不能让 docsite 构造可用 Provider。
4. 本机模式不强制测试请求；外部模式不接收 Provider Key。
5. 测试不读取维护者 keyring、不访问非环回网络、不回显任何测试秘密。
6. 独立 Broker 的隔离声明和同用户托管模式的成本控制声明保持清晰分离。

完成证据写入 `docs/validation/2026-08-19-broker-first-docsite-gateway.md`；清单本身不构成证据。
