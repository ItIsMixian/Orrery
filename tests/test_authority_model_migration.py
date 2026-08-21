from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src"
CLI_SOURCE = REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src"
OBSERVATORY_SOURCE = (
    REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src"
)
for source in (CORE_SOURCE, CLI_SOURCE, OBSERVATORY_SOURCE):
    sys.path.insert(0, str(source))

from project_orrery_cli.authority_migrate import (  # noqa: E402
    _apply_receipt,
    parse_args,
    run,
)
from project_orrery_cli.__main__ import main as cli_main  # noqa: E402
import project_orrery_core  # noqa: E402
from project_orrery_core.authority_migration import (  # noqa: E402
    AuthorityModelMigrationPlanError,
    materialize_authority_model_migration,
    plan_authority_model_migration,
)


def manifest(model: object = ...) -> dict[str, object]:
    value: dict[str, object] = {
        "name": "project-orrery",
        "manifest_format": 1,
        "document_schema": 1,
    }
    if model is not ...:
        value["authority_model_version"] = model
    return value


def write_manifest(root: Path, value: dict[str, object]) -> Path:
    path = root / ".project-orrery.json"
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    return path


def run_json(root: Path, *extra: str) -> tuple[int, dict[str, object]]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = run(
            parse_args(
                [
                    "--target",
                    str(root),
                    "--to",
                    "1",
                    "--json",
                    *extra,
                ]
            )
        )
    return code, json.loads(output.getvalue())


def run_apply(
    root: Path, receipt: str, *extra: str
) -> tuple[int, dict[str, object]]:
    return run_json(root, "--apply", "--apply-receipt", receipt, *extra)


class AuthorityModelMigrationPlannerTests(unittest.TestCase):
    def test_planner_is_not_yet_a_top_level_core_api(self) -> None:
        self.assertFalse(
            hasattr(project_orrery_core, "plan_authority_model_migration")
        )

    def test_legacy_project_gets_one_explicit_manifest_change(self) -> None:
        original = manifest()
        untouched = copy.deepcopy(original)
        plan = plan_authority_model_migration(original, target_version=1)

        self.assertTrue(plan["allowed"])
        self.assertTrue(plan["changed"])
        self.assertEqual(plan["reason_code"], "ready")
        self.assertEqual(plan["backup_scope"], [".project-orrery.json"])
        self.assertFalse(plan["writes_performed"])
        self.assertEqual(
            plan["changes"],
            [
                {
                    "path": ".project-orrery.json",
                    "operation": "set",
                    "field": "authority_model_version",
                    "before": {"present": False, "value": None},
                    "after": {"present": True, "value": 1},
                }
            ],
        )
        self.assertEqual(original, untouched)
        for field in ("manifest_format", "document_schema"):
            dimensions = plan["preserved_dimensions"][field]
            self.assertEqual(dimensions["before"], dimensions["after"])
            self.assertTrue(dimensions["compatible"])

    def test_orthogonal_versions_are_preserved_and_fail_closed(self) -> None:
        original = manifest()
        original["document_schema"] = 2
        plan = plan_authority_model_migration(original, target_version=1)
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["reason_code"], "orthogonal-version-incompatible")
        self.assertEqual(plan["changes"], [])
        dimensions = plan["preserved_dimensions"]["document_schema"]
        self.assertEqual(dimensions["before"], dimensions["after"])
        self.assertFalse(dimensions["compatible"])

    def test_already_selected_model_is_an_allowed_noop(self) -> None:
        plan = plan_authority_model_migration(manifest(1), target_version=1)
        self.assertTrue(plan["allowed"])
        self.assertFalse(plan["changed"])
        self.assertEqual(plan["reason_code"], "already-selected")
        self.assertEqual(plan["changes"], [])
        self.assertFalse(plan["backup_required"])

    def test_invalid_and_unsupported_sources_fail_closed(self) -> None:
        expected = ((True, "source-invalid"), (2, "source-unsupported"))
        for selected, reason in expected:
            with self.subTest(selected=selected):
                plan = plan_authority_model_migration(
                    manifest(selected), target_version=1
                )
                self.assertFalse(plan["allowed"])
                self.assertFalse(plan["changed"])
                self.assertEqual(plan["reason_code"], reason)
                self.assertEqual(plan["changes"], [])

    def test_discrete_support_does_not_imply_a_cross_version_path(self) -> None:
        plan = plan_authority_model_migration(
            manifest(1),
            target_version=3,
            supported_versions=(1, 3),
            known_versions=(1, 2, 3),
        )
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["reason_code"], "migration-path-unavailable")

    def test_unsupported_target_and_malformed_request_are_rejected(self) -> None:
        plan = plan_authority_model_migration(manifest(), target_version=3)
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["reason_code"], "target-unsupported")
        with self.assertRaises(AuthorityModelMigrationPlanError):
            plan_authority_model_migration(manifest(), target_version=True)

    def test_materialization_is_pure_and_rejects_blocked_plans(self) -> None:
        original = manifest()
        allowed = plan_authority_model_migration(original, target_version=1)
        proposed = materialize_authority_model_migration(original, allowed)
        self.assertNotIn("authority_model_version", original)
        self.assertEqual(proposed["authority_model_version"], 1)

        blocked = plan_authority_model_migration(manifest(99), target_version=1)
        with self.assertRaises(AuthorityModelMigrationPlanError):
            materialize_authority_model_migration(manifest(99), blocked)


class AuthorityModelMigrationCliTests(unittest.TestCase):
    def test_apply_receipt_binds_source_target_and_proposal(self) -> None:
        receipt = _apply_receipt("a" * 64, 1, "b" * 64)
        self.assertNotEqual(receipt, _apply_receipt("c" * 64, 1, "b" * 64))
        self.assertNotEqual(receipt, _apply_receipt("a" * 64, 2, "b" * 64))
        self.assertNotEqual(receipt, _apply_receipt("a" * 64, 1, "c" * 64))

    def test_unified_entrypoint_routes_to_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest())
            before = path.read_bytes()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = cli_main(
                    [
                        "migrate-authority-model",
                        "--target",
                        str(root),
                        "--to",
                        "1",
                        "--dry-run",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["command"], "migrate-authority-model")
            self.assertEqual(path.read_bytes(), before)

    def test_dry_run_reports_change_and_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest())
            before = path.read_bytes()

            code, payload = run_json(root, "--dry-run")

            self.assertEqual(code, 0)
            data = payload["data"]
            self.assertEqual(payload["command"], "migrate-authority-model")
            self.assertEqual(payload["versions"]["cli"], "0.1.4")
            self.assertEqual(data["project_root"], str(root.resolve()))
            self.assertTrue(data["allowed"])
            self.assertTrue(data["backup_required"])
            self.assertFalse(data["writes_performed"])
            self.assertEqual(data["operation_status"], "previewed")
            self.assertRegex(
                data["apply_precondition"]["receipt"], r"^[0-9a-f]{64}$"
            )
            self.assertEqual(
                data["apply_precondition"]["expected_manifest_sha256"],
                hashlib.sha256(before).hexdigest(),
            )
            self.assertEqual(
                data["manifest_sha256"], hashlib.sha256(before).hexdigest()
            )
            self.assertEqual(path.read_bytes(), before)

    def test_omitting_migration_mode_is_refused_without_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest())
            before = path.read_bytes()

            code, payload = run_json(root)

            self.assertEqual(code, 2)
            self.assertEqual(
                payload["errors"][0]["code"], "migration_mode_required"
            )
            self.assertFalse(payload["data"]["writes_performed"])
            self.assertEqual(path.read_bytes(), before)

    def test_unsupported_source_is_a_compatibility_failure_without_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(99))
            before = path.read_bytes()

            code, payload = run_json(root, "--dry-run")

            self.assertEqual(code, 5)
            self.assertEqual(payload["data"]["reason_code"], "source-unsupported")
            self.assertFalse(payload["data"]["writes_performed"])
            self.assertEqual(path.read_bytes(), before)

    def test_missing_manifest_is_an_operation_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            code, payload = run_json(Path(temporary), "--dry-run")
            self.assertEqual(code, 3)
            self.assertEqual(
                payload["errors"][0]["code"], "migration_plan_unavailable"
            )
            self.assertFalse(payload["data"]["writes_performed"])

    def test_invalid_target_is_an_invalid_request_without_reading_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            code, payload = run_json(Path(temporary), "--dry-run", "--to", "0")
            self.assertEqual(code, 2)
            self.assertEqual(payload["errors"][0]["code"], "target_version_invalid")
            self.assertFalse(payload["data"]["writes_performed"])

    def test_apply_requires_a_reviewed_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest())
            before = path.read_bytes()
            code, payload = run_json(root, "--apply")
            self.assertEqual(code, 2)
            self.assertEqual(payload["errors"][0]["code"], "apply_receipt_required")
            self.assertEqual(path.read_bytes(), before)

    def test_apply_backs_up_exact_bytes_and_atomically_writes_proposal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest())
            before = path.read_bytes()
            dry_code, dry = run_json(root, "--dry-run")
            receipt = dry["data"]["apply_precondition"]["receipt"]

            apply_code, applied = run_apply(root, receipt)

            self.assertEqual(dry_code, 0)
            self.assertEqual(apply_code, 0)
            data = applied["data"]
            self.assertTrue(data["writes_performed"])
            self.assertEqual(data["operation_status"], "applied")
            self.assertEqual(
                data["manifest_sha256_after"], data["proposed_manifest_sha256"]
            )
            updated = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(updated["authority_model_version"], 1)
            self.assertEqual(updated["manifest_format"], 1)
            self.assertEqual(updated["document_schema"], 1)
            backup = root / data["backup_path"]
            self.assertTrue(backup.is_file())
            self.assertEqual(backup.read_bytes(), before)

    def test_stale_receipt_fails_before_backup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest())
            _, dry = run_json(root, "--dry-run")
            receipt = dry["data"]["apply_precondition"]["receipt"]
            path.write_bytes(path.read_bytes() + b"\n")
            changed = path.read_bytes()

            code, payload = run_apply(root, receipt)

            self.assertEqual(code, 5)
            self.assertEqual(
                payload["errors"][0]["code"],
                "apply_receipt_stale_or_mismatched",
            )
            self.assertEqual(path.read_bytes(), changed)
            self.assertFalse((root / ".project-orrery-backup").exists())

    def test_apply_noop_creates_no_backup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            before = path.read_bytes()
            _, dry = run_json(root, "--dry-run")
            receipt = dry["data"]["apply_precondition"]["receipt"]

            code, payload = run_apply(root, receipt)

            self.assertEqual(code, 0)
            self.assertFalse(payload["data"]["writes_performed"])
            self.assertIsNone(payload["data"]["backup_path"])
            self.assertEqual(payload["data"]["operation_status"], "no-op")
            self.assertFalse(payload["data"]["predicted_bytes_changed"])
            self.assertEqual(
                payload["data"]["manifest_sha256"],
                payload["data"]["proposed_manifest_sha256"],
            )
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((root / ".project-orrery-backup").exists())

    def test_replace_failure_retains_backup_and_original_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-migrate-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest())
            before = path.read_bytes()
            _, dry = run_json(root, "--dry-run")
            receipt = dry["data"]["apply_precondition"]["receipt"]

            with mock.patch(
                "project_orrery_cli.authority_migrate.os.replace",
                side_effect=OSError("injected replace failure"),
            ):
                code, payload = run_apply(root, receipt)

            self.assertEqual(code, 3)
            self.assertEqual(
                payload["errors"][0]["code"], "authority_model_apply_failed"
            )
            self.assertEqual(path.read_bytes(), before)
            backup = root / payload["data"]["backup_path"]
            self.assertEqual(backup.read_bytes(), before)
            self.assertEqual(list(root.glob(".project-orrery.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
