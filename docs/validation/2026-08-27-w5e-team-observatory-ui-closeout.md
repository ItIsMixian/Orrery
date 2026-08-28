# Validation：W5E Team Observatory UI 收口

Date: 2026-08-27
Status: Worktree Candidate focused／adjacent／browser／structure／site／link／diff PASS；hosted Promotion、main merge 与 Release 未执行
Fact scope: `codex/w5e-team-observatory-ui-closeout`，base `CI1-tiered-parallel-validation@67a2fe90f26ff5ded839c4d60fea23dfcd36ba13`

## 结论

W5E 删除 Team 标题右侧重复边界 pill 与“现在的情况”摘要，把团队连接、可见成员、待处理请求、待同步四项状态上移。Team Mode、团队连接、在线状态和退出 Team Mode 始终位于非折叠首层；Host、内部 ID、sharing／heartbeat、last-seen、outbox、discovery、Coordinator generation、reconnect、测试请求、维护请求和最小元数据说明通过齿轮按钮进入 `role=dialog` 的次级本机设置面。

改动只属于 Observatory presentation。Core 0.1.11、CLI 0.1.15、Team schema／权限／revision／TTL／request receipt、LAN discovery／join、Host／Origin／cookie／16 KiB body、固定 POST 与错误脱敏均未改变；Observatory Candidate 从 0.1.7 提升至 0.1.8。组合式接口／Brownfield Migration 文档提交已吸收，但继续分别属于 Library 非权威草案和 HANDOFF 未来研究接续，不构成公共 API、ADR 或实现。

## 自动验证

- `python -X utf8 -m unittest tests.test_team_observatory tests.test_collaboration_team tests.test_project_orrery.ProjectOrreryTests.test_phase1_component_boundaries_and_compatibility_projection -v`：18/18 PASS，217.750s。
- `python -X utf8 scripts/ci/validate_ci.py --all`：PASS；Fast／Promotion、exact-SHA 和 fail-closed aggregator contract 保持有效。
- `python -X utf8 scripts/ci/test_inventory.py`：342 unique test IDs／26 shards／40 Fast，0 missing／duplicate／dead selector。
- `python -X utf8 scripts/ci/validate_repository_gates.py`：622 repository paths、335 Markdown、919 local links，0 forbidden runtime／generated artifact。
- `python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated`：PASS；Authority Model 1 strict eligible。
- 隔离 `build_docsite.py`：PASS；`1,781,677` bytes、13 ADR、6 State、7 subsystem、2 Snapshot、135 docs、23 Plans、7 Library。
- Python compile 与 `git diff --check`：PASS；只有既有 JSON／TOML LF→CRLF 工作副本提示。

## 浏览器验收

Browser: Codex in-app Chromium；只访问 root-only `127.0.0.1`，没有公网／DNS／第三方请求。测试结束后 Team Mode 已退出，viewport 已恢复。

### Desktop 1280px

- `document`／`body` scroll width `1265 < 1280`，无横向溢出。
- `.to-overview` 位于建议操作之前；旧“现在的情况”和共享边界 pill 均不存在。
- 外层实际可见按钮为“启动团队连接／开启在线状态／⚙／退出 Team Mode”。连接启动后切换为“暂停团队连接”，heartbeat 开启后切换为“关闭在线状态”；反向操作与退出均通过。
- 本机设置 dialog 可由齿轮打开、关闭按钮／Escape 关闭，`aria-expanded` 正确切换；桌面技术字段为 3 列。

### Mobile 390×844

- `document`／`body` scroll width `375 < 390`；overview `346.67px`，控制区 `310.67px`，无横向溢出。
- 四项状态为 2×2，四个外层控制为 2×2；工作区继续单列。
- dialog width `354.67px`、scroll width `353px`，技术字段为 2 列，按钮和最小元数据说明可读。

## 未完成边界

- 本记录不替代真实双机 LAN、Ubuntu exact-SHA、CI1 hosted 性能或 Promotion required checks。
- 页面仍是 self-host root-only Candidate，不进入默认 docsite、Skill template、managed tools 或公开 v0.2.0。
- 最新 Candidate 仍需中央整合审查、冻结新 SHA 和 Windows／Ubuntu 双 PASS，才能申请推广 `main`。
