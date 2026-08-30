"""Shared zh-CN display vocabulary for Observatory presentation layers.

Protocol identifiers remain unchanged.  These labels are presentation-only and
keep machine vocabulary out of primary views unless a technical-details panel
explicitly exposes it.
"""
from __future__ import annotations


NAVIGATION_LABELS = {
    "overview": "项目总览",
    "docs": "文档与搜索",
    "ask": "文档问答",
    "authority": "权威状态",
    "personal": "个人工作台",
    "team": "团队协作",
    "workstreams": "任务关系",
    "maintenance": "工作区维护",
}

STATUS_LABELS = {
    "available": "可用",
    "ready": "就绪",
    "unavailable": "暂不可用",
    "current": "当前",
    "stale": "历史状态",
    "unknown": "待确认",
    "idle": "空闲",
    "pending": "等待刷新",
    "running": "正在刷新",
    "succeeded": "刷新完成",
    "failed": "刷新失败",
    "timed-out": "刷新超时",
    "empty": "暂无证据",
}

WORKSPACE_CLASSIFICATION_LABELS = {
    "active-task": "进行中的任务",
    "integrated-closed": "已集成并关闭的候选工作区",
    "primary-worktree": "主工作区",
    "retained": "明确保留",
    "legacy-no-session": "缺少任务登记的历史工作区",
    "unknown": "待确认的工作区",
}

TECHNICAL_DETAILS_LABEL = "技术详情"

MAINTENANCE_REASON_LABELS = {
    "workspace-path-not-found": "工作区路径不存在",
    "workspace-path-boundary-not-safe": "工作区路径不在安全边界内",
    "legacy-or-unknown-workspace-requires-explicit-adoption": "历史或待确认工作区尚未明确接管",
    "workstream-is-active": "任务仍在进行",
    "review-or-integration-is-pending": "审查或集成尚未完成",
    "workspace-is-protected-or-retained": "工作区受保护或已明确保留",
    "git-identity-or-common-dir-not-verified": "Git 身份或公共目录尚未验证",
    "tracked-worktree-changes-present": "存在已跟踪但未提交的改动",
    "unknown-untracked-paths-present": "存在待确认的未跟踪文件",
    "unknown-or-sensitive-ignored-paths-present": "存在待确认或敏感的忽略文件",
    "git-private-closure-record-missing": "缺少 Git 私有区关闭记录",
    "closure-reason-is-not-integrated": "关闭原因不是已集成",
    "closure-workspace-path-does-not-match": "关闭记录与工作区路径不匹配",
    "final-integration-target-oid-drifted": "最终集成目标已变化",
    "closure-candidate-is-not-ancestor-of-integration-oid": "候选提交尚未进入集成目标",
    "review-package-evidence-missing": "缺少审查包证据",
    "review-package-content-hash-does-not-match-closure": "审查包与关闭记录不匹配",
    "review-candidate-head-does-not-match-closure": "候选提交与关闭记录不匹配",
    "passed-validation-evidence-missing": "缺少已通过的验证证据",
    "review-decision-evidence-missing": "缺少审查决定证据",
    "closure-validation-references-missing": "关闭记录缺少验证引用",
    "workspace-head-does-not-match-closure-final-head": "工作区提交与关闭记录不匹配",
    "unique-commit-check-failed": "无法确认是否存在独有提交",
    "workspace-has-commits-not-reachable-from-integration-oid": "工作区仍有未进入集成目标的提交",
    "workstream-session-is-not-integrated-or-closed": "任务尚未集成并关闭",
    "integrated-grace-period-active": "集成后的保护期尚未结束",
    "target-refresh-failed": "目标重新检查失败",
    "cached-target-evidence-drifted": "目标证据已变化",
    "authorization-evidence-drifted": "授权绑定的证据已变化",
}


def display_status(value: object) -> str:
    return STATUS_LABELS.get(str(value).lower(), str(value))


def workspace_classification(value: object) -> str:
    return WORKSPACE_CLASSIFICATION_LABELS.get(str(value), "待确认的工作区")


def maintenance_reason(value: object) -> str:
    return MAINTENANCE_REASON_LABELS.get(str(value), "其他保护原因（见技术详情）")


__all__ = [
    "NAVIGATION_LABELS",
    "MAINTENANCE_REASON_LABELS",
    "STATUS_LABELS",
    "TECHNICAL_DETAILS_LABEL",
    "WORKSPACE_CLASSIFICATION_LABELS",
    "display_status",
    "maintenance_reason",
    "workspace_classification",
]
