#!/usr/bin/env python3
"""Model-free layered Oracle and controls for context-routing task/Oracle v0.2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any


CONTROL_ROOT = Path(__file__).resolve().parent
FIXTURE_SOURCE = CONTROL_ROOT / "fixture-source"
FIXTURE_MANIFEST = CONTROL_ROOT / "fixture-manifest.json"
CLEAN_APPARATUS = CONTROL_ROOT / "apparatus-clean.json"
TASK_ID = "C1"
REQUIRED_FILES = {
    "src/orrery_fixture/__init__.py",
    "src/orrery_fixture/feedback.py",
    "src/orrery_fixture/storage.py",
    "docs/state/application.facts.json",
    "docs/PROGRESS.md",
    "tests/__init__.py",
    "tests/test_application.py",
}
EXPECTED_CHANGES = {
    "src/orrery_fixture/feedback.py",
    "src/orrery_fixture/storage.py",
    "docs/state/application.facts.json",
    "docs/PROGRESS.md",
}


FACT_RULES = {
    "feedback_auto_expiry": {
        "positive": (
            r"automatic expiry (?:now )?preserves (?:a |the )?user[- ]controlled snooze deadline",
            r"auto[- ]?expiry no longer (?:creates|extends)(?: or extends)? .*cooldowns? chosen by users",
            r"自动过期.*不会.*(?:创建|延长).*用户.*(?:稍后|暂停).*(?:期限|时间)",
        ),
        "contradiction": (
            r"automatic expiry still (?:creates|extends)(?: or extends)? .*cooldowns?",
            r"自动过期仍会.*(?:创建|延长).*用户.*(?:稍后|暂停)",
        ),
    },
    "v1_to_v2_migration": {
        "positive": (
            r"sqlite schema v?1[- ]to[- ]v?2 migration preserves existing rows and is repeatable",
            r"upgrading version 1 to version 2 keeps prior feedback rows and can safely run again",
            r"从版本 ?1升级到版本 ?2.*保留.*(?:记录|数据).*(?:重复执行|再次运行)",
        ),
        "contradiction": (
            r"storage remains at schema v?1;? .*v?2 migration is not implemented",
            r"存储仍(?:然)?是版本 ?1.*版本 ?2.*(?:尚未实现|没有实现)",
        ),
    },
    "future_version_rejection": {
        "positive": (
            r"future schema versions are rejected before any database write",
            r"a newer database schema is refused before changing stored data",
            r"未来版本数据库.*写入前拒绝.*(?:原有数据|数据).*(?:保持不变|不会改变)",
        ),
        "contradiction": (
            r"newer schema versions are accepted and normalized automatically",
            r"未来版本数据库.*(?:自动降级|接受后改写)",
        ),
    },
}


PROGRESS_VARIANTS = (
    """# Current progress

- Automatic expiry now preserves a user-controlled snooze deadline.
- SQLite schema v1-to-v2 migration preserves existing rows and is repeatable.
- Future schema versions are rejected before any database write.
- Four automated tests cover the baseline.
""",
    """# Current progress

- Auto expiry no longer creates or extends cooldowns chosen by users.
- Upgrading version 1 to version 2 keeps prior feedback rows and can safely run again.
- A newer database schema is refused before changing stored data.
- The baseline has four automated tests.
""",
    """# 当前进展

- 自动过期现在不会创建或延长用户主动设置的稍后期限。
- 从版本 1升级到版本 2 会保留原有记录，并且可以重复执行。
- 未来版本数据库会在写入前拒绝，原有数据保持不变。
- 当前基线包含四项自动化测试。
""",
)


POSITIVE_STORAGE = '''\
"""SQLite initialization with an idempotent, conservative v2 migration."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_VERSION = 2


def initialize_database(path: str | Path) -> None:
    connection = sqlite3.connect(path)
    try:
        current_version = connection.execute("PRAGMA user_version").fetchone()[0]
        if current_version > SCHEMA_VERSION:
            raise RuntimeError(f"unsupported future schema version: {current_version}")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS feedback ("
            "id INTEGER PRIMARY KEY, status TEXT NOT NULL, snoozed_until INTEGER)"
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(feedback)")}
        if "snoozed_until" not in columns:
            connection.execute("ALTER TABLE feedback ADD COLUMN snoozed_until INTEGER")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_control_status_deadline "
            "ON feedback(status, snoozed_until)"
        )
        connection.execute("PRAGMA user_version = 2")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
'''


def _dimension(verdict: str, findings: list[str] | None = None) -> dict[str, Any]:
    return {"verdict": verdict, "findings": findings or []}


def _combine(verdicts: list[str]) -> str:
    if "fail" in verdicts:
        return "fail"
    if "manual_review_required" in verdicts:
        return "manual_review_required"
    if verdicts and all(value == "pass" for value in verdicts):
        return "pass"
    return "not_evaluated"


def _run(arguments: list[str], repository: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        arguments,
        cwd=repository,
        env=environment,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=60,
    )


def _changed_paths(repository: Path) -> tuple[set[str], list[str]]:
    result = _run(["git", "status", "--porcelain=v1", "-z"], repository)
    if result.returncode:
        return set(), ["git status failed: " + (result.stdout + result.stderr).strip()]
    paths: set[str] = set()
    for entry in result.stdout.split("\0"):
        if not entry:
            continue
        value = entry[3:] if len(entry) > 3 else entry
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.add(value.replace("\\", "/"))
    return paths, []


def _validate_state_shape(value: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(value, dict):
        return ["State root must be an object"]
    if set(value) != {"schema_version", "authority", "component", "facts"}:
        failures.append("State root fields do not match the public schema")
    if value.get("schema_version") != 1:
        failures.append("State schema_version must be 1")
    if value.get("authority") != "state" or value.get("component") != "application":
        failures.append("State authority/component identity is invalid")
    facts = value.get("facts")
    if not isinstance(facts, dict) or set(facts) != {"feedback", "storage", "validation"}:
        return failures + ["State facts must expose feedback, storage and validation"]
    feedback = facts.get("feedback")
    if not isinstance(feedback, dict) or set(feedback) != {"auto_expiry_policy"}:
        failures.append("feedback State fields are invalid")
    elif feedback["auto_expiry_policy"] not in {"unknown", "bug_present", "fixed_preserves_user_snooze"}:
        failures.append("feedback.auto_expiry_policy has an invalid enum")
    storage = facts.get("storage")
    storage_keys = {"schema_version", "v2_migration", "future_version_policy"}
    if not isinstance(storage, dict) or set(storage) != storage_keys:
        failures.append("storage State fields are invalid")
    else:
        if not isinstance(storage["schema_version"], int) or isinstance(storage["schema_version"], bool) or storage["schema_version"] < 1:
            failures.append("storage.schema_version must be a positive integer")
        if storage["v2_migration"] not in {"not_implemented", "implemented"}:
            failures.append("storage.v2_migration has an invalid enum")
        if storage["future_version_policy"] not in {"unknown", "reject_before_write"}:
            failures.append("storage.future_version_policy has an invalid enum")
    validation = facts.get("validation")
    if not isinstance(validation, dict) or set(validation) != {"automated_tests"}:
        failures.append("validation State fields are invalid")
    elif not isinstance(validation["automated_tests"], int) or isinstance(validation["automated_tests"], bool) or validation["automated_tests"] < 0:
        failures.append("validation.automated_tests must be a non-negative integer")
    return failures


def _apparatus_verdict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _dimension("error", ["apparatus input must be an object"])
    expected = {
        "schema_version",
        "repository_boundary_valid",
        "external_reads",
        "unknown_tools",
        "sealed_inputs_modified",
    }
    errors: list[str] = []
    if set(value) != expected or value.get("schema_version") != 1:
        errors.append("apparatus input does not match schema version 1")
    if not isinstance(value.get("repository_boundary_valid"), bool):
        errors.append("repository_boundary_valid must be boolean")
    if not isinstance(value.get("external_reads"), list) or not all(isinstance(item, str) for item in value.get("external_reads", [])):
        errors.append("external_reads must be a string array")
    if not isinstance(value.get("unknown_tools"), list) or not all(isinstance(item, str) for item in value.get("unknown_tools", [])):
        errors.append("unknown_tools must be a string array")
    if not isinstance(value.get("sealed_inputs_modified"), bool):
        errors.append("sealed_inputs_modified must be boolean")
    if errors:
        return _dimension("error", errors)
    findings: list[str] = []
    if not value["repository_boundary_valid"]:
        findings.append("repository boundary was not proven")
    if value["external_reads"]:
        findings.append("external reads: " + ", ".join(value["external_reads"]))
    if value["unknown_tools"]:
        findings.append("unknown tools: " + ", ".join(value["unknown_tools"]))
    if value["sealed_inputs_modified"]:
        findings.append("sealed inputs were modified")
    return _dimension("contaminated" if findings else "clean", findings)


def _formal_verdict(repository: Path, task_id: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    failures: list[str] = []
    state_value: dict[str, Any] | None = None
    if task_id != TASK_ID:
        failures.append(f"unsupported task identity: {task_id}")
    missing = sorted(path for path in REQUIRED_FILES if not (repository / path).is_file())
    if missing:
        failures.append("missing public fixture files: " + ", ".join(missing))
    for relative in ("src/orrery_fixture/feedback.py", "src/orrery_fixture/storage.py"):
        path = repository / relative
        if not path.is_file():
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as error:
            failures.append(f"{relative} is not valid UTF-8 Python: {error}")
    state_path = repository / "docs/state/application.facts.json"
    if state_path.is_file():
        try:
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            failures.append(f"public State JSON cannot be read: {error}")
        else:
            failures.extend(_validate_state_shape(loaded))
            if isinstance(loaded, dict):
                state_value = loaded
    tests = _run(
        [sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-v"],
        repository,
    )
    if tests.returncode:
        failures.append("public fixture tests failed: " + (tests.stdout + tests.stderr).strip())
    elif "Ran 4 tests" not in tests.stdout + tests.stderr:
        failures.append("public fixture test discovery did not find the declared four tests")
    return _dimension("fail" if failures else "pass", failures), state_value


def _feedback_behavior(repository: Path) -> dict[str, Any]:
    code = textwrap.dedent(
        """
        from orrery_fixture.feedback import Feedback

        expired = Feedback(due_at=10)
        expired.auto_expire(10)
        assert expired.status == "expired"
        assert expired.snoozed_until is None

        existing = Feedback(due_at=10, snoozed_until=25)
        existing.auto_expire(10)
        existing.auto_expire(100)
        assert existing.status == "expired"
        assert existing.snoozed_until == 25

        snoozed = Feedback(due_at=15)
        snoozed.snooze(10, 20)
        snoozed.auto_expire(20)
        assert snoozed.status == "snoozed"
        assert snoozed.snoozed_until == 30
        snoozed.tick(30)
        assert snoozed.status == "pending" and snoozed.snoozed_until is None
        """
    )
    result = _run([sys.executable, "-X", "utf8", "-c", code], repository)
    if result.returncode:
        return _dimension("fail", ["public Feedback lifecycle failed: " + (result.stdout + result.stderr).strip()])
    return _dimension("pass")


def _storage_behavior(repository: Path) -> tuple[dict[str, Any], bool]:
    code = textwrap.dedent(
        """
        import json
        import sqlite3
        import tempfile
        from pathlib import Path
        from orrery_fixture.storage import SCHEMA_VERSION, initialize_database

        checks = {"schema_constant": SCHEMA_VERSION == 2}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old_path = root / "old.db"
            connection = sqlite3.connect(old_path)
            try:
                connection.execute("CREATE TABLE feedback (id INTEGER PRIMARY KEY, status TEXT NOT NULL)")
                connection.execute("INSERT INTO feedback(id, status) VALUES (7, 'pending')")
                connection.execute("PRAGMA user_version = 1")
                connection.commit()
            finally:
                connection.close()
            initialize_database(old_path)
            initialize_database(old_path)
            connection = sqlite3.connect(old_path)
            try:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(feedback)")}
                index_names = [row[1] for row in connection.execute("PRAGMA index_list(feedback)")]
                index_columns = [
                    [row[2] for row in connection.execute(f"PRAGMA index_info('{name}')")]
                    for name in index_names
                ]
                row = connection.execute("SELECT id, status, snoozed_until FROM feedback WHERE id=7").fetchone()
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            finally:
                connection.close()
            checks.update({
                "v2_shape": {"id", "status", "snoozed_until"} <= columns and version == 2,
                "index_order": ["status", "snoozed_until"] in index_columns,
                "old_row_preserved": row == (7, "pending", None),
                "idempotent": True,
            })

            future_path = root / "future.db"
            connection = sqlite3.connect(future_path)
            try:
                connection.execute("CREATE TABLE feedback (id INTEGER PRIMARY KEY, status TEXT NOT NULL, future_value TEXT)")
                connection.execute("INSERT INTO feedback VALUES (9, 'pending', 'keep-me')")
                connection.execute("PRAGMA user_version = 3")
                connection.commit()
            finally:
                connection.close()
            rejected = False
            try:
                initialize_database(future_path)
            except (RuntimeError, ValueError):
                rejected = True
            connection = sqlite3.connect(future_path)
            try:
                future_version = connection.execute("PRAGMA user_version").fetchone()[0]
                future_columns = [row[1] for row in connection.execute("PRAGMA table_info(feedback)")]
                future_row = connection.execute("SELECT * FROM feedback WHERE id=9").fetchone()
                future_indexes = list(connection.execute("PRAGMA index_list(feedback)"))
            finally:
                connection.close()
            checks["future_rejected_before_write"] = (
                rejected
                and future_version == 3
                and future_columns == ["id", "status", "future_value"]
                and future_row == (9, "pending", "keep-me")
                and future_indexes == []
            )
        print(json.dumps(checks, sort_keys=True))
        """
    )
    result = _run([sys.executable, "-X", "utf8", "-c", code], repository)
    if result.returncode:
        return _dimension("fail", ["public SQLite path failed: " + (result.stdout + result.stderr).strip()]), False
    try:
        checks = json.loads(result.stdout)
    except json.JSONDecodeError:
        return _dimension("fail", ["public SQLite probe returned invalid JSON"]), False
    failed = sorted(name for name, passed in checks.items() if passed is not True)
    return _dimension("fail" if failed else "pass", ["failed storage checks: " + ", ".join(failed)] if failed else []), bool(checks.get("future_rejected_before_write"))


def _narrative_verdict(repository: Path) -> dict[str, Any]:
    try:
        progress = (repository / "docs/PROGRESS.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return _dimension("fail", [f"PROGRESS cannot be read: {error}"])
    lowered = progress.lower()
    fact_results: dict[str, str] = {}
    findings: list[str] = []
    for fact_id, rules in FACT_RULES.items():
        contradicted = [pattern for pattern in rules["contradiction"] if re.search(pattern, lowered, re.IGNORECASE | re.DOTALL)]
        supported = [pattern for pattern in rules["positive"] if re.search(pattern, lowered, re.IGNORECASE | re.DOTALL)]
        if contradicted:
            fact_results[fact_id] = "fail"
            findings.append(f"{fact_id}: explicit contradiction remains")
        elif supported:
            fact_results[fact_id] = "pass"
        else:
            fact_results[fact_id] = "manual_review_required"
            findings.append(f"{fact_id}: no declared fact-unit paraphrase matched")
    result = _dimension(_combine(list(fact_results.values())), findings)
    result["facts"] = fact_results
    return result


def evaluate(repository: Path, apparatus: dict[str, Any], task_id: str = TASK_ID) -> dict[str, Any]:
    apparatus_result = _apparatus_verdict(apparatus)
    formal, state = _formal_verdict(repository, task_id)
    if formal["verdict"] == "pass":
        behavior = _feedback_behavior(repository)
        data_safety, future_runtime = _storage_behavior(repository)
        changed, change_errors = _changed_paths(repository)
        scope_findings = list(change_errors)
        missing = sorted(EXPECTED_CHANGES - changed)
        unexpected = sorted(changed - EXPECTED_CHANGES)
        if missing:
            scope_findings.append("required changes missing: " + ", ".join(missing))
        if unexpected:
            scope_findings.append("protected or unrelated paths changed: " + ", ".join(unexpected))
        scope = _dimension("fail" if scope_findings else "pass", scope_findings)
        narrative = _narrative_verdict(repository)
    else:
        behavior = data_safety = scope = narrative = _dimension("not_evaluated", ["formal validity failed"])
        future_runtime = False

    structured_findings: list[str] = []
    future_findings: list[str] = []
    omissions: list[str] = []
    if state is None or formal["verdict"] != "pass":
        structured = _dimension("not_evaluated", ["valid public State is unavailable"])
        future = _dimension("not_evaluated", ["valid public State is unavailable"])
    else:
        facts = state["facts"]
        expected = {
            "feedback.auto_expiry_policy": (facts["feedback"]["auto_expiry_policy"], "fixed_preserves_user_snooze"),
            "storage.schema_version": (facts["storage"]["schema_version"], 2),
            "storage.v2_migration": (facts["storage"]["v2_migration"], "implemented"),
            "validation.automated_tests": (facts["validation"]["automated_tests"], 4),
        }
        for field, (actual, wanted) in expected.items():
            if actual != wanted:
                omissions.append(field)
                structured_findings.append(f"{field} expected {wanted!r}, found {actual!r}")
        structured = _dimension("fail" if structured_findings else "pass", structured_findings)
        if facts["storage"]["future_version_policy"] != "reject_before_write":
            omissions.append("storage.future_version_policy")
            future_findings.append("public State omits reject_before_write")
        if not future_runtime:
            future_findings.append("public storage path does not reject a future schema before write")
        future = _dimension("fail" if future_findings else "pass", future_findings)

    semantic_dimensions = {
        "behavior": behavior,
        "data_safety": data_safety,
        "scope": scope,
        "narrative_consistency": narrative,
    }
    semantic = {
        "verdict": _combine([item["verdict"] for item in semantic_dimensions.values()]),
        "dimensions": semantic_dimensions,
    }
    future_narrative_verdict = narrative.get("facts", {}).get("future_version_rejection", "not_evaluated")
    narrative_future = _dimension(future_narrative_verdict)
    if future_narrative_verdict == "manual_review_required":
        narrative_future["findings"].append(
            "required future-version narrative was not recognized; manual review is required"
        )
        omissions.append("narrative.future_version_rejection")
    elif future_narrative_verdict == "fail":
        narrative_future["findings"].append("future-version narrative contains an explicit contradiction")
    state_dimensions = {
        "structured_state": structured,
        "future_version_safeguard": future,
        "narrative_future_version": narrative_future,
    }
    state_layer = {
        "verdict": _combine([item["verdict"] for item in state_dimensions.values()]),
        "dimensions": state_dimensions,
        "omissions": omissions,
    }
    if apparatus_result["verdict"] == "error":
        overall = "apparatus_error"
    elif apparatus_result["verdict"] == "contaminated":
        overall = "contaminated"
    elif formal["verdict"] == "fail" or semantic["verdict"] == "fail" or state_layer["verdict"] == "fail":
        overall = "fail"
    elif "manual_review_required" in {semantic["verdict"], state_layer["verdict"]}:
        overall = "manual_review_required"
    elif formal["verdict"] == semantic["verdict"] == state_layer["verdict"] == "pass":
        overall = "pass"
    else:
        overall = "fail"
    return {
        "schema_version": 2,
        "oracle_version": "0.2-static.1",
        "task_id": task_id,
        "overall_verdict": overall,
        "layers": {
            "apparatus_contamination": apparatus_result,
            "formal_validity": formal,
            "semantic_quality": semantic,
            "state_future_version": state_layer,
        },
    }


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def _initialize_repository(repository: Path) -> None:
    for command in (
        ["git", "init", "-b", "oracle-v0-2-fixture"],
        ["git", "config", "core.autocrlf", "false"],
        ["git", "add", "--all"],
        ["git", "-c", "user.name=Project Orrery Control", "-c", "user.email=control@local.invalid", "commit", "-m", "static control baseline"],
    ):
        result = _run(command, repository)
        if result.returncode:
            raise RuntimeError("cannot initialize static control repository: " + result.stdout + result.stderr)


def _positive_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "authority": "state",
        "component": "application",
        "facts": {
            "feedback": {"auto_expiry_policy": "fixed_preserves_user_snooze"},
            "storage": {
                "schema_version": 2,
                "v2_migration": "implemented",
                "future_version_policy": "reject_before_write",
            },
            "validation": {"automated_tests": 4},
        },
    }


def _apply_positive(repository: Path, progress_variant: int = 0) -> None:
    feedback = repository / "src/orrery_fixture/feedback.py"
    text = feedback.read_text(encoding="utf-8").replace(
        "            self.snoozed_until = max(self.snoozed_until or 0, now + 3600)\n",
        "            # Automatic expiry preserves the user's explicit snooze deadline.\n",
    )
    _write_text(feedback, text)
    _write_text(repository / "src/orrery_fixture/storage.py", POSITIVE_STORAGE)
    _write_text(
        repository / "docs/state/application.facts.json",
        json.dumps(_positive_state(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_text(repository / "docs/PROGRESS.md", PROGRESS_VARIANTS[progress_variant])


def _make_repository(root: Path, name: str, *, positive: bool = True, progress_variant: int = 0) -> Path:
    repository = root / name
    shutil.copytree(FIXTURE_SOURCE, repository)
    _initialize_repository(repository)
    if positive:
        _apply_positive(repository, progress_variant)
    return repository


def _expect(case: str, report: dict[str, Any], *, overall: str, path: tuple[str, ...] | None = None, verdict: str | None = None) -> None:
    if report["overall_verdict"] != overall:
        raise AssertionError(f"{case}: overall {report['overall_verdict']!r}, expected {overall!r}")
    if path is not None:
        current: Any = report
        for key in path:
            current = current[key]
        if current["verdict"] != verdict:
            raise AssertionError(f"{case}: {'.'.join(path)}={current['verdict']!r}, expected {verdict!r}")


def verify_fixture() -> dict[str, Any]:
    manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    try:
        schema = json.loads((CONTROL_ROOT / "public-state.schema.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        schema = {}
        failures.append(f"public State schema cannot be read: {error}")
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or schema.get("type") != "object":
        failures.append("public State schema does not declare the frozen JSON Schema contract")
    try:
        fixture_state = json.loads(
            (FIXTURE_SOURCE / "docs/state/application.facts.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        failures.append(f"public State fixture cannot be read: {error}")
    else:
        failures.extend("public State fixture: " + item for item in _validate_state_shape(fixture_state))
    declared: set[str] = set()
    for entry in manifest.get("files", []):
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            failures.append("invalid manifest entry")
            continue
        declared.add(relative)
        path = FIXTURE_SOURCE / relative
        if not path.is_file():
            failures.append(relative + ": missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            failures.append(relative + ": hash mismatch")
    actual_files = {
        path.relative_to(FIXTURE_SOURCE).as_posix()
        for path in FIXTURE_SOURCE.rglob("*")
        if path.is_file()
    }
    for relative in sorted(actual_files - declared):
        failures.append(relative + ": undeclared")
    for relative in sorted(declared - actual_files):
        failures.append(relative + ": declared but absent")
    return {
        "fixture": manifest.get("fixture"),
        "files": len(actual_files),
        "schema_valid": not any("schema" in item.lower() for item in failures),
        "state_fixture_valid": not any("state fixture" in item.lower() for item in failures),
        "verified": not failures,
        "failures": failures,
    }


def self_test() -> dict[str, Any]:
    fixture = verify_fixture()
    if not fixture["verified"]:
        raise AssertionError("fixture verification failed: " + repr(fixture["failures"]))
    clean = json.loads(CLEAN_APPARATUS.read_text(encoding="utf-8"))
    cases = 0
    with tempfile.TemporaryDirectory(prefix="orrery-oracle-v02-") as temporary:
        root = Path(temporary)

        repository = _make_repository(root, "baseline", positive=False)
        _expect("baseline-negative", evaluate(repository, clean), overall="fail")
        cases += 1

        for variant in range(3):
            repository = _make_repository(root, f"paraphrase-{variant}", progress_variant=variant)
            _expect(f"paraphrase-{variant}", evaluate(repository, clean), overall="pass")
            cases += 1

        repository = _make_repository(root, "index-name")
        storage = repository / "src/orrery_fixture/storage.py"
        _write_text(storage, storage.read_text(encoding="utf-8").replace("idx_control_status_deadline", "idx_name_is_not_an_oracle_input"))
        _expect("index-name-independent", evaluate(repository, clean), overall="pass")
        cases += 1

        contradictions = (
            ("feedback-en", "Automatic expiry still creates a cooldown for expired feedback."),
            ("feedback-zh", "自动过期仍会创建并延长用户的稍后期限。"),
            ("migration-en", "Storage remains at schema v1; the v2 migration is not implemented."),
            ("migration-zh", "存储仍然是版本 1，版本 2 迁移尚未实现。"),
            ("future-en", "Newer schema versions are accepted and normalized automatically."),
            ("future-zh", "未来版本数据库会自动降级并接受后改写。"),
        )
        for name, sentence in contradictions:
            repository = _make_repository(root, "contradiction-" + name)
            progress = repository / "docs/PROGRESS.md"
            _write_text(progress, progress.read_text(encoding="utf-8") + "\n- " + sentence + "\n")
            _expect(
                "contradiction-" + name,
                evaluate(repository, clean),
                overall="fail",
                path=("layers", "semantic_quality", "dimensions", "narrative_consistency"),
                verdict="fail",
            )
            cases += 1

        repository = _make_repository(root, "mutation-feedback")
        feedback = repository / "src/orrery_fixture/feedback.py"
        _write_text(
            feedback,
            feedback.read_text(encoding="utf-8").replace(
                "            # Automatic expiry preserves the user's explicit snooze deadline.\n",
                "            self.snoozed_until = now + 3600\n",
            ),
        )
        _expect(
            "mutation-feedback",
            evaluate(repository, clean),
            overall="fail",
            path=("layers", "semantic_quality", "dimensions", "behavior"),
            verdict="fail",
        )
        cases += 1

        repository = _make_repository(root, "mutation-index-order")
        storage = repository / "src/orrery_fixture/storage.py"
        _write_text(storage, storage.read_text(encoding="utf-8").replace("ON feedback(status, snoozed_until)", "ON feedback(snoozed_until, status)"))
        _expect(
            "mutation-index-order",
            evaluate(repository, clean),
            overall="fail",
            path=("layers", "semantic_quality", "dimensions", "data_safety"),
            verdict="fail",
        )
        cases += 1

        repository = _make_repository(root, "mutation-future-after-write")
        storage = repository / "src/orrery_fixture/storage.py"
        text = storage.read_text(encoding="utf-8")
        text = text.replace(
            "        if current_version > SCHEMA_VERSION:\n            raise RuntimeError(f\"unsupported future schema version: {current_version}\")\n",
            "        if current_version > SCHEMA_VERSION:\n            connection.execute(\"CREATE INDEX contaminated_write ON feedback(status)\")\n            connection.commit()\n            raise RuntimeError(f\"unsupported future schema version: {current_version}\")\n",
        )
        _write_text(storage, text)
        report = evaluate(repository, clean)
        _expect(
            "mutation-future-after-write",
            report,
            overall="fail",
            path=("layers", "state_future_version", "dimensions", "future_version_safeguard"),
            verdict="fail",
        )
        cases += 1

        repository = _make_repository(root, "mutation-helper-bypass")
        feedback = repository / "src/orrery_fixture/feedback.py"
        text = feedback.read_text(encoding="utf-8")
        text = text.replace(
            "    def auto_expire(self, now: int) -> None:\n",
            "    def _correct_but_unused(self, now: int) -> None:\n"
            "        if self.status == \"pending\" and now >= self.due_at:\n"
            "            self.status = \"expired\"\n\n"
            "    def auto_expire(self, now: int) -> None:\n",
        ).replace(
            "            # Automatic expiry preserves the user's explicit snooze deadline.\n",
            "            self.snoozed_until = now + 3600\n",
        )
        _write_text(feedback, text)
        _expect(
            "mutation-helper-bypass",
            evaluate(repository, clean),
            overall="fail",
            path=("layers", "semantic_quality", "dimensions", "behavior"),
            verdict="fail",
        )
        cases += 1

        repository = _make_repository(root, "mutation-state-omission")
        state_path = repository / "docs/state/application.facts.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["facts"]["storage"]["future_version_policy"] = "unknown"
        _write_text(state_path, json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        report = evaluate(repository, clean)
        _expect("mutation-state-omission", report, overall="fail", path=("layers", "state_future_version"), verdict="fail")
        if "storage.future_version_policy" not in report["layers"]["state_future_version"]["omissions"]:
            raise AssertionError("mutation-state-omission: omission was not classified")
        cases += 1

        repository = _make_repository(root, "mutation-scope")
        _write_text(repository / "unrelated.txt", "must remain protected\n")
        _expect(
            "mutation-scope",
            evaluate(repository, clean),
            overall="fail",
            path=("layers", "semantic_quality", "dimensions", "scope"),
            verdict="fail",
        )
        cases += 1

        repository = _make_repository(root, "formal-invalid-state")
        state_path = repository / "docs/state/application.facts.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        del state["facts"]["storage"]["future_version_policy"]
        _write_text(state_path, json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        _expect(
            "formal-invalid-state",
            evaluate(repository, clean),
            overall="fail",
            path=("layers", "formal_validity"),
            verdict="fail",
        )
        cases += 1

        repository = _make_repository(root, "ambiguous-narrative")
        _write_text(
            repository / "docs/PROGRESS.md",
            "# Progress\n\n"
            "- Automatic expiry now preserves a user-controlled snooze deadline.\n"
            "- SQLite schema v1-to-v2 migration preserves existing rows and is repeatable.\n"
            "- Compatibility handling was improved.\n",
        )
        _expect(
            "ambiguous-narrative",
            evaluate(repository, clean),
            overall="manual_review_required",
            path=("layers", "semantic_quality", "dimensions", "narrative_consistency"),
            verdict="manual_review_required",
        )
        cases += 1

        repository = _make_repository(root, "apparatus-contamination")
        contaminated = dict(clean)
        contaminated["external_reads"] = ["C:/outside/installed-skill/SKILL.md"]
        report = evaluate(repository, contaminated)
        _expect("apparatus-contamination", report, overall="contaminated")
        if report["layers"]["semantic_quality"]["verdict"] != "pass" or report["layers"]["state_future_version"]["verdict"] != "pass":
            raise AssertionError("apparatus-contamination: quality layers were rewritten")
        cases += 1

    return {
        "self_test": "passed",
        "cases": cases,
        "control_families": {
            "baseline_negative": 1,
            "paraphrase_positive": 3,
            "index_name_independence": 1,
            "contradiction": 6,
            "mutation": 6,
            "formal_invalid": 1,
            "manual_review": 1,
            "apparatus_contamination": 1,
        },
        "fixture_files": fixture["files"],
        "model_calls": 0,
        "pilot_created": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--verify-fixture", action="store_true")
    action.add_argument("--repository", type=Path)
    parser.add_argument("--apparatus", type=Path, default=CLEAN_APPARATUS)
    parser.add_argument("--task-id", default=TASK_ID)
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            report = self_test()
            exit_code = 0
        elif args.verify_fixture:
            report = verify_fixture()
            exit_code = 0 if report["verified"] else 1
        else:
            repository = args.repository.resolve(strict=True)
            apparatus = json.loads(args.apparatus.read_text(encoding="utf-8"))
            report = evaluate(repository, apparatus, args.task_id)
            exit_code = 0 if report["overall_verdict"] == "pass" else (2 if report["overall_verdict"] in {"contaminated", "apparatus_error"} else 1)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError, AssertionError) as error:
        report = {"self_test": "failed", "error": f"{type(error).__name__}: {error}", "model_calls": 0}
        exit_code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
