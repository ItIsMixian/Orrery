import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS = REPO_ROOT / "experiments" / "context-routing" / "harness"
PROXY = HARNESS / "context_read_proxy.py"
HOOK = HARNESS / "hook_audit.py"
VALIDATOR = HARNESS / "validate_access_audit.py"
CLI_VALIDATOR = HARNESS / "validate_cli_events.py"
SEALER = HARNESS / "seal_raw_evidence.py"
RETENTION_POLICY = HARNESS / "raw-evidence-retention-policy.json"


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class ContextReadProxyTests(unittest.TestCase):
    def make_environment(self, root: Path, audit_root: Path) -> dict[str, str]:
        audit_root.mkdir(parents=True, exist_ok=True)
        state = audit_root / "state.json"
        state.write_text(
            json.dumps({"schema_version": 1, "phase": "prewrite", "read_ranges": {}}),
            encoding="utf-8",
        )
        policy = audit_root / "policy.json"
        policy.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "proxy_script": ".benchmark/context_read_proxy.py",
                    "allowed_non_content_tools": ["update_plan"],
                    "postwrite_commands": ["git diff --check"],
                    "expected_write_paths": [],
                    "minimum_content_reads": 1,
                }
            ),
            encoding="utf-8",
        )
        return {
            **os.environ,
            "ORRERY_BENCHMARK_REPO_ROOT": str(root),
            "ORRERY_PROXY_AUDIT_LOG": str(audit_root / "proxy.jsonl"),
            "ORRERY_HOOK_AUDIT_LOG": str(audit_root / "hook.jsonl"),
            "ORRERY_ACCESS_STATE": str(state),
            "ORRERY_ACCESS_POLICY": str(policy),
        }

    def run_proxy(self, env: dict[str, str], *arguments: str):
        return subprocess.run(
            [sys.executable, str(PROXY), *arguments],
            cwd=env["ORRERY_BENCHMARK_REPO_ROOT"],
            env=env,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def run_hook(self, env: dict[str, str], payload: dict):
        return subprocess.run(
            [sys.executable, str(HOOK)],
            cwd=env["ORRERY_BENCHMARK_REPO_ROOT"],
            env=env,
            input=json.dumps(payload),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_proxy_records_exact_slice_and_requires_reason_for_expansion(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-proxy-") as temporary:
            parent = Path(temporary)
            root = parent / "repo"
            audit = parent / "audit"
            root.mkdir()
            (root / "a.txt").write_text("one\ntwo\nthree\n", encoding="utf-8", newline="\n")
            (root / "b.txt").write_text("bee\n", encoding="utf-8", newline="\n")
            (root / "c.txt").write_text("sea\n", encoding="utf-8", newline="\n")
            env = self.make_environment(root, audit)

            first = self.run_proxy(env, "read", "--path", "a.txt", "--start", "2", "--end", "3")
            self.assertEqual(0, first.returncode, msg=first.stderr)
            self.assertIn("two\nthree\n", first.stdout)
            second = self.run_proxy(env, "read", "--path", "b.txt")
            self.assertEqual(0, second.returncode, msg=second.stderr)
            refused = self.run_proxy(env, "read", "--path", "c.txt")
            self.assertEqual(2, refused.returncode)
            self.assertIn("expands the initial aperture", refused.stderr)
            expanded = self.run_proxy(
                env,
                "read",
                "--path",
                "c.txt",
                "--reason",
                "dependency-found",
            )
            self.assertEqual(0, expanded.returncode, msg=expanded.stderr)

            reads = [event for event in read_jsonl(audit / "proxy.jsonl") if event["operation"] == "read"]
            self.assertEqual(3, len(reads))
            selected = "two\nthree\n".encode("utf-8")
            self.assertEqual(hashlib.sha256(selected).hexdigest(), reads[0]["returned_sha256"])
            self.assertEqual(len(selected), reads[0]["returned_bytes"])
            self.assertFalse(reads[0]["expansion"])
            self.assertTrue(reads[2]["expansion"])

    def test_proxy_rejects_traversal_and_forbidden_metadata(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-paths-") as temporary:
            parent = Path(temporary)
            root = parent / "repo"
            audit = parent / "audit"
            root.mkdir()
            (parent / "outside.txt").write_text("secret", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("hidden", encoding="utf-8")
            env = self.make_environment(root, audit)
            traversal = self.run_proxy(env, "read", "--path", "../outside.txt")
            windows_absolute = self.run_proxy(env, "read", "--path", "C:\\outside.txt")
            metadata = self.run_proxy(env, "read", "--path", ".git/config")
            self.assertEqual(2, traversal.returncode)
            self.assertEqual(2, windows_absolute.returncode)
            self.assertEqual(2, metadata.returncode)
            link = root / "outside-link.txt"
            try:
                os.symlink(parent / "outside.txt", link)
            except OSError:
                pass
            else:
                linked = self.run_proxy(env, "read", "--path", "outside-link.txt")
                self.assertEqual(2, linked.returncode)

    def test_hooks_block_direct_reads_and_cross_check_model_response(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-hooks-") as temporary:
            parent = Path(temporary)
            root = parent / "repo"
            audit = parent / "audit"
            root.mkdir()
            (root / "a.txt").write_text("alpha\nbeta\n", encoding="utf-8", newline="\n")
            env = self.make_environment(root, audit)

            blocked = self.run_hook(
                env,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "direct-1",
                    "tool_input": {"command": "Get-Content -Raw a.txt"},
                },
            )
            self.assertEqual(0, blocked.returncode, msg=blocked.stderr)
            self.assertEqual(
                "deny",
                json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"],
            )

            proxy_command = (
                '"C:\\runtime\\pwsh.exe" -Command '
                "'python .benchmark/context_read_proxy.py read --path a.txt'"
            )
            allowed = self.run_hook(
                env,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "proxy-1",
                    "tool_input": {"command": proxy_command},
                },
            )
            self.assertEqual(0, allowed.returncode, msg=allowed.stderr)
            self.assertEqual({}, json.loads(allowed.stdout))

            injected = self.run_hook(
                env,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "proxy-injection",
                    "tool_input": {
                        "command": (
                            "python .benchmark/context_read_proxy.py read --path "
                            "(Get-Content secret.txt)"
                        )
                    },
                },
            )
            self.assertEqual(
                "deny",
                json.loads(injected.stdout)["hookSpecificOutput"]["permissionDecision"],
            )

            proxy_output = self.run_proxy(env, "read", "--path", "a.txt")
            self.assertEqual(0, proxy_output.returncode, msg=proxy_output.stderr)
            observed = self.run_hook(
                env,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "proxy-1",
                    "tool_input": {"command": proxy_command},
                    "tool_response": {
                        "output": proxy_output.stdout.replace("\n", "\r\n"),
                        "exit_code": 0,
                    },
                },
            )
            self.assertEqual(0, observed.returncode, msg=observed.stderr)

            validation = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--proxy-log",
                    str(audit / "proxy.jsonl"),
                    "--hook-log",
                    str(audit / "hook.jsonl"),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, validation.returncode, msg=validation.stdout + validation.stderr)
            summary = json.loads(validation.stdout)
            self.assertTrue(summary["apparatus_valid"])
            self.assertEqual(1, summary["content_reads_proved"])
            self.assertEqual(2, summary["denied_bypass_attempts"])

    def test_apply_patch_opens_only_postwrite_command_phase(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-phase-") as temporary:
            parent = Path(temporary)
            root = parent / "repo"
            audit = parent / "audit"
            root.mkdir()
            env = self.make_environment(root, audit)
            before = self.run_hook(
                env,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "test-before",
                    "tool_input": {"command": "git diff --check"},
                },
            )
            self.assertEqual("deny", json.loads(before.stdout)["hookSpecificOutput"]["permissionDecision"])
            write = self.run_hook(
                env,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "apply_patch",
                    "tool_use_id": "write-1",
                    "tool_input": {"command": "*** Begin Patch\n*** End Patch"},
                },
            )
            self.assertEqual({}, json.loads(write.stdout))
            after = self.run_hook(
                env,
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "test-after",
                    "tool_input": {"command": "git   diff --check"},
                },
            )
            self.assertEqual({}, json.loads(after.stdout))

    def test_cli_jsonl_proves_proxy_output_and_rejects_unapproved_command(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-cli-events-") as temporary:
            parent = Path(temporary)
            root = parent / "repo"
            audit = parent / "audit"
            root.mkdir()
            (root / "a.txt").write_text("alpha\nbeta\n", encoding="utf-8", newline="\n")
            env = self.make_environment(root, audit)
            proxy_output = self.run_proxy(env, "read", "--path", "a.txt", "--start", "1", "--end", "1")
            self.assertEqual(0, proxy_output.returncode, msg=proxy_output.stderr)
            proxy_command = (
                '"C:\\runtime\\pwsh.exe" -Command '
                "'python .benchmark/context_read_proxy.py read --path a.txt --start 1 --end 1'"
            )
            events_path = audit / "events.jsonl"
            events = [
                {
                    "type": "item.started",
                    "item": {
                        "id": "item-1",
                        "type": "command_execution",
                        "command": proxy_command,
                        "status": "in_progress",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item-1",
                        "type": "command_execution",
                        "command": proxy_command,
                        "aggregated_output": proxy_output.stdout.replace("\n", "\r\n"),
                        "exit_code": 0,
                        "status": "completed",
                    },
                },
                {"type": "item.completed", "item": {"id": "item-2", "type": "agent_message", "text": "done"}},
            ]
            events_path.write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8", newline="\n"
            )
            command = [
                sys.executable,
                str(CLI_VALIDATOR),
                "--events",
                str(events_path),
                "--proxy-log",
                str(audit / "proxy.jsonl"),
                "--policy",
                str(audit / "policy.json"),
            ]
            valid = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, valid.returncode, msg=valid.stdout + valid.stderr)
            self.assertEqual("codex-exec-jsonl-posthoc", json.loads(valid.stdout)["evidence_mode"])

            events.append(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "item-3",
                        "type": "command_execution",
                        "command": "Get-Content -Raw secret.txt",
                        "aggregated_output": "secret",
                        "exit_code": 0,
                        "status": "completed",
                    },
                }
            )
            events_path.write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8", newline="\n"
            )
            rejected = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(1, rejected.returncode)
            self.assertEqual(["Get-Content -Raw secret.txt"], json.loads(rejected.stdout)["unapproved_commands"])

    def test_cli_jsonl_accepts_raw_crlf_proxy_bytes_without_weakening_hash_match(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-cli-crlf-") as temporary:
            parent = Path(temporary)
            root = parent / "repo"; root.mkdir()
            audit = parent / "audit"
            (root / "windows.txt").write_bytes(b"alpha\r\nbeta\r\n")
            env = self.make_environment(root, audit)
            proxy_output = self.run_proxy(env, "read", "--path", "windows.txt", "--start", "1", "--end", "2")
            self.assertEqual(0, proxy_output.returncode, proxy_output.stderr)
            proxy_event = read_jsonl(audit / "proxy.jsonl")[0]
            header = proxy_output.stdout.splitlines()[0]
            request_id = proxy_event["request_id"]
            raw_crlf_output = header + "\nalpha\r\nbeta\r\n\nORRERY_READ_END " + request_id + "\n"
            command_text = "python .benchmark/context_read_proxy.py read --path windows.txt --start 1 --end 2"
            events = [
                {
                    "type": "item.started",
                    "item": {"id": "read-1", "type": "command_execution", "command": command_text, "status": "in_progress"},
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "read-1",
                        "type": "command_execution",
                        "command": command_text,
                        "aggregated_output": raw_crlf_output,
                        "exit_code": 0,
                        "status": "completed",
                    },
                },
            ]
            events_path = audit / "events.jsonl"
            events_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI_VALIDATOR),
                    "--events",
                    str(events_path),
                    "--proxy-log",
                    str(audit / "proxy.jsonl"),
                    "--policy",
                    str(audit / "policy.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            events[1]["item"]["aggregated_output"] = raw_crlf_output.replace("\r\n", "\r\r\n")
            events_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
            translated = subprocess.run(
                [
                    sys.executable,
                    str(CLI_VALIDATOR),
                    "--events",
                    str(events_path),
                    "--proxy-log",
                    str(audit / "proxy.jsonl"),
                    "--policy",
                    str(audit / "policy.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, translated.returncode, translated.stdout + translated.stderr)
            events[1]["item"]["aggregated_output"] = raw_crlf_output.replace("beta", "tampered")
            events_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(CLI_VALIDATOR),
                    "--events",
                    str(events_path),
                    "--proxy-log",
                    str(audit / "proxy.jsonl"),
                    "--policy",
                    str(audit / "policy.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(1, rejected.returncode)

    def test_cli_jsonl_rejects_unknown_local_or_hosted_item_type(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-cli-unknown-") as temporary:
            root = Path(temporary)
            events = root / "events.jsonl"
            proxy = root / "proxy.jsonl"
            policy = root / "policy.json"
            events.write_text(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"id": "mcp-1", "type": "mcp_tool_call", "name": "read_file"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            proxy.write_text("", encoding="utf-8")
            policy.write_text(
                json.dumps({"proxy_script": ".benchmark/context_read_proxy.py", "minimum_content_reads": 0}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI_VALIDATOR),
                    "--events",
                    str(events),
                    "--proxy-log",
                    str(proxy),
                    "--policy",
                    str(policy),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(1, result.returncode)
            self.assertEqual(["mcp_tool_call"], json.loads(result.stdout)["unexpected_item_types"])

    def test_cli_jsonl_normalizes_windows_wrappers_and_absolute_write_paths(self):
        with tempfile.TemporaryDirectory(prefix="orrery-h2-cli-normalize-") as temporary:
            root = Path(temporary)
            repository = root / "repo"
            repository.mkdir()
            product = repository / "product.py"
            product.write_text("pass\n", encoding="utf-8")
            events = root / "events.jsonl"
            proxy = root / "proxy.jsonl"
            policy = root / "policy.json"
            wrapped = '"C:\\runtime\\pwsh.exe" -Command \'python -m unittest discover -s tests -v\''
            records = [
                {
                    "type": "item.started",
                    "item": {
                        "id": "write-1",
                        "type": "file_change",
                        "status": "in_progress",
                        "changes": [{"path": str(product), "kind": "update"}],
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "write-1",
                        "type": "file_change",
                        "status": "completed",
                        "changes": [{"path": str(product), "kind": "update"}],
                    },
                },
                {
                    "type": "item.started",
                    "item": {
                        "id": "validation-1",
                        "type": "command_execution",
                        "command": wrapped,
                        "status": "in_progress",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "validation-1",
                        "type": "command_execution",
                        "command": wrapped,
                        "aggregated_output": "candidate tests failed",
                        "exit_code": 1,
                        "status": "failed",
                    },
                },
            ]
            events.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
            proxy.write_text("", encoding="utf-8")
            policy.write_text(
                json.dumps(
                    {
                        "proxy_script": ".benchmark/context_read_proxy.py",
                        "repository_root": str(repository),
                        "minimum_content_reads": 0,
                        "expected_write_paths": ["product.py"],
                        "postwrite_commands": ["python -m unittest discover -s tests -v"],
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(CLI_VALIDATOR),
                    "--events",
                    str(events),
                    "--proxy-log",
                    str(proxy),
                    "--policy",
                    str(policy),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual([], report["unapproved_commands"])
            self.assertEqual([], report["unexpected_write_paths"])
            self.assertEqual(["validation-1"], report["failed_postwrite_commands"])


class RawEvidenceRetentionTests(unittest.TestCase):
    def run_sealer(self, *arguments: str):
        return subprocess.run(
            [sys.executable, str(SEALER), *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_seal_verify_status_and_tamper_detection(self):
        with tempfile.TemporaryDirectory(prefix="orrery-raw-evidence-") as temporary:
            run_root = Path(temporary) / "pilot-005" / "run-a"
            run_root.mkdir(parents=True)
            (run_root / "events.jsonl").write_text('{"type":"turn.started"}\n', encoding="utf-8")
            (run_root / "stderr.log").write_text("", encoding="utf-8")
            manifest = run_root / "raw-evidence-manifest.json"
            sealed = self.run_sealer(
                "seal",
                "--run-root",
                str(run_root),
                "--policy",
                str(RETENTION_POLICY),
                "--pilot-id",
                "pilot-005",
                "--run-id",
                "run-a",
                "--classification",
                "exploratory",
                "--source-commit",
                "a" * 40,
                "--apparatus-version",
                "h2-read-proof-v0.1",
                "--created-at",
                "2026-08-18T00:00:00+08:00",
            )
            self.assertEqual(0, sealed.returncode, msg=sealed.stdout + sealed.stderr)
            value = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(2, len(value["files"]))
            self.assertFalse(any(Path(entry["path"]).is_absolute() for entry in value["files"]))
            verified = self.run_sealer("verify", "--manifest", str(manifest))
            self.assertEqual(0, verified.returncode, msg=verified.stdout + verified.stderr)
            status = self.run_sealer(
                "status",
                "--manifest",
                str(manifest),
                "--at",
                "2026-11-17T00:00:00+08:00",
            )
            self.assertEqual("expired", json.loads(status.stdout)["status"])
            self.assertFalse(json.loads(status.stdout)["automatic_deletion"])

            (run_root / "events.jsonl").write_text("tampered\n", encoding="utf-8")
            failed = self.run_sealer("verify", "--manifest", str(manifest))
            self.assertEqual(1, failed.returncode)
            reasons = {item["reason"] for item in json.loads(failed.stdout)["failures"]}
            self.assertIn("hash-mismatch", reasons)

            value["files"][0]["sha256"] = "not-a-sha256"
            manifest.write_text(json.dumps(value), encoding="utf-8")
            invalid_manifest = self.run_sealer("verify", "--manifest", str(manifest))
            self.assertEqual(2, invalid_manifest.returncode)
            self.assertIn("invalid manifest file hash", invalid_manifest.stderr)


class Pilot005ApparatusTests(unittest.TestCase):
    def test_frozen_apparatus_dry_run(self):
        runner = (
            REPO_ROOT
            / "experiments"
            / "context-routing"
            / "pilots"
            / "pilot-005"
            / "run_pilot.py"
        )
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(runner), "--dry-run"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["pilot"], "pilot-005")
        self.assertEqual(report["dry_run"], "passed")
        self.assertIn(
            "experiments/context-routing/pilots/pilot-005/operator/acceptance.py",
            report["control_hashes"],
        )

    def test_pilot_006_corrected_apparatus_dry_run(self):
        runner = (
            REPO_ROOT
            / "experiments"
            / "context-routing"
            / "pilots"
            / "pilot-006"
            / "run_pilot.py"
        )
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(runner), "--dry-run"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["pilot"], "pilot-006")
        self.assertEqual(report["dry_run"], "passed")
        self.assertIn(
            "experiments/context-routing/pilots/pilot-006/run_pilot.py",
            report["control_hashes"],
        )

    def test_pilot_007_b_adoption_apparatus_dry_run(self):
        runner = (
            REPO_ROOT
            / "experiments"
            / "context-routing"
            / "pilots"
            / "pilot-007"
            / "run_pilot.py"
        )
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(runner), "--dry-run"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=90,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["pilot"], "pilot-007")
        self.assertEqual(report["dry_run"], "passed")
        self.assertIn(
            "experiments/context-routing/pilots/pilot-007/operator/acceptance.py",
            report["control_hashes"],
        )


if __name__ == "__main__":
    unittest.main()
