# PO-CR-027：跨平台 byte-for-byte 可重复 release zip

修改 release 打包器，使同一源码内容在 Windows／Linux 行尾、文件 mtime 和源文件可执行位不同的副本中生成 byte-for-byte 完全相同的 zip。

要求：

- UTF-8 文本在归档内使用确定性 LF；二进制保持原字节。
- zip 条目顺序、时间戳、压缩参数和 Unix mode 固定；mode 不依赖宿主 `os.access()` 或源文件 chmod。
- 现有 release manifest、排除规则和普通发布测试不能回归。
- 为行为增加仓库测试；不要只写注释或平台判断。
