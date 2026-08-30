from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
    ROOT / "scripts" / "docsite",
):
    sys.path.insert(0, str(source))

import docsite_qa  # noqa: E402
from project_orrery_cli.operating_rules import (  # noqa: E402
    build_repository_route_inputs,
    preflight_repository_query,
)
from project_orrery_core.authority_route import (  # noqa: E402
    AuthorityRouteError,
    evaluate_authority_route,
)
from project_orrery_core.operating_rules import (  # noqa: E402
    OPERATING_RULES_V1_SHA256,
    inspect_operating_rules,
    load_operating_rules,
    operating_rules_path,
)


CORPUS_FIXTURE = (
    ROOT / "tests" / "fixtures" / "authority-meta-model" / "v1"
    / "portable-operating-rules-route-conformance.json"
)


def _claim(status: str, axis: str) -> dict:
    value = {
        "status": status,
        "fact_scope": "candidate" if status != "absent" else "historical",
        "reason_codes": [f"fixture-{axis}-{status}"],
        "negative_evidence": status == "absent",
    }
    if axis == "implementation":
        value["validation_status"] = "present" if status == "present" else status
    if axis == "public_default_release":
        for key in ("public_status", "default_status", "release_status"):
            value[key] = status
    return value


def _case_inputs(case: dict) -> tuple[dict, dict]:
    concept_id = case["concept_id"]
    facts = case["facts"]
    specifications = (
        ("state", 10, "semantic_decision"),
        ("adr", 20, "semantic_decision"),
        ("implementation", 40, "implementation"),
        ("distribution", 60, "distribution_consumer"),
        ("release", 80, "public_default_release"),
        ("template", 200, "semantic_decision"),
    )
    sources = []
    observations = {}
    for role, rank, axis in specifications:
        source_id = f"{concept_id}:{role}:fixture"
        sources.append({
            "source_id": source_id,
            "path": f"fixture/{concept_id}/{role}.json",
            "role": role,
            "authority_rank": rank,
            "lower_authority": role == "template",
            "required_for_axes": [] if role == "template" else [axis],
        })
        status = facts[axis]
        if role == "template":
            status = "absent" if facts["semantic_decision"] == "present" else "present"
        observations[source_id] = {
            "exists": True,
            "link_valid": True,
            "current": True,
            "claims": {axis: _claim(status, axis)},
            "assertion_kind": "derived" if role == "template" else "mechanical",
        }
    concepts = [{
        "concept_id": concept_id,
        "subsystem_id": case["subsystem_id"],
        "aliases": [concept_id, *case["aliases"]],
        "sources": sources,
    }]
    distractor = case.get("distractor")
    if distractor:
        distractor_id = distractor["concept_id"]
        distractor_source = {
            "source_id": f"{distractor_id}:state:fixture",
            "path": f"fixture/{distractor_id}/state.json",
            "role": "state",
            "authority_rank": 10,
            "required_for_axes": ["semantic_decision"],
        }
        concepts.append({
            "concept_id": distractor_id,
            "subsystem_id": "documentation-system",
            "aliases": [distractor_id, *distractor["aliases"]],
            "sources": [distractor_source],
        })
        observations[distractor_source["source_id"]] = {
            "exists": True, "link_valid": True, "current": True,
            "claims": {"semantic_decision": _claim("present", "semantic_decision")},
            "assertion_kind": "mechanical",
        }
    registry = {
        "schema_version": 1,
        "registry_id": "fixture-concept-registry-v1",
        "registry_version": 1,
        "index_source": "fixture/AGENTS.md",
        "concepts": concepts,
    }
    return registry, observations


class PortableOperatingRulesTests(unittest.TestCase):
    def test_core_inventory_and_skill_projection_have_one_exact_owner(self) -> None:
        raw = operating_rules_path().read_bytes()
        self.assertEqual(hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(), OPERATING_RULES_V1_SHA256)
        self.assertEqual(
            raw,
            (ROOT / "skills" / "project-orrery" / "references" / "orrery-operating-rules-v1.json").read_bytes(),
        )
        inventory = load_operating_rules()
        self.assertEqual(inventory["inventory_id"], "orrery-operating-rules-v1")
        self.assertGreaterEqual(len(inventory["rules"]), 8)
        self.assertEqual(len({item["rule_id"] for item in inventory["rules"]}), len(inventory["rules"]))
        for rule in inventory["rules"]:
            self.assertEqual(rule["project_fact_boundary"], "not-target-project-fact-or-seed")
            self.assertNotIn("orrery-current-state", json.dumps(rule, ensure_ascii=False))
        skill = (ROOT / "skills" / "project-orrery" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("orrery-operating-rules-v1", skill)
        self.assertIn("advisory", skill.lower())

    def test_missing_unknown_and_tampered_inventory_fail_closed_without_latest_fallback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="orrery-operating-rules-") as temporary:
            root = Path(temporary)
            missing = inspect_operating_rules(path=root / "missing.json")
            self.assertTrue(missing["unknown"])
            self.assertTrue(missing["read_only"])
            unknown = inspect_operating_rules(version=99)
            self.assertTrue(unknown["unknown"])
            self.assertFalse(unknown["guarantees"]["selects_latest_on_unknown"])
            tampered_path = root / "tampered.json"
            tampered_path.write_bytes(operating_rules_path().read_bytes() + b" ")
            tampered = inspect_operating_rules(path=tampered_path)
            self.assertTrue(tampered["unknown"])
            self.assertIn("digest", tampered["reason"])


class AuthorityRouteConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = json.loads(CORPUS_FIXTURE.read_text(encoding="utf-8"))

    def test_generalized_corpus_selects_governing_sources_and_four_independent_axes(self) -> None:
        self.assertGreaterEqual(len(self.corpus["cases"]), 9)
        self.assertGreaterEqual(len({case["subsystem_id"] for case in self.corpus["cases"]}), 9)
        for case in self.corpus["cases"]:
            with self.subTest(case=case["case_id"]):
                registry, observations = _case_inputs(case)
                receipt = evaluate_authority_route(
                    query=case["query"], query_class=case["query_class"],
                    registry=registry, observations=observations,
                )
                self.assertEqual(receipt["selection"]["concept_ids"][0], case["concept_id"])
                self.assertEqual(set(receipt["claim_dimensions"]), set(case["facts"]))
                self.assertEqual(
                    {axis: value["status"] for axis, value in receipt["claim_dimensions"].items()},
                    case["facts"],
                )
                self.assertEqual(receipt["novelty_absence_gate"]["status"], case["expected_gate"])
                if case["facts"]["semantic_decision"] == "present":
                    roles = [source["role"] for source in receipt["selected_governing_sources"]]
                    self.assertEqual(roles[:2], ["state", "adr"])
                if case.get("expect_lower_authority_exclusion"):
                    self.assertTrue(receipt["excluded_lower_authority_sources"])

    def test_route_mutations_fail_closed_instead_of_inventing_a_new_layer(self) -> None:
        base = self.corpus["cases"][0]
        registry, observations = _case_inputs(base)
        registry["concepts"][0]["aliases"].append("跨仓库共享的判断约束")
        paraphrase = evaluate_authority_route(
            query="跨仓库共享的判断约束为何仍藏在工具内部而没有抵达使用者？",
            registry=registry, observations=observations, query_class="visibility",
        )
        self.assertEqual(paraphrase["selection"]["concept_ids"], ["authority-meta-model"])
        self.assertEqual(paraphrase["novelty_absence_gate"]["status"], "rejected")

        conflict = evaluate_authority_route(
            query=base["query"], registry=registry, observations=observations,
            query_class="visibility",
        )
        self.assertEqual(conflict["claim_dimensions"]["semantic_decision"]["status"], "present")
        self.assertIn("template", {item["role"] for item in conflict["excluded_lower_authority_sources"]})

        for source_role, field in (("state", "current"), ("adr", "link_valid")):
            mutated = copy.deepcopy(observations)
            mutated[f"authority-meta-model:{source_role}:fixture"][field] = False
            receipt = evaluate_authority_route(
                query=base["query"], registry=registry, observations=mutated,
                query_class="visibility",
            )
            self.assertEqual(receipt["claim_dimensions"]["semantic_decision"]["status"], "unknown")
            self.assertEqual(receipt["novelty_absence_gate"]["status"], "unknown")

        unindexed = evaluate_authority_route(
            query="完全未登记的量子发布规则是否存在？",
            registry=registry, observations=observations, query_class="novelty-absence",
        )
        self.assertEqual(unindexed["selection"]["concept_ids"], [])
        self.assertTrue(all(value["status"] == "unknown" for value in unindexed["claim_dimensions"].values()))
        self.assertFalse(unindexed["novelty_absence_gate"]["absence_claim_allowed"])

        invalid_registry = copy.deepcopy(registry)
        invalid_registry["schema_version"] = 99
        with self.assertRaises(AuthorityRouteError):
            evaluate_authority_route(
                query=base["query"], registry=invalid_registry, observations=observations,
            )

        assertion_registry = {
            "schema_version": 1, "registry_id": "forged-v1", "registry_version": 1,
            "index_source": "AGENTS.md",
            "concepts": [{
                "concept_id": "forged-agent-capability", "subsystem_id": "adapter-runtime",
                "aliases": ["伪造 Agent 能力", "forged agent capability"],
                "sources": [{
                    "source_id": "forged-agent-capability:agent-assertion:only",
                    "path": "agent-receipt.json", "role": "agent-assertion",
                    "authority_rank": 1, "lower_authority": True,
                    "required_for_axes": ["semantic_decision"],
                }],
            }],
        }
        assertion_observations = {
            "forged-agent-capability:agent-assertion:only": {
                "exists": True, "link_valid": True, "current": True,
                "claims": {"semantic_decision": _claim("present", "semantic_decision")},
                "assertion_kind": "agent",
            }
        }
        forged = evaluate_authority_route(
            query="伪造 Agent 能力是否存在？", registry=assertion_registry,
            observations=assertion_observations, query_class="existence",
        )
        self.assertEqual(forged["claim_dimensions"]["semantic_decision"]["status"], "unknown")
        self.assertTrue(forged["excluded_lower_authority_sources"])

    def test_real_repository_aliases_hit_state_then_adr_and_report_distribution_gap_correctly(self) -> None:
        questions = (
            "跨项目通用原则在哪里？",
            "元规则层是不是一个全新的层？",
            "运行契约为什么普通用户看不到？",
            "Where are the portable rules delivered?",
            "Does the operating contract already exist?",
        )
        registry, observations = build_repository_route_inputs(ROOT, fact_scope="candidate")
        for index, question in enumerate(questions):
            with self.subTest(question=question):
                # Exercise the repository collector/wrapper once, then reuse its
                # normalized provider-neutral input for the alias matrix.  The
                # semantic assertions stay identical without repeatedly parsing
                # the same AGENTS/State graph in the Fast tier.
                receipt = (
                    preflight_repository_query(ROOT, question, fact_scope="candidate")
                    if index == 0
                    else evaluate_authority_route(
                        query=question, registry=registry, observations=observations,
                    )
                )
                self.assertEqual(receipt["selection"]["concept_ids"][0], "authority-meta-model")
                paths = [source["path"] for source in receipt["selected_governing_sources"]]
                self.assertEqual(paths[:2], [
                    "docs/state/authority-meta-model.md",
                    "docs/decisions/0009-authority-meta-model-and-semantic-conformance.md",
                ])
                self.assertEqual(receipt["claim_dimensions"]["semantic_decision"]["status"], "present")
                self.assertEqual(receipt["claim_dimensions"]["implementation"]["status"], "present")
                self.assertEqual(
                    receipt["claim_dimensions"]["implementation"]["validation_status"],
                    "present",
                )
                self.assertEqual(receipt["claim_dimensions"]["distribution_consumer"]["status"], "present")
                self.assertEqual(receipt["claim_dimensions"]["public_default_release"]["status"], "absent")
                self.assertEqual(receipt["novelty_absence_gate"]["status"], "rejected")

    def test_ask_docs_calls_preflight_and_pins_governing_evidence_before_model_selection(self) -> None:
        class FakeProvider:
            def __init__(self):
                self.calls = []

            def complete(self, request):
                self.calls.append(request)
                if len(self.calls) == 1:
                    return {"ids": ["seed-0"]}
                return {"answer": "既有语义层存在，当前差异在消费与发布轴。", "citations": []}

        corpus = [
            {
                "id": "state-authority-meta-model", "kind": "state",
                "path": "docs/state/authority-meta-model.md",
                "page": "state-authority-meta-model.html",
                "title": "Authority Meta Model State", "summary": "current facts",
                "text": "The existing Authority Meta Model is implemented internally.",
            },
            {
                "id": "adr-0009", "kind": "ADR",
                "path": "docs/decisions/0009-authority-meta-model-and-semantic-conformance.md",
                "page": "adr-0009.html",
                "title": "ADR-0009", "summary": "governing semantics",
                "text": "Accepted semantics do not imply distribution or public release.",
            },
            {
                "id": "seed-0", "kind": "seed", "path": "docs/core/principles.md",
                "page": "seed.html",
                "title": "Seed", "summary": "lower-priority local principle", "text": "Seed text.",
            },
        ]
        provider = FakeProvider()
        docsite_qa.configure_authority_route_preflight(
            lambda question: preflight_repository_query(ROOT, question, fact_scope="candidate")
        )
        try:
            result = docsite_qa.ask("为什么元规则没有出现在 Skill？", provider, corpus)
        finally:
            docsite_qa.configure_authority_route_preflight(None)
        self.assertEqual(result["retrieved"][:2], ["state-authority-meta-model", "adr-0009"])
        self.assertEqual(result["_route"]["selection"]["concept_ids"], ["authority-meta-model"])
        self.assertIn("distribution_consumer", provider.calls[1].system)
        self.assertIn("absence_claim_allowed", provider.calls[1].system)


if __name__ == "__main__":
    unittest.main()
