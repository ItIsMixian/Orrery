# Validation: SC1 Closed Worktree Removal

Date: 2026-08-29

Status: PASS; six closed worktree directories removed, all branches／commits preserved

Scope: local self-host workspace maintenance explicitly authorized by the maintainer after SC1 Canonical document
closeout. This is local external-state evidence, not automatic-cleanup product evidence.

## Preflight

Each target was revalidated immediately before removal:

- path remained under the named `C:\Users\1\.codex\worktrees\` root, which is the accepted junction into the D-drive Codex home;
- target existed and remained an exact registered worktree;
- tracked／staged／unstaged／untracked status was clean;
- ignored content matched only allowed `__pycache__`／`docs/_site`／`.pytest_cache` generated paths;
- Git-private session was `closed` with `closure_reason=superseded`;
- local branch and HEAD commit existed.

## Archived and removed targets

| Workstream | Branch | HEAD | Archived `worktree.json` SHA-256 |
|---|---|---|---|
| W5D-lan-collaboration-harness | `codex/w5d-lan-collaboration-harness` | `ae6913e` | `E7C29B205285EE6468BBF89F876ADABB4B4BA857851C506FD102486B1E794609` |
| CI4-opaque-cli-token-argument-reliability | `codex/ci4-opaque-cli-token-argument-reliability` | `a4b0ed3` | `7BA4EF740400E8450C64AA3F9AD26F5D6CC86B3EDAB828CB94942914EABD2057` |
| R1-orrery-rename-migration-audit | `codex/r1-orrery-rename-migration-audit` | `f991bef` | `187C00EEB9D2BC5F95603C21D1DAB020F3E36F9D6984F60E51FC2157E429A93B` |
| R3-orrery-brand-only-closeout | `codex/r3-orrery-brand-only-closeout` | `439c40f` | `E2F55D536B8012B62C966E909D5B387A2C77270763E7CA09130FC724A54CC62A` |
| R2-orrery-rename-decision-contract | `codex/r2-orrery-rename-decision-contract` | `1e67d4a` | `48593F8B271294ABFFF6AA401F5B90B6C7DE2D75A57E587551B0DE729CF07934` |
| W6-workspace-maintenance | `codex/w6-workspace-maintenance` | `db78a7f` | `7FB8547C7F107CDE89C722A68F147B177D2045388EA231DF226824B56DE8BFF9` |

The complete Git-private `orrery/` directory for each target was copied to
`.git/orrery/retired-worktree-sessions/2026-08-29/<branch>-<head>/`. Source and archive file lists／SHA-256 values
were compared before removal.

## Execution and postconditions

- `git worktree remove --force <exact-path>` was invoked separately for each revalidated target. Force only removed
  the allowed ignored generated content alongside the worktree directory.
- all six paths became absent and disappeared from `git worktree list`;
- all six local branches remained present and all six HEAD commits remained readable;
- no local branch delete, remote branch delete, ordinary recursive delete, source/history rewrite or release action ran;
- primary main remained clean and aligned with `origin/main`;
- registered worktree count became seven rather than six because an independent clean
  `codex/github-front-door-redesign` worktree was created concurrently and was outside this authorization.

## Residual boundary

Remaining CI1／CI5／W5C／W5E／SC1 and `github-front-door-redesign` worktrees were not removed. The bounded maintenance
scan had previously timed out at the explicit 25-second limit and produced no queue or authorization; this manual
operation therefore does not claim the automatic maintenance pipeline approved or executed deletion.
