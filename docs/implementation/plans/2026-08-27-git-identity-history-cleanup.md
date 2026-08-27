# 实施计划：Git 身份历史清理

Status: Planned; remote rewrite not authorized

Date: 2026-08-27

## 目标与边界

在低活动维护窗口中，把公开 Git 历史里的旧个人身份元数据统一替换为当前 GitHub 化名与 ID 型
noreply。只修改 commit/tag 元数据，不修改项目文件内容、产品架构、技术 ID 或发布功能。

任何旧姓名、旧邮箱、旧 handle 和精确映射值都不得进入 Git、文档、日志、fixture 或终端输出；执行时
只从本机受限临时映射读取，用后销毁。

## 执行步骤

1. **等待安全窗口**：所有活动 worktree clean 且已合入、封存或导出 patch；短时冻结远端写入。
2. **保存恢复点**：记录远端 heads/tags、Release 和 branch protection；在非同步本机目录创建完整 mirror
   备份。
3. **离线 dry-run**：在一次性 mirror 中重写 author、committer 和 annotated-tag tagger；验证旧身份类别
   为零，并确认每个 ref 的文件 tree、Release archive 和 checksum 不变。
4. **Candidate 验证**：先把清理后的 main tip 推到非 main 临时分支，取得 Windows／Ubuntu required
   checks 双 PASS；此时仍不更新 main。
5. **切换**：维护者再次明确授权后，临时允许必要的 force push，以固定旧 OID 更新可控 heads/tags，
   随即恢复原 branch protection。
6. **收尾**：复核公开 refs、tag、Release 和保护规则；旧 clone/worktree 重新创建，不得 merge 旧历史。
   对只读 PR refs／cached views 视需要联系 GitHub Support，并如实记录无法清理的第三方副本。

## 停止条件

存在 dirty/未知 worktree、未 push 唯一提交、ref 漂移、tree/checksum 差异、Candidate CI 失败、保护规则
无法恢复或缺少切换前明确授权时，立即停止；只保留本机报告，不修改远端。
