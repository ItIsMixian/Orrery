# ADR-0006：docsite 的模型调用统一经过 Broker

Status: Accepted
Date: 2026-08-19
Amends: [ADR-0003](0003-provider-bound-credentials-and-optional-local-broker.md)

## Context

ADR-0003 同时保留了直接 Provider 模式与可选 Broker。这个兼容选择让设置页把 OpenAI、
DeepSeek、自定义端点和 Local Broker 显示为同一级调用通道，也使缓存、single-flight、
模型白名单和预算门只覆盖主动选择 Broker 的用户。

用户明确要求 Broker 成为默认且唯一的 docsite 模型调用通道：OpenAI、DeepSeek 与自定义
服务只应作为 Broker 的上游注册项，不应继续作为绕过 Broker 的入口。同时，本地默认启动
不能被误述为进程隔离；真正的 Provider-Key 隔离仍要求独立 OS 身份。

## Decision

1. 动态 docsite 的问答、仪表盘、趋势雷达和可选连接测试全部只连接 OpenAI-compatible
   Broker 端点，不再直接连接第三方 Provider。
2. 设置页不再把 Local Broker 与 OpenAI／DeepSeek 并列。OpenAI、DeepSeek 和 Custom
   只表示“Broker 上游服务商”。
3. 默认模式为 **本机托管 Broker**：docsite 在同一进程内启动确定性环回 Broker，Provider
   Key 存入 Broker namespace，所有模型调用获得缓存、single-flight、模型白名单和预算门。
   该模式不声称隔离同一 OS 用户下的 Agent。
4. 保留 **外部隔离 Broker** 模式：Provider Key 必须在独立 OS 身份或等价外层边界中通过
   Broker CLI 配置；docsite 只保存 Broker client token，不接收该 Provider Key。
5. 项目 `ai-config.json` 的有效运行 Provider 恒为 `broker`。本机托管模式可额外保存非秘密
   的上游 Provider／Base URL 和模式标记；已有直接 Provider 配置失败关闭，必须显式重新
   输入 Key 注册到 Broker，不自动读取或迁移旧直接凭据。
6. “保存并启用”继续保持单步体验。可选“测试连接”也必须通过临时或外部 Broker 执行，
   不得为了测试恢复直接 Provider 请求。
7. `_llm.py` 中的通用 Provider／端点校验保留为 Broker 上游实现与旧 CLI 兼容基础，但
   docsite 运行入口必须显式要求 `provider == broker`；保留底层代码不等于保留直接 UI 或
   直接运行通道。

## Reasons

- 所有调用天然获得统一缓存、并发去重、模型限制和预算控制，减少重复 LLM 开销。
- UI 只表达一个调用拓扑，不再要求用户在“服务商”和“代理”之间做容易混淆的二选一。
- 默认托管模式无需额外服务安装；外部模式继续提供可证明的 Provider-Key 隔离路径。
- 显式区分成本控制与身份隔离，避免把同用户 Broker 包装成安全沙箱。

## Consequences

- 首次升级后，旧的 OpenAI／DeepSeek／Custom 直接配置不会自动启动后台模型调用；用户需
  在新设置页重新输入一次 Provider Key，或连接已经配置好的外部 Broker。
- 默认本机托管 Broker 由操作系统分配未占用环回端口并持久化实际端点；显式固定端口冲突时失败关闭。
- Provider 环境变量不再构成 docsite 的直接入口；外部自动化应提供 Broker URL 和
  `DOCSITE_API_KEY` client token。
- ADR-0003 关于“标准直接模式继续保留”的第 9 项不再适用于动态 docsite UI／运行时；
  其端点绑定、测试隔离、重定向拒绝和真实隔离边界继续有效。
- 公开 v0.2.0 资产不变；当前工作树实现仍需独立 Validation，不能称为已发布。

## Implementation and validation mapping

- Approved Design: [Broker-first docsite Provider gateway](../design/broker-first-docsite-provider-gateway.md)
- Implementation Plan: [2026-08-19 Broker-first docsite gateway](../implementation/plans/2026-08-19-broker-first-docsite-gateway.md)
- State Docs: [文档系统](../state/documentation-system.md)、[发布与工具链](../state/release-and-toolchain.md)、[测试覆盖](../state/test-coverage.md)
