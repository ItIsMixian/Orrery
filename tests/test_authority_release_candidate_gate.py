from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPOSITORY_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
for source in (
    REPOSITORY_ROOT / "packages" / "project-orrery-core" / "src",
    REPOSITORY_ROOT / "packages" / "project-orrery-cli" / "src",
    REPOSITORY_ROOT / "packages" / "project-orrery-observatory" / "src",
):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

import authority_release_candidate_gate as gate  # noqa: E402
from project_orrery_cli.context import CliContext, repository_context  # noqa: E402
from project_orrery_cli.scaffold import parse_args as scaffold_args  # noqa: E402
from project_orrery_cli.scaffold import run as scaffold_run  # noqa: E402
from project_orrery_core.manifests import ReleaseContract  # noqa: E402


FIXTURE = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "authority-meta-model"
    / "v1"
    / "release-candidate-gate.json"
)
PUBLIC_RELEASE = REPOSITORY_ROOT / "skills" / "project-orrery" / "release-manifest.json"
BUNDLED_RELEASE = (
    REPOSITORY_ROOT
    / "packages"
    / "project-orrery-core"
    / "src"
    / "project_orrery_core"
    / "data"
    / "release-v0.2.0.json"
)


def read_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"not an object: {path}")
    return value


def candidate_manifest(version: str = "0.2.1") -> dict[str, object]:
    value = copy.deepcopy(read_object(PUBLIC_RELEASE))
    value["version"] = version
    value["authority_model_version"] = 1
    value["compatibility"]["authority_model_versions"] = {"supported": [1]}
    value["distribution"]["tag"] = f"v{version}"
    value["distribution"]["skill_url"] = f"https://invalid.example/v{version}/skill"
    value["distribution"]["release_url"] = f"https://invalid.example/v{version}"
    value["distribution"]["archive_url"] = f"https://invalid.example/v{version}/archive.zip"
    return value


class AuthorityReleaseCandidateGateTests(unittest.TestCase):
    def test_fixture_and_policy_freeze_candidate_not_release_semantics(self) -> None:
        fixture = read_object(FIXTURE)
        policy = read_object(gate.POLICY_PATH)
        self.assertEqual(fixture["fixture_id"], "amm-release-candidate-gate-v1")
        self.assertEqual(fixture["gate_contract"], policy["contract"])
        self.assertEqual(policy["authority_model"], {"default": 1, "supported": [1]})
        self.assertFalse(fixture["expected"]["release_ready_without_external_blockers"])
        self.assertNotIn("version", policy)

    def test_historical_v020_inputs_match_frozen_hashes(self) -> None:
        policy = read_object(gate.POLICY_PATH)
        observed = gate._validate_historical_inputs(policy)
        self.assertEqual(
            observed["skills/project-orrery/release-manifest.json"],
            gate._canonical_text_sha256(PUBLIC_RELEASE),
        )
        self.assertEqual(
            observed[
                "packages/project-orrery-core/src/project_orrery_core/data/release-v0.2.0.json"
            ],
            gate._canonical_text_sha256(BUNDLED_RELEASE),
        )

    def test_candidate_manifest_pair_and_version_fail_closed(self) -> None:
        policy = read_object(gate.POLICY_PATH)
        malformed: list[dict[str, object]] = []

        missing_default = candidate_manifest()
        missing_default.pop("authority_model_version")
        malformed.append(missing_default)

        missing_support = candidate_manifest()
        missing_support["compatibility"].pop("authority_model_versions")
        malformed.append(missing_support)

        wrong_default = candidate_manifest()
        wrong_default["authority_model_version"] = 2
        malformed.append(wrong_default)

        duplicate = candidate_manifest()
        duplicate["compatibility"]["authority_model_versions"] = {"supported": [1, 1]}
        malformed.append(duplicate)

        old_version = candidate_manifest("0.2.0")
        malformed.append(old_version)

        wrong_tag = candidate_manifest()
        wrong_tag["distribution"]["tag"] = "v9.9.9"
        malformed.append(wrong_tag)

        secret_field = candidate_manifest()
        secret_field["api_key"] = "not-even-a-real-key"
        malformed.append(secret_field)

        for value in malformed:
            with self.subTest(value=value):
                with self.assertRaises(gate.CandidateGateError):
                    gate._validate_candidate_manifest(value, policy, None)

    def test_archive_inspector_rejects_traversal_duplicates_and_secrets(self) -> None:
        policy = read_object(gate.POLICY_PATH)
        with tempfile.TemporaryDirectory(prefix="orrery-gate-malicious-") as raw:
            root = Path(raw)
            cases = {
                "traversal.zip": [("project-orrery/../escape", b"x")],
                "windows-traversal.zip": [("project-orrery\\..\\escape", b"x")],
                "secret.zip": [("project-orrery/ai-config.json", b"{}")],
                "nested-secret.zip": [
                    ("project-orrery/docs/_site/nested/index.html", b"safe")
                ],
                "credential.zip": [
                    ("project-orrery/notes.txt", b"ghp_" + b"A" * 30)
                ],
                "duplicate.zip": [
                    ("project-orrery/SKILL.md", b"one"),
                    ("project-orrery/SKILL.md", b"two"),
                ],
                "case-collision.zip": [
                    ("project-orrery/SKILL.md", b"one"),
                    ("project-orrery/skill.md", b"two"),
                ],
            }
            for name, entries in cases.items():
                archive = root / name
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    with zipfile.ZipFile(archive, "w") as bundle:
                        for entry, content in entries:
                            bundle.writestr(entry, content)
                with self.subTest(name=name):
                    with self.assertRaises(gate.CandidateGateError):
                        gate._inspect_and_extract(archive, root / f"extract-{name}", policy)

    def test_subprocess_environment_is_allowlisted_and_timeout_fails_gate(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "OpenAI_Api_Key": "secret",
                "anthropic_token": "secret",
                "deepseek_key": "secret",
                "codex_home": "secret",
                "github_token": "secret",
                "gh_token": "secret",
                "aws_secret_access_key": "secret",
                "https_proxy": "http://proxy.invalid",
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            },
            clear=True,
        ):
            observed = gate._source_cli_environment()
        folded = {key.casefold() for key in observed}
        for forbidden in (
            "openai_api_key",
            "anthropic_token",
            "deepseek_key",
            "codex_home",
            "github_token",
            "gh_token",
            "aws_secret_access_key",
            "https_proxy",
        ):
            self.assertNotIn(forbidden, folded)
        self.assertIn("PYTHONPATH", observed)

        expired = subprocess.TimeoutExpired(["python"], 1)
        with mock.patch.object(gate.subprocess, "run", side_effect=expired):
            with self.assertRaisesRegex(gate.CandidateGateError, "timeout"):
                gate._run(["python"], cwd=REPOSITORY_ROOT)

    def test_cli_rejects_candidate_manifest_symlink_before_resolution(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-gate-cli-link-") as raw:
            root = Path(raw)
            target = root / "candidate-real.json"
            target.write_text(json.dumps(candidate_manifest()), encoding="utf-8")
            link = root / "candidate-link.json"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink privilege unavailable: {exc}")
            error = StringIO()
            with redirect_stderr(error):
                result = gate.main(
                    [
                        "--candidate-manifest",
                        str(link),
                        "--output-dir",
                        str(root / "output"),
                    ]
                )
            self.assertEqual(result, 2)
            self.assertIn("non-symlink", error.getvalue())
            self.assertFalse((root / "output").exists())

    def test_cli_preserves_candidate_manifest_lexical_path(self) -> None:
        candidate = Path.cwd() / "reviewed" / "candidate-link.json"
        output = Path.cwd() / "reviewed" / "output"
        original_resolve = Path.resolve

        def guarded_resolve(path: Path, *args: object, **kwargs: object) -> Path:
            if path == candidate:
                raise AssertionError("candidate manifest identity was dereferenced")
            return original_resolve(path, *args, **kwargs)

        with mock.patch.object(Path, "resolve", guarded_resolve), mock.patch.object(
            gate, "run_gate", return_value={"candidate_ready": False}
        ) as run, redirect_stdout(StringIO()):
            result = gate.main(
                [
                    "--candidate-manifest",
                    str(candidate),
                    "--output-dir",
                    str(output),
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.kwargs["candidate_manifest_path"], candidate)

    def test_source_inventory_rejects_plaintext_secret_and_symlink(self) -> None:
        policy = read_object(gate.POLICY_PATH)
        with tempfile.TemporaryDirectory(prefix="orrery-gate-source-") as raw:
            root = Path(raw)
            (root / "SKILL.md").write_text("sk-" + "A" * 30, encoding="utf-8")
            with mock.patch.object(gate, "SKILL_ROOT", root):
                with self.assertRaisesRegex(gate.CandidateGateError, "credential"):
                    gate._source_files(policy)

            (root / "SKILL.md").write_text("safe", encoding="utf-8")
            target = root / "target.txt"
            target.write_text("safe", encoding="utf-8")
            link = root / "link.txt"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink privilege unavailable: {exc}")
            with mock.patch.object(gate, "SKILL_ROOT", root):
                with self.assertRaisesRegex(gate.CandidateGateError, "symlinks"):
                    gate._source_files(policy)

    def test_invalid_candidate_fails_without_creating_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-gate-fail-") as raw:
            root = Path(raw)
            manifest = root / "candidate.json"
            value = candidate_manifest()
            value["authority_model_version"] = True
            manifest.write_text(json.dumps(value), encoding="utf-8")
            output = root / "output"
            with self.assertRaises(gate.CandidateGateError):
                gate.run_gate(candidate_manifest_path=manifest, output_dir=output)
            self.assertFalse(output.exists())

    def test_neutral_scaffold_candidate_preflights_before_any_write(self) -> None:
        source = repository_context()
        context = CliContext(
            release=ReleaseContract(candidate_manifest()),
            authority_root=source.authority_root,
            observatory_root=source.observatory_root,
        )
        with tempfile.TemporaryDirectory(prefix="orrery-gate-neutral-") as raw:
            root = Path(raw)
            new_target = root / "new"
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = scaffold_run(
                    scaffold_args(["--target", str(new_target), "--title", "New"]),
                    context,
                )
            self.assertEqual(code, 0)
            self.assertEqual(
                read_object(new_target / ".project-orrery.json")["authority_model_version"],
                1,
            )

            legacy = root / "legacy"
            legacy.mkdir()
            legacy_manifest = {
                "name": "project-orrery",
                "manifest_format": 1,
                "document_schema": 1,
            }
            (legacy / ".project-orrery.json").write_text(
                json.dumps(legacy_manifest), encoding="utf-8"
            )
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = scaffold_run(
                    scaffold_args(["--target", str(legacy), "--upgrade-tools"]),
                    context,
                )
            self.assertEqual(code, 0)
            self.assertNotIn(
                "authority_model_version",
                read_object(legacy / ".project-orrery.json"),
            )

            invalid = root / "invalid"
            invalid.mkdir()
            invalid_manifest = {**legacy_manifest, "authority_model_version": True}
            manifest_path = invalid / ".project-orrery.json"
            manifest_path.write_text(json.dumps(invalid_manifest), encoding="utf-8")
            before = gate._tree_digest(invalid)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = scaffold_run(
                    scaffold_args(["--target", str(invalid), "--upgrade-tools"]),
                    context,
                )
            self.assertEqual(code, 2)
            self.assertEqual(gate._tree_digest(invalid), before)

            non_regular = root / "non-regular"
            non_regular.mkdir()
            (non_regular / "sentinel.txt").write_text("unchanged", encoding="utf-8")
            (non_regular / ".project-orrery.json").mkdir()
            before = gate._tree_digest(non_regular)
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = scaffold_run(
                    scaffold_args(["--target", str(non_regular), "--upgrade-tools"]),
                    context,
                )
            self.assertEqual(code, 2)
            self.assertEqual(gate._tree_digest(non_regular), before)

    def test_standalone_candidate_rejects_non_regular_manifest_before_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-gate-standalone-shape-") as raw:
            root = Path(raw)
            skill = root / "project-orrery"
            shutil.copytree(gate.SKILL_ROOT, skill)
            (skill / "release-manifest.json").write_text(
                json.dumps(candidate_manifest(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            target = root / "target"
            target.mkdir()
            (target / "sentinel.txt").write_text("unchanged", encoding="utf-8")
            (target / ".project-orrery.json").mkdir()
            before = gate._tree_digest(target)
            result = gate._run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(skill / "scripts" / "install_project_orrery.py"),
                    "--target",
                    str(target),
                    "--upgrade-tools",
                ],
                cwd=root,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("regular file", result.stderr)
            self.assertEqual(gate._tree_digest(target), before)

    def test_full_offline_gate_is_deterministic_and_keeps_release_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-gate-full-") as raw:
            root = Path(raw)
            manifest = root / "candidate.json"
            manifest.write_text(
                json.dumps(candidate_manifest(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            first_output = root / "first"
            second_output = root / "second"
            first = gate.run_gate(
                candidate_manifest_path=manifest,
                output_dir=first_output,
                expected_version="0.2.1",
            )
            second = gate.run_gate(
                candidate_manifest_path=manifest,
                output_dir=second_output,
                expected_version="0.2.1",
            )
            self.assertEqual(first, second)
            self.assertTrue(first["candidate_ready"])
            self.assertFalse(first["release_ready"])
            self.assertEqual(
                first["release_blockers"],
                [
                    "maintainer-version-selection",
                    "m2.2-consumer-production-evidence",
                ],
            )
            self.assertEqual(
                first["offline_installer"]["new_scaffold"],
                "authority-model-1-selected-adoption-pending",
            )
            self.assertEqual(
                first["offline_installer"]["legacy_ordinary_upgrade"],
                "selector-missing-preserved",
            )
            self.assertEqual(
                first["offline_installer"]["legacy_baseline"],
                "current-source-with-public-v0.2-manifest",
            )
            self.assertEqual(
                first["explicit_authority_lifecycle"]["execution_path"],
                "source-neutral-cli",
            )
            self.assertEqual(
                first["explicit_authority_lifecycle"]["migration"],
                "receipt-gated",
            )
            self.assertTrue(
                first["explicit_authority_lifecycle"]["exact_restore"]
            )
            self.assertIn(
                "authority-model-validated-by-selector",
                first["claims_not_established"],
            )
            archive = first_output / first["archive"]["name"]
            second_archive = second_output / second["archive"]["name"]
            self.assertEqual(archive.read_bytes(), second_archive.read_bytes())
            self.assertEqual(
                hashlib.sha256(archive.read_bytes()).hexdigest(),
                first["archive"]["sha256"],
            )
            with zipfile.ZipFile(archive) as bundle:
                packaged = json.loads(
                    bundle.read("project-orrery/release-manifest.json")
                )
            self.assertEqual(packaged["authority_model_version"], 1)
            self.assertEqual(
                packaged["compatibility"]["authority_model_versions"]["supported"],
                [1],
            )


if __name__ == "__main__":
    unittest.main()
