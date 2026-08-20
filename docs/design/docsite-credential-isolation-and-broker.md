# docsite 凭据隔离与本地 Broker

Status: Approved
Governing ADR: [ADR-0003](../decisions/0003-provider-bound-credentials-and-optional-local-broker.md)
Updated: 2026-08-19

## 安全目标与非目标

系统分别保护三类边界：

1. **防误泄露**：Provider Key 不进入 HTML、状态 API、日志、缓存、项目配置、Git 或发布包。
2. **防错误端点**：Key 只能与明确绑定的 Provider 类型和规范化 Base URL 一起使用。
3. **进程隔离**：可选 Broker 在独立 OS 身份下持有 Provider Key，docsite 只持有可轮换、
   有预算上限的 Broker client token。

标准 keyring 模式不试图抵抗同一 OS 用户下的任意进程。独立 Broker 也不自动阻止拥有
client token 的调用者消耗额度；预算、模型白名单和频率限制负责降低这类风险。

## Provider 绑定状态机

`ai-config.json` 只持久化非秘密字段：

```json
{
  "provider": "deepseek",
  "baseUrl": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "enabled": true,
  "providerFingerprint": "sha256:..."
}
```

指纹由 Provider 类型与规范化 Base URL 计算。启动时仅当以下条件全部满足才构造客户端：

- `enabled` 为 `true`；
- Base URL 合法、显式且符合 Provider 主机策略；
- 持久化指纹与当前计算值恒等；
- 当前 Provider 对应的环境变量或绑定 keyring 槽存在 Key；
- 模型字段非空。

任何条件失败都返回可解释状态，并且不启动后台 LLM 生成。启动状态检查不会为了判断
旧共享槽是否存在而读取其秘密。设置页一次“保存并启用”会
原子写入非秘密配置、保存当前绑定槽中的新 Key、重新加载 Provider，然后在成功时刷新
需要生成的卡片；这些正常生成调用与额外“测试连接”调用分开表达。可选“测试连接”只在
用户明确点击时发送最小请求。

## 端点策略

| Provider | Base URL 规则 | Key 来源 |
|---|---|---|
| OpenAI | HTTPS，主机必须为 `api.openai.com` | `OPENAI_API_KEY` 或绑定 keyring |
| DeepSeek | HTTPS，主机必须为 `api.deepseek.com` | `DEEPSEEK_API_KEY` 或绑定 keyring |
| Local Broker | HTTP/HTTPS，仅环回地址 | `DOCSITE_API_KEY` 或绑定的 Broker client token |
| Custom | 远程必须 HTTPS；HTTP 仅环回地址 | `DOCSITE_API_KEY` 或绑定 keyring |

URL 不允许用户名、密码、query 或 fragment。SDK 不允许把认证请求跟随到另一来源。

## 本地 HTTP 防护

- 服务只绑定 `127.0.0.1`。
- 所有请求校验 `Host` 为当前环回监听地址；有副作用请求必须具有同源 `Origin`。
- 仪表盘手动刷新使用同源 JSON `POST`；旧的查询参数 `GET` 不再触发模型调用。
- 设置写操作继续使用每进程随机 token 和常量时间比较。
- 动态响应使用 `no-store`、`nosniff`、拒绝 framing、限制 referrer 与浏览器权限，并配置
  只允许同源连接的 CSP。
- 设置和问答请求体均设上限；错误信息在进入响应或日志前去除已知秘密。

## Broker 进程

`llm_broker.py` 是标准库 HTTP 服务加 `httpx` 上游客户端，不调用 Agent。它提供：

- `configure`：在 Broker 所在 OS 身份的独立 keyring namespace 中保存 Provider Key，
  写入非秘密用户级配置，并生成可轮换 client token；
- `serve`：只在环回地址提供 OpenAI-compatible `/v1/chat/completions`；
- `status`／`rotate-client-token`／`delete-key`：管理生命周期但不输出 Provider Key；
- 精确请求内容哈希缓存、进程内 single-flight、模型白名单、非流式日请求／token 预算；
- 禁止跟随上游重定向，日志不包含请求正文、Authorization 或响应正文。

Broker 缓存位于 Broker OS 用户的数据目录，按 Provider、端点和请求体哈希隔离，只保存
响应与使用量，不保存 Provider Key。POSIX 下状态目录收紧为 `0700`、SQLite 为 `0600`；
Windows 依赖独立用户配置目录的 ACL。流式请求直接转发且不写缓存。

## 成本控制

- docsite 卡片缓存加入权威语料指纹；相关文档与 Provider 指纹未变时继续复用，不只依赖 TTL。
- docsite 的四个后台生成线程通过进程内锁和原子替换合并写入 `.doccache.json`，避免彼此覆盖
  后导致下次启动重复调用。
- Broker 对完全相同的非流式请求进行内容寻址缓存，并合并并发重复请求。
- 确定性统计继续由本地代码计算，不交给 LLM。
- Broker 只把配置允许的默认／快速／综合模型转发到上游。每个未缓存请求必须提供正数
  `max_tokens`；Broker 先按请求 UTF-8 字节数加输出上限保守预留每日 token 预算，再用
  非流式响应报告的实际用量结算。流式响应保留该预留，缓存命中不计上游调用。

## 兼容与发布

- 标准模式仍可不运行 Broker。
- Broker 文件属于 viewer managed tools，默认安装创建、`--upgrade-tools` 先备份再升级。
- v0.2.0 发布资产不回写；当前实现只构成后续版本候选。
- 根自托管副本与发布模板保持语义一致，模板只保留项目标题占位差异。
