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

from project_orrery_cli.__main__ import main as cli_main  # noqa: E402
from project_orrery_cli.authority_restore import (  # noqa: E402
    _restore_receipt,
    parse_args,
    run,
)
import project_orrery_core  # noqa: E402
from project_orrery_core.authority_migration import (  # noqa: E402
    plan_authority_model_restore,
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


def manifest_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def write_manifest(root: Path, value: dict[str, object]) -> Path:
    path = root / ".project-orrery.json"
    path.write_bytes(manifest_bytes(value))
    return path


def write_backup(
    root: Path,
    value: object,
    *,
    directory: str = "20260821T000000.000000Z-0123456789ab",
) -> tuple[Path, str]:
    relative = (
        Path(".project-orrery-backup")
        / "authority-model"
        / directory
        / ".project-orrery.json"
    )
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_bytes(manifest_bytes(value))
    return path, relative.as_posix()


def run_json(
    root: Path, backup: str | Path, *extra: str
) -> tuple[int, dict[str, object]]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = run(
            parse_args(
                [
                    "--target",
                    str(root),
                    "--backup",
                    str(backup),
                    "--json",
                    *extra,
                ]
            )
        )
    return code, json.loads(output.getvalue())


def run_apply(
    root: Path, backup: str | Path, receipt: str
) -> tuple[int, dict[str, object]]:
    return run_json(
        root,
        backup,
        "--apply",
        "--restore-receipt",
        receipt,
    )


class AuthorityModelRestorePlannerTests(unittest.TestCase):
    def test_restore_planner_is_not_a_top_level_core_api(self) -> None:
        self.assertFalse(hasattr(project_orrery_core, "plan_authority_model_restore"))

    def test_supported_project_can_restore_matching_legacy_backup(self) -> None:
        current = manifest(1)
        backup = manifest()
        untouched_current = copy.deepcopy(current)
        untouched_backup = copy.deepcopy(backup)

        plan = plan_authority_model_restore(current, backup)

        self.assertTrue(plan["allowed"])
        self.assertTrue(plan["changed"])
        self.assertEqual(plan["reason_code"], "ready")
        self.assertEqual(plan["current"]["status"], "supported")
        self.assertEqual(plan["backup"]["status"], "legacy-unversioned")
        self.assertTrue(plan["unrelated_fields_match"])
        self.assertTrue(plan["undo_backup_required"])
        self.assertEqual(current, untouched_current)
        self.assertEqual(backup, untouched_backup)

    def test_unrelated_manifest_changes_are_blocked(self) -> None:
        backup = manifest()
        backup["name"] = "another-project"
        plan = plan_authority_model_restore(manifest(1), backup)
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["reason_code"], "backup-unrelated-fields-differ")

    def test_invalid_unsupported_and_orthogonal_inputs_fail_closed(self) -> None:
        cases = [
            (manifest(True), "backup-model-invalid"),
            (manifest(99), "backup-model-unsupported"),
            ({**manifest(), "document_schema": 2}, "orthogonal-version-incompatible"),
        ]
        for backup, reason in cases:
            with self.subTest(reason=reason):
                plan = plan_authority_model_restore(manifest(1), backup)
                self.assertFalse(plan["allowed"])
                self.assertEqual(plan["reason_code"], reason)

    def test_current_project_must_use_a_supported_model(self) -> None:
        plan = plan_authority_model_restore(manifest(), manifest())
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["reason_code"], "current-model-not-supported")


class AuthorityModelRestoreCliTests(unittest.TestCase):
    def test_restore_receipt_binds_current_backup_path_and_backup_bytes(self) -> None:
        receipt = _restore_receipt("a" * 64, "one/backup.json", "b" * 64)
        self.assertNotEqual(
            receipt, _restore_receipt("c" * 64, "one/backup.json", "b" * 64)
        )
        self.assertNotEqual(
            receipt, _restore_receipt("a" * 64, "two/backup.json", "b" * 64)
        )
        self.assertNotEqual(
            receipt, _restore_receipt("a" * 64, "one/backup.json", "c" * 64)
        )

    def test_unified_entrypoint_routes_to_restore_dry_run(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            _, relative = write_backup(root, manifest())
            before = path.read_bytes()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = cli_main(
                    [
                        "restore-authority-model",
                        "--target",
                        str(root),
                        "--backup",
                        relative,
                        "--dry-run",
                        "--json",
                    ]
                )
            payload = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["command"], "restore-authority-model")
            self.assertEqual(path.read_bytes(), before)

    def test_dry_run_reports_exact_restore_without_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            backup, relative = write_backup(root, manifest())
            before = path.read_bytes()

            code, payload = run_json(root, relative, "--dry-run")

            self.assertEqual(code, 0)
            data = payload["data"]
            self.assertEqual(payload["versions"]["cli"], "0.1.8")
            self.assertEqual(data["backup_path"], relative)
            self.assertEqual(
                data["backup_sha256"], hashlib.sha256(backup.read_bytes()).hexdigest()
            )
            self.assertEqual(data["backup"]["status"], "legacy-unversioned")
            self.assertTrue(data["predicted_bytes_changed"])
            self.assertFalse(data["writes_performed"])
            self.assertRegex(
                data["restore_precondition"]["receipt"], r"^[0-9a-f]{64}$"
            )
            self.assertEqual(path.read_bytes(), before)

    def test_mode_and_receipt_validation_happen_before_file_access(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            code, payload = run_json(root, "missing", "--apply")
            self.assertEqual(code, 2)
            self.assertEqual(payload["errors"][0]["code"], "restore_receipt_required")

            code, payload = run_json(
                root,
                "missing",
                "--apply",
                "--restore-receipt",
                "not-a-receipt",
            )
            self.assertEqual(code, 2)
            self.assertEqual(payload["errors"][0]["code"], "restore_receipt_invalid")

    def test_external_absolute_and_traversal_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            write_manifest(root, manifest(1))
            external = root.parent / "external-authority-backup.json"
            external.write_bytes(manifest_bytes(manifest()))
            try:
                for requested in (external, Path("..") / external.name):
                    with self.subTest(requested=requested):
                        code, payload = run_json(root, requested, "--dry-run")
                        self.assertEqual(code, 2)
                        self.assertEqual(
                            payload["errors"][0]["code"],
                            "restore_backup_out_of_scope",
                        )
            finally:
                external.unlink(missing_ok=True)

    def test_backup_file_symlink_is_rejected_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            write_manifest(root, manifest(1))
            relative = (
                Path(".project-orrery-backup")
                / "authority-model"
                / "20260821T000000.000000Z-0123456789ab"
                / ".project-orrery.json"
            )
            with mock.patch.object(Path, "is_symlink", return_value=True):
                code, payload = run_json(root, relative, "--dry-run")
            self.assertEqual(code, 2)
            self.assertEqual(
                payload["errors"][0]["code"], "restore_backup_out_of_scope"
            )

    def test_missing_or_malformed_backup_fails_without_writing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            before = path.read_bytes()
            missing = (
                Path(".project-orrery-backup")
                / "authority-model"
                / "missing"
                / ".project-orrery.json"
            )
            code, payload = run_json(root, missing, "--dry-run")
            self.assertEqual(code, 3)
            self.assertEqual(
                payload["errors"][0]["code"], "restore_backup_unavailable"
            )

            invalid_shape = (
                Path(".project-orrery-backup")
                / "authority-model"
                / "malformed"
                / ".project-orrery.json"
            )
            invalid_path = root / invalid_shape
            invalid_path.parent.mkdir(parents=True)
            invalid_path.write_bytes(manifest_bytes(manifest()))
            code, payload = run_json(root, invalid_shape, "--dry-run")
            self.assertEqual(code, 2)
            self.assertEqual(
                payload["errors"][0]["code"], "restore_backup_out_of_scope"
            )

            backup, relative = write_backup(
                root,
                manifest(),
                directory="20260821T000001.000000Z-abcdef012345",
            )
            backup.write_bytes(b"not json")
            code, payload = run_json(root, relative, "--dry-run")
            self.assertEqual(code, 5)
            self.assertEqual(
                payload["errors"][0]["code"], "restore_manifest_incompatible"
            )
            self.assertEqual(path.read_bytes(), before)

    def test_unrelated_backup_is_a_compatibility_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            unrelated = manifest()
            unrelated["name"] = "foreign-project"
            _, relative = write_backup(root, unrelated)
            before = path.read_bytes()

            code, payload = run_json(root, relative, "--dry-run")

            self.assertEqual(code, 5)
            self.assertEqual(
                payload["data"]["reason_code"], "backup-unrelated-fields-differ"
            )
            self.assertEqual(path.read_bytes(), before)

    def test_apply_restores_exact_bytes_and_retains_exact_undo_backup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            current = path.read_bytes()
            backup, relative = write_backup(root, manifest())
            restored = backup.read_bytes()
            _, dry = run_json(root, relative, "--dry-run")
            receipt = dry["data"]["restore_precondition"]["receipt"]

            code, payload = run_apply(root, relative, receipt)

            self.assertEqual(code, 0)
            data = payload["data"]
            self.assertTrue(data["writes_performed"])
            self.assertEqual(data["operation_status"], "restored")
            self.assertEqual(path.read_bytes(), restored)
            undo = root / data["undo_backup_path"]
            self.assertEqual(undo.read_bytes(), current)
            self.assertIn("authority-model-restore", undo.parts)

    def test_receipt_fails_closed_when_current_or_backup_changes(self) -> None:
        for changed_input in ("current", "backup"):
            with self.subTest(changed_input=changed_input):
                with tempfile.TemporaryDirectory(
                    prefix="orrery-model-restore-"
                ) as temporary:
                    root = Path(temporary)
                    path = write_manifest(root, manifest(1))
                    backup, relative = write_backup(root, manifest())
                    _, dry = run_json(root, relative, "--dry-run")
                    receipt = dry["data"]["restore_precondition"]["receipt"]
                    if changed_input == "current":
                        path.write_bytes(path.read_bytes() + b"\n")
                    else:
                        backup.write_bytes(backup.read_bytes() + b"\n")
                    current = path.read_bytes()

                    code, payload = run_apply(root, relative, receipt)

                    self.assertEqual(code, 5)
                    self.assertEqual(
                        payload["errors"][0]["code"],
                        "restore_receipt_stale_or_mismatched",
                    )
                    self.assertEqual(path.read_bytes(), current)
                    self.assertFalse(
                        (root / ".project-orrery-backup" / "authority-model-restore").exists()
                    )

    def test_identical_supported_backup_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            before = path.read_bytes()
            _, relative = write_backup(root, manifest(1))
            _, dry = run_json(root, relative, "--dry-run")
            receipt = dry["data"]["restore_precondition"]["receipt"]

            code, payload = run_apply(root, relative, receipt)

            self.assertEqual(code, 0)
            self.assertFalse(payload["data"]["writes_performed"])
            self.assertEqual(payload["data"]["operation_status"], "no-op")
            self.assertIsNone(payload["data"]["undo_backup_path"])
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse(
                (root / ".project-orrery-backup" / "authority-model-restore").exists()
            )

    def test_replace_failure_keeps_current_and_exact_undo_backup(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-model-restore-") as temporary:
            root = Path(temporary)
            path = write_manifest(root, manifest(1))
            current = path.read_bytes()
            _, relative = write_backup(root, manifest())
            _, dry = run_json(root, relative, "--dry-run")
            receipt = dry["data"]["restore_precondition"]["receipt"]

            with mock.patch(
                "project_orrery_cli.authority_migrate.os.replace",
                side_effect=OSError("injected replace failure"),
            ):
                code, payload = run_apply(root, relative, receipt)

            self.assertEqual(code, 3)
            self.assertEqual(
                payload["errors"][0]["code"], "authority_model_restore_failed"
            )
            self.assertEqual(path.read_bytes(), current)
            undo = root / payload["data"]["undo_backup_path"]
            self.assertEqual(undo.read_bytes(), current)
            self.assertEqual(list(root.glob(".project-orrery.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
