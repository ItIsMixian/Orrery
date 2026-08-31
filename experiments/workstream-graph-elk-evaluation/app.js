(() => {
  "use strict";

  const state = {
    fixture: null,
    view: "succession",
    layers: { affected: false, semantic: false, external: false },
    zoom: 1,
    panX: 22,
    panY: 22,
    selected: null,
    layout: null,
    visibleNodes: [],
    visibleEdges: [],
    visibleBoundaries: [],
    reports: {},
    dragging: null,
  };

  const els = {
    tabs: [...document.querySelectorAll("[data-view]")],
    context: document.querySelector(".context-controls"),
    layerChecks: [...document.querySelectorAll("[data-layer]")],
    zoomValue: document.querySelector("[data-zoom-value]"),
    svg: document.querySelector(".graph"),
    viewport: document.querySelector(".canvas-viewport"),
    loading: document.querySelector(".loading"),
    title: document.querySelector("[data-view-title]"),
    description: document.querySelector("[data-view-description]"),
    inspector: document.querySelector(".inspector"),
    inspectorBody: document.querySelector("[data-inspector]"),
    closeInspector: document.querySelector("[data-close-inspector]"),
    ledger: document.querySelector("[data-ledger]"),
    layoutStatus: document.querySelector("[data-layout-status]"),
    factCount: document.querySelector("[data-fact-count]"),
  };

  const svgNS = "http://www.w3.org/2000/svg";
  const cardWidth = 248;
  const cardHeight = 108;
  const nodeById = (id) => state.fixture.nodes.find((node) => node.id === id);
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[char]);
  const createSvg = (tag, attrs = {}) => {
    const element = document.createElementNS(svgNS, tag);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  };

  function visibleFactSet() {
    const view = state.fixture.views[state.view];
    const ids = new Set(view.full_card_ids);
    let boundaries = [];
    if (state.view === "w_compound") {
      if (state.layers.external) view.external_context_ids.forEach((id) => ids.add(id));
      else boundaries = (view.phase_panels || []).flatMap((panel) => panel.boundary_stubs || []);
    }
    if (state.view === "project_structure") {
      const candidates = [];
      if (state.layers.semantic) candidates.push(...view.semantic_context_ids);
      if (state.layers.affected) candidates.push(...view.affected_context_ids);
      const uniqueExternal = [...new Set(candidates)].filter((id) => !ids.has(id));
      uniqueExternal.slice(0, 12).forEach((id) => ids.add(id));
      const recordedOverflow = state.layers.affected ? Number(String([].concat(view.boundary_ids || [])[0] || "").split("+")[1] || 0) : 0;
      const overflow = recordedOverflow + Math.max(0, uniqueExternal.length - 12);
      if (overflow) boundaries = [{ id: `context-overflow+${overflow}`, label: `+${overflow} 外部关联`, kind: "summary" }];
    }
    const nodes = [...ids].map(nodeById).filter(Boolean);
    const boundaryEndpoints = new Set(boundaries.map((boundary) => boundary.endpoint_id).filter(Boolean));
    const edges = view.edges.filter((edge) => (ids.has(edge.source) || boundaryEndpoints.has(edge.source)) && (ids.has(edge.target) || boundaryEndpoints.has(edge.target)));
    return { view, nodes, edges, boundaries };
  }

  function elkNode(node) {
    return {
      id: node.id,
      width: cardWidth,
      height: cardHeight,
      layoutOptions: { "elk.portConstraints": "FIXED_SIDE" },
      ports: [
        { id: `${node.id}::west`, width: 1, height: 1, layoutOptions: { "elk.port.side": "WEST" } },
        { id: `${node.id}::east`, width: 1, height: 1, layoutOptions: { "elk.port.side": "EAST" } },
      ],
    };
  }

  function buildGraph(nodes, edges, boundaries, groups) {
    const nodeIds = new Set(nodes.map((node) => node.id));
    const boundaryByEndpoint = new Map(boundaries.filter((boundary) => boundary.endpoint_id).map((boundary) => [boundary.endpoint_id, boundary.id]));
    const layoutEndpoint = (id) => nodeIds.has(id) ? id : boundaryByEndpoint.get(id);
    const graph = {
      id: "root",
      layoutOptions: {
        "elk.algorithm": "layered",
        "elk.direction": "RIGHT",
        "elk.edgeRouting": "ORTHOGONAL",
        "elk.hierarchyHandling": "INCLUDE_CHILDREN",
        "elk.separateConnectedComponents": "true",
        "elk.spacing.componentComponent": "72",
        "elk.spacing.nodeNode": "52",
        "elk.layered.spacing.nodeNodeBetweenLayers": "112",
        "elk.layered.spacing.edgeNodeBetweenLayers": "46",
        "elk.layered.spacing.edgeEdgeBetweenLayers": "22",
        "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
        "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP",
        "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
        "elk.padding": "[top=28,left=28,bottom=28,right=28]",
      },
      children: [],
      edges: edges.map((edge) => ({
        id: edge.id,
        sources: [`${layoutEndpoint(edge.source)}::east`],
        targets: [`${layoutEndpoint(edge.target)}::west`],
        labels: [{ id: `${edge.id}::label`, text: edge.label, width: Math.max(56, edge.label.length * 13 + 18), height: 24 }],
        layoutOptions: { "elk.layered.priority.direction": edge.kind === "series" ? "2" : "7" },
      })),
    };

    if (state.view === "w_compound") {
      const groupMap = new Map(groups.map((group) => [group.id, { ...group, children: [] }]));
      nodes.forEach((node) => {
        const item = elkNode(node);
        if (node.phase_id && groupMap.has(node.phase_id)) groupMap.get(node.phase_id).children.push(item);
        else graph.children.push(item);
      });
      [...groupMap.values()].filter((group) => group.kind === "phase").forEach((phase) => {
        if (!phase.children.length) return;
        const phaseGraph = {
          id: phase.id,
          children: phase.children,
          layoutOptions: {
            "elk.algorithm": "layered",
            "elk.direction": "DOWN",
            "elk.edgeRouting": "ORTHOGONAL",
            "elk.padding": "[top=46,left=22,bottom=22,right=22]",
            "elk.spacing.nodeNode": "34",
          },
        };
        const parent = groupMap.get(phase.parent);
        if (parent) parent.children.push(phaseGraph);
      });
      const program = groupMap.get("workstream-w");
      if (program?.children.length) {
        graph.children.unshift({
          id: program.id,
          children: program.children,
          layoutOptions: {
            "elk.algorithm": "layered",
            "elk.direction": "RIGHT",
            "elk.edgeRouting": "ORTHOGONAL",
            "elk.padding": "[top=50,left=26,bottom=26,right=26]",
            "elk.spacing.nodeNode": "34",
          },
        });
      }
    } else {
      graph.children = nodes.map(elkNode);
    }

    boundaries.forEach((boundary) => graph.children.push({
      id: boundary.id,
      width: boundary.kind === "summary" ? 154 : 178,
      height: boundary.kind === "summary" ? 54 : 66,
      layoutOptions: { "elk.portConstraints": "FIXED_SIDE" },
      ports: [
        { id: `${boundary.id}::west`, width: 1, height: 1, layoutOptions: { "elk.port.side": "WEST" } },
        { id: `${boundary.id}::east`, width: 1, height: 1, layoutOptions: { "elk.port.side": "EAST" } },
      ],
    }));
    if (state.view === "project_structure" && state.layers.affected && !state.layers.semantic) {
      graph.layoutOptions = {
        "elk.algorithm": "box",
        "elk.spacing.nodeNode": "34",
        "elk.padding": "[top=28,left=28,bottom=28,right=28]",
      };
      graph.edges = [];
    }
    graph.inputNodeIds = [...nodeIds];
    return graph;
  }

  function phaseLeafNode(node, direction) {
    const vertical = direction === "DOWN";
    return {
      id: node.id,
      width: cardWidth,
      height: cardHeight,
      layoutOptions: { "elk.portConstraints": "FIXED_SIDE" },
      ports: [
        { id: `${node.id}::in`, width: 1, height: 1, layoutOptions: { "elk.port.side": vertical ? "NORTH" : "WEST" } },
        { id: `${node.id}::out`, width: 1, height: 1, layoutOptions: { "elk.port.side": vertical ? "SOUTH" : "EAST" } },
      ],
    };
  }

  function phaseBoundaryNode(boundary, direction) {
    const vertical = direction === "DOWN";
    return {
      id: boundary.id,
      width: 178,
      height: 66,
      layoutOptions: { "elk.portConstraints": "FIXED_SIDE" },
      ports: [
        { id: `${boundary.id}::in`, width: 1, height: 1, layoutOptions: { "elk.port.side": vertical ? "NORTH" : "WEST" } },
        { id: `${boundary.id}::out`, width: 1, height: 1, layoutOptions: { "elk.port.side": vertical ? "SOUTH" : "EAST" } },
      ],
    };
  }

  function translatePoint(point, x, y) {
    return point ? { ...point, x: point.x + x, y: point.y + y } : point;
  }

  function translateEdge(edge, x, y) {
    return {
      ...edge,
      sections: (edge.sections || []).map((section) => ({
        ...section,
        startPoint: translatePoint(section.startPoint, x, y),
        bendPoints: (section.bendPoints || []).map((point) => translatePoint(point, x, y)),
        endPoint: translatePoint(section.endPoint, x, y),
      })),
      labels: (edge.labels || []).map((label) => ({ ...label, x: label.x + x, y: label.y + y })),
    };
  }

  async function layoutWPhaseMultiples(view) {
    const edgeById = new Map(view.edges.map((edge) => [edge.id, edge]));
    const layouts = await Promise.all(view.phase_panels.map(async (panel) => {
      const members = panel.member_ids.map(nodeById).filter(Boolean);
      const memberIds = new Set(panel.member_ids);
      const boundaryByEndpoint = new Map(panel.boundary_stubs.map((stub) => [stub.endpoint_id, stub.id]));
      const endpoint = (id) => memberIds.has(id) ? id : boundaryByEndpoint.get(id);
      const panelEdges = panel.edge_ids.map((id) => edgeById.get(id)).filter(Boolean);
      const input = {
        id: panel.id,
        layoutOptions: {
          "elk.algorithm": "layered",
          "elk.direction": panel.direction,
          "elk.edgeRouting": "ORTHOGONAL",
          "elk.separateConnectedComponents": "true",
          "elk.spacing.componentComponent": "34",
          "elk.spacing.nodeNode": "34",
          "elk.layered.spacing.nodeNodeBetweenLayers": "72",
          "elk.layered.spacing.edgeNodeBetweenLayers": "34",
          "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
          "elk.padding": "[top=18,left=18,bottom=18,right=18]",
        },
        children: [...members.map((node) => phaseLeafNode(node, panel.direction)), ...panel.boundary_stubs.map((stub) => phaseBoundaryNode(stub, panel.direction))],
        edges: panelEdges.map((edge) => ({
          id: edge.id,
          sources: [`${endpoint(edge.source)}::out`],
          targets: [`${endpoint(edge.target)}::in`],
          labels: [{ id: `${edge.id}::label`, text: edge.label, width: Math.max(56, edge.label.length * 13 + 18), height: 24 }],
        })),
      };
      const layout = await new ELK().layout(input);
      return { panel, layout, width: layout.width + 32, height: layout.height + 58 };
    }));

    const byPhase = new Map(layouts.map((item) => [item.panel.phase_id, item]));
    const w5 = byPhase.get("workstream-w5");
    const w6 = byPhase.get("workstream-w6");
    const w7 = byPhase.get("workstream-w7");
    const phaseGap = 26;
    const placements = new Map([
      [w5.panel.phase_id, { x: 28, y: 50 }],
      [w6.panel.phase_id, { x: 28 + w5.width + phaseGap, y: 50 }],
      [w7.panel.phase_id, { x: 28 + w5.width + phaseGap + w6.width + phaseGap, y: 50 }],
    ]);
    const contentHeight = Math.max(w5.height, w6.height, w7.height);
    const program = {
      id: "workstream-w",
      x: 24,
      y: 24,
      width: 28 + w5.width + phaseGap + w6.width + phaseGap + w7.width + 28,
      height: 50 + contentHeight + 28,
      children: [],
    };
    const rootEdges = [];
    layouts.forEach(({ panel, layout, width, height }) => {
      const placement = placements.get(panel.phase_id);
      const childOffsetX = 16;
      const childOffsetY = 42;
      program.children.push({
        id: panel.phase_id,
        x: placement.x,
        y: placement.y,
        width,
        height,
        children: (layout.children || []).map((child) => ({ ...child, x: child.x + childOffsetX, y: child.y + childOffsetY })),
      });
      const edgeOffsetX = program.x + placement.x + childOffsetX;
      const edgeOffsetY = program.y + placement.y + childOffsetY;
      (layout.edges || []).forEach((edge) => rootEdges.push(translateEdge(edge, edgeOffsetX, edgeOffsetY)));
    });
    return {
      id: "root",
      width: program.x + program.width + 24,
      height: program.y + program.height + 24,
      children: [program],
      edges: rootEdges,
      inputNodeIds: state.visibleNodes.map((node) => node.id),
    };
  }

  function absoluteLayout(layout) {
    const nodes = new Map();
    const groups = new Map();
    const walk = (children, offsetX = 0, offsetY = 0, ancestry = []) => {
      (children || []).forEach((child) => {
        const x = offsetX + (child.x || 0);
        const y = offsetY + (child.y || 0);
        if (child.children) {
          groups.set(child.id, { ...child, absX: x, absY: y, ancestry });
          walk(child.children, x, y, [...ancestry, child.id]);
        } else {
          nodes.set(child.id, { ...child, absX: x, absY: y, ancestry });
        }
      });
    };
    walk(layout.children);
    return { nodes, groups };
  }

  function edgeClass(edge) {
    if (edge.certainty === "stale") return "edge stale";
    if (edge.kind === "dependency") return "edge dependency";
    if (edge.kind === "series") return "edge series";
    return "edge confirmed";
  }

  function pointsForSection(section) {
    return [section.startPoint, ...(section.bendPoints || []), section.endPoint].filter(Boolean);
  }

  function render(layout) {
    els.svg.replaceChildren();
    const defs = createSvg("defs");
    [
      ["arrow-confirmed", "#87e3da"],
      ["arrow-series", "#96a4b6"],
      ["arrow-proposed", "#f1c967"],
      ["arrow-stale", "#96a4b6"],
    ].forEach(([id, fill]) => {
      const marker = createSvg("marker", { id, viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 6, markerHeight: 6, orient: "auto-start-reverse" });
      marker.append(createSvg("path", { d: "M 0 0 L 10 5 L 0 10 z", fill }));
      defs.append(marker);
    });
    els.svg.append(defs);
    const root = createSvg("g", { class: "graph-root" });
    els.svg.append(root);
    const abs = absoluteLayout(layout);
    const view = state.fixture.views[state.view];

    [...abs.groups.values()].sort((a, b) => (a.ancestry?.length || 0) - (b.ancestry?.length || 0)).forEach((group) => {
      const groupSpec = view.groups.find((item) => item.id === group.id);
      const g = createSvg("g", { "data-group-id": group.id });
      g.append(createSvg("rect", { x: group.absX, y: group.absY, width: group.width, height: group.height, rx: 13, class: `group-box ${groupSpec?.kind || "phase"}` }));
      const label = createSvg("text", { x: group.absX + 18, y: group.absY + 25, class: `group-label ${groupSpec?.kind || "phase"}` });
      label.textContent = groupSpec?.label || group.id;
      g.append(label);
      root.append(g);
    });

    const edgeById = new Map(state.visibleEdges.map((edge) => [edge.id, edge]));
    (layout.edges || []).forEach((elkEdge) => {
      const edge = edgeById.get(elkEdge.id);
      if (!edge) return;
      const group = createSvg("g", { class: "edge-hit", tabindex: "0", role: "button", "aria-label": `${edge.label}：${edge.source} 到 ${edge.target}`, "data-edge-id": edge.id });
      (elkEdge.sections || []).forEach((section) => {
        const points = pointsForSection(section).map((point) => `${point.x},${point.y}`).join(" ");
        const marker = edge.certainty === "stale" ? "arrow-stale" : edge.kind === "dependency" ? "arrow-proposed" : edge.kind === "series" ? "arrow-series" : "arrow-confirmed";
        group.append(createSvg("polyline", { points, class: edgeClass(edge), "marker-end": `url(#${marker})` }));
      });
      (elkEdge.labels || []).forEach((label) => {
        if (!Number.isFinite(label.x) || !Number.isFinite(label.y)) return;
        group.append(createSvg("rect", { x: label.x, y: label.y, width: label.width, height: label.height, class: "edge-label-bg" }));
        const text = createSvg("text", { x: label.x + label.width / 2, y: label.y + label.height / 2 + 1, class: "edge-label-text" });
        text.textContent = edge.label;
        group.append(text);
      });
      group.addEventListener("click", (event) => { event.stopPropagation(); selectFact("edge", edge.id); });
      group.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") selectFact("edge", edge.id); });
      root.append(group);
    });

    const boundaryById = new Map(state.visibleBoundaries.map((boundary) => [boundary.id, boundary]));
    abs.nodes.forEach((placed, id) => {
      if (boundaryById.has(id)) {
        const boundary = boundaryById.get(id);
        const g = createSvg("g", { "data-boundary-id": id });
        g.append(createSvg("rect", { x: placed.absX, y: placed.absY, width: placed.width, height: placed.height, rx: 10, class: "boundary" }));
        const text = createSvg("text", { x: placed.absX + placed.width / 2, y: placed.absY + placed.height / 2, class: "boundary-text" });
        text.textContent = boundary.label;
        g.append(text);
        root.append(g);
        return;
      }
      const node = nodeById(id);
      if (!node) return;
      const g = createSvg("g", { class: `node-hit${state.selected?.id === id ? " selected" : ""}`, tabindex: "0", role: "button", "aria-label": `${node.code} ${node.title}，${node.status}`, "data-node-id": id });
      const fullText = createSvg("title");
      fullText.textContent = `${node.code} · ${node.title}\n${node.id}\n${node.status} · ${node.primary_subsystem} · ${node.lifecycle}`;
      g.append(fullText);
      g.append(createSvg("rect", { x: placed.absX, y: placed.absY, width: placed.width, height: placed.height, class: `node-card ${node.status_code}` }));
      const clipId = `node-clip-${Math.abs([...id].reduce((hash, char) => ((hash << 5) - hash + char.charCodeAt(0)) | 0, 0))}`;
      const clip = createSvg("clipPath", { id: clipId });
      clip.append(createSvg("rect", { x: placed.absX + 10, y: placed.absY + 6, width: placed.width - 20, height: placed.height - 12, rx: 7 }));
      defs.append(clip);
      const copy = createSvg("g", { "clip-path": `url(#${clipId})` });
      const status = createSvg("text", { x: placed.absX + 16, y: placed.absY + 22, class: `node-status ${node.status_code === "in-progress" ? "" : "warn"}` });
      status.textContent = node.status;
      const code = createSvg("text", { x: placed.absX + 16, y: placed.absY + 49, class: "node-code" });
      code.textContent = node.code;
      const title = createSvg("text", { x: placed.absX + 72, y: placed.absY + 49, class: "node-title" });
      title.textContent = node.title.length > 18 ? `${node.title.slice(0, 18)}…` : node.title;
      const idText = createSvg("text", { x: placed.absX + 16, y: placed.absY + 76, class: "node-meta" });
      idText.textContent = node.id.length > 30 ? `${node.id.slice(0, 30)}…` : node.id;
      const meta = createSvg("text", { x: placed.absX + 16, y: placed.absY + 96, class: "node-meta" });
      meta.textContent = `${node.primary_subsystem} · ${node.lifecycle}`;
      copy.append(status, code, title, idText, meta);
      g.append(copy);
      g.addEventListener("click", (event) => { event.stopPropagation(); selectFact("node", id); });
      g.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") selectFact("node", id); });
      root.append(g);
    });

    root.setAttribute("transform", `translate(${state.panX} ${state.panY}) scale(${state.zoom})`);
    updateCanvasExtent();
    els.loading.hidden = true;
    state.layout = layout;
    renderLedger();
  }

  function renderLedger() {
    els.ledger.replaceChildren();
    state.visibleNodes.forEach((node) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "ledger-item";
      button.innerHTML = `<b>${escapeHtml(node.code)}</b><span><strong>${escapeHtml(node.title)}</strong><small>${escapeHtml(node.status)} · ${escapeHtml(node.primary_subsystem)}</small></span>`;
      button.addEventListener("click", () => selectFact("node", node.id));
      els.ledger.append(button);
    });
    state.visibleEdges.forEach((edge) => {
      const item = document.createElement("div");
      item.className = `ledger-edge ${edge.kind}`;
      item.textContent = `${nodeById(edge.source)?.code} → ${nodeById(edge.target)?.code} · ${edge.label}`;
      els.ledger.append(item);
    });
  }

  function selectFact(type, id) {
    state.selected = { type, id };
    document.querySelectorAll(".selected").forEach((item) => item.classList.remove("selected"));
    const selected = document.querySelector(type === "node" ? `[data-node-id="${CSS.escape(id)}"]` : `[data-edge-id="${CSS.escape(id)}"]`);
    selected?.classList.add("selected");
    if (type === "node") {
      const node = nodeById(id);
      els.inspectorBody.innerHTML = `<h3>${escapeHtml(node.code)} · ${escapeHtml(node.title)}</h3><p class="sub">${escapeHtml(node.status)}</p><dl class="fact-list"><div><dt>任务 ID</dt><dd>${escapeHtml(node.id)}</dd></div><div><dt>生命周期</dt><dd>${escapeHtml(node.lifecycle)}</dd></div><div><dt>运行状态</dt><dd>${escapeHtml(node.runtime)}</dd></div><div><dt>证据状态</dt><dd>${escapeHtml(node.evidence)}</dd></div><div><dt>范围状态</dt><dd>${escapeHtml(node.scope)}</dd></div><div><dt>主模块</dt><dd>${escapeHtml(node.primary_subsystem)}</dd></div><div><dt>系列</dt><dd>${escapeHtml(node.series_id || "无")}</dd></div><div><dt>Program / Phase</dt><dd>${escapeHtml([node.program_id, node.phase_id].filter(Boolean).join(" / ") || "无")}</dd></div></dl>`;
    } else {
      const edge = state.visibleEdges.find((item) => item.id === id);
      els.inspectorBody.innerHTML = `<h3>${escapeHtml(edge.label)}</h3><p class="sub">记录方向与屏幕阅读方向分开显示</p><dl class="fact-list"><div><dt>关系 ID</dt><dd>${escapeHtml(edge.id)}</dd></div><div><dt>类型</dt><dd>${escapeHtml(edge.kind)}</dd></div><div><dt>确定性</dt><dd>${escapeHtml(edge.certainty)}</dd></div><div><dt>屏幕方向</dt><dd>${escapeHtml(nodeById(edge.source)?.code)} → ${escapeHtml(nodeById(edge.target)?.code)}</dd></div><div><dt>布局职责</dt><dd>ELK 坐标／正交线路／标签</dd></div></dl>`;
    }
    els.inspector.classList.add("open");
  }

  function closeInspector() {
    state.selected = null;
    document.querySelectorAll(".selected").forEach((item) => item.classList.remove("selected"));
    els.inspector.classList.remove("open");
    els.inspectorBody.innerHTML = '<p class="empty-copy">选择任务卡片或关系线，查看 Orrery 输入事实与 ELK 几何输出。</p>';
  }

  function rectOverlap(a, b, inset = 0.01) {
    return a.x + inset < b.x + b.width && a.x + a.width - inset > b.x && a.y + inset < b.y + b.height && a.y + a.height - inset > b.y;
  }

  function segmentHitsRect(a, b, rect) {
    if (a.x === b.x) return a.x > rect.x && a.x < rect.x + rect.width && Math.max(Math.min(a.y, b.y), rect.y) < Math.min(Math.max(a.y, b.y), rect.y + rect.height);
    if (a.y === b.y) return a.y > rect.y && a.y < rect.y + rect.height && Math.max(Math.min(a.x, b.x), rect.x) < Math.min(Math.max(a.x, b.x), rect.x + rect.width);
    return false;
  }

  function segmentIntersection(a, b, c, d) {
    const verticalA = a.x === b.x;
    const verticalB = c.x === d.x;
    if (verticalA === verticalB) return false;
    const v1 = verticalA ? [a, b] : [c, d];
    const h1 = verticalA ? [c, d] : [a, b];
    const x = v1[0].x;
    const y = h1[0].y;
    return x > Math.min(h1[0].x, h1[1].x) && x < Math.max(h1[0].x, h1[1].x) && y > Math.min(v1[0].y, v1[1].y) && y < Math.max(v1[0].y, v1[1].y);
  }

  function geometryReport(layout, elapsedMs) {
    const abs = absoluteLayout(layout);
    const nodeRects = [...abs.nodes.entries()].filter(([id]) => !id.includes("overflow+")).map(([id, node]) => ({ id, x: node.absX, y: node.absY, width: node.width, height: node.height, ancestry: node.ancestry }));
    const groupRects = [...abs.groups.entries()].map(([id, group]) => ({ id, x: group.absX, y: group.absY, width: group.width, height: group.height, ancestry: group.ancestry }));
    const nodeNodeOverlaps = [];
    nodeRects.forEach((a, index) => nodeRects.slice(index + 1).forEach((b) => { if (rectOverlap(a, b)) nodeNodeOverlaps.push([a.id, b.id]); }));
    const containerExternalNodeOverlaps = [];
    groupRects.forEach((group) => nodeRects.forEach((node) => { if (!node.ancestry.includes(group.id) && rectOverlap(group, node)) containerExternalNodeOverlaps.push([group.id, node.id]); }));
    const edgeById = new Map(state.visibleEdges.map((edge) => [edge.id, edge]));
    const labelNodeOverlaps = [];
    const routeNodeIntersections = [];
    const routes = [];
    const stretches = [];
    (layout.edges || []).forEach((elkEdge) => {
      const edge = edgeById.get(elkEdge.id);
      if (!edge) return;
      (elkEdge.labels || []).forEach((label) => {
        if (!Number.isFinite(label.x) || !Number.isFinite(label.y)) return;
        const rect = { x: label.x, y: label.y, width: label.width, height: label.height };
        nodeRects.forEach((node) => { if (rectOverlap(rect, node)) labelNodeOverlaps.push([elkEdge.id, node.id]); });
      });
      (elkEdge.sections || []).forEach((section, sectionIndex) => {
        const points = pointsForSection(section);
        routes.push({ edgeId: elkEdge.id, sectionIndex, points });
        let length = 0;
        for (let index = 0; index < points.length - 1; index += 1) {
          const a = points[index];
          const b = points[index + 1];
          length += Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
          nodeRects.filter((node) => node.id !== edge.source && node.id !== edge.target).forEach((node) => { if (segmentHitsRect(a, b, node)) routeNodeIntersections.push([elkEdge.id, node.id]); });
        }
        const direct = Math.max(1, Math.abs(points[0].x - points.at(-1).x) + Math.abs(points[0].y - points.at(-1).y));
        stretches.push({ edge_id: elkEdge.id, ratio: Number((length / direct).toFixed(3)), route_length: Number(length.toFixed(2)) });
      });
    });
    const unmarkedCrossings = [];
    routes.forEach((routeA, index) => routes.slice(index + 1).forEach((routeB) => {
      const edgeA = edgeById.get(routeA.edgeId);
      const edgeB = edgeById.get(routeB.edgeId);
      if (new Set([edgeA.source, edgeA.target, edgeB.source, edgeB.target]).size < 4) return;
      for (let a = 0; a < routeA.points.length - 1; a += 1) for (let b = 0; b < routeB.points.length - 1; b += 1) if (segmentIntersection(routeA.points[a], routeA.points[a + 1], routeB.points[b], routeB.points[b + 1])) unmarkedCrossings.push([routeA.edgeId, routeB.edgeId]);
    }));
    const externalResources = performance.getEntriesByType("resource").map((entry) => entry.name).filter((url) => new URL(url).origin !== location.origin);
    return {
      view: state.view,
      layers: { ...state.layers },
      input_full_card_ids: state.visibleNodes.map((node) => node.id),
      input_boundary_ids: state.visibleBoundaries.map((boundary) => boundary.id),
      input_edge_ids: state.visibleEdges.map((edge) => edge.id),
      output_bounds: { width: Number(layout.width.toFixed(2)), height: Number(layout.height.toFixed(2)) },
      layout_time_ms: Number(elapsedMs.toFixed(2)),
      node_node_overlaps: nodeNodeOverlaps,
      container_external_node_overlaps: containerExternalNodeOverlaps,
      label_node_overlaps: labelNodeOverlaps,
      route_node_intersections: routeNodeIntersections,
      unmarked_crossings: unmarkedCrossings,
      route_stretch: stretches,
      external_network_requests: externalResources,
      post_processed_coordinates: false,
      engine_owned_fact_set_changes: false,
    };
  }

  async function layoutCurrentView() {
    els.loading.hidden = false;
    closeInspector();
    const { view, nodes, edges, boundaries } = visibleFactSet();
    state.visibleNodes = nodes;
    state.visibleEdges = edges;
    state.visibleBoundaries = boundaries;
    els.title.textContent = view.label;
    els.description.textContent = view.description;
    els.context.hidden = !["project_structure", "w_compound"].includes(state.view);
    document.querySelectorAll(".project-control").forEach((item) => { item.hidden = state.view !== "project_structure"; });
    document.querySelectorAll(".external-control").forEach((item) => { item.hidden = state.view !== "w_compound"; });
    els.factCount.textContent = `${nodes.length} tasks · ${edges.length} relations`;
    els.layoutStatus.textContent = "ELK 正在布局";
    const start = performance.now();
    const layout = state.view === "w_compound" && !state.layers.external
      ? await layoutWPhaseMultiples(view)
      : await new ELK().layout(buildGraph(nodes, edges, boundaries, view.groups || []));
    const elapsed = performance.now() - start;
    const report = geometryReport(layout, elapsed);
    state.reports[state.view] = report;
    window.__GX2_REPORT__ = state.reports;
    window.__GX2_FIXTURE__ = state.fixture;
    document.getElementById("gx2-report").textContent = JSON.stringify(state.reports);
    render(layout);
    els.layoutStatus.textContent = `ELK ${elapsed.toFixed(1)} ms · ${layout.width.toFixed(0)}×${layout.height.toFixed(0)}`;
  }

  function setZoom(next, anchorX = els.viewport.clientWidth / 2, anchorY = els.viewport.clientHeight / 2) {
    const bounded = Math.max(.3, Math.min(2, next));
    const beforeX = (anchorX - state.panX) / state.zoom;
    const beforeY = (anchorY - state.panY) / state.zoom;
    state.zoom = bounded;
    state.panX = anchorX - beforeX * bounded;
    state.panY = anchorY - beforeY * bounded;
    els.zoomValue.value = `${Math.round(bounded * 100)}%`;
    document.querySelector(".graph-root")?.setAttribute("transform", `translate(${state.panX} ${state.panY}) scale(${state.zoom})`);
    updateCanvasExtent();
  }

  function updateCanvasExtent() {
    if (!state.layout) return;
    els.svg.setAttribute("width", Math.max(els.viewport.clientWidth, Math.ceil(state.layout.width * state.zoom + 44)));
    els.svg.setAttribute("height", Math.max(els.viewport.clientHeight, Math.ceil(state.layout.height * state.zoom + 44)));
  }

  function fitGraph() {
    if (!state.layout) return;
    const padding = 34;
    const next = Math.min(1, (els.viewport.clientWidth - padding * 2) / state.layout.width, (els.viewport.clientHeight - padding * 2) / state.layout.height);
    state.zoom = Math.max(.3, next);
    state.panX = Math.max(padding, (els.viewport.clientWidth - state.layout.width * state.zoom) / 2);
    state.panY = Math.max(padding, (els.viewport.clientHeight - state.layout.height * state.zoom) / 2);
    setZoom(state.zoom, 0, 0);
  }

  function bindControls() {
    els.tabs.forEach((tab) => tab.addEventListener("click", async () => {
      state.view = tab.dataset.view;
      state.zoom = 1; state.panX = 22; state.panY = 22;
      els.zoomValue.value = "100%";
      els.tabs.forEach((item) => item.setAttribute("aria-selected", String(item === tab)));
      await layoutCurrentView();
    }));
    els.layerChecks.forEach((input) => input.addEventListener("change", async () => {
      state.layers[input.dataset.layer] = input.checked;
      state.zoom = 1; state.panX = 22; state.panY = 22;
      await layoutCurrentView();
    }));
    document.querySelector('[data-zoom="out"]').addEventListener("click", () => setZoom(state.zoom - .1));
    document.querySelector('[data-zoom="in"]').addEventListener("click", () => setZoom(state.zoom + .1));
    document.querySelector('[data-zoom="fit"]').addEventListener("click", fitGraph);
    els.viewport.addEventListener("wheel", (event) => {
      if (!event.ctrlKey) return;
      event.preventDefault();
      const rect = els.viewport.getBoundingClientRect();
      setZoom(state.zoom + (event.deltaY < 0 ? .1 : -.1), event.clientX - rect.left, event.clientY - rect.top);
    }, { passive: false });
    els.viewport.addEventListener("pointerdown", (event) => {
      if (event.target.closest(".node-hit,.edge-hit")) return;
      state.dragging = { x: event.clientX, y: event.clientY, panX: state.panX, panY: state.panY };
      els.viewport.setPointerCapture(event.pointerId);
    });
    els.viewport.addEventListener("pointermove", (event) => {
      if (!state.dragging) return;
      state.panX = state.dragging.panX + event.clientX - state.dragging.x;
      state.panY = state.dragging.panY + event.clientY - state.dragging.y;
      document.querySelector(".graph-root")?.setAttribute("transform", `translate(${state.panX} ${state.panY}) scale(${state.zoom})`);
    });
    els.viewport.addEventListener("pointerup", () => { state.dragging = null; });
    els.svg.addEventListener("click", closeInspector);
    els.closeInspector.addEventListener("click", closeInspector);
  }

  async function init() {
    if (typeof ELK !== "function") throw new Error("Local ELK bundle was not loaded");
    const response = await fetch("fixture.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Fixture load failed: ${response.status}`);
    state.fixture = await response.json();
    bindControls();
    await layoutCurrentView();
  }

  init().catch((error) => {
    console.error(error);
    els.loading.textContent = `布局失败：${error.message}`;
    els.layoutStatus.textContent = "ELK 布局失败";
  });
})();
