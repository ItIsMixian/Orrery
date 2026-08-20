# PO-CR-034：SQLite v1 → v2 幂等迁移

把 `feedback` 表从 v1 升级到 v2：增加 nullable `snoozed_until INTEGER`，并建立按
`status, snoozed_until` 查询的索引。已有行必须保留；旧库升级、全新建库和重复初始化都应成功，
最终 `PRAGMA user_version` 为 2。

如果数据库的 `user_version` 高于程序支持的版本，初始化必须在任何 schema 或数据写入前保守失败，
不得把未来版本降回 2。复合索引的列顺序必须与查询顺序一致。

增加覆盖旧行保留、重复初始化和未来版本拒绝的迁移回归测试，并按仓库规则更新受影响的 State 与
PROGRESS。不得重写历史 ADR、修改反馈状态模块、HANDOFF 或删除预置数据。
