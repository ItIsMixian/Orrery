# Context-routing design candidates

Designs in this directory are research proposals. They have no authority over the released Project Orrery Skill until an explicit ADR accepts them.

- [Orrery Context Aperture v0.1 (Simplified Chinese)](context-aperture-v0.1.zh-CN.md)
- [Orrery Context Aperture H2 (Simplified Chinese)](context-aperture-v0.2-h2.zh-CN.md)
- [Harness content-read proof v0.1 (Simplified Chinese)](harness-content-read-proof-v0.1.zh-CN.md)
- [Raw evidence retention v0.1 (Simplified Chinese)](raw-evidence-retention-v0.1.zh-CN.md)
- [Context Manifest B adoption candidate v0.1 (Simplified Chinese)](context-manifest-b-adoption-v0.1.zh-CN.md)
- [Skill Entry Router R v0.1 (Simplified Chinese)](skill-entry-router-v0.1.zh-CN.md)
- [Scope Acquisition Router S v0.1 (Simplified Chinese)](scope-acquisition-router-v0.1.zh-CN.md)
- [Real-development task and Oracle v0.2 (Simplified Chinese)](real-development-task-oracle-v0.2.zh-CN.md)
- [Pilot 003 evidence](../results/2026-08-18-pilot-003-terra-medium.md)
- [Pilot 003 B/C confirmatory evidence](../results/2026-08-18-pilot-003-bc-confirmatory-terra-medium.md)
- [Pilot 004 B/H holdout evidence](../results/2026-08-18-pilot-004-bh-holdout-terra-medium.md)
- [Pilot 005 / 006 B/H2 evidence](../results/2026-08-18-pilot-005-006-bh2-terra-medium.md)

All current candidates remain non-authoritative. H2 removed model-authored protocol prose and used a Harness read proxy plus independent CLI-event auditing, but the paired Pilot 006 tasks found 18.5% higher total input than B. H2 therefore failed its frozen adoption gate and will not receive an adoption ADR.

Pilot 007 froze the historical B label and completed a direct comparison with current process P. The run exposed a shared formal-validation defect; corrected task quality remained equal while B missed every cost/benefit gate. B is not adopted. See the [Pilot 007 R2 result](../results/2026-08-18-pilot-007-pb-adoption-terra-medium.md).

Pilot 008 originally prepared Skill Entry Router R, but no model sample ran. ADR-0005 corrected the primary
question to cumulative input before the first product write. The reframed S candidate keeps the frozen Skill
constant and varies only the target repository's linear versus task-first Agent entrance; passive app-server
usage measurement replaces Agent-authored protocol. R remains an unadopted historical candidate.

Pilot 009 completed six valid P/S runs. S met every frozen cost guard, including aggregate pre-write input at
82.74% of P, but corrected task quality was only 2/3 on both sides. S is not adopted. The task/Oracle v0.2
candidate separates behavioral, safety, scope, structured-State and narrative verdicts and adds paraphrase and
mutation controls before another Pilot.

The [C1 Oracle v0.2 static controls](../results/2026-08-22-c1-oracle-v0.2-static-controls.md) implement that model-free gate
with 20 passing cases. They permit a request for Pilot 010 design only; no Pilot 010 packet or model run exists.
