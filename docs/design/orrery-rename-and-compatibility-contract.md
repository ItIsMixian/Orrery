# Orrery Rename and Compatibility Contract

Status: Approved

Updated: 2026-08-28

Governing decision: [ADR-0015](../decisions/0015-orrery-brand-and-compatibility-contract.md)

Approval boundary: ADR-0015 is Accepted and this Design is Approved. That releases the decision/design gate for a
separate R3 Workstream; it does not claim that R3, R4, R5 or local maintenance has been implemented.

## 1. Identity model

Every occurrence belongs to exactly one authority class before it may change:

| Class | Example | Rule |
|---|---|---|
| Current brand | `Orrery`, active UI/title/description | R3 may migrate allowlisted human-facing text |
| Stable technical ID | `project-orrery`, `project_orrery_cli`, `.project-orrery.json` | retain; aliases are additive and versioned |
| Protocol ID | `$id`, `contract_type`, hash domain, API/model version | retain for the lifetime of that protocol version |
| Historical fact | v0.2.0 asset, ADR/Validation/Pilot command | never rewrite; add present-day context elsewhere |

Self-host pages and State must be able to state all four simultaneously. “Brand rollout complete” means the R3
allowlist is current; it never means legacy identifiers or historical strings are absent.

## 2. Compatibility matrix

| Surface | Current/canonical value | R3 | R4 alias behavior | R5/default transition | Rollback |
|---|---|---|---|---|---|
| README EN/ZH, active prose | Orrery plus mixed legacy text | migrate allowlist | n/a | n/a | revert text only |
| Observatory/Broker titles | `Project Orrery · Documentation` etc. | change self-host display; preserve target title token | old flags/config unchanged | none required | old title constant |
| repository description | current Orrery description | read-only verify; remote change requires maintainer | old repo redirect remains | none | GitHub settings rollback |
| GitHub URL/badges/install | `ItIsMixian/Orrery` | current links only | old URL 301 is alias | first new Release keeps `project-orrery-*` asset filenames and shows Orrery as brand | restore prior link; no asset rewrite |
| Skill name/directory | `project-orrery` | unchanged | one canonical Skill plus host-proven thin alias only | optional preferred invocation | remove alias, keep old Skill |
| plugin/Adapter ID | `project-orrery-*` | display fields only | no alias by default; host-proven thin alias maps to same ID/CLI | optional preferred display | restore metadata |
| CLI | `project-orrery` + sub-entrypoints | unchanged | explicit opt-in, collision-checked thin `orrery` launcher to one implementation | may become preferred, not sole | uninstall alias; old commands remain |
| Python distributions | `project-orrery-*` | unchanged | no `orrery` distribution | remain stable unless later ADR | no migration needed |
| Python imports | `project_orrery_*` | unchanged | no `import orrery` | remain stable unless later ADR | no migration needed |
| project manifest | `.project-orrery.json`, `name=project-orrery`, `title=Orrery` | title already target | old path is canonical reader | no default path switch | existing file unchanged |
| env/headers | `ORRERY_*`, `X-Orrery-*` | unchanged | single namespace | unchanged | n/a |
| local config | `ai-config.json`, `.doccache.json`, `.port` | unchanged | no duplicate files | future change needs migration receipt | old reader remains |
| keyring | existing project-orrery/broker services | unchanged | dual-read only if later namespace exists; single-write after explicit save | never bulk-copy secret | delete new slot only after verified old fallback |
| cache/backup/trash | `.project-orrery-*` roots | unchanged | dual-read if a later root exists | old backups remain recoverable | stop new writer; read old root |
| schema/contract/hash | v1 IDs/domains | unchanged | readers may advertise aliases, IDs do not change | semantic v2 only, never brand-only v2 | v1 reader remains |
| Authority Model | version 1 | unchanged | capability metadata only | separate model ADR | current model selection remains |
| Workstream/receipt IDs | issued values | unchanged | no reissue | no cleanup | append-only history |
| v0.2.0/frozen evidence | exact tag/assets/checksum/manifest | denylist | old reader test | immutable | hash gate fails closed |
| local root/Saved Project | current machine paths | unchanged | independent of public alias rollout | separate maintenance after R3 exact-SHA enters main | restore old path/re-add Saved Project |

## 3. Alias resolver and mixed versions

The resolver has one implementation and ordered routes:

1. accept the stable technical ID unconditionally within the supported window;
2. accept a new alias only when the installed component declares the alias capability;
3. resolve both routes to the same callable/module and compare version/API constraints;
4. if two complete implementations, divergent manifests, or different write plans are present, fail closed with a
   human-readable remediation and stable machine error category;
5. never infer alias support from directory name, display text or repository rename redirect.

The R4 CLI alias is an explicit opt-in, collision-checked thin launcher. It must dispatch to the canonical CLI and
must not copy the command tree or business implementation. Host integrations default to display-name migration only;
they add a thin alias only after that host independently proves safe discovery, upgrade and uninstall behavior.

For CLI JSON mode, warnings go to structured `warnings` or stderr according to the existing envelope contract; stdout
remains parseable and exit codes are identical. Human deprecation notices may begin only in a later 0.3.x release and
must be once-per-invocation, actionable and suppressible for automation. No warning may claim scheduled removal.

## 4. Brownfield migration states

| Observed state | Required behavior |
|---|---|
| old only | continue without write; offer dry-run alias capability |
| new alias only | resolve canonical implementation and record its stable ID |
| old + thin alias, same implementation/hash | supported mixed state; report both routes |
| two full implementations | fail closed; do not choose by mtime/path order |
| old/new config both equal | keep canonical old path until explicit migration |
| old/new config divergent | fail before writes; require human selection and backup |
| old backup only | restore remains supported |
| unknown/future manifest | preserve files and refuse migration |

An installed-user migration must be `inspect → dry-run → explicit apply → verify → receipt → optional restore`.
Scaffolding and ordinary `--upgrade-tools` never migrate identifiers, secret slots, config, backups or authored docs.

## 5. Warning, secret, telemetry and privacy contract

- Alias/collision observations are local-only and contain versions, stable IDs and bounded paths, not source/diff body.
- No operation enumerates or exports real keyring values. A user save may write one selected slot; rollback removes only
  the new slot it created after proving the old fallback still works.
- Cache, prompt, answer, transcript, API key, client token, unpushed diff and full command history never enter alias
  telemetry, release artifacts, Team projection or Validation.
- Orrery adds no anonymous/network telemetry. “No warning observed” and “no issue reported” are not migration evidence.
- Team Mode remains opt-in metadata-only/request-only; central views cannot execute identifier migration.

## 6. Phase sequencing and gates

### R3 — Brand-only

Change only allowlisted active display text and its golden/UI tests. Denylist all v0.2/frozen/history/protocol paths.
No manifest ID, path, CLI, import, Skill discovery or remote setting changes are bundled.

### R4 — Compatible identifiers and aliases

Introduce versioned alias capability, resolver, collision diagnostics and the explicit opt-in CLI thin launcher.
Each platform must prove install/upgrade/uninstall, explicit/implicit invocation, missing/incompatible CLI and single
discovery before receiving a host alias. Until then it changes display name only and retains the canonical ID.

### R5 — Optional package/CLI transition

Re-evaluate whether the R4 `orrery` launcher becomes preferred/default. The first new public Release continues to use
stable `project-orrery-*` archive/asset filenames while displaying the Orrery brand; changing later asset display
filenames requires a separate compatibility review. Python distribution/import remain unchanged under ADR-0015.
R5 may conclude “no default transition”; that is a valid outcome. A release still requires a separately selected
SemVer and immutable candidate manifest.

### Optional cleanup

No cleanup begins before a complete 0.3.x window and 0.4.0 review eligibility. Schema/readers, old project manifests,
v0.2 assets, receipts, Workstream IDs, secret fallback and backup restore are never cleanup targets. Removal needs a
new ADR and explicit user evidence; silence is insufficient.

## 7. Local directory, Saved Project and D-drive order

R3 Brand-only must be complete, pass the exact-SHA gates and enter `main` before filesystem relocation. The local
maintenance does not wait for R4 or R5. In a separately authorized maintenance Workstream:

1. freeze a clean exact commit; preserve branches and Git-private Workstream evidence;
2. save and close or recreate linked worktrees through Git-safe operations rather than moving registered worktree directories;
3. rename the primary local root from `project-orrery` to `Orrery` only after path consumers are inventoried;
4. re-add/update the Codex Saved Project and recreate required worktrees from preserved branches;
5. run repository/CLI/Observatory checks and retain a rollback path to the old root;
6. only then create a separate Workstream for moving Codex application data to D:, without treating ADR acceptance,
   R3 promotion or product-rename receipts as authorization for application-data migration.

## 8. Promotion and rollback

Every R3/R4/R5 candidate must be pushed to a non-main ref at an exact SHA and obtain
`smoke-test (windows-latest)` plus `smoke-test (ubuntu-latest)` before main promotion. Feature branches do not update
root PROGRESS/HANDOFF; the unique integrator does. Rollback is phase-local: R3 reverts display text, R4 removes only
aliases/capabilities it added, R5 returns the preferred/default route while retaining old readers and assets.

R3 may now start only as its own registered Workstream. R4 and R5 remain later independent Workstreams and are not
implicitly authorized by R3 implementation or promotion.
