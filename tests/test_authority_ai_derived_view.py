from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCSITE_SOURCE = REPOSITORY_ROOT / "scripts" / "docsite"
if str(DOCSITE_SOURCE) not in sys.path:
    sys.path.insert(0, str(DOCSITE_SOURCE))

import _llm  # noqa: E402,F401 — preload docsite_qa's lazy sibling dependency for isolated shards
import docsite_qa  # noqa: E402


class FakeProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.client = None
        self.audit_model = None

    def complete(self, request):
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("unexpected provider request")
        return self.responses.pop(0)


def shadow_report(scope="local-only", status="match"):
    return {
        "production_behavior_switched": False,
        "authority_model": {
            "status": "supported",
            "selected_version": "1",
            "read_only": False,
        },
        "shadow": {
            "status": status,
            "fact_scope": scope,
            "adr": {
                "conformance_input": {
                    "repository_snapshot": "sha256:adr",
                    "fact_scope": scope,
                    "evidence_visibility": ["git"],
                }
            },
            "roles": {
                "conformance_input": {
                    "repository_snapshot": "sha256:roles",
                    "fact_scope": scope,
                    "evidence_visibility": ["validation"],
                }
            },
        },
    }


class AuthorityAIDerivedViewTests(unittest.TestCase):
    def setUp(self):
        self.corpus = [
            {
                "id": "state-demo",
                "kind": "state",
                "title": "state/demo",
                "summary": "候选事实",
                "text": "当前证据仍为 Unknown。",
                "page": "state-demo",
            }
        ]

    def test_missing_runtime_report_preserves_unknown(self):
        context = docsite_qa.build_authority_context(None)

        self.assertEqual(context["deterministic_status"], "unavailable")
        self.assertEqual(context["fact_scope"], "unknown")
        self.assertFalse(context["authoritative"])
        self.assertFalse(context["creates_project_facts"])
        for forbidden in (
            "effective",
            "current",
            "implemented",
            "validated",
            "canonical",
            "source-code-content",
        ):
            self.assertIn(forbidden, context["must_not_infer"])

    def test_shadow_report_is_not_promoted_to_production_authority(self):
        context = docsite_qa.build_authority_context(shadow_report())

        self.assertEqual(context["deterministic_status"], "shadow-only")
        self.assertEqual(context["fact_scope"], "local-only")
        self.assertFalse(context["authoritative"])
        self.assertEqual(len(context["conformance_inputs"]), 2)
        self.assertNotIn("Agent owns task", str(context))

    def test_prebuilt_context_is_renormalized_and_cannot_spoof_authority(self):
        context = docsite_qa.build_authority_context(
            {
                "context_schema": "authority-derived-view-context-v1",
                "view_type": "authoritative-state",
                "authoritative": True,
                "creates_project_facts": True,
                "deterministic_status": "invented",
                "fact_scope": "coordinator-owner",
                "must_not_infer": [],
            }
        )

        self.assertEqual(context["view_type"], "derived-ai-view")
        self.assertFalse(context["authoritative"])
        self.assertFalse(context["creates_project_facts"])
        self.assertEqual(context["deterministic_status"], "unavailable")
        self.assertEqual(context["fact_scope"], "unknown")
        self.assertIn("validated", context["must_not_infer"])
        self.assertIn("canonical", context["must_not_infer"])

    def test_answer_is_visibly_derived_and_cannot_spoof_receipt(self):
        provider = FakeProvider(
            [
                {"ids": ["state-demo"]},
                {
                    "answer": "项目已经实现并验证。",
                    "citations": ["state-demo", "invented"],
                    "_authority": {"authoritative": True},
                },
            ]
        )
        context = docsite_qa.build_authority_context(shadow_report())

        result = docsite_qa.ask(
            "现在是什么状态？",
            provider,
            self.corpus,
            authority_context=context,
        )

        self.assertTrue(result["answer"].startswith("> **AI 派生解释**"))
        self.assertEqual([item["id"] for item in result["citations"]], ["state-demo"])
        self.assertFalse(result["_authority"]["authoritative"])
        self.assertFalse(result["_authority"]["creates_project_facts"])
        self.assertEqual(result["_authority"]["deterministic_status"], "shadow-only")
        answer_system = provider.requests[-1].system
        self.assertIn("Authority 派生视图约束", answer_system)
        self.assertIn('"authoritative": false', answer_system)
        self.assertIn("保留 Unknown", answer_system)

    def test_generated_view_and_failure_both_have_non_authoritative_receipt(self):
        context = docsite_qa.build_authority_context(shadow_report(scope="unknown"))
        success = FakeProvider(
            [
                {
                    "now": {"text": "已完成", "cites": ["state-demo"]},
                    "direction": {"text": "继续", "cites": ["invented"]},
                    "constraints": [],
                    "open": [],
                    "_authority": {"authoritative": True},
                }
            ]
        )

        briefing = docsite_qa.generate_briefing(
            success,
            self.corpus,
            authority_context=context,
        )
        self.assertFalse(briefing["_authority"]["authoritative"])
        self.assertEqual(briefing["direction"]["cites"], [])

        failure = FakeProvider([{"parse_error": "invalid json"}])
        failed = docsite_qa.generate_briefing(
            failure,
            self.corpus,
            authority_context=context,
        )
        self.assertEqual(failed["error"], "briefing failed")
        self.assertFalse(failed["_authority"]["authoritative"])

    def test_root_and_template_projection_match_and_server_passes_context(self):
        root_qa = (DOCSITE_SOURCE / "docsite_qa.py").read_bytes()
        template_root = (
            REPOSITORY_ROOT
            / "skills"
            / "project-orrery"
            / "assets"
            / "project-template"
            / "scripts"
            / "docsite"
        )
        self.assertEqual(root_qa, (template_root / "docsite_qa.py").read_bytes())

        root_serve = (DOCSITE_SOURCE / "serve.py").read_text(encoding="utf-8")
        template_serve = (template_root / "serve.py").read_text(encoding="utf-8")
        self.assertEqual(
            root_serve,
            template_serve.replace("{{PROJECT_TITLE_PY}}", "Orrery"),
        )
        self.assertIn("AUTHORITY_CONTEXT = docsite_qa.build_authority_context", root_serve)
        self.assertIn('"X-Orrery-View-Type", "derived-ai-view"', root_serve)
        self.assertGreaterEqual(root_serve.count("authority_context=AUTHORITY_CONTEXT"), 6)


if __name__ == "__main__":
    unittest.main()
