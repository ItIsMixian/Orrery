# Orrery 开发文档

本目录是 Orrery 仓库自身的文档权威根。

```text
产品意图 → Seed → 有效 ADR → 已批准 Design → 实际实现 → State Docs → Validation → Snapshot
```

## 当前入口

- [当前进度](PROGRESS.md)
- [跨会话交接](HANDOFF.md)
- [产品哲学](product-philosophy.md)
- [核心原则](core/principles.md)
- [ADR-0001：自托管采纳](decisions/0001-project-orrery-self-hosting.md)
- [State Docs](state/)
- [验证记录](validation/)
- [开发日志](DEVLOG.md)
- [研究 Library](library/README.md)
- [上下文路由实验](../experiments/context-routing/README.md)

## 证据分层

详细实验 Prompt、Runner、Oracle 和可发布结果留在 `experiments/`；大型隔离仓库与 JSONL 留在仓库外本地 benchmark 根。Docs 保存当前结论、风险和可复现验证，不复制全部原始数据。

运行 `start-docsite.bat` 可打开本地观测台。`docs/_site/index.html` 是生成物，禁止手工编辑。
