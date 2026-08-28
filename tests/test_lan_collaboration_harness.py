from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for source in (
    ROOT / "packages" / "project-orrery-core" / "src",
    ROOT / "packages" / "project-orrery-cli" / "src",
    ROOT / "scripts" / "acceptance",
):
    sys.path.insert(0, str(source))

from project_orrery_core.team import (  # noqa: E402
    build_discovery_packet,
    enable_team,
    publish_discovery_once,
    scan_discovery_candidates,
    start_coordinator_server,
    stop_owned_coordinator_server,
    validate_discovery_packet,
)
from run_lan_collaboration_acceptance import (  # noqa: E402
    ControlledDiscoveryTransport,
    run_acceptance,
    validate_acceptance_run,
)
from project_orrery_cli import team as team_cli  # noqa: E402
from tests.fixtures.collaboration.git_fixture import CollaborationGitFixture  # noqa: E402


DISCOVERY_KEYS = {
    "schema_version", "contract_type", "protocol_version", "project_fingerprint",
    "host_hint", "device_hint", "endpoint", "nonce", "generated_at", "expires_at",
}


class LanCollaborationHarnessTests(unittest.TestCase):
    def test_cli_exposes_explicit_discovery_and_manual_coordinator_switch_only(self):
        parser = team_cli.build_parser()
        scan = parser.parse_args(["discovery-scan", "--bind-ip", "127.0.0.1", "--json"])
        self.assertEqual(scan.action, "discovery-scan")
        serve = parser.parse_args([
            "serve", "--bind", "0.0.0.0", "--advertise-address", "192.168.50.10",
        ])
        self.assertEqual(serve.advertise_address, "192.168.50.10")
        switch = parser.parse_args([
            "coordinator-switch-create", "--target-member-id", "reviewer",
            "--target-host-id", "host-b", "--target-device-id", "device-b",
            "--endpoint", "http://127.0.0.1:42852",
        ])
        self.assertEqual(switch.action, "coordinator-switch-create")
        self.assertNotIn("leader", parser.format_help().lower())

    def test_discovery_contract_is_minimal_untrusted_expiring_and_cross_project_closed(self):
        with CollaborationGitFixture() as fixture:
            enable_team(fixture.repository, member_id="owner", device_id="device-a", host_id="host-a")
            enable_team(fixture.clone, member_id="reviewer", device_id="device-b", host_id="host-b")
            server, runtime = start_coordinator_server(fixture.repository, port=0)
            try:
                packet = build_discovery_packet(fixture.repository, endpoint=runtime["endpoint"])
                self.assertEqual(set(packet), DISCOVERY_KEYS)
                self.assertLessEqual(len(json.dumps(packet, separators=(",", ":")).encode("utf-8")), 1024)
                self.assertNotIn("member_id", packet)
                self.assertNotIn("workstream", packet)
                self.assertNotIn("credential", packet)
                with self.assertRaisesRegex(ValueError, "expired"):
                    validate_discovery_packet(packet, now=packet["expires_at"])

                bus = ControlledDiscoveryTransport()
                published = publish_discovery_once(
                    fixture.repository, endpoint=runtime["endpoint"], target="127.0.0.1", transport=bus,
                )
                bus.packets.append(bus.packets[0])
                scanned = scan_discovery_candidates(
                    fixture.clone, bind="127.0.0.1", transport=bus,
                )
                self.assertEqual(len(scanned["candidates"]), 1)
                self.assertEqual(scanned["rejected_count"], 1)
                self.assertFalse(scanned["membership_granted"])
                self.assertFalse(published["membership_granted"])

                spoofed = copy.deepcopy(packet)
                spoofed["project_fingerprint"] = "0" * 64
                spoofed["nonce"] = "1" * 32
                foreign = ControlledDiscoveryTransport()
                foreign.packets.append(json.dumps(spoofed, sort_keys=True, separators=(",", ":")).encode("utf-8"))
                rejected = scan_discovery_candidates(
                    fixture.clone, bind="127.0.0.1", transport=foreign,
                )
                self.assertEqual(rejected["candidates"], [])
                self.assertEqual(rejected["rejected_count"], 1)
            finally:
                server.server_close()

    def test_one_click_two_clone_runner_emits_sealed_sanitized_verdict(self):
        with tempfile.TemporaryDirectory(prefix="orrery-w5d-test-") as temporary:
            run_root, verdict = run_acceptance(Path(temporary))
            self.assertEqual(verdict["verdict"], "passed")
            self.assertEqual(validate_acceptance_run(run_root)["validated_artifacts"], 3)
            manifest = json.loads((run_root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["parameters"]["members"], 2)
            self.assertFalse(manifest["parameters"]["external_network"])
            self.assertFalse(manifest["real_lan_validated"])
            serialized = json.dumps(manifest, sort_keys=True).lower()
            self.assertNotIn(str(run_root).lower(), serialized)
            self.assertNotIn("credential_token", serialized)
            stages = run_root / "stage-results.json"
            stages.write_text(stages.read_text(encoding="utf-8") + " ", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                validate_acceptance_run(run_root)


if __name__ == "__main__":
    unittest.main()
