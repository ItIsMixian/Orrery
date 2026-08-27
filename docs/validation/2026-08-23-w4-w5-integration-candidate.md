# Validation：W4／W5A 联合 integration candidate

Date: 2026-08-23
Scope: 在 `main@7932a9c` 上依次吸收分级验证原则、W4A/W4B Personal Observatory 与 W5A opt-in Team foundation；只形成非 main Candidate，不更新 Canonical main、不发布
Status: Implementation candidate PASS；final documentation SHA checks pending；等待维护者确认后才允许合并 main

## 输入与顺序

- Base：`7932a9c01efb2e5125da1962873e67383982d98c`；
- 分级验证原则：原提交 `1967b30`，集成提交 `b41ef16`；
- W4：`335f10a → 2b9b556 → e5a198e → 7188e6e`，集成提交 `bf79e14 → c3a4a73 → 96ba6ad → 347b42e`；
- W5A：`ac0f4eb → 2329bac`，集成提交 `0bc1568 → 84e411e`；
- 共享 Plan／State／DEVLOG／Validation index 采用加法合并；代码路径没有冲突；
- 联合组件版本：Core 0.1.8、CLI 0.1.13、Observatory 0.1.2，均为 `unreleased`。

## 产品边界

- W4 是 root-only opt-in、只读 Personal 页面；W3 review／integration／cleanup 结论全部来自 Core，provider 缺失／失败／旧 schema 时只降级 W3 区域，不破坏 W4A；
- W5A 默认 Personal zero-network；`team enable` 不监听，显式 `team serve` 才启动 Coordinator；loopback 默认，LAN bind 还需本机开关；
- Team payload 是 64 KiB 上限的严格 metadata envelope，递归拒绝 Prompt／回答／reasoning／transcript／源码正文／diff／凭据／token／API key 等字段；
- 中央视图只读且 request-only；本机接受／拒绝写 private receipt，始终 `execution_performed=false`；
- 没有自动发现、真实多机/LAN、自动选主、云 relay、多设备迁移、Team UI、远程 shell／Agent／merge／delete；
- 用户级 Skill、发布模板默认入口、公开 v0.2.0、tag 和 Release 均未改变。

## 联合验证

- W4 + W5 + component projection focused：26/26 PASS，176.862s；
- 动态全仓：316 项，313 PASS + 3 个既有 Windows symlink privilege skips，1220.014s；
- integrated structure：PASS；Authority status `integrated candidate`，模型 1 可严格评估；
- legacy 隔离 docsite：`D:\coding warehouse\project-orrery-validation-w4-w5-candidate\index.html`，1,532 KB，118 docs；
- W4 explicit opt-in：`personal.html` 1,611,282 bytes；`personal.json` 260,793 bytes，`status=ready`、`read_only=true`、`network_performed=false`、`team_runtime_enabled=false`；
- Markdown：340 files／874 local links；1 个 D1 positive fixture 预期 missing，0 unexpected missing；
- high-confidence secret scan、forbidden tracked artifact、两份 schema JSON 与 `git diff --check`：PASS。

## 待维护者确认

- 本 Candidate 尚未 push／合并 main；远端 exact-SHA required checks 尚未完成；
- W5A 只证明 loopback 和 IP-literal 安全边界，不证明真实多机或实际局域网质量；
- Personal 页面没有 Team 页签；W5A 只提供稳定 `team-read-only-projection` interface；
- 明早维护者应先审阅本记录、W4 页面和 W5A 边界，再决定是否允许 Candidate-first promotion。

## 远端候选证据

- Implementation candidate `2bc62077a4127da0e450857df84c10c293368ddd`，GitHub Actions [`32603440758`](https://github.com/yw9299-stack/project-orrery/actions/runs/32603440758)；
- Ubuntu：PASS，1m16s；
- Windows attempt 1：唯一错误为既有 `test_graphical_ai_settings_api_is_local_and_never_echoes_keys` 对本机假上游的 10s HTTP timeout；W3/W4/W5 新增测试全部通过；
- Windows attempt 2：同一 SHA PASS，8m44s；首次失败保留，不重分类；
- 本次状态同步会形成新的纯文档 SHA；它必须再次取得 required checks，才是可由维护者批准的最终 merge candidate。

## Windows 本机 HTTP 测试装置修复

- 状态同步 SHA `43678f6` 的 GitHub Actions [`33095474987`](https://github.com/yw9299-stack/project-orrery/actions/runs/33095474987)：Ubuntu PASS（1m11s），Windows 唯一错误仍是图形化 AI 设置测试对 `127.0.0.1:9` 的 10s 本机请求 timeout；W3/W4/W5 新增测试均通过；
- 关闭端口在 Windows hosted runner 上并不保证立即 connection-refused，连续两个 SHA 复现后不再允许靠 rerun 碰运气；
- 测试改为在进程内启动 loopback `ThreadingHTTPServer`，确定性返回 HTTP 503；仍验证 docsite 返回 500、失败关闭且不回显 API Key，不改变产品代码或放宽外部网络边界；
- 修复后定向动态测试 1/1 PASS，4.767s；包含本段和装置修复的最终 exact SHA 必须重新取得 Windows／Ubuntu required checks。
