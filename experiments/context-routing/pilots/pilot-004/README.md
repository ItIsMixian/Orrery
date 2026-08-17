# Project Orrery context-routing pilot 004

> Status: completed once; raw run sealed, v1 Oracle apparatus failure documented  
> Authority: research infrastructure; not an ADR or released routing policy

Pilot 004 compares the existing B baseline with a new H (hybrid Context
Aperture) treatment. The task suite is prospective: it uses a frozen product
baseline and independent operator acceptance, not a reference patch stored in
the Agent repository.

- [Task-suite design](TASK-DESIGN.zh-CN.md)
- [Operator acceptance design](operator/acceptance-design.zh-CN.md)
- [Frozen H treatment](variants/H.zh-CN.md)
- [Corrected read-only review Oracle](operator/holdout_acceptance_v2.py)
- [Result and adoption decision](../../results/2026-08-18-pilot-004-bh-holdout-terra-medium.md)
- Agent-facing task drafts are under `tasks/`.

The six Agent runs used `gpt-5.6-terra` at medium reasoning. H matched B on
correctness and reduced self-reported reads, but used 47% more input tokens,
so it was not promoted into an ADR or released routing policy.
