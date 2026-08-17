#!/usr/bin/env python3
"""Deterministic no-network Codex CLI stand-in for pilot runner tests."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().astimezone().isoformat()


def parse_contract(prompt: str) -> tuple[str, str, list[str], list[str]]:
    task_match = re.search(r"<!-- task_id: (PO-CR-\d{3}) -->", prompt)
    variant_match = re.search(r"<!-- variant: ([ABC]) -->", prompt)
    if not task_match or not variant_match:
        raise ValueError("Prompt contract identity is missing")

    writes_section = prompt.split("## expected_product_writes", 1)[1].split("## validation_commands", 1)[0]
    validation_section = prompt.split("## validation_commands", 1)[1].split("---", 1)[0]
    writes = re.findall(r"^- `([^`]+)`$", writes_section, flags=re.MULTILINE)
    validations = re.findall(r"^- `([^`]+)`$", validation_section, flags=re.MULTILINE)
    if not writes or not validations:
        raise ValueError("Prompt contract paths or validation commands are missing")
    return task_match.group(1), variant_match.group(1), writes, validations


def event(sequence: int, kind: str, scope: str, target: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "sequence": sequence,
        "event_type": kind,
        "target_scope": scope,
        "target": target,
        "reason_code": overrides.pop("reason_code", None),
        "content_extent": overrides.pop("content_extent", None),
        "range_or_query": overrides.pop("range_or_query", None),
        "declared_before_access": overrides.pop("declared_before_access", None),
    }
    value.update(overrides)
    return value


def main() -> int:
    arguments = sys.argv[1:]
    if arguments == ["--version"]:
        print("mock-codex 1.0")
        return 0
    if not arguments or arguments[0] != "exec":
        print("mock only supports --version and exec", file=sys.stderr)
        return 64

    repository = Path(arguments[arguments.index("-C") + 1]).resolve()
    final_path = Path(arguments[arguments.index("-o") + 1]).resolve()
    prompt = sys.stdin.read()
    task_id, variant, writes, validations = parse_contract(prompt)
    started_at = now()

    product_paths = [repository / writes[0]]
    if task_id == "PO-CR-006":
        product_paths.extend(repository / relative for relative in writes[1:])
    for product_path in product_paths:
        suffix = (
            "\n<!-- mock pilot change -->\n"
            if product_path.suffix.lower() == ".md"
            else "\n# mock pilot change\n"
        )
        product_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if product_path.exists() else "w"
        with product_path.open(mode, encoding="utf-8", newline="\n") as handle:
            handle.write(suffix)

    events: list[dict[str, object]] = []
    if variant == "A":
        fixed_chain = [
            "README.md",
            "skills/project-orrery/SKILL.md",
            "skills/project-orrery/references/architecture.md",
            "skills/project-orrery/references/migration-contract.md",
            "skills/project-orrery/assets/project-template/AGENTS.md",
            "skills/project-orrery/scripts/install_project_orrery.py",
            "skills/project-orrery/scripts/validate_installation.py",
        ]
        for path in fixed_chain:
            events.append(
                event(
                    len(events) + 1,
                    "content_read",
                    "repository",
                    path,
                    reason_code="fixed-chain",
                    content_extent="full",
                    declared_before_access=True,
                )
            )
        context_manifest = None
        selected_evidence = None
    else:
        context_manifest = {
            "task_classification": "mock integration task",
            "retrieval_strategy": None if variant == "B" else "single_file",
            "initial_content_paths": [{"path": writes[0], "reason": "mock targeted evidence"}],
            "expected_product_writes": writes,
            "expected_validation": validations,
            "expansion_conditions": ["expand only when contracted evidence is insufficient"],
            "content_file_budget": None if variant == "B" else 2,
        }
        selected_evidence = (
            None
            if variant == "B"
            else [{"path": writes[0], "scope": "full", "fact": "mock evidence selected"}]
        )
        events.append(
            event(
                1,
                "content_read",
                "repository",
                writes[0],
                reason_code="manifest-initial",
                content_extent="full",
                declared_before_access=True,
            )
        )

    for product_path in product_paths:
        events.append(
            event(
                len(events) + 1,
                "write",
                "repository",
                product_path.relative_to(repository).as_posix(),
                reason_code="contracted-product-write",
                declared_before_access=True,
            )
        )
    for validation in validations:
        kind = "test" if "unittest" in validation or "py_compile" in validation else "command"
        events.append(event(len(events) + 1, kind, "command", validation, reason_code="validation"))
    events.append(
        event(
            len(events) + 1,
            "write",
            "repository",
            ".benchmark/agent-receipt.json",
            reason_code="agent-self-report",
            declared_before_access=True,
        )
    )

    receipt = {
        "schema_version": 1,
        "pilot_id": "pilot-003",
        "prompt_revision": "po-context-routing-pilot-003-v2",
        "task_id": task_id,
        "variant": variant,
        "external_context_preflight": "clean",
        "agent_started_at": started_at,
        "agent_ended_at": now(),
        "prewrite": {
            "context_manifest": context_manifest,
            "selected_evidence": selected_evidence,
        },
        "events": events,
        "operator_questions": [],
        "validation": [f"passed: {command}" for command in validations],
        "uncertainty": [],
        "evidence_note": "Agent self-report; not an independent Harness audit",
    }
    receipt_path = repository / ".benchmark" / "agent-receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_text = f"Mock completed {task_id}-{variant}; receipt: .benchmark/agent-receipt.json"
    final_path.write_text(final_text + "\n", encoding="utf-8")
    thread_id = f"mock-{task_id.lower()}-{variant.lower()}"
    jsonl = [
        {"type": "thread.started", "thread_id": thread_id},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": final_text}},
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 20,
                "output_tokens": 10,
                "reasoning_output_tokens": 5,
            },
        },
    ]
    for item in jsonl:
        print(json.dumps(item, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
