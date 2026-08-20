# {{PROJECT_TITLE}} documentation

This directory follows the Project Orrery authority model.

`product intent -> Seed -> effective ADR -> approved Design -> implementation -> State Docs -> Validation -> Snapshot`

Backlog and Library feed proposals. PROGRESS and HANDOFF guide current readers. DEVLOG preserves implementation history.

Run `start-docsite.bat` from the repository root to open the local reader after installing `scripts/docsite/requirements.txt`. Dynamic AI calls are Broker-only: managed mode provides caching and budget controls but is not an isolation boundary from same-user processes; use an external `scripts/docsite/llm_broker.py` under a separate OS identity when Provider-key isolation is required.
