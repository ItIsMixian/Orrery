# Pilot 004 operator-only acceptance 设计

> 此文件描述 Harness 侧验收，不得复制进 Agent 的隔离仓库或 Prompt。

## PO-CR-012

- fake credential backend：成功、not-found、异常三种模式；记录删除调用和顺序。
- 删除异常时断言项目 `ai-config.json` 字节不变、Provider 未 reload、返回为脱敏失败。
- 成功时断言 credential delete 先于 legacy plaintext rewrite，模型字段保留。
- 模拟 credential delete 成功但 project rewrite 失败：不得返回完整成功，重新读取的状态必须说明仍由 legacy config 提供 Key，第二次调用可继续收敛。
- 环境变量 Key 存在时成功删除 keyring 后仍返回 `hasKey=true` 且来源为 environment。
- 用包含 sentinel secret 和内部路径的异常测试公开响应不泄漏。

## PO-CR-013

- fake HTTP response 的 `read` 记录请求大小；超过上限的响应必须在 `limit + 1` 范围内拒绝。
- 分别提供合法、项目名错误、非法 semver、损坏 JSON 的 fresh／stale cache。
- monkeypatch `os.replace` 失败，断言旧缓存 byte-for-byte 不变且无临时文件。
- URL 使用带 query secret 的地址，网络异常正文也包含该 secret；公开 warning 不得包含它。
- 验证 offline 和 manifest-file 不触网。

## PO-CR-014

- 对 shared helper、checker、installer、validator 运行同一组 legacy/current/future manifest table tests。
- instrument `backup_file`、`write_bytes`、`replace` 和 manifest write；不兼容时副作用计数必须为 0。
- 兼容升级仍产生备份并更新受管工具；dry run 只报告计划。
- import shared module 时禁止网络、文件写入和 `SystemExit`。

## PO-CR-015（保留）

- barrier 同时启动至少 8 个 writer，循环更新不同 key 与同 key；验证不同 key 无丢失，同 key 结果属于完整提交之一。
- replacement failure 保留旧缓存并清理临时文件。
- 损坏 JSON、数组顶层和字段结构错误均能启动并回到空／有效默认状态。

## Oracle 自测要求

每项 Oracle 至少包含：

1. 一个故意不安全／不完整 fixture，证明测试会失败；
2. 一个最小安全 fixture，证明测试不会绑死函数签名或具体分层方式；
3. 对异常类型和失败原因的检查，避免把无关 `TypeError` 当成预期安全失败；
4. checksummed operator artifact，并在封存结果中记录版本和 SHA-256。
