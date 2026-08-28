"use strict";

const FIXTURE_URL = "fixtures/workstream-graph.provisional.v1.json";
const SVG_NS = "http://www.w3.org/2000/svg";

const ui = {
  svg: document.querySelector("#relation-graph"),
  graphFrame: document.querySelector("#graph-frame"),
  empty: document.querySelector("#empty-state"),
  graphTitle: document.querySelector("#graph-title"),
  graphSummary: document.querySelector("#graph-summary"),
  modeIndex: document.querySelector("#mode-index"),
  subsystem: document.querySelector("#subsystem-filter"),
  status: document.querySelector("#status-filter"),
  history: document.querySelector("#history-toggle"),
  reset: document.querySelector("#reset-view"),
  inspector: document.querySelector("#inspector-content"),
  selectionKind: document.querySelector("#selection-kind"),
  ledger: document.querySelector("#relation-ledger"),
  evidenceIndex: document.querySelector("#evidence-index"),
  live: document.querySelector("#live-region")
};

const state = {
  fixture: null,
  mode: "succession",
  historyExpanded: false,
  subsystem: "all",
  status: "all",
  selection: {kind: "node", id: "w7c-a"}
};

const modeCopy = {
  succession: {
    index: "01",
    title: "Succession view",
    summary: "Active tip, inheritance chain, and one same-base sibling. Three earlier Workstreams are folded."
  },
  dependency: {
    index: "02",
    title: "Dependency view",
    summary: "W7C-B converges on two explicit predecessors; an evidence-poor influence stays Unknown."
  },
  conflict: {
    index: "03",
    title: "Conflict overlay",
    summary: "Confirmed fixture overlap is cross-hatched and labelled Direct; the semantic proposal remains broken."
  }
};

const positions = {
  successionCollapsed: {
    "history-w5c-w5d": {x: 55, y: 176, width: 182},
    ci1: {x: 296, y: 176},
    w5e: {x: 520, y: 176},
    "w7c-a": {x: 810, y: 82},
    w7a: {x: 810, y: 284}
  },
  successionExpanded: {
    w5c: {x: 12, y: 176, width: 142},
    w6: {x: 174, y: 176, width: 142},
    w5d: {x: 336, y: 176, width: 142},
    ci1: {x: 498, y: 176, width: 142},
    w5e: {x: 660, y: 176, width: 142},
    "w7c-a": {x: 904, y: 82, width: 154},
    w7a: {x: 904, y: 284, width: 154}
  },
  dependency: {
    w7a: {x: 90, y: 70},
    "w7c-a": {x: 90, y: 282},
    w5d: {x: 390, y: 324},
    "w7c-b": {x: 795, y: 176}
  },
  conflict: {
    w7a: {x: 92, y: 76},
    "w7c-a": {x: 800, y: 76},
    w5e: {x: 92, y: 298},
    "w7c-b": {x: 800, y: 298}
  }
};

function htmlElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
  return node;
}

function nodeById(id) {
  return state.fixture.nodes.find((node) => node.id === id);
}

function edgeById(id) {
  return state.fixture.edges.find((edge) => edge.id === id);
}

function matchesFilters(node) {
  const subsystemMatch = state.subsystem === "all" || node.subsystems.includes(state.subsystem);
  const statusMatch = state.status === "all" || node.runtime_condition === state.status;
  return subsystemMatch && statusMatch;
}

function relevantIds() {
  const ids = new Set();
  state.fixture.edges
    .filter((edge) => edge.view === state.mode)
    .forEach((edge) => {
      ids.add(edge.source);
      ids.add(edge.target);
    });
  if (state.mode === "succession") ids.add(state.fixture.default_active_tip_id);
  return ids;
}

function visibleGraph() {
  const relevant = relevantIds();
  const filteredNodes = state.fixture.nodes.filter((node) => relevant.has(node.id) && matchesFilters(node));
  const filteredIds = new Set(filteredNodes.map((node) => node.id));
  const collapsed = state.mode === "succession" && !state.historyExpanded;
  const history = state.fixture.collapsed_history[0];
  const historyIds = new Set(history.node_ids);
  const historyVisible = filteredNodes.some((node) => historyIds.has(node.id));
  const endpoint = (id) => collapsed && historyIds.has(id) ? history.id : id;

  const displayNodes = filteredNodes.filter((node) => !collapsed || !historyIds.has(node.id));
  if (collapsed && historyVisible) {
    displayNodes.unshift({
      id: history.id,
      label: "HISTORY",
      title: history.label,
      runtime_condition: "collapsed",
      evidence_freshness: "historical",
      subsystems: ["multi-worktree-collaboration"],
      is_cluster: true,
      node_ids: history.node_ids,
      summary: history.summary,
      evidence: []
    });
  }

  const displayIds = new Set(displayNodes.map((node) => node.id));
  const seen = new Set();
  const displayEdges = state.fixture.edges
    .filter((edge) => edge.view === state.mode)
    .map((edge) => ({...edge, displaySource: endpoint(edge.source), displayTarget: endpoint(edge.target)}))
    .filter((edge) => displayIds.has(edge.displaySource) && displayIds.has(edge.displayTarget))
    .filter((edge) => {
      if (edge.displaySource === edge.displayTarget) return false;
      const signature = `${edge.displaySource}:${edge.displayTarget}:${edge.view}`;
      if (seen.has(signature)) return false;
      seen.add(signature);
      return true;
    });

  return {nodes: displayNodes, edges: displayEdges, filteredIds};
}

function activePositions() {
  if (state.mode === "succession") {
    return state.historyExpanded ? positions.successionExpanded : positions.successionCollapsed;
  }
  return positions[state.mode];
}

function installDefs() {
  const defs = svgElement("defs");
  [
    ["arrow-confirmed", "#76d7d0"],
    ["arrow-uncertain", "#f1b95b"],
    ["arrow-conflict", "#ff765f"]
  ].forEach(([id, color]) => {
    const marker = svgElement("marker", {
      id, viewBox: "0 0 10 10", refX: 9, refY: 5,
      markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse"
    });
    marker.append(svgElement("path", {d: "M 0 0 L 10 5 L 0 10 z", fill: color}));
    defs.append(marker);
  });
  ui.svg.append(defs);
}

function edgeGeometry(source, target) {
  const sw = source.width || 160;
  const tw = target.width || 160;
  const sh = source.height || 92;
  const th = target.height || 92;
  const sourceCenter = {x: source.x + sw / 2, y: source.y + sh / 2};
  const targetCenter = {x: target.x + tw / 2, y: target.y + th / 2};
  const goingRight = targetCenter.x >= sourceCenter.x;
  const start = {x: goingRight ? source.x + sw : source.x, y: sourceCenter.y};
  const end = {x: goingRight ? target.x : target.x + tw, y: targetCenter.y};
  const bend = Math.max(70, Math.abs(end.x - start.x) * .42);
  const c1 = {x: start.x + (goingRight ? bend : -bend), y: start.y};
  const c2 = {x: end.x - (goingRight ? bend : -bend), y: end.y};
  return {
    d: `M ${start.x} ${start.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${end.x} ${end.y}`,
    labelX: (start.x + end.x) / 2,
    labelY: (start.y + end.y) / 2 - 11
  };
}

function edgeLabel(edge) {
  if (edge.certainty === "unknown") return "? UNKNOWN";
  if (edge.certainty === "proposed") return "PROPOSED";
  if (edge.view === "conflict") return "L3 / DIRECT";
  if (edge.relation.includes("sibling")) return "SAME BASE";
  if (edge.view === "dependency") return "REQUIRED";
  return "CONTINUES";
}

function renderEdge(edge, layout) {
  const source = layout[edge.displaySource];
  const target = layout[edge.displayTarget];
  if (!source || !target) return null;
  const geometry = edgeGeometry(source, target);
  const group = svgElement("g", {
    class: "graph-edge",
    tabindex: 0,
    role: "button",
    "aria-label": `${edgeLabel(edge)} edge from ${nodeById(edge.source).label} to ${nodeById(edge.target).label}`,
    "data-edge-id": edge.id,
    "data-view": edge.view,
    "data-certainty": edge.certainty
  });
  const marker = edge.view === "conflict" ? "arrow-conflict" :
    edge.certainty === "confirmed" ? "arrow-confirmed" : "arrow-uncertain";
  const title = svgElement("title");
  title.textContent = `${edge.relation}; ${edge.certainty}; select for evidence`;
  const visible = svgElement("path", {class: "edge-path", d: geometry.d, "marker-end": `url(#${marker})`});
  const hit = svgElement("path", {class: "edge-hit", d: geometry.d});
  const label = edgeLabel(edge);
  const labelWidth = Math.max(64, label.length * 6.5 + 16);
  const labelBg = svgElement("rect", {
    class: "edge-label-bg", x: geometry.labelX - labelWidth / 2, y: geometry.labelY - 11,
    width: labelWidth, height: 22
  });
  const labelText = svgElement("text", {
    class: "edge-label", x: geometry.labelX, y: geometry.labelY + 3, "text-anchor": "middle"
  });
  labelText.textContent = label;
  group.append(title, visible, hit, labelBg, labelText);
  group.addEventListener("click", () => selectItem("edge", edge.id));
  group.addEventListener("keydown", activateOnKeyboard(() => selectItem("edge", edge.id)));
  return group;
}

function renderNode(node, layout) {
  const position = layout[node.id];
  if (!position) return null;
  const width = position.width || 160;
  const height = position.height || 92;
  const classes = ["graph-node"];
  if (node.is_active_tip) classes.push("is-active");
  if (node.runtime_condition === "stale-unknown" || node.phase === "proposed") classes.push("is-proposed");
  if (node.is_cluster) classes.push("is-cluster");
  if (state.selection.kind === (node.is_cluster ? "cluster" : "node") && state.selection.id === node.id) classes.push("is-selected");
  const group = svgElement("g", {
    class: classes.join(" "),
    tabindex: 0,
    role: "button",
    "aria-label": node.is_cluster ? `${node.title}, collapsed history` : `${node.label}, ${node.title}, ${node.runtime_condition}`,
    "data-node-id": node.id,
    transform: `translate(${position.x} ${position.y})`
  });
  const title = svgElement("title");
  title.textContent = node.is_cluster ? `${node.summary}; select for details` : `${node.label}: ${node.title}; select for evidence`;
  if (node.is_active_tip) {
    group.append(svgElement("rect", {class: "tip-ring", x: -7, y: -7, width: width + 14, height: height + 14}));
  }
  group.append(svgElement("rect", {class: "node-body", x: 0, y: 0, width, height}));

  const label = svgElement("text", {class: "node-label", x: 13, y: 24});
  label.textContent = node.label;
  const titleText = svgElement("text", {class: "node-title", x: 13, y: 47});
  titleText.textContent = node.title.length > 24 ? `${node.title.slice(0, 22)}…` : node.title;
  const meta = svgElement("text", {class: "node-meta", x: 13, y: 70});
  meta.textContent = node.is_cluster ? node.summary : node.runtime_condition.toUpperCase().replaceAll("-", " ");
  group.append(title, label, titleText, meta);

  const badge = node.is_active_tip ? "ACTIVE TIP" : node.phase === "proposed" ? "PROPOSED" : "";
  if (badge) {
    const badgeWidth = badge.length * 6 + 15;
    group.append(svgElement("rect", {class: "node-badge", x: width - badgeWidth - 8, y: 8, width: badgeWidth, height: 18}));
    const badgeText = svgElement("text", {class: "node-badge-text", x: width - badgeWidth / 2 - 8, y: 20, "text-anchor": "middle"});
    badgeText.textContent = badge;
    group.append(badgeText);
  }

  const kind = node.is_cluster ? "cluster" : "node";
  group.addEventListener("click", () => selectItem(kind, node.id));
  group.addEventListener("keydown", activateOnKeyboard(() => selectItem(kind, node.id)));
  return group;
}

function activateOnKeyboard(action) {
  return (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      action();
    }
  };
}

function renderGraph() {
  const graph = visibleGraph();
  const layout = activePositions();
  ui.svg.replaceChildren();
  installDefs();
  const edgeLayer = svgElement("g", {"aria-label": "Relations"});
  const nodeLayer = svgElement("g", {"aria-label": "Workstreams"});
  graph.edges.forEach((edge) => {
    const element = renderEdge(edge, layout);
    if (element) edgeLayer.append(element);
  });
  graph.nodes.forEach((node) => {
    const element = renderNode(node, layout);
    if (element) nodeLayer.append(element);
  });
  ui.svg.append(edgeLayer, nodeLayer);
  ui.empty.hidden = graph.nodes.length > 0;
  ui.graphFrame.dataset.mode = state.mode;
  ui.graphTitle.textContent = modeCopy[state.mode].title;
  ui.modeIndex.textContent = modeCopy[state.mode].index;
  ui.graphSummary.textContent = state.mode === "succession" && state.historyExpanded
    ? "Expanded synthetic lineage. Collapse it to return to the operational default."
    : modeCopy[state.mode].summary;
  ui.history.disabled = state.mode !== "succession";
  ui.history.setAttribute("aria-pressed", String(state.historyExpanded));
  ui.history.innerHTML = `<span aria-hidden="true">${state.historyExpanded ? "−" : "＋"}</span> ${state.historyExpanded ? "Collapse history" : "Expand history"}`;
  renderLedger(graph);
}

function renderLedger(graph) {
  ui.ledger.replaceChildren();
  if (!graph.nodes.length) {
    ui.ledger.append(htmlElement("p", "inspector-placeholder", "No visible relations."));
    return;
  }
  graph.nodes.forEach((node) => {
    const kind = node.is_cluster ? "cluster" : "node";
    const button = htmlElement("button", "ledger-item");
    button.type = "button";
    button.dataset.kind = kind;
    button.dataset.id = node.id;
    button.dataset.certainty = node.phase === "proposed" ? "proposed" : "confirmed";
    if (state.selection.kind === kind && state.selection.id === node.id) button.classList.add("is-selected");
    const code = htmlElement("span", "ledger-code", node.is_cluster ? "↳ 3×" : node.label);
    const copy = htmlElement("span", "ledger-copy");
    copy.append(htmlElement("strong", "", node.title), htmlElement("small", "", node.is_cluster ? node.summary : node.subsystems.join(" · ")));
    const status = htmlElement("span", "ledger-state", node.runtime_condition.replaceAll("-", " ").toUpperCase());
    button.append(code, copy, status);
    button.addEventListener("click", () => selectItem(kind, node.id));
    ui.ledger.append(button);
  });
  graph.edges.forEach((edge) => {
    const source = nodeById(edge.source);
    const target = nodeById(edge.target);
    const button = htmlElement("button", "ledger-item");
    button.type = "button";
    button.dataset.kind = "edge";
    button.dataset.id = edge.id;
    button.dataset.certainty = edge.certainty;
    button.dataset.view = edge.view;
    if (state.selection.kind === "edge" && state.selection.id === edge.id) button.classList.add("is-selected");
    const symbol = edge.view === "conflict" ? "×" : edge.certainty === "confirmed" ? "→" : "⇢ ?";
    const code = htmlElement("span", "ledger-code", symbol);
    const copy = htmlElement("span", "ledger-copy");
    copy.append(htmlElement("strong", "", `${source.label} → ${target.label}`), htmlElement("small", "", edge.relation));
    const certainty = htmlElement("span", "ledger-state", edgeLabel(edge));
    button.append(code, copy, certainty);
    button.addEventListener("click", () => selectItem("edge", edge.id));
    ui.ledger.append(button);
  });
}

function appendFact(list, label, value) {
  const row = htmlElement("div");
  row.append(htmlElement("dt", "", label), htmlElement("dd", "", value));
  list.append(row);
}

function evidenceBlock(evidence) {
  const block = htmlElement("div", "evidence-block");
  block.append(htmlElement("h4", "", "EVIDENCE LINKS"));
  const list = htmlElement("ul");
  if (!evidence.length) {
    list.append(htmlElement("li", "", "Collapsed presentation group; inspect its synthetic child nodes."));
  } else {
    evidence.forEach((item) => {
      const row = htmlElement("li");
      const anchor = htmlElement("a", "", `${item.label} · ${item.kind}`);
      anchor.href = item.href;
      row.append(anchor);
      list.append(row);
    });
  }
  block.append(list);
  return block;
}

function renderInspector() {
  ui.inspector.replaceChildren();
  let heading;
  let subtitle;
  let evidence = [];
  const facts = htmlElement("dl", "fact-list");
  const symbol = htmlElement("span", `selection-symbol ${state.selection.kind === "edge" ? "edge" : ""}`);

  if (state.selection.kind === "edge") {
    const edge = edgeById(state.selection.id);
    if (!edge) return;
    const source = nodeById(edge.source);
    const target = nodeById(edge.target);
    symbol.textContent = edge.view === "conflict" ? "×" : "→";
    heading = `${source.label} → ${target.label}`;
    subtitle = edge.relation;
    evidence = edge.evidence;
    appendFact(facts, "Lens", edge.view);
    appendFact(facts, "Certainty", edge.certainty);
    appendFact(facts, "Direction", `${edge.source} → ${edge.target}`);
    appendFact(facts, "Severity", edge.severity || "not applicable");
    appendFact(facts, "Edge ID", edge.id);
    ui.selectionKind.textContent = "EDGE";
  } else if (state.selection.kind === "cluster") {
    const cluster = state.fixture.collapsed_history.find((item) => item.id === state.selection.id);
    if (!cluster) return;
    symbol.textContent = "3×";
    heading = cluster.label;
    subtitle = "Consumer-generated presentation cluster";
    appendFact(facts, "Contains", cluster.node_ids.join(" → "));
    appendFact(facts, "Summary", cluster.summary);
    appendFact(facts, "Authority", "provisional / non-authoritative");
    appendFact(facts, "Cluster ID", cluster.id);
    ui.selectionKind.textContent = "CLUSTER";
  } else {
    const node = nodeById(state.selection.id);
    if (!node) return;
    symbol.textContent = node.is_active_tip ? "◎" : node.label;
    heading = node.label;
    subtitle = node.title;
    evidence = node.evidence;
    appendFact(facts, "Lifecycle", node.phase);
    appendFact(facts, "Runtime", node.runtime_condition);
    appendFact(facts, "Freshness", node.evidence_freshness);
    appendFact(facts, "Subsystems", node.subsystems.join(", "));
    appendFact(facts, "Branch", node.branch);
    appendFact(facts, "Ref", node.short_ref);
    ui.selectionKind.textContent = "NODE";
  }

  const header = htmlElement("div");
  header.append(symbol, htmlElement("h3", "", heading), htmlElement("p", "selection-subtitle", subtitle), facts);
  const evidenceSide = evidenceBlock(evidence);
  evidenceSide.append(htmlElement("p", "provisional-note", "Fixture evidence only. This selection cannot create or confirm a production relation."));
  ui.inspector.append(header, evidenceSide);
}

function selectItem(kind, id) {
  state.selection = {kind, id};
  renderGraph();
  renderInspector();
  const label = kind === "edge" ? edgeLabel(edgeById(id)) : kind === "cluster" ? "collapsed history" : nodeById(id).label;
  ui.live.textContent = `Selected ${label}; evidence inspector updated.`;
}

function renderEvidenceIndex() {
  const seen = new Set();
  ui.evidenceIndex.replaceChildren();
  [...state.fixture.nodes, ...state.fixture.edges].forEach((item) => {
    (item.evidence || []).forEach((evidence) => {
      const id = evidence.href.startsWith("#") ? evidence.href.slice(1) : evidence.href;
      if (!id || seen.has(id)) return;
      seen.add(id);
      const row = htmlElement("li", "", `${evidence.label} · ${evidence.kind}`);
      row.id = id;
      ui.evidenceIndex.append(row);
    });
  });
}

function populateFilters() {
  const subsystems = [...new Set(state.fixture.nodes.flatMap((node) => node.subsystems))].sort();
  subsystems.forEach((value) => {
    const option = htmlElement("option", "", value);
    option.value = value;
    ui.subsystem.append(option);
  });
  const statuses = [...new Set(state.fixture.nodes.map((node) => node.runtime_condition))].sort();
  statuses.forEach((value) => {
    const option = htmlElement("option", "", value.replaceAll("-", " "));
    option.value = value;
    ui.status.append(option);
  });
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll("[data-mode]").forEach((button) => {
    if (!button.classList.contains("lens-button")) return;
    const active = button.dataset.mode === mode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  const graph = visibleGraph();
  const selectionVisible = graph.nodes.some((node) => node.id === state.selection.id) || graph.edges.some((edge) => edge.id === state.selection.id);
  if (!selectionVisible) {
    const fallback = graph.nodes.find((node) => node.id === state.fixture.default_active_tip_id) || graph.nodes[0];
    if (fallback) state.selection = {kind: fallback.is_cluster ? "cluster" : "node", id: fallback.id};
  }
  renderGraph();
  renderInspector();
  ui.live.textContent = `${modeCopy[mode].title} active.`;
}

function resetView() {
  state.mode = "succession";
  state.historyExpanded = false;
  state.subsystem = "all";
  state.status = "all";
  state.selection = {kind: "node", id: state.fixture.default_active_tip_id};
  ui.subsystem.value = "all";
  ui.status.value = "all";
  setMode("succession");
}

function installInteractions() {
  document.querySelectorAll(".lens-button").forEach((button) => {
    button.addEventListener("click", () => setMode(button.dataset.mode));
  });
  ui.history.addEventListener("click", () => {
    if (state.mode !== "succession") return;
    state.historyExpanded = !state.historyExpanded;
    renderGraph();
    if (!state.historyExpanded && ["w5c", "w6", "w5d"].includes(state.selection.id)) {
      state.selection = {kind: "cluster", id: "history-w5c-w5d"};
      renderGraph();
      renderInspector();
    }
    ui.live.textContent = state.historyExpanded ? "Historical succession expanded." : "Historical succession collapsed.";
  });
  ui.reset.addEventListener("click", resetView);
  ui.subsystem.addEventListener("change", () => {
    state.subsystem = ui.subsystem.value;
    renderGraph();
    ui.live.textContent = `Subsystem filter set to ${state.subsystem}.`;
  });
  ui.status.addEventListener("change", () => {
    state.status = ui.status.value;
    renderGraph();
    ui.live.textContent = `Runtime status filter set to ${state.status}.`;
  });
}

async function loadFixture() {
  try {
    const response = await fetch(FIXTURE_URL, {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const fixture = await response.json();
    if (fixture.authority !== "provisional/non-authoritative") {
      throw new Error("fixture is missing the provisional authority boundary");
    }
    state.fixture = fixture;
    state.selection = {kind: "node", id: fixture.default_active_tip_id};
    populateFilters();
    renderEvidenceIndex();
    installInteractions();
    renderGraph();
    renderInspector();
    document.documentElement.dataset.prototypeReady = "true";
  } catch (error) {
    ui.inspector.replaceChildren(
      htmlElement("p", "provisional-note", `Fixture failed to load: ${error.message}. Serve this directory over loopback HTTP; direct file loading cannot fetch JSON.`)
    );
    ui.empty.hidden = false;
  }
}

loadFixture();
