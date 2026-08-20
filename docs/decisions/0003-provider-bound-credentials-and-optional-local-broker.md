# ADR-0003：Provider 凭据必须绑定端点，并提供可选隔离 Broker

Status: Accepted
Date: 2026-08-19

## Context

动态 docsite 原先把所有 OpenAI-compatible Provider 共用的 API Key 存在同一个
`project-orrery / OPENAI_API_KEY` 通用凭据槽，并允许 Base URL 缺省时由 SDK 回退到
OpenAI 默认端点。系统凭据库避免了明文落盘和页面回显，却不是同一操作系统用户下的
进程隔离边界；docsite、测试子进程或拥有同等权限的 Agent 仍可取得完整秘密。

一次动态 UI 回归暴露了这个组合风险：临时测试项目继承了维护者的真实 keyring，且
没有对应的 Provider 配置。虽然没有密钥原文进入输出、仓库或缓存，也没有证据证明
外部请求成功，现有设计仍无法排除错误端点尝试。

另一方面，强制用户先执行一次付费“测试连接”、再单独点击“启用”会损害本地观测台
体验，也额外产生模型调用。需要在不增加强制 LLM 请求的前提下保留单次“保存并启用”
和后续自动恢复。

## Decision

1. 凭据按规范化后的 Provider 类型与 Base URL 绑定到独立系统凭据槽。切换 Provider、
   主机或端口不得自动复用旧槽中的 Key。
2. OpenAI、DeepSeek 与本地 Broker 都必须使用显式 Base URL。没有显式端点、配置指纹
   不匹配或配置未启用时，Provider 失败关闭，不回退到 SDK 默认端点。
3. 远程 Provider 只允许 HTTPS；HTTP 只允许环回地址。OpenAI 与 DeepSeek 预设必须
   命中各自的固定官方主机，本地 Broker 必须命中环回地址。
4. UI 保留单次“保存并启用”。保存时只做确定性本地校验、绑定凭据和初始化客户端，
   不强制发出模型测试请求；“测试连接”继续作为明确、可选且可能产生费用的动作。
5. 已启用配置只有在持久化 Provider 指纹与当前规范化配置一致时才可在启动后自动调用。
   首次安装、配置漂移和凭据缺失不得触发后台模型请求。
6. 测试必须使用空 keyring 或显式假后端，并阻断非环回网络；测试不得把维护者真实凭据
   当作装置输入。
7. 发布工具提供可选的确定性本地 Broker。Broker 自身不运行 Agent，只代理固定端点、
   绑定 Provider Key、执行缓存／single-flight／预算控制，并且永不提供导出 Provider Key
   的接口。
8. 只有当 Broker 运行在与 Agent 不同的操作系统身份或等价外层隔离中、且 Key 在该边界
   内单独配置时，产品才可称其隔离了 Provider Key。同一用户启动 Broker 只能声称减少
   调用和集中路由，不能声称 Agent 无法读取密钥。
9. 标准 keyring 模式继续保留以兼容轻量安装，但 UI 和文档必须明确它只保护静态存储与
   回显，不构成同用户进程隔离。

## Reasons

- 端点绑定与失败关闭直接消除“一个通用 Key 被错误 Base URL 复用”的类别风险。
- 单次保存不需要额外模型请求，能保留现有体验；安全条件由本地状态机而非付费探测证明。
- Broker 把长期 Provider Key 移出 docsite 进程，同时可用内容寻址缓存、重复请求合并和
  预算门减少 LLM 开销。
- 明确区分标准模式与隔离模式，避免把 keyring 的静态加密误述为进程级安全边界。

## Consequences

- 既有共享 keyring 槽不会在启动时读取或自动迁移。用户必须在设置页明确重新输入 Key
  并保存，或执行删除操作；这两个显式动作会清理旧共享槽。
- 环境变量也改为按 Provider 选择：OpenAI 使用 `OPENAI_API_KEY`，DeepSeek 使用
  `DEEPSEEK_API_KEY`，自定义端点和 Broker 使用 `DOCSITE_API_KEY`。
- 自定义远程 HTTP Provider 将不再可用；本地兼容服务仍可通过环回 HTTP 使用。
- Broker 是可选工具，不在本次工作树实现完成前改变已发布 v0.2.0 的事实，也不会自动被
  安装成系统服务或创建操作系统账户。

## Implementation and validation mapping

- Approved Design: [docsite 凭据隔离与本地 Broker](../design/docsite-credential-isolation-and-broker.md)
- Implementation Plan: [2026-08-19 docsite 凭据安全加固](../implementation/plans/2026-08-19-docsite-credential-hardening.md)
- State Docs: [文档系统](../state/documentation-system.md)、[发布与工具链](../state/release-and-toolchain.md)、[测试覆盖](../state/test-coverage.md)
- Validation: 完成后写入 `docs/validation/2026-08-19-docsite-credential-hardening.md`
