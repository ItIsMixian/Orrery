import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "experiments" / "context-routing" / "validate_benchmark.py"
CORPUS_PATH = REPO_ROOT / "experiments" / "context-routing" / "corpus.json"
SCHEMA_DIR = REPO_ROOT / "experiments" / "context-routing" / "schemas"
RUNS_DIR = REPO_ROOT / "experiments" / "context-routing" / "runs"
PILOT_002_DIR = REPO_ROOT / "experiments" / "context-routing" / "pilots" / "pilot-002"
PILOT_003_DIR = REPO_ROOT / "experiments" / "context-routing" / "pilots" / "pilot-003"
PILOT_003_VALIDATOR_PATH = PILOT_003_DIR / "validate_pilot.py"
PILOT_003_RUNNER_PATH = PILOT_003_DIR / "run_pilot.py"
PILOT_003_SECURITY_PATH = PILOT_003_DIR / "security_acceptance.py"
PILOT_004_DIR = REPO_ROOT / "experiments" / "context-routing" / "pilots" / "pilot-004"
PILOT_004_REVIEW_ORACLE_PATH = PILOT_004_DIR / "operator" / "holdout_acceptance_v2.py"

SPEC = importlib.util.spec_from_file_location("context_routing_validator", VALIDATOR_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)

PILOT_003_SPEC = importlib.util.spec_from_file_location("pilot_003_validator", PILOT_003_VALIDATOR_PATH)
PILOT_003_VALIDATOR = importlib.util.module_from_spec(PILOT_003_SPEC)
assert PILOT_003_SPEC.loader is not None
PILOT_003_SPEC.loader.exec_module(PILOT_003_VALIDATOR)

PILOT_003_RUNNER_SPEC = importlib.util.spec_from_file_location("pilot_003_runner", PILOT_003_RUNNER_PATH)
PILOT_003_RUNNER = importlib.util.module_from_spec(PILOT_003_RUNNER_SPEC)
assert PILOT_003_RUNNER_SPEC.loader is not None
PILOT_003_RUNNER_SPEC.loader.exec_module(PILOT_003_RUNNER)

PILOT_003_SECURITY_SPEC = importlib.util.spec_from_file_location(
    "pilot_003_security", PILOT_003_SECURITY_PATH
)
PILOT_003_SECURITY = importlib.util.module_from_spec(PILOT_003_SECURITY_SPEC)
assert PILOT_003_SECURITY_SPEC.loader is not None
PILOT_003_SECURITY_SPEC.loader.exec_module(PILOT_003_SECURITY)

PILOT_004_REVIEW_SPEC = importlib.util.spec_from_file_location(
    "pilot_004_review_oracle", PILOT_004_REVIEW_ORACLE_PATH
)
PILOT_004_REVIEW_ORACLE = importlib.util.module_from_spec(PILOT_004_REVIEW_SPEC)
assert PILOT_004_REVIEW_SPEC.loader is not None
PILOT_004_REVIEW_SPEC.loader.exec_module(PILOT_004_REVIEW_ORACLE)


def make_run(task_id="PO-CR-001"):
    return {
        "schema_version": 1,
        "run_id": "example-run",
        "task_id": task_id,
        "variant": "B",
        "repository_commit": "e38ef8d70cc267666f8ef3c76d01eccf0f677b4e",
        "started_at": "2026-08-17T10:00:00Z",
        "ended_at": "2026-08-17T10:05:00Z",
        "execution": {
            "model": None,
            "harness": "test",
            "toolchain": None,
            "permission_profile": "read-write",
            "prompt_revision": "test-fixture-v1",
            "prompt_sha256": None,
            "external_context_policy": "repository_only",
            "operator_interventions": []
        },
        "events": [
            {
                "sequence": 1,
                "timestamp": "2026-08-17T10:00:01Z",
                "event_type": "content_read",
                "observed_by": "agent",
                "target_scope": "repository",
                "target": "README.md",
                "reason_code": "agent-report"
            },
            {
                "sequence": 2,
                "timestamp": "2026-08-17T10:00:02Z",
                "event_type": "content_read",
                "observed_by": "harness",
                "target_scope": "repository",
                "target": "skills/project-orrery/SKILL.md",
                "reason_code": "manifest"
            }
        ],
        "metrics": {
            "input_tokens": None,
            "output_tokens": None,
            "wall_time_seconds": 300,
            "provider_cost": None,
            "documents_touched": 0,
            "documentation_sync_seconds": None,
            "conflict_warning_delay_seconds": None
        },
        "artifacts": {
            "changed_paths": ["README.md"],
            "diff_git_oid": None
        },
        "outcome": {
            "task_accepted": None,
            "validation_passed": None,
            "missed_dependencies": None,
            "irrelevant_reads": None,
            "necessary_reads_missed": None,
            "scope_expansions": 0,
            "notes": "Schema fixture only."
        },
        "evaluation": {
            "reference_match": "not_evaluated",
            "apparatus_valid": None,
            "confounds": [],
            "notes": "Schema fixture only."
        }
    }


class ContextRoutingBenchmarkTests(unittest.TestCase):
    def test_pilot_004_h_is_frozen_and_corrected_oracle_self_tests(self):
        h_path = PILOT_004_DIR / "variants" / "H.zh-CN.md"
        self.assertEqual(
            "2181e00c69ed9026cd3164479d6294eaa3a8b51c143eb56599462fc52b78be1d",
            hashlib.sha256(h_path.read_bytes()).hexdigest(),
        )
        self.assertEqual([], PILOT_004_REVIEW_ORACLE.self_test())

    @classmethod
    def setUpClass(cls):
        with CORPUS_PATH.open("r", encoding="utf-8") as handle:
            cls.corpus = json.load(handle)
        cls.task_ids = {task["id"] for task in cls.corpus["tasks"]}

    def test_historical_corpus_matches_git(self):
        errors = VALIDATOR.validate_corpus(self.corpus, REPO_ROOT, check_git=True)
        self.assertEqual([], errors)
        self.assertEqual(24, len(self.corpus["tasks"]))

    def test_schema_documents_are_valid_json(self):
        for name in ("task-corpus.schema.json", "run-record.schema.json"):
            with self.subTest(name=name):
                with (SCHEMA_DIR / name).open("r", encoding="utf-8") as handle:
                    schema = json.load(handle)
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
        with (PILOT_003_DIR / "agent-receipt.schema.json").open("r", encoding="utf-8") as handle:
            receipt_schema = json.load(handle)
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", receipt_schema["$schema"])

    def test_corpus_rejects_parent_and_absolute_paths(self):
        corpus = copy.deepcopy(self.corpus)
        corpus["tasks"][0]["oracle"]["reference_changed_paths"] = ["../secret.txt"]
        corpus["tasks"][1]["oracle"]["curated_context_paths"] = ["C:/private/file.md"]
        errors = VALIDATOR.validate_corpus(corpus, REPO_ROOT, check_git=False)
        self.assertTrue(any("unsafe path" in error and "../secret.txt" in error for error in errors))
        self.assertTrue(any("unsafe path" in error and "C:/private/file.md" in error for error in errors))

    def test_agent_self_report_is_not_independent_access_evidence(self):
        summary = VALIDATOR.summarize_run(make_run())
        self.assertEqual(2, summary["total_events"])
        self.assertEqual(1, summary["independently_observed_events"])
        self.assertTrue(summary["content_read_compliance_observable"])

        agent_only = make_run()
        agent_only["events"] = agent_only["events"][:1]
        summary = VALIDATOR.summarize_run(agent_only)
        self.assertEqual(0, summary["independently_observed_events"])
        self.assertFalse(summary["content_read_compliance_observable"])

    def test_run_record_requires_known_task_monotonic_events_and_timezones(self):
        run = make_run(task_id="PO-CR-999")
        run["events"][1]["sequence"] = 1
        run["ended_at"] = "2026-08-17T09:59:00Z"
        run["events"][0]["timestamp"] = "2026-08-17T10:00:01"
        errors = VALIDATOR.validate_run_record(run, self.task_ids)
        self.assertTrue(any("not in the corpus" in error for error in errors))
        self.assertTrue(any("strictly increasing" in error for error in errors))
        self.assertTrue(any("must not be earlier" in error for error in errors))
        self.assertTrue(any("must include a timezone" in error for error in errors))

    def test_valid_run_record_passes(self):
        self.assertEqual([], VALIDATOR.validate_run_record(make_run(), self.task_ids))

    def test_run_record_rejects_invalid_prompt_provenance_metadata(self):
        run = make_run()
        run["execution"]["prompt_sha256"] = "NOT-A-SHA"
        run["execution"]["external_context_policy"] = "trust-me"
        run["execution"]["operator_interventions"] = [""]
        errors = VALIDATOR.validate_run_record(run, self.task_ids)
        self.assertTrue(any("prompt_sha256" in error for error in errors))
        self.assertTrue(any("external_context_policy" in error for error in errors))
        self.assertTrue(any("operator_interventions" in error for error in errors))

    def test_committed_run_records_validate(self):
        run_paths = sorted(path for path in RUNS_DIR.glob("*.json") if not path.name.startswith("_"))
        self.assertGreaterEqual(len(run_paths), 3)
        for path in run_paths:
            with self.subTest(path=path.name):
                with path.open("r", encoding="utf-8") as handle:
                    run = json.load(handle)
                self.assertEqual([], VALIDATOR.validate_run_record(run, self.task_ids))

    def test_pilot_002_packet_supplies_gold_fact_without_reference_leakage(self):
        with (PILOT_002_DIR / "pilot-config.json").open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        common = (PILOT_002_DIR / config["common_task_file"]).read_text(encoding="utf-8")
        task = next(task for task in self.corpus["tasks"] if task["id"] == config["task_id"])

        self.assertEqual("repository_only", config["external_context_policy"])
        self.assertIn(config["canonical_skill_url"], common)
        self.assertNotIn(task["source"]["base_commit"], common)
        self.assertNotIn(task["source"]["reference_commit"], common)
        self.assertIn("RUN CONTAMINATED", common)
        self.assertIn("搜索若返回多个文件的匹配正文", common)

    @unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
    def test_prepare_pilot_002_creates_isolated_repositories_and_prompt_hashes(self):
        script = PILOT_002_DIR / "prepare_pilot.ps1"
        with tempfile.TemporaryDirectory(prefix="project-orrery-pilot-002-test-") as temporary_parent:
            output_root = Path(temporary_parent) / "prepared"
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-OutputRoot",
                    str(output_root),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)

            manifest_path = output_root / "_operator" / "pilot-manifest.json"
            with manifest_path.open("r", encoding="utf-8-sig") as handle:
                manifest = json.load(handle)
            self.assertEqual("pilot-002", manifest["pilot_id"])
            self.assertEqual("repository_only", manifest["external_context_policy"])
            self.assertEqual(3, len(manifest["variants"]))

            overlay_contents = set()

            for variant_record in manifest["variants"]:
                variant = variant_record["variant"]
                repository = output_root / f"PO-CR-004-{variant}"
                prompt_path = Path(variant_record["prompt_path"])
                prompt_bytes = prompt_path.read_bytes()
                self.assertTrue(prompt_bytes.startswith(b"\xef\xbb\xbf"))
                self.assertEqual(
                    variant_record["prompt_sha256"],
                    hashlib.sha256(prompt_bytes).hexdigest(),
                )
                prompt_text = prompt_bytes.decode("utf-8-sig")
                self.assertIn(manifest["canonical_skill_url"], prompt_text)
                self.assertIn("共同任务包", prompt_text)
                self.assertIn("运行前检查", prompt_text)
                self.assertFalse((repository / "_operator").exists())

                overlay_path = repository / ".codex" / "config.toml"
                overlay_bytes = overlay_path.read_bytes()
                overlay_contents.add(overlay_bytes)
                self.assertEqual(
                    manifest["harness_overlay"]["sha256"],
                    hashlib.sha256(overlay_bytes).hexdigest(),
                )
                overlay_text = overlay_bytes.decode("utf-8")
                self.assertGreaterEqual(overlay_text.count("[[skills.config]]"), 4)
                self.assertGreaterEqual(overlay_text.count("enabled = false"), 4)

                remote = subprocess.run(
                    ["git", "remote"],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                history = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual("", remote.stdout.strip())
                self.assertEqual("1", history.stdout.strip())
                self.assertEqual("", status.stdout.strip())

            self.assertEqual(1, len(overlay_contents))

    def test_pilot_003_packet_covers_multifile_cross_module_and_security_work(self):
        with (PILOT_003_DIR / "pilot-config.json").open("r", encoding="utf-8") as handle:
            config = json.load(handle)
        task_ids = [task["task_id"] for task in config["tasks"]]
        self.assertEqual(["PO-CR-006", "PO-CR-010", "PO-CR-011"], task_ids)
        corpus_by_id = {task["id"]: task for task in self.corpus["tasks"]}
        self.assertEqual("documentation", corpus_by_id["PO-CR-006"]["category"])
        self.assertEqual("cross_module", corpus_by_id["PO-CR-010"]["category"])
        self.assertEqual("security", corpus_by_id["PO-CR-011"]["category"])
        self.assertEqual(
            ["PO-CR-010", "PO-CR-011"],
            config["security_acceptance"]["task_ids"],
        )

        common = (PILOT_003_DIR / config["common_protocol_file"]).read_text(encoding="utf-8")
        self.assertIn(".benchmark/agent-receipt.json", common)
        self.assertIn("Agent self-report; not an independent Harness audit", common)
        self.assertIn("完整 `CONTEXT MANIFEST`", common)

        for task_config in config["tasks"]:
            task = corpus_by_id[task_config["task_id"]]
            task_packet = (PILOT_003_DIR / task_config["task_file"]).read_text(encoding="utf-8")
            self.assertIn(task_config["task_id"], task_packet)
            self.assertNotIn(task["source"]["base_commit"], task_packet)
            self.assertNotIn(task["source"]["reference_commit"], task_packet)
            self.assertGreaterEqual(len(task["oracle"]["reference_changed_paths"]), 2)

        runner_text = (PILOT_003_DIR / "run_pilot.py").read_text(encoding="utf-8")
        summary_text = (PILOT_003_DIR / "summarize_pilot.py").read_text(encoding="utf-8")
        self.assertIn("--resume", runner_text)
        self.assertIn("--dry-run", runner_text)
        self.assertIn("ThreadPoolExecutor", runner_text)
        self.assertIn("never silently retried", runner_text)
        self.assertIn("not proof of exact model-visible file bytes", runner_text)
        self.assertIn("not an ADR", summary_text)

    def test_harness_product_change_collection_includes_untracked_files(self):
        with tempfile.TemporaryDirectory(prefix="project-orrery-change-capture-") as temporary:
            repository = Path(temporary)
            subprocess.run(["git", "init", "-b", "test"], cwd=repository, check=True, capture_output=True)
            (repository / "README.md").write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repository, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@local.invalid",
                    "commit",
                    "-m",
                    "baseline",
                ],
                cwd=repository,
                check=True,
                capture_output=True,
            )
            (repository / "README.md").write_text("after\n", encoding="utf-8")
            (repository / "README.zh-CN.md").write_text("新增\n", encoding="utf-8")

            collected = PILOT_003_RUNNER.collect_product_changes(repository)
            entries = {entry["path"]: entry for entry in collected["entries"]}
            self.assertEqual("tracked", entries["README.md"]["kind"])
            self.assertEqual("untracked", entries["README.zh-CN.md"]["kind"])
            self.assertEqual("harness", collected["observed_by"])
            self.assertEqual(64, len(entries["README.zh-CN.md"]["sha256"]))

    def test_security_oracle_detects_environment_haskey_regression(self):
        with tempfile.TemporaryDirectory(prefix="project-orrery-security-oracle-") as temporary:
            repository = Path(temporary)
            module_path = repository / PILOT_003_SECURITY.LLM_RELATIVE
            module_path.parent.mkdir(parents=True)
            module_path.write_text(
                "import json, os, tempfile\n"
                "from pathlib import Path\n"
                "_PROJECT_ROOT = Path(__file__).resolve().parents[2]\n"
                "def _keyring_get(): return None\n"
                "def store_key(key): return 'test'\n"
                "def _is_real_key(key): return isinstance(key, str) and bool(key.strip())\n"
                "def _read_json(path):\n"
                "    try: return json.loads(path.read_text(encoding='utf-8'))\n"
                "    except Exception: return None\n"
                "def _atomic_write_json(path, data):\n"
                "    path.parent.mkdir(parents=True, exist_ok=True)\n"
                "    fd, name = tempfile.mkstemp(prefix='.ai-config-', suffix='.tmp', dir=path.parent)\n"
                "    os.close(fd); temporary = Path(name)\n"
                "    try:\n"
                "        temporary.write_text(json.dumps(data), encoding='utf-8')\n"
                "        os.replace(temporary, path)\n"
                "    finally:\n"
                "        if temporary.exists(): temporary.unlink()\n"
                "def save_config(config=None):\n"
                "    supplied = dict(config or {}); path = _PROJECT_ROOT / 'ai-config.json'\n"
                "    existing = _read_json(path) or {}; key = supplied.get('apiKey', existing.get('apiKey'))\n"
                "    if _is_real_key(key): store_key(key)\n"
                "    saved = {'model': supplied.get('model', existing.get('model'))}\n"
                "    _atomic_write_json(path, saved)\n"
                "    return {'hasKey': bool(_keyring_get())}\n"
                "def load_config():\n"
                "    key = os.environ.get('OPENAI_API_KEY') or _keyring_get()\n"
                "    return {'hasKey': bool(key)}\n",
                encoding="utf-8",
            )

            result = PILOT_003_SECURITY.evaluate(repository, "PO-CR-011")
            self.assertFalse(result["ok"])
            self.assertTrue(
                any("loses environment-derived hasKey" in error for error in result["errors"]),
                msg=result,
            )

    def test_security_oracle_detects_config_write_before_credential_storage(self):
        with tempfile.TemporaryDirectory(prefix="project-orrery-security-order-") as temporary:
            root = Path(temporary)
            unsafe = root / "unsafe.py"
            safe = root / "safe.py"
            unsafe.write_text(
                "def save_config(update):\n"
                "    path.write_text('config')\n"
                "    store_key(update['api_key'])\n",
                encoding="utf-8",
            )
            safe.write_text(
                "def save_config(update):\n"
                "    store_key(update['api_key'])\n"
                "    path.write_text('config')\n",
                encoding="utf-8",
            )
            unsafe_errors, _ = PILOT_003_SECURITY.check_storage_before_persistence([unsafe])
            safe_errors, _ = PILOT_003_SECURITY.check_storage_before_persistence([safe])
            self.assertTrue(any("before store_key" in error for error in unsafe_errors))
            self.assertEqual([], safe_errors)

    def test_security_oracle_accepts_keyword_only_save_and_split_http_flow(self):
        calls = []

        def keyword_only_save(*, api_key=None, model=None):
            calls.append((api_key, model))
            return {"hasKey": bool(api_key)}

        result = PILOT_003_SECURITY.invoke_save_config(
            keyword_only_save,
            {"apiKey": "secret", "model": "model"},
        )
        self.assertEqual({"hasKey": True}, result)
        self.assertEqual([("secret", "model")], calls)

        with tempfile.TemporaryDirectory(prefix="project-orrery-security-split-flow-") as temporary:
            module_path = Path(temporary) / "serve.py"
            module_path.write_text(
                "def save_settings(data):\n"
                "    path.write_text('config')\n"
                "def do_POST(data):\n"
                "    store_key(data['apiKey'])\n"
                "    save_settings(data)\n",
                encoding="utf-8",
            )
            errors, _ = PILOT_003_SECURITY.check_storage_before_persistence([module_path])
            self.assertEqual([], errors)

    def test_pilot_003_receipt_enforces_manifest_budget_and_prior_expansion(self):
        run = {
            "run_key": "PO-CR-006-C",
            "task_id": "PO-CR-006",
            "variant": "C",
            "expected_product_write_paths": ["README.md", "README.zh-CN.md"],
            "validation_commands": [["git", "diff", "--check"]],
        }
        manifest = {
            "pilot_id": "pilot-003",
            "prompt_revision": "po-context-routing-pilot-003-v2",
            "agent_receipt": {"path": ".benchmark/agent-receipt.json"},
        }
        operator_run = {"interventions": []}
        context_manifest = {
            "task_classification": "documentation / medium",
            "retrieval_strategy": "multi_file",
            "initial_content_paths": [
                {"path": "README.md", "reason": "English source"},
                {"path": "README.zh-CN.md", "reason": "Target if present"},
            ],
            "expected_product_writes": ["README.md", "README.zh-CN.md"],
            "expected_validation": ["git diff --check"],
            "expansion_conditions": ["A linked rule is missing"],
            "content_file_budget": 2,
        }
        receipt = {
            "schema_version": 1,
            "pilot_id": "pilot-003",
            "prompt_revision": "po-context-routing-pilot-003-v2",
            "task_id": "PO-CR-006",
            "variant": "C",
            "external_context_preflight": "clean",
            "agent_started_at": "2026-08-17T10:00:00+08:00",
            "agent_ended_at": "2026-08-17T10:05:00+08:00",
            "prewrite": {
                "context_manifest": context_manifest,
                "selected_evidence": [
                    {"path": "README.md", "scope": "full", "fact": "English is the default entry"}
                ],
            },
            "events": [
                {
                    "sequence": 1,
                    "event_type": "content_read",
                    "target_scope": "repository",
                    "target": "README.md",
                    "reason_code": "manifest-initial",
                    "content_extent": "full",
                    "range_or_query": None,
                    "declared_before_access": True,
                },
                {
                    "sequence": 2,
                    "event_type": "write",
                    "target_scope": "repository",
                    "target": "README.md",
                    "reason_code": "task-target",
                    "content_extent": None,
                    "range_or_query": None,
                    "declared_before_access": None,
                },
                {
                    "sequence": 3,
                    "event_type": "write",
                    "target_scope": "repository",
                    "target": "README.zh-CN.md",
                    "reason_code": "task-target",
                    "content_extent": None,
                    "range_or_query": None,
                    "declared_before_access": None,
                },
                {
                    "sequence": 4,
                    "event_type": "test",
                    "target_scope": "command",
                    "target": "git diff --check",
                    "reason_code": "validation",
                    "content_extent": None,
                    "range_or_query": None,
                    "declared_before_access": None,
                },
                {
                    "sequence": 5,
                    "event_type": "write",
                    "target_scope": "repository",
                    "target": ".benchmark/agent-receipt.json",
                    "reason_code": "agent-self-report",
                    "content_extent": None,
                    "range_or_query": None,
                    "declared_before_access": None,
                },
            ],
            "operator_questions": [],
            "validation": ["git diff --check: passed"],
            "uncertainty": [],
            "evidence_note": "Agent self-report; not an independent Harness audit",
        }
        self.assertEqual([], PILOT_003_VALIDATOR.validate_receipt(receipt, run, manifest, operator_run))

        invalid = copy.deepcopy(receipt)
        invalid["events"].insert(
            1,
            {
                "sequence": 2,
                "event_type": "content_read",
                "target_scope": "repository",
                "target": "skills/project-orrery/SKILL.md",
                "reason_code": "undeclared",
                "content_extent": "full",
                "range_or_query": None,
                "declared_before_access": False,
            },
        )
        for index, event in enumerate(invalid["events"], start=1):
            event["sequence"] = index
        errors = PILOT_003_VALIDATOR.validate_receipt(invalid, run, manifest, operator_run)
        self.assertTrue(any("without prior expansion" in error for error in errors))

    def test_pilot_003_resume_contaminates_an_interrupted_attempt_without_retry(self):
        with tempfile.TemporaryDirectory(prefix="project-orrery-pilot-003-recovery-") as temporary:
            output_root = Path(temporary)
            repository = output_root / "PO-CR-006-A"
            repository.mkdir()
            manifest = {
                "agent_receipt": {"path": ".benchmark/agent-receipt.json"},
                "runs": [{"run_key": "PO-CR-006-A", "repository_path": str(repository)}],
            }
            operator_log = {"runs": [{"run_key": "PO-CR-006-A", "status": "running"}]}
            state = {
                "runs": {
                    "PO-CR-006-A": {
                        "last_result": None,
                        "note": None,
                    }
                }
            }
            calls = []
            original = PILOT_003_RUNNER.record_action

            def fake_record_action(recorder, root, action, **values):
                calls.append((action, values))

            PILOT_003_RUNNER.record_action = fake_record_action
            try:
                PILOT_003_RUNNER.recover_interrupted_runs(
                    output_root=output_root,
                    recorder=Path("unused.ps1"),
                    manifest=manifest,
                    operator_log=operator_log,
                    state=state,
                )
            finally:
                PILOT_003_RUNNER.record_action = original

            self.assertEqual("Contaminate", calls[0][0])
            self.assertIn("not retried", calls[0][1]["Message"])
            self.assertIn("no automatic retry", state["runs"]["PO-CR-006-A"]["note"])

    @unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
    def test_prepare_pilot_003_records_profile_and_creates_nine_clean_repositories(self):
        script = PILOT_003_DIR / "prepare_pilot.ps1"
        validator = PILOT_003_DIR / "validate_pilot.py"
        recorder = PILOT_003_DIR / "record_operator_run.ps1"
        with tempfile.TemporaryDirectory(prefix="project-orrery-pilot-003-test-") as temporary_parent:
            output_root = Path(temporary_parent) / "prepared"
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-OutputRoot",
                    str(output_root),
                    "-Model",
                    "test-model",
                    "-ReasoningEffort",
                    "test-effort",
                    "-PermissionProfile",
                    "test-permissions",
                    "-Harness",
                    "test-harness",
                    "-NetworkPolicy",
                    "disabled",
                    "-TimeBudgetMinutes",
                    "5",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)

            prepared_validation = subprocess.run(
                [sys.executable, str(validator), "--output-root", str(output_root), "--prepared-only"],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(
                0,
                prepared_validation.returncode,
                msg=prepared_validation.stdout + prepared_validation.stderr,
            )

            with (output_root / "_operator" / "pilot-manifest.json").open("r", encoding="utf-8-sig") as handle:
                manifest = json.load(handle)
            with (output_root / "_operator" / "execution-profile.json").open("r", encoding="utf-8-sig") as handle:
                profile = json.load(handle)
            with (output_root / "_operator" / "operator-run-log.json").open("r", encoding="utf-8-sig") as handle:
                operator_log = json.load(handle)

            self.assertEqual("pilot-003", manifest["pilot_id"])
            self.assertEqual(9, len(manifest["runs"]))
            self.assertEqual(["PO-CR-006", "PO-CR-010", "PO-CR-011"], manifest["selection"]["task_ids"])
            self.assertEqual(["A", "B", "C"], manifest["selection"]["variants"])
            self.assertEqual(9, manifest["selection"]["run_count"])
            self.assertEqual("test-model", profile["model"])
            self.assertEqual("test-effort", profile["reasoning_effort"])
            self.assertEqual("test-permissions", profile["permission_profile"])
            profile_bytes = (output_root / "_operator" / "execution-profile.json").read_bytes()
            self.assertEqual(manifest["execution_profile"]["sha256"], hashlib.sha256(profile_bytes).hexdigest())
            self.assertEqual(9, len(operator_log["runs"]))
            security_path = output_root / "_operator" / "security-acceptance.py"
            self.assertTrue(security_path.is_file())
            self.assertEqual(
                manifest["security_acceptance"]["sha256"],
                hashlib.sha256(security_path.read_bytes()).hexdigest(),
            )
            self.assertTrue(all(run["status"] == "pending" for run in operator_log["runs"]))

            corpus_by_id = {task["id"]: task for task in self.corpus["tasks"]}
            overlay_contents = set()
            for run in manifest["runs"]:
                repository = Path(run["repository_path"])
                prompt_bytes = Path(run["prompt_path"]).read_bytes()
                self.assertTrue(prompt_bytes.startswith(b"\xef\xbb\xbf"))
                self.assertEqual(run["prompt_sha256"], hashlib.sha256(prompt_bytes).hexdigest())
                prompt_text = prompt_bytes.decode("utf-8-sig")
                task = corpus_by_id[run["task_id"]]
                self.assertIn(run["task_id"], prompt_text)
                self.assertIn("agent-receipt.json", prompt_text)
                self.assertNotIn(task["source"]["base_commit"], prompt_text)
                self.assertNotIn(task["source"]["reference_commit"], prompt_text)

                overlay_bytes = (repository / ".codex" / "config.toml").read_bytes()
                overlay_contents.add(overlay_bytes)
                self.assertEqual(manifest["harness_overlay"]["sha256"], hashlib.sha256(overlay_bytes).hexdigest())
                exclude_text = (repository / ".git" / "info" / "exclude").read_text(encoding="utf-8")
                self.assertIn(".benchmark/agent-receipt.json", exclude_text)

                remote = subprocess.run(
                    ["git", "remote"], cwd=repository, check=True, capture_output=True, text=True, encoding="utf-8"
                )
                history = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual("", remote.stdout.strip())
                self.assertEqual("1", history.stdout.strip())
                self.assertEqual("", status.stdout.strip())
            self.assertEqual(1, len(overlay_contents))

            start = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(recorder),
                    "-OutputRoot",
                    str(output_root),
                    "-Action",
                    "Start",
                    "-RunKey",
                    "PO-CR-006-A",
                    "-ThreadId",
                    "test-thread",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, start.returncode, msg=start.stdout + start.stderr)
            intervention = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(recorder),
                    "-OutputRoot",
                    str(output_root),
                    "-Action",
                    "Intervention",
                    "-TaskId",
                    "PO-CR-006",
                    "-Message",
                    "same answer",
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(0, intervention.returncode, msg=intervention.stdout + intervention.stderr)
            with (output_root / "_operator" / "operator-run-log.json").open("r", encoding="utf-8-sig") as handle:
                updated_log = json.load(handle)
            run_a = next(run for run in updated_log["runs"] if run["run_key"] == "PO-CR-006-A")
            self.assertEqual("running", run_a["status"])
            self.assertEqual("test-thread", run_a["thread_id"])
            task_runs = [run for run in updated_log["runs"] if run["task_id"] == "PO-CR-006"]
            self.assertTrue(all(len(run["interventions"]) == 1 for run in task_runs))

    @unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
    def test_pilot_003_runner_completes_selected_bc_matrix_and_resumes_idempotently(self):
        runner = PILOT_003_DIR / "run_pilot.py"
        mock_agent = REPO_ROOT / "tests" / "fixtures" / "mock_codex_exec.py"
        with tempfile.TemporaryDirectory(prefix="project-orrery-pilot-003-runner-") as temporary_parent:
            output_root = Path(temporary_parent) / "automated"
            base_command = [
                sys.executable,
                str(runner),
                "--output-root",
                str(output_root),
                "--model",
                "mock-model",
                "--reasoning-effort",
                "mock-effort",
                "--permission-profile",
                "workspace-write; approval=automatic-review",
                "--time-budget-minutes",
                "2",
                "--max-parallel",
                "3",
                "--agent-command",
                sys.executable,
                "--agent-prefix-arg",
                str(mock_agent),
                "--task-id",
                "PO-CR-010",
                "--task-id",
                "PO-CR-011",
                "--variant",
                "B",
                "--variant",
                "C",
            ]
            dry_run = subprocess.run(
                [*base_command, "--dry-run"],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
            )
            self.assertEqual(0, dry_run.returncode, msg=dry_run.stdout + dry_run.stderr)
            with (output_root / "_operator" / "automation-state.json").open(
                "r", encoding="utf-8-sig"
            ) as handle:
                dry_state = json.load(handle)
            self.assertTrue(all(run["attempts"] == 0 for run in dry_state["runs"].values()))

            result = subprocess.run(
                [*base_command, "--resume"],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
            )
            self.assertEqual(0, result.returncode, msg=result.stdout + result.stderr)

            operator = output_root / "_operator"
            with (operator / "operator-run-log.json").open("r", encoding="utf-8-sig") as handle:
                operator_log = json.load(handle)
            with (operator / "automation-state.json").open("r", encoding="utf-8-sig") as handle:
                state = json.load(handle)
            with (operator / "automation-summary.json").open("r", encoding="utf-8-sig") as handle:
                summary = json.load(handle)

            self.assertIsNotNone(operator_log["sealed_at"])
            self.assertTrue(all(run["status"] == "completed" for run in operator_log["runs"]))
            self.assertTrue(state["sealed"])
            self.assertEqual(0, state["validation_exit_code"])
            self.assertTrue(all(run["attempts"] == 1 for run in state["runs"].values()))
            self.assertNotIn("A", summary["variants"])
            self.assertEqual(2, summary["variants"]["B"]["completed"])
            self.assertEqual(2, summary["variants"]["C"]["completed"])
            self.assertEqual(["PO-CR-010", "PO-CR-011"], summary["selection"]["task_ids"])
            self.assertEqual(["B", "C"], summary["selection"]["variants"])
            self.assertEqual(1, summary["variants"]["B"]["mean_content_reads_self_reported"])
            self.assertEqual(200, summary["variants"]["B"]["usage_totals"]["input_tokens"])
            self.assertTrue((operator / "comparison.md").is_file())
            self.assertFalse((operator / "automation.lock").exists())
            for run_key in state["runs"]:
                run_artifacts = operator / "runs" / run_key
                self.assertTrue((run_artifacts / "events.jsonl").is_file())
                self.assertTrue((run_artifacts / "stderr.log").is_file())
                self.assertTrue((run_artifacts / "final-message.txt").is_file())
                self.assertTrue((run_artifacts / "runner-result.json").is_file())
                self.assertTrue((run_artifacts / "product-changes.json").is_file())
                with (run_artifacts / "product-changes.json").open("r", encoding="utf-8") as handle:
                    changes = json.load(handle)
                self.assertTrue(changes["entries"])

            resumed = subprocess.run(
                [*base_command, "--resume"],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            self.assertEqual(0, resumed.returncode, msg=resumed.stdout + resumed.stderr)
            with (operator / "automation-state.json").open("r", encoding="utf-8-sig") as handle:
                resumed_state = json.load(handle)
            self.assertTrue(all(run["attempts"] == 1 for run in resumed_state["runs"].values()))


if __name__ == "__main__":
    unittest.main()
