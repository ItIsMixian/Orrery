# Unified Observatory Architecture & Shell

Status: Approved

Date: 2026-08-29

Governing ADR: [ADR-0016](../decisions/0016-unified-observatory-shell-and-single-local-entry.md)

Maintainer approval: **approved on 2026-08-29**. Approval constrains future implementation but does not claim that the
production shell, launcher or default transition exists.

## 1. Product contract

最终用户只需要一个可见启动入口、一个本地浏览器 URL 和一个导航壳；默认不出现命令行窗口，显式 debug
模式最多出现一个控制台。该体验 contract 不要求单进程，也不限制 supervisor 管理的内部 listener 数量。
Shell 组合以下 consumer，但不拥有它们的项目语义：

| Navigation identity | Consumer | Source boundary | Dynamic authority |
|---|---|---|---|
| `overview` | shell summary | capability descriptors only | none |
| `docs` / `search` | canonical Markdown reader/index | `build_docsite` inputs | read-only |
| `ask` | AI Q&A / briefing / roadmap | docs corpus + Broker gates | provider opt-in only |
| `authority` | Authority managed consumer | A3 contract or Unavailable | deterministic read-only; selection remains maintainer-owned |
| `personal` | Personal Observatory | Core collaboration/maintenance projections | host-local projection |
| `team` | Team Observatory | versioned Team projection/request contract | explicit opt-in; central request-only |
| `workstreams` | Workstream Graph | W7 Core graph + succession plan | read-only |
| `maintenance` | Workspace Maintenance | W6/W6.1 Core contract | host-local, action-specific confirmation |

Navigation identity is stable and independent of localized labels, DOM IDs, route prefixes or consumer package names.
The shell may change labels without changing saved navigation or API contracts.

### Production docsite inheritance boundary

Unified Shell unifies startup entry, browser URL, navigation identity, capability orchestration and supervised
lifecycle. It does **not** replace the current docsite product design. Production implementation must treat these as
inheritance baselines:

- current `build_docsite.py` document reading and search behavior;
- current `serve.py` dynamic docsite and Broker-mediated AI Q&A consumer behavior;
- the author-document information architecture and its source/navigation relationships;
- the recognizable Orrery docsite visual experience and reading workflow.

Implementation should wrap, register or adapt the current build/serve consumers instead of rewriting the document site
from scratch. Internal refactoring is limited to the unified front door, consumer registration, supervision, public
route composition, common security middleware and lifecycle ownership needed for this architecture. Localized UI
adjustments required to compose a consumer are allowed, but they do not authorize a comprehensive visual redesign.

`experiments/unified-observatory-shell/` is a synthetic **architecture interaction study** for mode boundaries,
capability states, navigation identity and error isolation. It is not a final UI specification, component system or
docsite redesign reference. Any comprehensive visual redesign requires a separate task and explicit maintainer approval.

## 2. Current responsibility inventory

This table records the inspected `main@d07e1a15ea8ecd6c46c606b20483a0b058f4f1b2` baseline; it is not the proposed implementation.

| Current entry | Real responsibility | Listener / route ownership | Security / lifecycle ownership |
|---|---|---|---|
| `start-docsite.bat` | selects Python, sets loopback `NO_PROXY`, runs `serve.py`, keeps terminal open and reports non-zero exit | none itself | child process lifetime; no Team entry |
| `serve.py` | builds legacy reader once, injects Ask/AI settings, builds corpus, serves docs/AI/refresh/settings | `127.0.0.1`, `DOCSITE_PORT` or first free `8765..8784`; `.port`; `/`, `/briefing`, `/roadmap`, `/milestones`, `/radar`, `/ask*`, `/api/ai-config`, `/api/refresh/*` | exact-port loopback Host, same-origin mutating requests, per-start settings token, CSP/no-store; closes UI server and `.port` on exit |
| managed Broker inside `serve.py` | provider credential route, cache, budget, allowlist, single-flight | additional ephemeral/configured `127.0.0.1` HTTP listener | daemon thread; settings switch/delete explicitly stops it; main shutdown relies on process exit |
| `serve_team_observatory.py` | composes Personal + Team + optional Graph and handles Team/Maintenance control | separate ephemeral `127.0.0.1` server; `/team/`, `/team/api/*` | exact Host/Origin, HttpOnly `SameSite=Strict` cookie scoped `/team/`, bounded exact JSON; `server_close()` stops owned Coordinator |
| Team Coordinator owned by Team UI | local projection/request broker and explicit discovery probe | another ephemeral listener started after local action | Team UI owns start/stop; central remains request-only |
| `build_docsite.py` | canonical static reader, search, current dashboard, document-family navigation and optional shadow diagnostic | no listener; writes generated HTML only | static read-only; shadow failure returns legacy render |
| `build_authority_projection.py` | root-only opt-in M2.2 projection from CLI/Core bundle | no listener; injects panel | all-or-legacy fallback; Candidate only |
| `build_personal_observatory.py` | root-only opt-in Personal projection and maintenance catch-up/status | no listener; injects Personal + Maintenance pages | maintenance controls available only when caller declares dynamic control |
| `build_workstream_relation_graph.py` | root-only default-off W7 graph consumer | no listener; injects Graph page | validates provider/graph/plan, all-or-Unavailable, read-only |

Current navigation is constructed by the base builder and then modified through string markers by Personal, Team and
Graph injectors. There is no explicit consumer registry, route collision check or shared server lifecycle.

## 3. Runtime mode axes

Modes are orthogonal axes, not one overloaded status:

| Axis | Values | Rule |
|---|---|---|
| visible transport | `static-file`, `local-loopback-url` | static has no API/cookie/control; dynamic exposes one browser URL |
| process topology | `in-process`, `supervised-helper`, `mixed` | implementation choice; every helper is hidden and lifecycle-owned |
| console presentation | `headless-default`, `debug-one-console` | default shows none; explicit debug shows at most one |
| local execution | `read-only`, `host-local-control` | each action declares its own capability and confirmation gate |
| external network | `zero-network`, `provider-opt-in`, `team-opt-in` | Personal default is zero-network; provider and Team are independent opt-ins |
| Authority consumer | `legacy`, `shadow`, `candidate-projection`, `enabled`, `rollback`, `unavailable` | supplied by A3; shell never promotes a selection |
| evidence state | `current`, `cached`, `stale`, `unknown`, `unavailable` | display exactly; never collapse into green/ready |

Opening the dynamic shell does not enable provider or Team networking. Static mode never exposes a fake enabled control.

## 4. Single visible URL and internal topology

The default managed runtime exposes exactly one user-facing Observatory URL on `127.0.0.1`. Its public route table is:

| Method / route | Owner | Capability / mutation |
|---|---|---|
| `GET /` | shell | shell HTML and static bootstrap |
| `GET /api/v1/health` | shell | non-secret process/capability health |
| `GET /api/v1/capabilities` | shell | sanitized registry; no credential, absolute private path or source body |
| `GET /api/v1/docs/search` | docs | bounded local search |
| `POST /api/v1/ai/ask` / `ask-stream` | AI | provider-opt-in derived view |
| `GET/POST/DELETE /api/v1/ai/settings...` | AI | host-local credential/config workflow |
| `GET /api/v1/authority/status` | Authority | read-only A3 summary; no selection inference |
| `GET /api/v1/personal/status` | Personal | local projection |
| `GET /api/v1/team/status` | Team | unavailable until explicit Team opt-in |
| `POST /api/v1/team/requests...` | Team | request creation/decision; never execution |
| `GET /api/v1/workstreams/graph` | Graph | W7 read-only provider |
| `GET /api/v1/maintenance/status` | Maintenance | W6/W6.1 projection |
| `POST /api/v1/maintenance/refresh` | Maintenance | background local scan request |
| `POST /api/v1/maintenance/preflight` | Maintenance | target-scoped read-only revalidation |
| `POST /api/v1/maintenance/remove-worktree` | Maintenance | action-specific local confirmation/authorization only |

All UI pages remain one document and use `/#/<navigation-identity>` so the same saved identity works in static and
dynamic modes. API prefixes are not navigation identities. Unknown routes return 404; the shell never falls through to
HTML for `/api/`.

The public URL contract is independent of the internal process topology:

| Internal capability | Allowed topology | Required gates |
|---|---|---|
| managed Broker | in-process adapter or supervised hidden helper/loopback endpoint | provider behavior parity, credential/endpoint isolation, authenticated channel, bounded shutdown |
| Team Coordinator/transport | in-process or supervised listener/helper after Team opt-in | explicit transport boundary, project identity, no public UI route, deterministic stop |
| background maintenance/indexing | in-process worker or supervised hidden helper | zero-network default, bounded work, Git-private diagnostics, deterministic stop |

Internal endpoints are not navigation identities, are never opened in a browser and never require separate user
startup. Loopback helpers use scoped authentication and do not inherit UI cookie authority. A Team LAN listener is the
explicit opt-in exception to loopback-only binding and retains its own project/member authentication. Every helper
registers health, log and shutdown hooks with the supervisor. No topology is accepted without crash-recovery evidence
showing that helper processes and bound ports are reclaimed.

## 5. Capability discovery and consumer registration

Discovery is an explicit, code-owned allowlist; the shell does not scan arbitrary directories or import untrusted
plugins. Each registration conforms to `unified-observatory-consumer-registration-v1`:

```json
{
  "schema_version": 1,
  "consumer_id": "workspace-maintenance",
  "consumer_version": "provider-owned",
  "shell_api_versions": [1],
  "navigation": {"identity": "maintenance", "label": "工作区维护", "order": 80},
  "route_prefix": "/api/v1/maintenance",
  "capabilities": ["read-status", "background-refresh", "target-preflight", "local-remove-worktree"],
  "mode_requirements": {"transport": "local-loopback", "network": "zero-network"},
  "privilege": "host-local-action-specific",
  "authority": "derived-control-view",
  "static_fallback": "read-only-unavailable",
  "failure_policy": "quarantine-consumer",
  "source_contract": {"id": "maintenance-provider", "version": "unknown-until-W6.1-integrates"}
}
```

Registration validation requires unique consumer ID, navigation identity and route prefix; supported shell API;
known privilege class; declared static fallback; deterministic startup/shutdown hooks; and a source-contract version.
Missing or incompatible providers create an Unavailable registration. Route collision, privilege escalation or unsafe
fallback is a shell startup error, not last-writer-wins behavior.

Consumers own projection construction, sanitization and domain actions. Shell owns navigation, route dispatch,
security middleware, public capability summaries and lifecycle. Browser code never parses Git/session/Markdown into
domain facts.

The docsite consumer remains owner of document rendering, search, AI presentation, author information architecture and
recognizable visual behavior. The shell may adapt its registration and public routes but cannot silently replace those
product responsibilities.

## 6. Common local security contract

- Bind the public UI/control URL only to `127.0.0.1`; accept exact current-port `127.0.0.1` or `localhost` Host.
- Hidden loopback helpers bind `127.0.0.1`, use capability-scoped authentication and are not browser destinations.
  An explicitly enabled Team LAN transport follows its separate ADR-0008 identity/network boundary.
- Every mutation requires exact same Origin, acceptable `Sec-Fetch-Site`, an HttpOnly per-start random
  `orrery_local_control` cookie with `SameSite=Strict; Path=/`, exact JSON field allowlist and bounded body.
- Destructive actions additionally require provider-owned action-specific IDs and fresh preflight; the shell cookie is
  not deletion authority.
- Apply no-store, nosniff, frame denial, no-referrer, bounded CSP and sanitized errors to all routes.
- Never return provider keys, Broker tokens, Git-private absolute paths, prompts/answers/transcripts, source/diff body
  or arbitrary commands/URLs.
- Sharing one cookie and route dispatcher does not combine capability authorization. Each handler rechecks its provider
  capability and mode.

## 7. Lifecycle and shutdown

Startup order:

1. launch the supervisor headlessly by default, or attach the single explicit debug console;
2. resolve repository root and static shell inputs without writing author files;
3. validate explicit registrations, public routes and declared internal topology;
4. start required hidden helpers with scoped credentials, health probes and registered shutdown hooks;
5. bind the public loopback UI/control URL and atomically write its `.port` identity;
6. build/activate per-consumer ready/Unavailable bootstrap independently;
7. open the public URL once; never open an internal endpoint.

Shutdown order:

1. stop accepting new public mutations and internal work;
2. bound/drain public and helper requests;
3. call consumer/helper shutdown hooks in reverse dependency order;
4. stop or terminate bounded hidden helpers and flush bounded local receipts/caches/logs;
5. close public/internal listeners and remove runtime identity files only when they still match this supervisor instance;
6. verify no registered child, helper endpoint or stale ready marker remains.

Browser close is not by itself process authority. Explicit shell exit, debug Ctrl+C, normal supervisor shutdown,
startup failure and crash recovery use the same idempotent ownership model. The implementation may use a Windows Job
Object, process group or equivalent child ownership, but must prove that abnormal supervisor termination cannot leave
helpers running. Failures and sanitized diagnostics go to a Git-private/runtime log surfaced by the diagnostics page.

## 8. Static fallback and error isolation

- Static build emits docs/search plus precomputed safe projections when available. Dynamic-only controls are absent or
  disabled with precise copy; no browser attempt is made to call `/api/` under `file:`.
- A consumer build/provider/schema/render error becomes one Unavailable page with a stable navigation identity and
  sanitized diagnostic. Other consumers and docs remain usable.
- Authority is all-or-legacy/all-or-Unavailable; no partial claim panel.
- Maintenance cache failure keeps last-known data visibly stale/Unknown and disables execute until fresh preflight.
- Team failure leaves Personal zero-network and request capability disabled.
- AI/Broker failure leaves docs/search and deterministic projections operational.
- Shell integrity, duplicate routes, unsafe registration or base docs failure stops startup closed.

## 9. W6.1 and A3 join interfaces

### W6.1 Maintenance cache / Quick Remove

Observed concurrent evidence is Worktree-only, not canonical. W6.1 proposes cache `current/stale/Unknown`, background
refresh, target preflight and Quick Remove. U1 requires an adapter with these logical calls:

```text
describe() -> version/readiness/capabilities
snapshot() -> cache state + queue + protected reasons + background status
request_refresh(reason) -> accepted/background operation ID
preflight(target_id) -> current evidence-bound eligibility
remove_worktree(item_id, local_confirmation) -> provider authorization + receipt
```

Exact W6.1 schema/version and target/item identifiers remain **Unknown until its Candidate is committed, reviewed and
integrated**. The shell maps the accepted provider to `/api/v1/maintenance/*`; it does not preserve the provisional
`/control/api/maintenance/*` path as a public contract and does not copy cache invalidation or Git execution.

### A3 Authority managed consumer

Observed concurrent evidence is currently a Worktree Plan only. U1 expects `authority-managed-consumer-v1` (or its
reviewed successor) to provide requested/effective selection, active consumer, readiness/blockers, exact input/hash
bindings, rollout plan hash and rollback plan hash. Shell consumes only its sanitized status and complete staged render.
Until A3 supplies a compatible ready contract, `authority` remains Unavailable/legacy. Shell cannot turn
`candidate-projection` into `enabled`, cannot satisfy human selection and cannot accept AI/Coordinator escalation.

## 10. Windows one-click experience and compatibility

Candidate final experience:

```text
double-click Start Orrery (final shortcut/stub/script identity selected later)
  → start a hidden supervisor; no command-line window remains visible
  → write startup/helper diagnostics to a Git-private runtime log
  → open http://127.0.0.1:<port>/ once
  → Diagnostics can open the local log through a sanitized, local-only action

explicit debug launcher or Start Orrery --console
  → show at most one console for supervisor and aggregated helper logs
  → Ctrl+C requests unified shutdown and leaves no helper process or bound port
```

`start-docsite.bat` remains a thin compatibility forwarder for at least the ADR-0015 compatibility window, optionally
opening `/#/docs`. A feature flag or explicit legacy launcher keeps the current `serve.py` rollback path during staged
adoption. The compatibility entry must not open two URLs or require users to start helper processes separately. The
final implementation may use a hidden script host, `pythonw`, packaged launcher or equivalent; U1 does not choose the
shipping mechanism.

## 11. Versioning, rollback and public-template boundary

- Shell contract/API: `unified-observatory-shell-v1` and `/api/v1`.
- Registration: `unified-observatory-consumer-registration-v1`.
- Consumer/domain contracts retain independent versions; shell compatibility is a discrete supported set.
- Per-consumer rollback unregisters/quarantines that consumer and preserves its own data/state.
- Whole-shell rollback selects current legacy docsite bytes/entry without schema migration or author-document write.
- Production migration begins by adapting the current `build_docsite.py`／`serve.py` consumers; a from-scratch docsite
  rewrite or comprehensive visual redesign is outside this Design.
- No U1 artifact enters current public template, managed tools, installer, release manifest or v0.2.0.
- Public adoption requires accepted ADR, approved Design, implementation and migration plan, root/public template
  reconciliation, component/version decisions, exact Candidate SHA, Windows/Ubuntu required checks and explicit release.
