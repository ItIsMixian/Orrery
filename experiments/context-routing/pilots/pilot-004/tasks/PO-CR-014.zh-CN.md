# 任务 PO-CR-014：升级写入前的共享兼容性门

这是一个高风险、跨模块兼容性任务。

消除更新检查、安装／升级和安装验证之间对 Project Orrery manifest／document schema 兼容规则的重复解释。把纯兼容性判断收敛到一个无 CLI 副作用的共享模块，并让三个消费者使用同一结果。

必须保持这些行为：

- update checker 的 JSON／人类输出语义保持兼容；
- validator 继续识别 legacy v0.1 manifest，并报告超出支持范围的 schema／format；
- installer 在 `--upgrade-tools` 的任何备份、工具替换或 `.project-orrery.json` 写入之前完成兼容性预检；不兼容时退出且目标仓库零变更；
- dry run 能明确报告“可直接升级”或“需要迁移审阅”，但不写文件；
- 共享模块只包含可测试的纯解析／判断逻辑，不在 import 时读取网络、修改文件或退出进程；
- 不改变“安装不等于正式采纳”的权限边界。

只修改 Prompt 头部允许的产品路径。若新增共享模块，它必须位于同一 scripts 包内；不要修改模板文档、release manifest、测试或发布资产。

验收标准：三个入口对相同 manifest 得到一致结论；不兼容升级在第一个文件系统副作用之前停止；兼容路径继续保留现有备份和升级行为。
