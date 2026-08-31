from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "project-orrery-core" / "src"))

from project_orrery_core.schema import WORKSTREAM_PROGRAM_HIERARCHY_SCHEMA  # noqa: E402
from project_orrery_core.workstream_program_hierarchy import (  # noqa: E402
    SELF_HOST_W_MEMBERS,
    append_group_event,
    append_membership_event,
    apply_self_host_w_repair,
    inspect_program_hierarchy,
)
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


STAMP = "2026-08-30T18:00:00Z"


class WorkstreamProgramHierarchyTests(unittest.TestCase):
    def test_schema_human_authority_cas_and_path_fail_closed(self) -> None:
        from jsonschema import Draft202012Validator

        Draft202012Validator.check_schema(WORKSTREAM_PROGRAM_HIERARCHY_SCHEMA)
        with CollaborationGitFixture() as fixture:
            with self.assertRaisesRegex(ValueError, "human integrator"):
                append_group_event(
                    fixture.worktree_a, group_id="program-a", group_kind="program",
                    parent_group_id=None, display_label="Program A", order=1,
                    event_kind="accepted", expected_revision=0, actor_kind="agent",
                    actor_id="agent-a", actor_role="proposer", recorded_at=STAMP,
                )
            append_group_event(
                fixture.worktree_a, group_id="program-a", group_kind="program",
                parent_group_id=None, display_label="Program A", order=1,
                event_kind="accepted", expected_revision=0, actor_kind="human",
                actor_id="owner", actor_role="integrator", recorded_at=STAMP,
            )
            append_group_event(
                fixture.worktree_a, group_id="phase-a1", group_kind="phase",
                parent_group_id="program-a", display_label="Phase A1", order=1,
                event_kind="accepted", expected_revision=0, actor_kind="human",
                actor_id="owner", actor_role="integrator", recorded_at=STAMP,
            )
            with self.assertRaisesRegex(ValueError, "CAS"):
                append_group_event(
                    fixture.worktree_a, group_id="program-a", group_kind="program",
                    parent_group_id=None, display_label="Program A changed", order=1,
                    event_kind="accepted", expected_revision=0, actor_kind="human",
                    actor_id="owner", actor_role="integrator", recorded_at=STAMP,
                )
            append_membership_event(
                fixture.worktree_a, membership_id="member-task-a", workstream_id="task-a",
                group_path=("program-a", "phase-a1"), event_kind="accepted",
                expected_revision=0, actor_kind="human", actor_id="owner",
                actor_role="integrator", recorded_at=STAMP,
            )
            inspection = inspect_program_hierarchy(fixture.worktree_a)
            self.assertEqual(inspection["memberships"][0]["workstream_id"], "task-a")
            self.assertFalse(any(inspection["relation_effects"].values()))
            self.assertFalse(inspection["name_inference_performed"])

    def test_exact_self_host_repair_is_idempotent_and_never_uses_prefix_inference(self) -> None:
        with CollaborationGitFixture() as fixture:
            first = apply_self_host_w_repair(fixture.worktree_a, integrator_id="local-owner", recorded_at=STAMP)
            second = apply_self_host_w_repair(fixture.worktree_a, integrator_id="local-owner", recorded_at=STAMP)
            self.assertTrue(first["writes_performed"])
            self.assertFalse(second["writes_performed"])
            inspection = second["hierarchy"]
            self.assertEqual(len(inspection["groups"]), 4)
            self.assertEqual(len(inspection["memberships"]), sum(map(len, SELF_HOST_W_MEMBERS.values())))
            self.assertNotIn("W-looking-but-not-approved", {
                item["workstream_id"] for item in inspection["memberships"]
            })
            serialized = json.dumps(inspection, ensure_ascii=False)
            self.assertNotIn("series_id", serialized)
            self.assertFalse(any(inspection["relation_effects"].values()))


if __name__ == "__main__":
    unittest.main()
