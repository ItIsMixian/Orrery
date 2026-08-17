# Pilot 003 — GPT-5.6 Terra / medium

> Status: completed execution, protocol-invalid receipt format  
> Authority: research evidence only; this report does not change the released Skill

## Execution

- Model: `gpt-5.6-terra`
- Reasoning effort: `medium`
- Runs: 9/9 completed, one attempt each
- Sandbox: workspace write with automatic approval review
- Network for task tools: disabled
- Independent rerun after collection: all nine repositories passed `git diff --check`, the specified Python compile checks, and the repository's three unit tests

The full validator returned `1` because every Agent wrote `validation` as
`[{"command": ..., "result": ...}]`, while prompt revision v1 required an array of strings.
The raw run was sealed without rewriting the receipts. Prompt revision v2 now states the string-only contract explicitly.

## Routing cost signal

| Variant | Mean self-reported content reads | Input tokens | Cached input tokens | Output tokens |
|---|---:|---:|---:|---:|
| A — fixed chain | 9.33 | 1,909,926 | 1,741,824 | 23,646 |
| B — manifest plus expansion | 5.33 | 1,089,516 | 970,240 | 27,093 |
| C — selective retrieval | 1.67 | 761,922 | 668,928 | 20,258 |

Relative to A, C used about 60% fewer input tokens and reported about 82% fewer content reads. B reduced input by about 43%, but its unconstrained expansions remained expensive on cross-module work.

These numbers are directional rather than a winner declaration. Content reads remain Agent self-report, and token totals include Harness/session context that Project Orrery does not independently control.

## Qualitative review

### PO-CR-006 — bilingual README

All three variants produced separate, mutually linked English and Simplified Chinese entrances while retaining the distinction between accepted decisions and implemented facts. C's translation was concise and natural. The new untracked `README.zh-CN.md` also exposed a reporting gap: ordinary `git diff --name-only` omits untracked product files.

### PO-CR-010 — provider settings API

All three variants implemented the expected routes and passed compilation. C produced the smallest implementation, reused `_llm.py`, added body/type/URL/model validation, disabled caching, and redacted provider failures. A persisted non-secret configuration before storing a submitted key, which creates an undesirable partial-save ordering if credential storage fails. B was functional but moved more validation policy into the HTTP layer and expanded to more context.

### PO-CR-011 — secret-free persistence

All variants placed keys behind the credential-store boundary and used atomic replacement for non-secret JSON. B preserved environment-derived `hasKey` status through the resolved configuration. A and C returned post-save `hasKey` from the submitted/legacy key or keyring only, so an environment-only credential could be reported as absent from that return path. Existing tests did not detect this detail.

## Post-run apparatus check

After sealing the raw run, an operator-side security oracle was added to the
apparatus and executed read-only against the six security/cross-module result
repositories. It reproduced the qualitative review without altering those
repositories:

| Run | Retrospective security result |
|---|---|
| PO-CR-010-A | failed: non-secret configuration persisted before credential storage |
| PO-CR-010-B / C | passed |
| PO-CR-011-A / C | failed: post-save return lost environment-derived `hasKey` |
| PO-CR-011-B | passed |

The runner now also freezes a Harness-authored `product-changes.json` by
combining tracked changes with `git ls-files --others --exclude-standard`.
This closes the missing-untracked-file gap for future runs; it does not rewrite
the already sealed pilot-003 raw evidence.

## Result

The evidence supports a hybrid candidate:

- use C's small initial context and selected-evidence discipline;
- retain B's reason-coded expansion for dependencies, security boundaries, and validation failures;
- treat the initial file budget as an aperture, not a permanent ceiling;
- require stronger acceptance tests before lower context use can count as a quality win.

See [Orrery Context Aperture v0.1](../designs/context-aperture-v0.1.zh-CN.md).
