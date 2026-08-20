# Broker-first docsite Provider gateway

Status: Approved
Governing ADRs: [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md) | [ADR-0006](../decisions/0006-broker-only-docsite-provider-gateway.md)
Updated: 2026-08-19

## 统一拓扑

```text
docsite panels / Q&A / connection test
                 │ Broker client token
                 ▼
      OpenAI-compatible loopback Broker
          │ endpoint pin / allowlist
          │ cache / single-flight / budget
          ▼
       registered upstream Provider
```

docsite 的 `_reload_provider()` 必须以 Broker-only 条件构造客户端。任何保存的直接 Provider、
`OPENAI_BASE_URL` 或第三方 Key 即使仍能被通用 `_llm.py` 解析，也不能成为动态站调用通道。

## 两种 Broker 模式

### 本机托管（默认）

- 设置页收集上游 Provider、Base URL、模型和 Provider Key。
- Provider Key 写入 `project-orrery-broker/provider` namespace；Broker client token 使用独立
  namespace，并复制到 docsite 的 Broker endpoint 绑定槽。
- docsite 在环回地址自动启动 Broker HTTP server，再把项目非秘密配置保存为
  `provider: broker`。
- 保存顺序为：校验上游 → 保存／确认 Broker Provider Key → 启动 Broker → 保存 client
  token → 最后启用项目配置。任何中间步骤失败都不得启用模型调用。
- 同一 OS 用户的 docsite 进程会在配置时接触 Provider Key，也能访问该用户的 Broker
  namespace；此模式只提供统一路由与成本控制。

### 外部隔离

- 设置页只收集 Broker Base URL、模型和 client token，不出现 Provider Key 注册动作。
- Provider Key 由 `llm_broker.py configure` 在独立 OS 身份内配置。
- docsite 不调用 Broker 管理接口，也不自动迁移直接模式 Key。
- 外部 Broker 仍必须为环回地址；跨主机 Broker 不进入当前信任模型。

## 设置与状态模型

项目 `ai-config.json` 保存：

```json
{
  "provider": "broker",
  "baseUrl": "http://127.0.0.1:49152/v1",
  "model": "deepseek-chat",
  "enabled": true,
  "providerFingerprint": "sha256:...",
  "brokerMode": "managed",
  "upstreamProvider": "deepseek",
  "upstreamBaseUrl": "https://api.deepseek.com"
}
```

`49152` 仅为格式示例；首次启动默认由操作系统分配未占用端口，之后持久化实际端点。Key、client token、预算数据库和缓存均不进入项目配置。状态 API 只返回布尔值和非秘密绑定
信息。旧直接配置在状态中标记为需要迁移，但不得读取旧共享 keyring 槽或自动复制 Key。

## 可选连接测试

- 本机托管模式使用临时环回 Broker 与临时 SQLite 执行测试，不写项目配置或正式缓存。
- 外部模式直接测试用户给出的 Broker endpoint／client token。
- 两种模式都使用 Broker 的 endpoint、模型白名单、预算和重定向规则；不存在直连测试。

## 生命周期与失败路径

- 启动时只有 `brokerMode=managed` 且项目 Provider 为 `broker` 才自动恢复本机 Broker。
- 默认自动端口避免新注册冲突；显式固定端口冲突、Broker Key 缺失、client token 缺失、配置指纹漂移或依赖缺失均失败关闭。
- 切换到外部模式会停止当前进程托管的 Broker，并删除当前同用户托管模式的 Provider Key 与 Broker token；不会停止其他进程或删除外部 Broker Key。
- 删除本机托管凭据会先停止 Broker，再删除 Provider Key、Broker token 和 docsite client
  token；缓存保留，避免把“删除凭据”扩展成数据删除。

## 兼容边界

- `_llm.py` 的 direct-capable 类型继续服务 Broker 上游校验、隔离测试和旧脚本兼容，不从
  docsite UI 暴露。
- 根观测台和发布模板保持语义一致；Observatory component manifest 的 managed-tool 清单
  不变。
- v0.2.0 发布资产不回写，新行为属于后续未发布候选。
