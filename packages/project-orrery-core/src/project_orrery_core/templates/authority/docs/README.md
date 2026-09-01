# {{PROJECT_TITLE}} documentation

This directory follows the Project Orrery authority model.

`product intent -> Seed -> effective ADR -> approved Design -> implementation -> State Docs -> Validation -> Snapshot`

Backlog and Library feed proposals. PROGRESS and HANDOFF guide current readers. DEVLOG preserves implementation history.

After installing `scripts/docsite/requirements.txt`, Windows users can run `Start Orrery.vbs` for the normal hidden-console experience or `Start Orrery Console.bat` for one diagnostic console. Both reuse the same Unified supervisor, PID, port, and loopback URL. Dynamic AI calls are Broker-only: managed mode provides caching and budget controls but is not an isolation boundary from same-user processes; use an external `scripts/docsite/llm_broker.py` under a separate OS identity when Provider-key isolation is required.
