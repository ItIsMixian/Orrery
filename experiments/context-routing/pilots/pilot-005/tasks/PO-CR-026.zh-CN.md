# PO-CR-026：版本化 managed-tools 契约

这是一个跨模块、高风险的升级安全任务。

把 Project Orrery 可升级工具白名单从安装器中的私有常量提升为一个版本化、机器可读的 `managed-tools.json` 契约，并让安装器与验证器共同使用它。发布清单必须声明自己支持的契约格式。

必须保持：

- 契约至少包含正整数格式版本和非空、无重复的仓库相对 POSIX 路径列表；
- 路径不得是绝对路径，不得含空段、`.`、`..`、反斜杠、盘符、冒号或指向模板根外的结果；
- 契约格式与 release manifest 声明不一致、JSON 损坏、字段类型错误、重复或不安全路径时，安装器必须在目标写入前失败，验证器也必须明确失败；
- 正常安装写入 `.project-orrery.json` 的 `managed_tools` 与 `expected_tool_hashes` 必须由同一契约推导，不能继续存在第二份手写列表；
- 验证器需要检查已安装 manifest 的 managed-tools 集合和 hash key 集合是否与当前契约一致；混合工具链仍可作为 warning，但不能把契约漂移报告成完整 current；
- 现有首次安装、作者文件保留、`--upgrade-tools` 备份、`--dry-run` 和集成验证行为保持兼容。

只修改 RUN CONTRACT 允许的四个产品路径，不修改测试、文档或模板正文。
