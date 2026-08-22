# Versioned context-routing pilots

Each pilot directory is an immutable experiment packet once its first run starts. Corrections belong in a new pilot directory; never rewrite a used prompt in place.

- `pilot-001` is represented by the legacy root-level `START-PILOT.zh-CN.md`, `prepare_pilot.ps1`, and `prompts/` files. Its apparatus defects are documented in the [pilot-001 comparison](../results/2026-08-17-po-cr-004-pilot-001.md).
- `pilot-002` is the corrected packet. It supplies the missing public repository fact, enforces repository-only context or a contaminated-run stop, defines content-producing searches as reads, and generates prompt checksums.
- `pilot-003` is the first multi-task packet. It prepares nine isolated repositories for documentation, cross-module, and security work; records the shared execution profile and operator timing outside the Agent; preserves structured pre-write declarations in ignored Agent receipts; and includes an independent artifact validator. Its local one-command runner executes one A/B/C task group at a time, captures Codex JSONL, resumes without silently retrying interrupted attempts, and generates a machine-readable summary plus a Markdown comparison. A real GPT-5.6 Terra / medium run is documented in [`results/2026-08-18-pilot-003-terra-medium.md`](../results/2026-08-18-pilot-003-terra-medium.md); all nine executions completed, while the sealed v1 run remains protocol-invalid because its validation receipts used structured objects instead of the required strings.
- `pilot-004` is the first prospective B/H holdout packet. Six GPT-5.6 Terra / medium runs completed across credential revocation, update-cache integrity, and a shared compatibility gate. Its frozen v1 Oracle is retained as an apparatus-failure artifact; corrected read-only acceptance passed B and H 3/3. The [result](../results/2026-08-18-pilot-004-bh-holdout-terra-medium.md) does not adopt H because H consumed 47% more input tokens and took about 15% longer.
- `pilot-005` freezes the first two-task B/H2 packet. All four raw runs are retained as apparatus failures because the common validator and isolation layer mishandled Windows command wrappers, absolute paths, Git history, and contract keys.
- `pilot-006` keeps the same task goals and treatment while correcting only the shared apparatus. B and H2 passed both task Oracles. A checksummed v3 read-only review resolves a CRLF stdout false negative without rewriting the sealed runs. The [combined result](../results/2026-08-18-pilot-005-006-bh2-terra-medium.md) does not adopt H2 because it used 18.5% more total input tokens than B.
- `pilot-007` completed six P/B runs. All R0 manifests verify, but a shared nested-branch validation defect and one invalid B access run prevent a clean adoption comparison. Read-only review found equal corrected task quality (2/3 each), while B exceeded the input, output, and time gates and missed the minimum proxy-byte benefit. The [R2 result](../results/2026-08-18-pilot-007-pb-adoption-terra-medium.md) does not adopt B.
- `pilot-008` started one formal P/S pair and stopped as designed. Both exact Scope measurements and R0 manifests
  are preserved, but P was contaminated by an external installed-Skill read and the shared migration Oracle imposed
  names and document wording absent from the task. Its directional ratios are diagnostic only and cannot support
  adoption; see the [apparatus-stop validation](../../../docs/validation/2026-08-19-pilot-008-formal-apparatus-stop.md).
- `pilot-009` keeps the same complete Skill, task goals, P/S entrance treatment, model profile, and adoption gates.
  It assigns new task IDs, corrects the demonstrated semantic Oracle false negatives, explicitly excludes installed
  Skill input, disables app-server skill search, and retains full-event rejection plus paired fail-stop behavior.
  Six formal runs completed with valid apparatus and Scope evidence. S used 82.74% of P's aggregate pre-write input,
  but read-only quality was only 2/3 on both sides; the [R2 result](../results/2026-08-19-pilot-009-ps-scope-terra-medium.md)
  does not adopt S.

There is no `pilot-010` packet. The model-free [C1 Oracle v0.2 controls](../results/2026-08-22-c1-oracle-v0.2-static-controls.md)
are ready for a future design request, but they do not authorize or instantiate another run.
