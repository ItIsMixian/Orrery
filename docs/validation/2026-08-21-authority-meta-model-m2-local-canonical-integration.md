# Authority Meta Model M2 本地 Canonical 集成

Date: 2026-08-21

Result: Passed — local Canonical integration only; unreleased

Scope: M2.1 complete internal CLI claims, M2.2 root-only opt-in Observatory projection and M2.3 local release-candidate gate. This record does not validate a default managed production switch, stable public API, selected SemVer, public manifest, tag, push or release.

Governing ADRs: [ADR-0004](../decisions/0004-platform-neutral-core-and-adapter-boundaries.md), [ADR-0009](../decisions/0009-authority-meta-model-and-semantic-conformance.md), [ADR-0010](../decisions/0010-core-owned-authority-evaluator.md), [ADR-0011](../decisions/0011-authority-model-version-and-compatibility.md)

Parent Plan: [Authority Meta Model conformance and gradual extraction](../implementation/plans/2026-08-21-authority-meta-model-conformance-and-extraction.md)

## Integration evidence

- A clean integration worktree and branch were created from local `main@65ef774`.
- M2.1 `db81691` and M2.2 `06ee3eb` formed a linear chain and were integrated by `--ff-only`.
- M2.3 `cfd76e4` shared the M2.1 baseline and was merged as the independent second branch through merge commit `bb03040`.
- The only textual conflicts were additive entries in `docs/implementation/README.md`, `docs/state/test-coverage.md` and `docs/validation/README.md`; both M2.2 and M2.3 facts were retained. No product-code conflict existed.
- The three source worktrees were clean and still pointed to their reported validated commits before integration.

## Combined verification

| Check | Result |
| --- | --- |
| Authority suite | PASS — 163 discovered; 160 passed and 3 skipped for existing Windows symlink privilege boundaries. |
| Full repository suite | PASS — 231 discovered; 226 passed and 5 skipped for existing Windows symlink privilege or optional dynamic dependencies. |
| M2.3 release-candidate gate | PASS — 12 discovered; 10 passed and 2 Windows symlink privilege skips. |
| Integrated structure | PASS — self-host project reports Authority Model 1 supported and strict evaluation eligible. |
| Default legacy docsite | PASS — 1179 KB checkpoint；11 ADR、6 State、7 subsystems、2 snapshots、88 classified docs、15 plans、6 library docs. |
| Explicit M2.2 projection | PASS — 1255 KB checkpoint；projection `ready`，`scope: candidate` 与 `reconciliation: match` markers present. |
| Markdown local links | PASS — 277 Markdown files、639 local links／images、0 missing targets. |
| `git diff --check` | PASS after final documentation synchronization. |

The combined suite contains both M2.2 and M2.3 additions; it therefore uses the merged totals above instead of copying either branch's 219-test result.

## Authority result

- M2.1, M2.2 and M2.3 implementation bytes and their branch Validation records may now be read from the local Canonical baseline rather than as isolated Worktree Candidates.
- M2.1 remains an internal contract and does not replace legacy CLI status or exit behavior.
- M2.2 remains root-only and explicit opt-in; disabling the switch or any reconciliation failure returns the legacy page. It is not managed production evidence.
- M2.3 can establish `candidate_ready=true`, but `release_ready` remains false until the maintainer selects the actual next SemVer／candidate manifest and a separate production-consumer review accepts M2.2 activation.
- Public v0.2.0 manifests, archives, checksums and release facts remain unchanged. No network, user-level Skill mutation, push, tag or Release occurred.
