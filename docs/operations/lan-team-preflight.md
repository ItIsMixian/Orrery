# LAN Team 双机验收 preflight

Status: Candidate runbook

Updated: 2026-08-27

本说明为未来真实双机验收准备；W5D 单机 Harness **不证明**真实网卡、交换机、防火墙、睡眠／唤醒或跨 OS LAN 已通过。

## 安全前提

- 两台设备持有同一项目历史与 `.project-orrery.json`，但使用独立 clone、member／device／host identity 和 Git-private credential。
- 只使用私有 IPv4 literal；不要填 DNS 名、公网 IP、端口转发、云 relay 或常驻公网服务。
- Team enable、Coordinator Host 和 discovery 是三个独立本机动作。`team enable` 本身不监听、不广播；停止 discovery/Host 或 disable 后检查端口已经消失。
- 发现候选永远是不可信提示。必须继续校验 opaque project fingerprint、一次性 invitation、成员身份与 Host-local Admin 确认；发现本身不能读取 Team projection。
- 本轮协议仍是实验性未发布源码；真实验收应在受信任局域网和临时测试项目／凭据上完成，不使用生产秘密。

## 双机步骤

以下使用已安装的 `project-orrery` 入口；源码 checkout 可通过等价的包入口运行。

1. 两端先执行 `project-orrery team status --target <repo> --json`，确认初始为 Personal zero-network；记录各自 `git rev-parse HEAD`、OS、Python、Core／CLI 版本和私有 IPv4。
2. Host 端显式执行：

   ```text
   project-orrery team enable --target <repo> --member-id <owner> --device-id <device-a> --host-id <host-a> --allow-lan-bind
   project-orrery team serve --target <repo> --bind 0.0.0.0 --advertise-address <host-private-ip> --port <coordinator-port>
   ```

3. 在另一个 Host 终端显式启动最小广播；停止该进程即完全停止 discovery：

   ```text
   project-orrery team discovery-serve --target <repo> --endpoint http://<host-private-ip>:<coordinator-port> --target-ip 255.255.255.255 --port 42853
   ```

4. 成员端 enable Team（这一步仍不监听／广播），再运行有界扫描：

   ```text
   project-orrery team enable --target <repo> --member-id <reviewer> --device-id <device-b> --host-id <host-b> --allow-lan-bind
   project-orrery team discovery-scan --target <repo> --bind-ip 0.0.0.0 --port 42853 --timeout-seconds 2 --json
   ```

   记录 candidate ID、fingerprint 是否匹配和 `membership_granted=false`。若广播被防火墙阻断，继续第 5 步的手工 endpoint fallback，不降低 join 门。

5. Host 创建一小时内过期的 invitation；成员以 candidate ID 选择发现地址，或省略 candidate ID 使用 invitation 中的手工地址：

   ```text
   project-orrery team invite-create --target <host-repo> --candidate-member-id <reviewer> --endpoint http://<host-private-ip>:<coordinator-port> --json
   project-orrery team join-request --target <member-repo> --invite <invite> --candidate-id <candidate-id> --json
   project-orrery team join-confirm --target <host-repo> --request-id <request-id> --json
   project-orrery team join-finalize --target <member-repo> --json
   ```

6. 两端分别 capture/sync，验证 Member → Workstream、TTL Stale／Unknown、断线期间本地 Git 工作不受影响；恢复 Host 后验证 revision 继续单调增加，旧 revision 被拒绝。
7. 手工 Coordinator Host switch 由当前 Host-local Admin 创建 10 分钟内过期的 switch invitation，目标成员 claim 后再启动新 Host。旧 Host 必须返回 retired，不能接受新 revision；不得观察到自动 leader election。
8. 发送 request-only 请求并在目标成员本机 accept/reject，确认 receipt 恒为 `execution_performed=false`；撤销 capability 后验证旧 credential 立即失败。

## 结束与证据

- 停止 discovery 与两个 Host 进程，随后 `team disable`；验证本地 branch、worktree、Validation 与作者文档未删除或改写。
- 原始日志、IP、临时 invitation 和 credential 只留在受限的仓库外运行根。提交到 Git 的 Validation 只保留脱敏阶段结果、命令、版本、校验和与 machine-readable verdict。
- 只有两台真实设备完成上述步骤后，才能新增“真实 LAN 已验证”的窄范围结论；不得从单机 loopback／受控 transport 外推。
