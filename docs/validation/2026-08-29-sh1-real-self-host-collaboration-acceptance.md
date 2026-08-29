# SH1 Real Self-host Collaboration Acceptance Validation

Date: 2026-08-29

Status: real self-host read-only／bounded-scan evidence complete; Fast／Checkpoint PASS; one archive-consumer
product finding deferred because its regression inventory overlaps A3

Fact scope: `codex/sh1-real-self-host-collaboration-acceptance`; real evidence captured with Git HEAD and protected
`main` both at `d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2`. Worktree-local authored changes are bound separately by
the recorded dirty／Scope fingerprints. This branch does not update canonical State, root entrances or shared indexes.

## Write and safety boundary

The Codex-created linked worktree was initially detached and clean at exact `d07e1a`. SH1 created only the branch
`codex/sh1-real-self-host-collaboration-acceptance`; it did not create another task worktree. The primary-write guard
reported `allowed=true`, `is_primary=false`, integration／merge base `d07e1a`, worktree ID
`local-a3b095bcbb72c15b35b1bef9` and zero initial dirty entries.

Before the first authored-file write, Git-private `SH1-real-self-host-collaboration-acceptance` was registered at
`D:/coding warehouse/project-orrery/.git/worktrees/project-orrery1/orrery/worktree.json`. Initial session SHA-256 was
`D6718718E4475DE3E9F657F0278717D4F88FF21569721878F556F75243F45528`; the session deliberately had no
`base_workstream_id`／`task_base_oid`, so its relationship remained `legacy-unknown` instead of being guessed from
the SC1 branch, the shared HEAD or path similarity.

No relation apply／undo／recovery, maintenance authorize／execute, remove-worktree, branch deletion, Team action,
author-document auto-writeback, source deletion, network action, push, main update, tag or Release occurred. The only
Git-private writes were the required SH1 registration and one explicitly bounded read-only maintenance scan receipt;
the scan reports `workspace_writes_performed=false`, `destructive_action_performed=false` and
`network_performed=false`.

## Real self-host evidence

### Registered worktrees and live sessions

Command: `git worktree list --porcelain`, followed by byte-level SHA-256 of each session resolved through
`git -C <exact-worktree> rev-parse --git-path orrery/worktree.json`.

Capture `2026-08-29T15:50:09.4585336Z` had 11 registered worktrees and registry SHA-256
`5D981442F7EB28594F7011F415B07952F63FD0180503DEF4D51E17F84212E1FF`.

| Worktree fact | HEAD | Session SHA-256 | Declared lifecycle／runtime／evidence |
|---|---|---|---|
| primary `main` | `d07e1a` | absent | no Workstream session; primary is a separate protected axis |
| CI1 | `67a2fe9` | `FDAE21BEA9E890F85D25D246ED2F3B8E3F6C36FFD710989EBC214288B64A63BA` | validating／waiting-for-user／current |
| CI5 | `9ee831f` | `2A5F8ED8A38FECE2D33A6A67FBB818C22FDA08B8193D57F5CA42EE20C90BCC90` | validating／offline／current |
| `github-front-door-redesign` | `c53c39b` | absent | 11 dirty entries; unavailable/Unknown, not inferred from its branch or path |
| SC1 | registered HEAD `d07e1a` | `7A169EC97F015DB53CACC3B2532A7F891C078702140A3AD68122B542611AE914` | session HEAD `a9369dd`; validating／active／current declaration, but mechanically stale |
| W5C | `6dd508f` | `9F565626695DE9FF5818C51031F293F0457A481BD49016581A45039D7639F025` | validating／waiting-for-user／current |
| W5E | `692d19b` | `6A90B4A254607B6B6A325243795CEE429504551392A0DF580D8F833FCE0B4A9D` | validating／waiting-for-user／current |
| U1 | `d07e1a` | `7193C99CDDAC5B7916563D92C7530ED3A8EE15C8D6F644580CEBDF5CFE21FC95` | implementing／active／unknown |
| SH1 | `d07e1a` | `D6718718E4475DE3E9F657F0278717D4F88FF21569721878F556F75243F45528` | implementing／active／unknown |
| W6.1 | `d07e1a` | `8B9D22691916FAC144D7B542531C7551FFC3C40A72C6C75374F515001CC21653` | implementing／active／unknown |
| A3 | `d07e1a` | `96F7FBAF549FA011941B4F431A31B766AF957CA6CC2F88ED051EB4DDB8D4B665` | implementing／active／unknown |

The table keeps declared lifecycle, runtime and evidence independent. It does not translate `runtime=active` into
an active tip when the session or Scope is stale/Unknown.

### Closed archive and removed worktrees

The bounded archive root
`D:/coding warehouse/project-orrery/.git/orrery/retired-worktree-sessions/2026-08-29` contained exactly six files.
Its sorted `relative-path=SHA-256` manifest hash was
`C2764282C66842192C78D40CC71BD38B8C5E7C62BCCE70DB4BA28798459D1DC9`.

Every archived session independently decoded as `closed/offline/current/superseded`. The six file hashes were the
SC1-recorded values: W5D `E7C29B…`, CI4 `7BA4EF…`, R1 `187C00…`, R2 `48593F…`, R3 `E2F55D…`, and W6
`7FB854…`. For each exact archived branch, `git rev-parse <ref>` still equalled the archived full HEAD and
`git cat-file -e <head>^{commit}` succeeded. None of those six branch refs appeared in the current worktree registry.
This proves archive readability, branch/commit retention and worktree deregistration separately; it does not infer
the prior directory path from a branch name.

### Scope and findings

Commands:

```text
project-orrery worktree status --target . --json
project-orrery worktree scope inspect --target . --json
project-orrery worktree overlap --target . --json
```

- status exit 0, output SHA-256 `780FAFD3220607343411B65DE105C3414A8EDDEE5757899D1EF0F1059D4358C8`;
  authored Plan creation changed the dirty fingerprint to
  `076dba45ff55b8e201957d433bdaa44f68511667611b5a3b2f07ea3353e477ba`, so the initial session was correctly
  projected stale with reason `dirty-fingerprint-changed`.
- Scope exit 0, output SHA-256 `75E61A835DE680D859CDADB7CF49A0459A11F2DBCE81ED277FF2C279D4072651`,
  Scope fingerprint `deed7c1ba086161f122759c1dd93a0049f3bd1995e455063aa140ed42f7de7df`; only SH1's declared Plan,
  Validation and optional exclusive test/fixture paths appeared.
- overlap intentionally exited 5／warning. The exact summarized run output SHA-256 was
  `A8EA7448D5A41D958EBB533FFF3E9888895847B62439DD6558501D636AE0EABD`: 191 current local findings overall,
  including four involving SH1. `finding-2e0aca8b5c70bf639f43` was Semantic L2 with W6.1 only because both declared
  `scripts/ci/validate_ci.py`; W5C's broad stale `docs/implementation/**`／`docs/validation/**` expectations produced
  Direct L3 `finding-a810a02fec825aed036a` and `finding-7cc10dd9702c06e3f92e`; the sessionless front-door worktree
  produced Unknown L2 `finding-8db9ff81c3f1989f3f09`.

SH1 did not refresh or acknowledge Scope/finding. In particular it did not treat stale W5C scope as silently closed,
or treat the sessionless front-door worktree as safe.

### Relation graph, succession and transaction inspection

Commands were the source-checkout CLI equivalents of:

```text
project-orrery relations graph --target . --no-legacy --json
project-orrery relations graph --target . --json
project-orrery relations succession-plan --target . --json
project-orrery relations discover --target . --json
project-orrery relations inspect --target . --json
```

- Native-only graph: valid, zero nodes/edges/active tips, graph hash
  `bfbfdacc4e24c20cd28aab9b6e0d7425662f6c7910f1a7e4367df7562d2dcffe`. The native relation store remained absent.
- Legacy graph: valid, ten nodes, two explicit lineage edges, zero active tips, graph hash
  `670cb04a34826a4e6e178c2d04aec3f8add5b09adf98f8f3a5cf564f7aabef98`. Edge
  `legacy-6e984ad2df2530d7db6f0baa` is CI1 → W5D and edge `legacy-974f86d59bce771a447d6ddf` is W5E → CI1;
  both remained stale because endpoint/Scope evidence was not current. The graph did not suppress either pair.
- Succession plan reused exact graph hash `670cb04…`, returned no active tips and no suppression. It retained two
  compare pairs: CI1↔W5D for post-fork-or-Unknown/stale reasons and CI1↔W5E for stale/unconfirmed reasons.
- Discover performed no writes and intentionally exited 5 because Unknown evidence remained. Discovery hash was
  `8835f3a6fdadaadb7bdc66ae755faeabb0c21d0c22f8b04fa0b69a6b685f22e4`: the two explicit legacy lineages were
  only proposed, while A3, CI5, SC1, SH1, U1, W5C and W6.1 stayed Unknown for `legacy-no-lineage-evidence`.
  `similarity_inference_permitted=false` and no similarity hint was used.
- Transaction inspect was read-only with project hash
  `6020d516634ef87da9bd4523e894e3908cbeeb635f54a537c0ff0d2b409e434e`, graph hash `670cb04…`, no journal,
  receipt or pending recovery ID, and `network_performed=false`. Its `apply_eligible`／`undo_eligible` flags mean only
  that no recovery journal or graph parse error blocks a later separately confirmed plan; they are not an execution
  authorization and no plan/confirmation was created.

### Maintenance status and the single bounded scan

Before SH1's scan, read-only status exposed the historical timed-out run
`maintenance-scan-6dac66da1b4771fad3c804ec` at stale integration OID `c53c39b…`, with empty queue,
no authorization/receipt, automatic deletion false, remote branch `unobserved-zero-network`, and scheduler
`unsupported-phase-4`.

SH1 made exactly one full scan attempt:

```text
project-orrery maintenance scan --target . --reason manual --timeout 25 --json
```

It succeeded in 21.298 wall-clock seconds (product timestamps span 20.357s), scan ID
`maintenance-scan-f2666acc039a5c02389f4b34`, exact integration OID `d07e1a`, inventory content hash
`1f48d8d4ed9f4c4050f6c695452ce026494108cec689edc1a62097c3ac02dbf3`, 11 worktrees, 0 stale, 0 suggested,
1 Unknown, 9 active/pending protections, 1 primary protection and 1 explicit-adoption/classification protection.
Queue, authorization and receipt lists remained empty. The resulting `last-run.json` SHA-256 was
`0018F46C1F8F4ABF149E036FAC5BCB6EE850438659EDBEF5490F6761560439A0`; the 16-file maintenance private-state
manifest hash was `4D8D642DE859857B2472A7E725DBD58C1B1A377F219666C4A47153D27CC18947`.

The prior 12-worktree/25s failure was not repeated. This 11-worktree run completed inside the same budget, so SH1
does not assert a new performance or cache defect and changes no W6.1-owned code/UI/cache path.

## Product finding and overlap stop

`load_legacy_session_projection` enumerates only live `git worktree list` paths. Consequently the real archived W5D
session (`closed/offline/current/superseded`, exact SHA `E7C29B…`) is not consumed after its worktree removal; the
legacy graph instead synthesizes W5D as a `relation-only` node with unknown lifecycle/runtime/evidence and no HEAD.
Archive readability and graph interpretation therefore diverge even though the graph correctly refuses to guess.

The minimal regression belongs in `tests/test_workstream_relations.py`, with the product change in
`packages/project-orrery-core/src/project_orrery_core/workstream_relations.py`; registering the new unittest also
requires `scripts/ci/test-shards.json`. A3's exact current session declares `scripts/ci/test-shards.json` in its write
set. Per the SH1 overlap boundary, implementation stopped before adding the regression or product fix. Central
integration should schedule this as an explicit post-A3 relation/archive follow-up, decide the bounded archive
schema/precedence contract, then add the failing regression before implementation.

## Synthetic contract evidence

Synthetic evidence is not used to replace the real findings above.

- Fast profile: 57/57 PASS in 2.394993s under 15s; manifest SHA-256
  `6e55d66f7fa50cce9184207b816c9785ab7e2749766d7f2c92279a1e492895a3`, inventory SHA-256
  `7a3908505c0a6f7023762d5f5018628d09feef68a26e38e2c74f197559227580`.
- The first Checkpoint invocation was interrupted before final `Ran/OK` and exit code and is not counted.
- Checkpoint rerun: 81/81 PASS in 33.842646s under 90s, with the same manifest/inventory hashes. It includes all
  W7 relation graph tests, the dependency-light execution/no-delete contract and the fail-closed maintenance contract;
  it does not claim the long Promotion-only real Git journeys ran.
- `python -X utf8 scripts/ci/validate_ci.py --all`: PASS.
- integrated structure: PASS, `authority_status=integrated candidate`, Authority Model 1 supported.
- the first repository-gate run correctly failed only because this Validation target had not yet been written. It is
  not counted as a pass; the completed authored tree is revalidated below.

## Completed authored-tree checks

- completed repository gates: PASS over 672 tracked/untracked repository paths, 365 Markdown files and 914 local
  links, with no forbidden runtime/generated artifacts;
- isolated default docsite: PASS at 1,980,592 bytes, SHA-256
  `6FA3A85FB1470B65F5C79BC2616FB8581A04DA92F914E4C52BC82481D1423259`, 15 ADRs, 6 States, 7 subsystems,
  2 snapshots, 162 docs, 33 plans and 8 Library entries; output stayed under a system temporary directory;
- `git diff --check`: PASS.

The exact committed Candidate then reruns Fast／Checkpoint and an integration dry-run. Final branch SHA and those
post-commit checks are reported in the task handoff to avoid pretending that a document can embed the SHA of the
commit that contains itself.
