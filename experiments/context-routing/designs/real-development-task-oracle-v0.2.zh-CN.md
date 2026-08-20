# 真实开发任务与 Oracle v0.2

Status: research candidate; not product policy
Date: 2026-08-19
Evidence: Pilot 008 apparatus stop and Pilot 009 R2

## 要解决的问题

真实开发任务不能退化为文档字符串测试。Pilot 008 暗中要求索引名和固定 State 词形；Pilot 009 虽移除
这些要求，仍用 `auto-expiry` 等英文 substring 验收自然语言，导致语义正确的实现被判失败。与此同时，
Pilot 009 的迁移任务确实遗漏 PROGRESS 中的未来版本拒绝事实，不能因为 Oracle 曾有假阴性就放弃文档
一致性验收。

## 分层 verdict

每个任务分别输出以下维度，最终 pass 才做合取：

1. `behavior`: 从公共 API 或真实调用链验证行为，不调用 Agent 新增的专用 helper 逃避集成路径。
2. `data_safety`: 验证迁移幂等、原数据、失败前无写入、凭据和日志边界。
3. `scope`: 必需路径已改、受保护路径未改、真实测试发现通过。
4. `structured_state`: 只检查仓库在任务前已经公开的 State 字段、枚举或 schema；不得发明隐藏名字。
5. `narrative_consistency`: 检查 PROGRESS／HANDOFF 是否保留已知矛盾或遗漏任务明确要求的主要事实，不
   要求同义事实采用固定英文短语。

行为与数据失败始终优先于文档；报告必须保留各维度，不能只给一个 `candidate_passed`。

## 公平 Oracle 规则

- exact match 只用于 Prompt 或仓库正文已经公开的 API、字段、任务 ID、schema version 和安全枚举。
- 对自然语言使用事实单元和反向矛盾检测；若自动语义判断不可靠，标为 `manual_review_required`，不得
  用一个隐藏 substring 直接判 fail。
- 每项自然语言事实至少有三种同义 positive controls 和两种 contradiction controls。英文连字符、时态、
  中英文切换和合理的长短句不得改变 verdict。
- positive fixture 必须由与正式 Prompt 相同的公开信息完成；negative fixture 要分别注入单一行为、数据、
  范围和事实链缺陷，证明 Oracle 能定位维度。
- 行为 probe 做 mutation check：删除关键 guard、交换索引列、把失败检查移到写入后、跳过真实调用链时
  必须失败。
- 不要求 Agent 创建实验 Manifest、Receipt 或访问总结；所有实验元数据仍由 Harness 生成。

## 下一批任务用例

滚动任务池优先加入以下五类，正式三任务 Pilot 至少选择两项代码主交付，并避免连续两轮完全复用同一
实现缺陷：

### A. 状态转换 Bug

自动过期、显式 snooze、重复事件和截止边界同轮覆盖。Oracle 从公开 API 验证状态与时间字段；State 在
baseline 预置 `feedback_auto_expiry_policy: unknown`，Agent 只需更新公开字段，不猜命名。

### B. 事务性迁移

在 v1→v2 基础上注入迁移中途失败，要求 schema、`user_version` 和旧行原子回滚；未来版本仍必须写前
拒绝。该任务比“增加一列”更能覆盖真实数据安全，并用数据库快照而不是索引名验收。

### C. 小功能闭环

增加“暂停陪伴 30 分钟”：命令入口、持久化偏好、安全门控、自动恢复和测试形成真实调用链。Fixture
提供最小模块，不要求 UI 像素或实验文档；Oracle 使用可控时钟验证暂停与恢复。

### D. 凭据撤销安全修复

删除 Provider 时同步删除对应凭据，并证明配置、日志、异常和测试输出不含 secret；模拟 keyring 失败时
保留可恢复状态。安全 Oracle 检查调用顺序和最终存储，不依赖 helper 名。

### E. 当前事实对齐

代码不改，只修正 State、PROGRESS、HANDOFF。State 使用公开结构化字段作为主要机器事实；叙事文档只
检查关键事实覆盖和矛盾消除，并通过多种同义 positive controls。

## 启动门

新 Pilot 在任何模型样本前必须通过：每任务 baseline negative、positive、mutation、paraphrase controls；
P/S Prompt 等长；嵌套 Git 隔离；完整事件 validator；Scope analyzer synthetic pipeline；新 runtime 无模型
握手。缺一项就只报告 apparatus not ready。
