# Validation：分级验证原则记录

Date: 2026-08-22
Scope: 记录验证分级原则、W3／W4 当前人工执行方式及现有 Promotion 安全边界；不实现 runner、缓存或 CI 跳过
Status: PASS（documentation-only）

## 已确认

- Product Seed 增加“验证强度与阶段、风险匹配”的长期原则。
- 协作 Plan 定义 `Fast → Checkpoint → Candidate → Promotion` 的触发时机、责任和结论边界。
- Test Coverage State 只记录当前人工采用；没有把未来自动 runner、影响分析或证据复用写成当前事实。
- Fast／Checkpoint 不可替代 Candidate／Promotion；Project Orrery self-host 的 exact-SHA Windows／Ubuntu required checks 保持不变。
- 当前调整没有改变发布契约、Authority Meta Model 或跨模块安全门，因此不新增 ADR。

## 文档级检查

- 原则、Plan、State、DEVLOG 与 Validation 索引职责分离；
- 没有修改 `docs/PROGRESS.md` 或 `docs/HANDOFF.md`；
- 没有实现或声称测试 runner、缓存、自动影响映射、跨 SHA 证据复用和 CI path skipping；
- 后续实现上述工具时必须新增实现 Validation；若改变 required evidence 或 main promotion 充分条件，必须先走 ADR。

## 实际证据

- integrated structure：PASS；authority status 为 `integrated candidate`，模型 1 可严格评估；
- 文档治理专项：11/11 PASS（0.021s）；
- 隔离静态站：`D:\coding warehouse\project-orrery-validation-tiering-site\index.html`，1,453 KB，114 份文档；
- 新增及既有直接链接目标检查：PASS；
- `git diff --check`：PASS；
- 未运行默认或动态全仓：本轮是 documentation-only Checkpoint，完整回归保留给冻结后的联合 integration candidate。
