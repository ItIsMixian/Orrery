# PO-CR-028：R0 到 R1 的安全脱敏导出

为 context-routing Harness 增加 `export_sanitized_evidence.py`：读取已经 seal 的 R0 manifest，写出可移植 R1 JSON，只保留运行身份、分类、源提交、原 manifest 哈希和文件 inventory 的相对路径／字节数／SHA-256。

要求：

- CLI：`--manifest <raw-evidence-manifest.json> --output <outside-run-root.json>`。
- 导出前验证 R0 manifest；拒绝把输出写进 R0 run root，也拒绝覆盖 manifest 或其受管文件。
- R1 不得包含 Provider 消息、源码／Prompt 正文、stderr 内容、本机绝对路径或疑似 secret。
- 输出键和排序确定，重复导出 byte-for-byte 一致。
- 在 Harness README 说明 R1 仍需人工审阅后才能公开，并增加回归测试。
