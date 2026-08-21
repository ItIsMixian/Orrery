# 2026-08-21 M2.3 Authority release／installer candidate gate

Result: Passed — Worktree Candidate only

Date: 2026-08-21

Branch: `codex/m2-3-authority-release-gate`

Baseline: M2.1 Worktree Candidate `db81691`

Environment: Windows, Python 3.13.5, no network, no user-level Skill mutation

Plan: [M2.3 Authority Model 1 release／installer candidate gate](../implementation/plans/2026-08-21-m2-3-authority-release-candidate-gate.md)

## Scope

This validation covers a local, provider-neutral gate for a maintainer-supplied candidate release manifest. It does not
choose Project Orrery's next SemVer, edit the public release manifest, publish an archive, switch an Authority consumer,
or establish a stable Core API.

The legacy baseline is deliberately described as **current source executed with the public v0.2 manifest**. The test does
not claim to replay the downloaded public v0.2 ZIP. Public v0.2 release facts remain governed by the historical release
Validation and Snapshot.

## Evidence

### Historical inputs and staging

- `packaging/authority-release-candidate-policy.json` freezes normalized-LF SHA-256 values for the public v0.2 manifest,
  Core bundled `release-v0.2.0.json`, and Phase 0 baseline fixture.
- The candidate manifest is supplied separately and replaces `release-manifest.json` only while building the isolated
  staging ZIP. None of the three historical source files is written.
- Two packages built from identical source, policy and candidate input are byte-for-byte identical. Archive paths,
  timestamps and permission modes are deterministic.
- Final output is assembled in a sibling staging directory and moved into the previously absent output path only after
  all lifecycle checks pass. Preflight failures do not create a success receipt or final output directory.

### Installer and Authority lifecycle

- A candidate release must declare `authority_model_version: 1` and the exact discrete support set `[1]`; missing pairs,
  invalid values, duplicates, unsupported values, old versions, mismatched tags and secret-bearing manifests fail closed.
- A new offline standalone scaffold selects model 1 while retaining `authority_status=migration_pending`; selector
  presence is not treated as implementation or validation evidence.
- Current source with the public v0.2 manifest creates a legacy-unversioned baseline. An ordinary candidate
  `--upgrade-tools` run preserves the missing selector.
- Neutral and standalone installers reject invalid, unsupported, symlink/reparse and non-regular target manifests before
  managed tools or manifests are written. Target tree digests remain unchanged.
- Explicit migration is exercised through the source neutral CLI, not attributed to the standalone Skill archive. It
  still requires the Core/CLI review receipt; restore requires its own receipt and recovers the exact pre-migration
  manifest bytes. The gate receipt records this as a separate `explicit_authority_lifecycle` section.
- The self-host project explicitly selects model 1 and passes integrated structure validation, without upgrading that
  selector into an implemented/validated claim.

### Security and offline boundaries

- Gate subprocesses receive an explicit environment allowlist and do not inherit Provider, Agent, GitHub/GH, AWS or
  proxy credentials; every subprocess has a 120-second timeout that fails the gate.
- Source inventory and archive inspection independently reject symlinks, traversal (including Windows backslashes),
  case-insensitive duplicate entries, forbidden generated/cache/credential paths and plaintext credential patterns.
- Windows tests that require creating a real symlink are skipped when the process lacks that OS privilege. A separate
  platform-independent CLI regression verifies that `main()` preserves the candidate manifest's lexical path instead of
  resolving away its identity before `run_gate()`.

## Commands and results

```text
python -X utf8 -m unittest tests.test_authority_release_candidate_gate -v
12 tests discovered: 10 passed, 2 symlink-privilege tests skipped.

python -X utf8 -m unittest discover -s tests -p "test_authority_*.py" -q
151 tests discovered: 148 passed, 3 skipped.

python -X utf8 -m unittest discover -s tests -q
219 tests discovered: 214 passed, 5 skipped.

python -X utf8 skills/project-orrery/scripts/validate_installation.py --target . --require-integrated
Passed.

python -X utf8 scripts/docsite/build_docsite.py --out <temporary-output>
Passed; generated output remained outside the repository.

Markdown local-link scan
Passed; no missing local targets.

git diff --check
Passed; no whitespace errors were reported.
```

## Conclusion and remaining blockers

M2.3 is a validated Worktree Candidate for a local next-release gate. A passing receipt may state
`candidate_ready=true`, but it must keep `release_ready=false`. Public release remains blocked by:

1. maintainer selection and review of the actual next SemVer／candidate manifest; and
2. M2.2 consumer production evidence.

No tag, GitHub Release, public source manifest change, user-level installation, Observatory production projection or
network action occurred.
