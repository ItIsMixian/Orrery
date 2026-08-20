#!/usr/bin/env python3
"""Independent behavior-first acceptance Oracle for Pilot 009."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Callable


PILOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_SOURCE = PILOT_DIR / "fixture-source"

TASK_PATHS = {
    "PO-CR-033": {
        "src/orrery_fixture/feedback.py",
        "tests/test_feedback.py",
        "docs/state/application.md",
        "docs/PROGRESS.md",
    },
    "PO-CR-034": {
        "src/orrery_fixture/storage.py",
        "tests/test_storage.py",
        "docs/state/application.md",
        "docs/PROGRESS.md",
    },
    "PO-CR-035": {
        "docs/state/application.md",
        "docs/PROGRESS.md",
        "docs/HANDOFF.md",
    },
}


def run_command(arguments: list[str], repository: Path, *, code: str | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repository / "src")
    command = arguments + ([code] if code is not None else [])
    return subprocess.run(
        command,
        cwd=repository,
        env=environment,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=120,
    )


def changed_paths(repository: Path) -> set[str]:
    result = run_command(["git", "status", "--porcelain=v1", "-z"], repository)
    if result.returncode:
        raise RuntimeError("cannot inspect candidate changed paths")
    paths: set[str] = set()
    for entry in result.stdout.split("\0"):
        if not entry:
            continue
        value = entry[3:] if len(entry) > 3 else entry
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        if not value.startswith(".benchmark/"):
            paths.add(value.replace("\\", "/"))
    return paths


def require_exact_changes(repository: Path, task_id: str, failures: list[str]) -> None:
    actual = changed_paths(repository)
    expected = TASK_PATHS[task_id]
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        failures.append("required paths were not changed: " + ", ".join(missing))
    if unexpected:
        failures.append("protected or unrelated paths changed: " + ", ".join(unexpected))


def run_probe(repository: Path, code: str, label: str, failures: list[str]) -> None:
    result = run_command([sys.executable, "-X", "utf8", "-c"], repository, code=code)
    if result.returncode:
        failures.append(label + ": " + (result.stdout + result.stderr).strip())


def check_progress(repository: Path, task_id: str, failures: list[str]) -> None:
    progress = (repository / "docs/PROGRESS.md").read_text(encoding="utf-8")
    lowered = progress.lower()
    if task_id == "PO-CR-033":
        fixed = task_id.lower() in lowered or (
            ("auto-expiry" in lowered or "自动过期" in progress)
            and any(token in lowered for token in ("does not", "never", "fixed"))
        )
        if not fixed:
            failures.append("PROGRESS does not record the implemented auto-expiry cooldown behavior")
    elif task_id == "PO-CR-034":
        migrated = "sqlite" in lowered and "v2" in lowered and "v1" in lowered and (
            "future" in lowered or "未来" in progress
        )
        if not migrated:
            failures.append("PROGRESS does not record v1-to-v2 migration and future-version rejection")
    else:
        failures.append(f"unsupported progress check task: {task_id}")


def check_033(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    require_exact_changes(repository, "PO-CR-033", failures)
    run_probe(
        repository,
        textwrap.dedent(
            """
            from orrery_fixture.feedback import Feedback

            expired = Feedback(due_at=10)
            expired.auto_expire(10)
            assert expired.status == "expired"
            assert expired.snoozed_until is None, "auto expiry created a cooldown"

            existing = Feedback(due_at=10, snoozed_until=25)
            existing.auto_expire(10)
            existing.auto_expire(100)
            assert existing.status == "expired"
            assert existing.snoozed_until == 25, "repeated auto expiry changed an existing deadline"

            snoozed = Feedback(due_at=15)
            snoozed.snooze(10, 20)
            snoozed.auto_expire(20)
            assert snoozed.status == "snoozed", "automatic expiry overrode an explicit snooze"
            assert not snoozed.should_prompt(29)
            snoozed.tick(30)
            assert snoozed.status == "pending" and snoozed.snoozed_until is None
            assert snoozed.should_prompt(30)

            assert not expired.should_prompt(10), "expired feedback became promptable"
            """
        ),
        "feedback lifecycle behavior failed",
        failures,
    )
    state = (repository / "docs/state/application.md").read_text(encoding="utf-8")
    if "feedback_auto_expiry_cooldown_bug: fixed" not in state:
        failures.append("Application State does not record the feedback fix")
    check_progress(repository, "PO-CR-033", failures)
    return failures, []


def check_034(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    require_exact_changes(repository, "PO-CR-034", failures)
    run_probe(
        repository,
        textwrap.dedent(
            """
            import sqlite3
            import tempfile
            from pathlib import Path
            from orrery_fixture.storage import SCHEMA_VERSION, initialize_database

            assert SCHEMA_VERSION == 2

            with tempfile.TemporaryDirectory() as temporary:
                old_path = Path(temporary) / "old.db"
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
                assert {"id", "status", "snoozed_until"} <= columns
                assert ["status", "snoozed_until"] in index_columns
                assert row == (7, "pending", None)
                assert version == 2

                fresh_path = Path(temporary) / "fresh.db"
                initialize_database(fresh_path)
                connection = sqlite3.connect(fresh_path)
                try:
                    fresh_columns = {row[1] for row in connection.execute("PRAGMA table_info(feedback)")}
                    fresh_version = connection.execute("PRAGMA user_version").fetchone()[0]
                finally:
                    connection.close()
                assert "snoozed_until" in fresh_columns and fresh_version == 2

                future_path = Path(temporary) / "future.db"
                connection = sqlite3.connect(future_path)
                try:
                    connection.execute("CREATE TABLE feedback (id INTEGER PRIMARY KEY, status TEXT NOT NULL, future_value TEXT)")
                    connection.execute("INSERT INTO feedback VALUES (9, 'pending', 'keep-me')")
                    connection.execute("PRAGMA user_version = 3")
                    connection.commit()
                finally:
                    connection.close()
                try:
                    initialize_database(future_path)
                except (RuntimeError, ValueError):
                    pass
                else:
                    raise AssertionError("future schema version was not rejected")
                connection = sqlite3.connect(future_path)
                try:
                    future_version = connection.execute("PRAGMA user_version").fetchone()[0]
                    future_columns = [row[1] for row in connection.execute("PRAGMA table_info(feedback)")]
                    future_row = connection.execute("SELECT * FROM feedback WHERE id=9").fetchone()
                    future_indexes = list(connection.execute("PRAGMA index_list(feedback)"))
                finally:
                    connection.close()
                assert future_version == 3
                assert future_columns == ["id", "status", "future_value"]
                assert future_row == (9, "pending", "keep-me")
                assert future_indexes == []
            """
        ),
        "SQLite migration behavior failed",
        failures,
    )
    state = (repository / "docs/state/application.md").read_text(encoding="utf-8")
    if "storage_schema_version: 2" not in state:
        failures.append("Application State is missing storage_schema_version: 2")
    migration_lines = [line for line in state.splitlines() if "storage_v2_migration:" in line]
    if not migration_lines or any(
        token in migration_lines[0].lower() for token in ("unknown", "not implemented")
    ):
        failures.append("Application State does not record the implemented v2 migration behavior")
    check_progress(repository, "PO-CR-034", failures)
    return failures, []


def check_035(repository: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    require_exact_changes(repository, "PO-CR-035", failures)
    tests = run_command([sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-v"], repository)
    if tests.returncode:
        failures.append("baseline application tests no longer pass: " + (tests.stdout + tests.stderr).strip())
    if "Ran 4 tests" not in tests.stdout + tests.stderr:
        failures.append("independent test discovery did not find the expected four tests")
    state = (repository / "docs/state/application.md").read_text(encoding="utf-8")
    for token in (
        "feedback_auto_expiry_cooldown_bug: present",
        "storage_schema_version: 1",
        "storage_v2_migration: not implemented",
        "automated_tests: 4",
    ):
        if token not in state:
            failures.append("Application State is missing current fact: " + token)
    progress = (repository / "docs/PROGRESS.md").read_text(encoding="utf-8")
    handoff = (repository / "docs/HANDOFF.md").read_text(encoding="utf-8")
    if "4 automated tests" not in progress:
        failures.append("PROGRESS does not record the four-test baseline")
    if "schema v1" not in handoff or "4 tests" not in handoff or "auto-expiry cooldown bug" not in handoff:
        failures.append("HANDOFF does not expose the current schema, tests and feedback risk")
    contradictions = {
        "PROGRESS": [
            token for token in ("Feedback expiry and snooze behavior is complete", "SQLite v2 migration is complete", "3 automated tests")
            if token in progress
        ],
        "HANDOFF": [
            token for token in ("No known product gaps", "schema v2", "3 tests")
            if token in handoff
        ],
    }
    for document, tokens in contradictions.items():
        if tokens:
            failures.append(document + " retains contradicted claims: " + ", ".join(tokens))
    return failures, []


CHECKS: dict[str, Callable[[Path], tuple[list[str], list[str]]]] = {
    "PO-CR-033": check_033,
    "PO-CR-034": check_034,
    "PO-CR-035": check_035,
}


def initialize_fixture(repository: Path) -> None:
    commands = (
        ["git", "init", "-b", "pilot-009-fixture"],
        ["git", "config", "core.autocrlf", "false"],
        ["git", "add", "--all"],
        ["git", "-c", "user.name=Project Orrery Benchmark", "-c", "user.email=benchmark@local.invalid", "commit", "-m", "fixture baseline"],
    )
    for command in commands:
        result = run_command(command, repository)
        if result.returncode:
            raise RuntimeError("cannot initialize Oracle fixture: " + result.stdout + result.stderr)


def replace_tokens(path: Path, replacements: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8", newline="\n")


def apply_positive_033(repository: Path) -> None:
    path = repository / "src/orrery_fixture/feedback.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "            self.snoozed_until = max(self.snoozed_until or 0, now + 3600)\n",
        "            # Automatic expiry never changes the user-controlled snooze deadline.\n",
    )
    path.write_text(text, encoding="utf-8", newline="\n")
    tests = repository / "tests/test_feedback.py"
    test_text = tests.read_text(encoding="utf-8").replace(
        "    def test_future_feedback_remains_pending(self) -> None:\n",
        "    def test_auto_expiry_does_not_create_cooldown(self) -> None:\n"
        "        feedback = Feedback(due_at=10)\n"
        "        feedback.auto_expire(10)\n"
        "        self.assertEqual(feedback.status, \"expired\")\n"
        "        self.assertIsNone(feedback.snoozed_until)\n\n"
        "    def test_future_feedback_remains_pending(self) -> None:\n",
    )
    tests.write_text(test_text, encoding="utf-8", newline="\n")
    replace_tokens(repository / "docs/state/application.md", {"feedback_auto_expiry_cooldown_bug: unknown": "feedback_auto_expiry_cooldown_bug: fixed"})
    with (repository / "docs/PROGRESS.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("- PO-CR-033 completed with feedback regression coverage.\n")


def apply_positive_034(repository: Path) -> None:
    (repository / "src/orrery_fixture/storage.py").write_text(
        textwrap.dedent(
            '''\
            """SQLite initialization with an idempotent v2 migration."""

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
                        "CREATE INDEX IF NOT EXISTS idx_feedback_status_snoozed "
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
        ),
        encoding="utf-8",
        newline="\n",
    )
    tests = repository / "tests/test_storage.py"
    text = tests.read_text(encoding="utf-8")
    text = text.replace("test_repeated_v1_initialization_is_safe", "test_repeated_v2_initialization_is_safe")
    text = text.replace("self.assertEqual(version, 1)", "self.assertEqual(version, 2)")
    text = text.replace(
        "\n\nif __name__ == \"__main__\":",
        "\n\n    def test_v1_row_survives_v2_migration(self) -> None:\n"
        "        with tempfile.TemporaryDirectory() as temporary:\n"
        "            path = Path(temporary) / \"old.db\"\n"
        "            connection = sqlite3.connect(path)\n"
        "            try:\n"
        "                connection.execute(\"CREATE TABLE feedback (id INTEGER PRIMARY KEY, status TEXT NOT NULL)\")\n"
        "                connection.execute(\"INSERT INTO feedback VALUES (7, 'pending')\")\n"
        "                connection.execute(\"PRAGMA user_version = 1\")\n"
        "                connection.commit()\n"
        "            finally:\n"
        "                connection.close()\n"
        "            initialize_database(path)\n"
        "            connection = sqlite3.connect(path)\n"
        "            try:\n"
        "                row = connection.execute(\"SELECT id, status, snoozed_until FROM feedback\").fetchone()\n"
        "            finally:\n"
        "                connection.close()\n"
        "            self.assertEqual(row, (7, 'pending', None))\n"
        "\n"
        "    def test_future_schema_is_rejected_without_downgrade(self) -> None:\n"
        "        with tempfile.TemporaryDirectory() as temporary:\n"
        "            path = Path(temporary) / \"future.db\"\n"
        "            connection = sqlite3.connect(path)\n"
        "            try:\n"
        "                connection.execute(\"CREATE TABLE feedback (id INTEGER PRIMARY KEY, status TEXT NOT NULL, future_value TEXT)\")\n"
        "                connection.execute(\"PRAGMA user_version = 3\")\n"
        "                connection.commit()\n"
        "            finally:\n"
        "                connection.close()\n"
        "            with self.assertRaises(RuntimeError):\n"
        "                initialize_database(path)\n"
        "            connection = sqlite3.connect(path)\n"
        "            try:\n"
        "                version = connection.execute(\"PRAGMA user_version\").fetchone()[0]\n"
        "            finally:\n"
        "                connection.close()\n"
        "            self.assertEqual(version, 3)\n"
        "\n\nif __name__ == \"__main__\":",
    )
    tests.write_text(text, encoding="utf-8", newline="\n")
    replace_tokens(
        repository / "docs/state/application.md",
        {
            "storage_schema_version: unknown": "storage_schema_version: 2",
            "storage_v2_migration: unknown": "storage_v2_migration: implemented",
        },
    )
    with (repository / "docs/PROGRESS.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("- PO-CR-034 completed: SQLite v1-to-v2 preserves rows, is idempotent, and rejects future versions.\n")


def apply_positive_035(repository: Path) -> None:
    replace_tokens(
        repository / "docs/state/application.md",
        {
            "feedback_auto_expiry_cooldown_bug: unknown": "feedback_auto_expiry_cooldown_bug: present",
            "storage_schema_version: unknown": "storage_schema_version: 1",
            "storage_v2_migration: unknown": "storage_v2_migration: not implemented",
            "automated_tests: 3": "automated_tests: 4",
        },
    )
    replace_tokens(
        repository / "docs/PROGRESS.md",
        {
            "Feedback expiry and snooze behavior is complete.": "Feedback auto-expiry cooldown bug remains open.",
            "SQLite v2 migration is complete.": "SQLite schema v1 remains current; v2 migration is not implemented.",
            "Validation: 3 automated tests passed.": "Validation: 4 automated tests passed.",
        },
    )
    replace_tokens(
        repository / "docs/HANDOFF.md",
        {
            "No known product gaps. Storage is at schema v2 and all 3 tests pass.":
                "Storage remains at schema v1; 4 tests pass. The auto-expiry cooldown bug remains open.",
        },
    )


POSITIVE_APPLIERS = {
    "PO-CR-033": apply_positive_033,
    "PO-CR-034": apply_positive_034,
    "PO-CR-035": apply_positive_035,
}


def self_test() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="orrery-p009-oracle-") as temporary:
        root = Path(temporary)
        for task_id, check in CHECKS.items():
            repository = root / task_id
            shutil.copytree(FIXTURE_SOURCE, repository)
            initialize_fixture(repository)
            negative, apparatus = check(repository)
            if apparatus:
                failures.append(f"{task_id} baseline produced apparatus errors: {apparatus}")
            if not negative:
                failures.append(f"{task_id} baseline negative control unexpectedly passed")
            POSITIVE_APPLIERS[task_id](repository)
            positive, apparatus = check(repository)
            if apparatus or positive:
                failures.append(f"{task_id} positive control failed: {apparatus + positive}")
    return failures, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--task-id", choices=tuple(CHECKS))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            failures, apparatus = self_test()
        elif args.repository and args.task_id:
            failures, apparatus = CHECKS[args.task_id](args.repository.resolve(strict=True))
        else:
            parser.error("provide --self-test or --repository with --task-id")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        failures, apparatus = [], [f"oracle exception: {type(error).__name__}: {error}"]
    result = {
        "schema_version": 1,
        "passed": not failures and not apparatus,
        "task_failures": failures,
        "apparatus_errors": apparatus,
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 2 if apparatus else (1 if failures else 0)


if __name__ == "__main__":
    raise SystemExit(main())
