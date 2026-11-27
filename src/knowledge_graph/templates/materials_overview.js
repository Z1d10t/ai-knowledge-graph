/* Materials terminology knowledge graph — delivery page.
 *
 * Views: 全库大图 (community map) · 全部关系 (filtered) · 类型汇总 (type ring) · 术语邻域.
 * Data: data/*.json, evidence shards fetched per paper. No network, no CDN.
 */
(function () {
  "use strict";

  // ------------------------------------------------------------------ i18n
  const I18N = {
    zh: {
      title: "材料专业术语知识图谱",
      subtitle: "{papers} 篇论文 · {relations} 条关系 · 从术语进入证据",
      searchPlaceholder: "搜术语 / 别名 / 缩写 / 中文（如 ALD、4Cl-BZS、甲酸根）",
      viewGraph: "全库大图", viewFull: "全部关系", viewType: "类型汇总",
      download: "下载三元组", exportPng: "导出 PNG",
      communities: "社区", types: "类型", filters: "筛选",
      family: "谓词族", paper: "论文", showAnomalies: "显示方向异常",
      clearFilters: "清除筛选", allPapers: "全部论文", allFamilies: "全部谓词族",
      footNote: "颜色 = 社区；虚线圆与标题 = 类型区域；点击节点查看关系与证据。",
      totalRelations: "全库关系", filteredRelations: "当前筛选", drawnRelations: "当前已绘制",
      details: "详情", panelHint: "点击图中的术语、关系或搜索结果查看详情与原文证据。",
      footerNote: "证据按论文分片加载 · 页面离线运行",
      graphLabel: "全库大图", fullLabel: "全部关系", typeLabel: "类型汇总", nbLabel: "术语邻域",
      nodeId: "节点 ID", papers: "论文数", relations: "关系数", mentions: "提及数",
      aliases: "别名 / 表面形式", outEdges: "出边", inEdges: "入边",
      expandHere: "以它为中心展开", expandMore: "再展开一批", locateFull: "在全库大图中定位",
      evidence: "原文证据", openPaper: "打开论文 Markdown", locateMissing: "定位缺失",
      directionFlag: "方向待复核", noLineFlag: "无行号", quality: "质量",
      zhLabel: "中文建议", community: "社区", viewAll: "全部",
      relationDetail: "关系详情", predicate: "谓词", direction: "方向", typesEnds: "两端类型",
      paperField: "论文", subject: "主语", object: "宾语", loading: "加载中…",
      noEvidence: "没有找到这条关系的证据分片。", quoteEmpty: "（原文引文为空）",
      context: "上下文", searchEmpty: "没有找到「{q}」。可尝试完整术语、缩写或中文建议标签。",
      searchHint: "输入术语、缩写或中文名",
      graphHint: "滚轮缩放 · 拖拽平移 · 点击节点看详情 · 双击进入邻域；颜色 = 社区，虚线圆 = 类型区域。",
      typeHint: "点击类型节点进入该范围的术语与关系。",
      nbHint: "邻域：{nodes} 个节点 / {edges} 条关系（上限 {maxNodes}/{maxEdges}）· 点击节点继续 · 双击设为起点。",
      noRelations: "暂无", exportTip: "已导出 {name}", exportFail: "导出失败：{msg}",
      onlySearch: "仅检索", instanceMember: "所属论文", resetView: "重置视图",
      markedAnomaly: "方向异常", markedNoLine: "无行号证据", keepAtLeastOne: "至少保留一个类型",
      relationCount: "{n} 条",
    },
    en: {
      title: "Materials Terminology Knowledge Graph",
      subtitle: "{papers} papers · {relations} relations · trace from a term to its evidence",
      searchPlaceholder: "Search term / alias / abbreviation / Chinese (e.g. ALD, 4Cl-BZS, formate)",
      viewGraph: "Full graph", viewFull: "All relations", viewType: "Type summary",
      download: "Download triples", exportPng: "Export PNG",
      communities: "Communities", types: "Types", filters: "Filters",
      family: "Predicate family", paper: "Paper", showAnomalies: "Show direction flags",
      clearFilters: "Clear filters", allPapers: "All papers", allFamilies: "All families",
      footNote: "Colour = community; dashed discs and titles = type regions; click a node for relations and evidence.",
      totalRelations: "All relations", filteredRelations: "Filtered", drawnRelations: "Drawn",
      details: "Details", panelHint: "Click a term, relation or search result to see details and evidence.",
      footerNote: "Evidence shards load per paper · fully offline",
      graphLabel: "Full graph", fullLabel: "All relations", typeLabel: "Type summary", nbLabel: "Neighbourhood",
      nodeId: "Node ID", papers: "Papers", relations: "Relations", mentions: "Mentions",
      aliases: "Aliases / surface forms", outEdges: "Outgoing", inEdges: "Incoming",
      expandHere: "Explore from here", expandMore: "Expand more", locateFull: "Locate in full graph",
      evidence: "Evidence", openPaper: "Open paper Markdown", locateMissing: "line not located",
      directionFlag: "direction flagged", noLineFlag: "no line", quality: "Quality",
      zhLabel: "Chinese label", community: "Community", viewAll: "All",
      relationDetail: "Relation", predicate: "Predicate", direction: "Direction", typesEnds: "End types",
      paperField: "Paper", subject: "Subject", object: "Object", loading: "Loading…",
      noEvidence: "No evidence shard found for this relation.", quoteEmpty: "(empty quote)",
      context: "Context", searchEmpty: "No match for \"{q}\". Try the full term, an abbreviation or a Chinese label.",
      searchHint: "Type a term, abbreviation or Chinese name",
      graphHint: "Wheel to zoom · drag to pan · click a node for details · double-click for its neighbourhood. Colour = community, dashed disc = type region.",
      typeHint: "Click a type node to enter that range of terms and relations.",
      nbHint: "Neighbourhood: {nodes} nodes / {edges} edges (cap {maxNodes}/{maxEdges}) · click to continue · double-click to recentre.",
      noRelations: "None", exportTip: "Saved {name}", exportFail: "Export failed: {msg}",
      onlySearch: "search only", instanceMember: "Paper", resetView: "Reset view",
      markedAnomaly: "direction flagged", markedNoLine: "no evidence line", keepAtLeastOne: "Keep at least one type",
      relationCount: "{n} relations",
    },
  };
  const LANG_KEY = "materials-kg-lang";
  let lang = localStorage.getItem(LANG_KEY) === "en" ? "en" : "zh";
  const t = (key, vars) => {
    const text = (I18N[lang] && I18N[lang][key]) || I18N.zh[key] || key;
    return vars ? text.replace(/\{(\w+)\}/g, (m, k) => (vars[k] != null ? vars[k] : m)) : text;
  };

  // ------------------------------------------------------------------ helpers
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => Number(n || 0).toLocaleString("en-US");
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
  const GREEK = { "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon", "θ": "theta",
    "λ": "lambda", "μ": "u", "ω": "omega", "π": "pi", "σ": "sigma" };
  const SUB = "₀₁₂₃₄₅₆₇₈₉";
  const SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹";
  function searchKey(text) {
    let s = String(text == null ? "" : text).toLowerCase();
    for (const k of Object.keys(GREEK)) s = s.split(k).join(GREEK[k]);
    s = s.replace(/[₀-₉]/g, (d) => String(SUB.indexOf(d)));
    s = s.replace(/[⁰-⁹]/g, (d) => String(SUP.indexOf(d)));
    s = s.replace(/[−–—]/g, "-").replace(/[×·⋅]/g, "x");
    return s.replace(/[^a-z0-9\u3400-\u9fff]+/g, "");
  }
  function toast(message) {
    const node = $("toast");
    node.textContent = message;
    node.classList.remove("hidden");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => node.classList.add("hidden"), 2600);
  }

  const state = {
    meta: null, nodes: null, edges: null, relids: null, overview: null,
    adjacency: null, searchKeys: null, communities: null, regions: null, patches: null,
    communityColor: {}, typeColor: {}, nodeColor: [], nodeTypeLabel: [],
    evidenceCache: new Map(),
    view: "graph",
    filters: { types: new Set(), family: "", paper: "", anomalies: false, community: -1 },
    filtered: [], drawn: 0,
    viewport: { scale: 1, tx: 0, ty: 0 },
    screen: new Float32Array(0),
    hover: -1, selected: null,
    network: null, visNodes: null, visEdges: null,
    nbStart: null, nbNodes: 150, nbEdges: 300,
    raf: 0, exportMode: false,
  };

  // ------------------------------------------------------------------ data
  async function fetchJSON(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) throw new Error(path + " -> " + response.status);
    return response.json();
  }

  async function boot() {
    try {
      const query = new URLSearchParams(location.search);
      const queryLang = query.get("lang");
      if (queryLang === "en" || queryLang === "zh") {
        lang = queryLang;
        localStorage.setItem(LANG_KEY, lang);
      }
      const [meta, nodes, edges, relids, overview, adjacency, search, communities] = await Promise.all([
        fetchJSON("data/meta.json"),
        fetchJSON("data/nodes.json"),
        fetchJSON("data/edges.json"),
        fetchJSON("data/relids.json"),
        fetchJSON("data/overview.json"),
        fetchJSON("data/adjacency.json"),
        fetchJSON("data/search.json"),
        fetchJSON("data/communities.json"),
      ]);
      state.meta = meta;
      state.nodes = nodes;
      state.edges = edges;
      state.relids = relids;
      state.overview = overview;
      state.adjacency = adjacency;
      state.searchKeys = search.k || search;
      state.communities = communities.list || [];
      state.regions = communities.regions || [];
      state.patches = communities.patches || [];
      state.communityColor = {};
      for (const community of state.communities) state.communityColor[community.id] = community.color;
      state.typeColor = meta.types.map((type) => type.color);
      state.screen = new Float32Array(nodes.length * 2);
      state.nodeColor = new Array(nodes.length);
      for (let i = 0; i < nodes.length; i += 1) {
        const community = nodes[i][10];
        state.nodeColor[i] = (community >= 0 && state.communityColor[community])
          ? state.communityColor[community] : meta.types[nodes[i][2]].color;
      }
      state.filters.types = new Set(meta.types.map((type) => type.id));
      $("count-total").textContent = fmt(meta.relations);
      $("count-filtered").textContent = fmt(meta.relations);
      $("count-drawn").textContent = fmt(meta.relations);
      state.exportMode = new URLSearchParams(location.search).get("export") === "1";
      if (state.exportMode) document.body.classList.add("export-mode");
      applyLanguage();
      buildSidebar();
      bindEvents();
      showGraph(true);
      setHint(t("graphHint"));
      applyHash();
    } catch (error) {
      const footer = $("footer-meta");
      if (footer) footer.textContent = "data load failed: " + error.message;
      console.error(error);
    }
  }

  // ------------------------------------------------------------------ i18n application
  function applyLanguage() {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach((element) => {
      const key = element.dataset.i18n;
      if (I18N[lang][key]) element.textContent = I18N[lang][key];
    });
    const input = $("search-input");
    if (input) input.placeholder = t("searchPlaceholder");
    $("btn-lang").textContent = lang === "zh" ? "EN" : "中文";
    const subtitle = document.querySelector(".brand .subtitle");
    if (subtitle && state.meta) {
      subtitle.textContent = t("subtitle", {
        papers: fmt(state.meta.papers), relations: fmt(state.meta.relations),
      });
    }
    $("footer-meta").textContent = state.meta
      ? `${fmt(state.meta.papers)} papers · ${fmt(state.meta.concepts)} concepts · ` +
        `${fmt(state.meta.instances)} instances · ${fmt(state.meta.relations)} relations · ` +
        `${fmt(state.meta.in_generated || state.meta.generated)}`
      : "";
    if (state.meta) $("footer-meta").textContent =
      `${fmt(state.meta.papers)} ${lang === "zh" ? "篇论文" : "papers"} · ${fmt(state.meta.concepts)} ` +
      `${lang === "zh" ? "个概念" : "concepts"} · ${fmt(state.meta.instances)} ${lang === "zh" ? "个实例" : "instances"} · ` +
      `${fmt(state.meta.relations)} ${lang === "zh" ? "条关系" : "relations"} · ${state.meta.generated}`;
    if (state.meta) buildLegend();
    updateViewLabel();
  }

  function typeLabel(typeIndex) {
    const type = state.meta.types[typeIndex];
    if (!type) return "";
    return lang === "zh" ? (type.label_zh || type.id) : (type.label_en || type.id);
  }
  function familyLabel(family) {
    if (!family) return "";
    if (typeof family === "object") {
      return lang === "zh" ? (family.label_zh || family.id) : (family.label_en || family.id);
    }
    const entry = state.meta.families.find((item) => item.id === family);
    if (!entry) return family;
    return lang === "zh" ? (entry.label_zh || entry.id) : (entry.label_en || entry.id);
  }

  function updateViewLabel() {
    const label = $("view-label");
    if (!label) return;
    label.textContent = state.view === "graph"
      ? (state.filters.community >= 0 ? `${t("community")} · ${state.communities[state.filters.community] ? state.communities[state.filters.community].label : ""}` : t("graphLabel"))
      : state.view === "type" ? t("typeLabel")
      : state.view === "neighbourhood" ? t("nbLabel") : t("fullLabel");
    $("btn-graph").classList.toggle("primary", state.view === "graph");
    $("btn-type").classList.toggle("primary", state.view === "type");
  }

  // ------------------------------------------------------------------ sidebar
  function buildSidebar() {
    const list = $("community-list");
    list.innerHTML = "";
    const top = state.communities.slice(0, 14);
    $("community-count").textContent = fmt(state.communities.length);
    const all = document.createElement("div");
    all.className = "community" + (state.filters.community < 0 ? " active" : "");
    all.innerHTML = `<span class="dot" style="background:#c3ccd6"></span>
      <span class="name">${esc(t("viewAll"))}</span>`;
    all.onclick = () => { state.filters.community = -1; renderGraph(); buildSidebar(); updateViewLabel(); };
    list.appendChild(all);
    top.forEach((community) => {
      const row = document.createElement("div");
      row.className = "community" + (state.filters.community === community.id ? " active" : "");
      row.title = community.label;
      row.innerHTML = `<span class="dot" style="background:${esc(community.color)}"></span>
        <span class="name">${esc(short(community.label, 26))}</span>
        <span class="size">${fmt(community.size)}</span>`;
      row.onclick = () => {
        state.filters.community = community.id;
        state.view = "graph";
        renderGraph();
        buildSidebar();
        updateViewLabel();
        toast(`${t("community")}: ${community.label}`);
      };
      list.appendChild(row);
    });

    const typeList = $("type-list");
    typeList.innerHTML = "";
    state.meta.types.forEach((type, index) => {
      const chip = document.createElement("span");
      chip.className = "type-chip" + (state.filters.types.has(type.id) ? "" : " off");
      chip.innerHTML = `<span class="dot" style="background:${esc(type.color)}"></span>
        <span>${esc(lang === "zh" ? type.label_zh : type.label_en)}</span>`;
      chip.onclick = () => {
        if (state.filters.types.has(type.id)) {
          if (state.filters.types.size === 1) { toast(t("keepAtLeastOne")); return; }
          state.filters.types.delete(type.id);
        } else {
          state.filters.types.add(type.id);
        }
        chip.classList.toggle("off", !state.filters.types.has(type.id));
        state.view = "graph";
        renderGraph();
        updateViewLabel();
      };
      typeList.appendChild(chip);
    });

    const familySelect = $("family-select");
    familySelect.innerHTML = `<option value="">${esc(t("allFamilies"))}</option>` +
      state.meta.families.map((family) =>
        `<option value="${esc(family.id)}">${esc(lang === "zh" ? family.label_zh : family.label_en)}</option>`
      ).join("");
    familySelect.value = state.filters.family;
    const paperSelect = $("paper-select");
    if (!paperSelect.options.length) {
      paperSelect.innerHTML = `<option value="">${esc(t("allPapers"))}</option>` +
        state.meta.paper_ids.map((id) =>
          `<option value="${esc(id)}">${esc(id.slice(0, 3))} · ${esc(short(state.meta.papers_meta[id] ? state.meta.papers_meta[id].title : id, 54))}</option>`
        ).join("");
    }
    paperSelect.value = state.filters.paper;
    $("anomaly-toggle").checked = state.filters.anomalies;
  }

  function buildLegend() {
    const legend = $("legend");
    legend.innerHTML = state.meta.types.map((type) =>
      `<span class="item"><span class="dot" style="background:${esc(type.color)}"></span>${
        esc(lang === "zh" ? type.label_zh : type.label_en)}</span>`
    ).join("");
  }

  // ------------------------------------------------------------------ filtering
  function computeFiltered() {
    const typeSet = state.filters.types;
    const allTypes = typeSet.size === state.meta.types.length;
    const family = state.filters.family;
    const paper = state.filters.paper;
    const allowAnomaly = state.filters.anomalies;
    const community = state.filters.community;
    const paperIndex = paper ? state.meta.paper_ids.indexOf(paper) : -1;
    const familyIndex = family ? state.meta.families.findIndex((item) => item.id === family) : -1;
    const result = [];
    for (let i = 0; i < state.edges.length; i += 1) {
      const row = state.edges[i];
      if (!allowAnomaly && (row[6] & 1)) continue;
      if (paperIndex >= 0 && row[5] !== paperIndex) continue;
      if (familyIndex >= 0 && row[4] !== familyIndex) continue;
      const subject = state.nodes[row[1]];
      const object = state.nodes[row[2]];
      if (community >= 0 && subject[10] !== community && object[10] !== community) continue;
      if (!allTypes && !typeSet.has(state.meta.types[subject[2]].id)
          && !typeSet.has(state.meta.types[object[2]].id)) continue;
      result.push(i);
    }
    return result;
  }

  // ------------------------------------------------------------------ graph view
  function showGraph(resetFilters) {
    if (resetFilters) {
      state.filters = { types: new Set(state.meta.types.map((type) => type.id)),
        family: "", paper: "", anomalies: false, community: -1 };
      buildSidebar();
    }
    state.view = "graph";
    setView("graph");
    state.filtered = computeFiltered();
    fitView();
    renderGraph();
    updateViewLabel();
    setHint(t("graphHint"));
  }

  function setView(view) {
    $("graph-canvas").classList.toggle("hidden", view !== "graph");
    $("overlay-canvas").classList.toggle("hidden", view !== "graph");
    $("overview-canvas").classList.toggle("hidden", view !== "type");
    $("network").classList.toggle("hidden", view !== "neighbourhood");
    if (view !== "graph") $("tooltip").classList.add("hidden");
  }

  function canvasSize(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth, height = canvas.clientHeight;
    if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
      canvas.width = Math.max(1, Math.round(width * dpr));
      canvas.height = Math.max(1, Math.round(height * dpr));
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width, height };
  }

  function fitView() {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const edgeIndex of state.filtered) {
      const row = state.edges[edgeIndex];
      for (const nodeIndex of [row[1], row[2]]) {
        const node = state.nodes[nodeIndex];
        if (node[8] < minX) minX = node[8];
        if (node[8] > maxX) maxX = node[8];
        if (node[9] < minY) minY = node[9];
        if (node[9] > maxY) maxY = node[9];
      }
    }
    if (!isFinite(minX)) { minX = 0; minY = 0; maxX = 1; maxY = 1; }
    const pad = 120;
    minX -= pad; minY -= pad; maxX += pad; maxY += pad;
    state.world = { minX, minY, w: Math.max(1, maxX - minX), h: Math.max(1, maxY - minY) };
    const canvas = $("graph-canvas");
    const topPad = state.exportMode ? 110 : 0;
    const bottomPad = state.exportMode ? 48 : 0;
    const availableHeight = Math.max(80, canvas.clientHeight - topPad - bottomPad);
    const scale = Math.min(canvas.clientWidth / state.world.w, availableHeight / state.world.h) * 0.96;
    state.viewport.scale = scale;
    state.viewport.tx = (canvas.clientWidth - state.world.w * scale) / 2 - minX * scale;
    state.viewport.ty = topPad + (availableHeight - state.world.h * scale) / 2 - minY * scale;
  }

  function toScreen(x, y) {
    return [x * state.viewport.scale + state.viewport.tx, y * state.viewport.scale + state.viewport.ty];
  }

  function renderGraph() {
    const { ctx, width, height } = canvasSize($("graph-canvas"));
    ctx.clearRect(0, 0, width, height);
    const scale = state.viewport.scale;
    const used = new Set();
    for (const edgeIndex of state.filtered) {
      const row = state.edges[edgeIndex];
      used.add(row[1]);
      used.add(row[2]);
    }
    state.used = used;

    // soft type-region discs
    for (const region of state.regions) {
      const [x, y] = toScreen(region.cx, region.cy);
      const r = region.r * scale;
      if (r < 6 || x + r < 0 || y + r < 0 || x - r > width || y - r > height) continue;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = hexToRgba(region.color, 0.05);
      ctx.fill();
      ctx.strokeStyle = hexToRgba(region.color, 0.16);
      ctx.lineWidth = 1.2;
      ctx.setLineDash([4, 6]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // edges, coloured by the subject type (soft, batched per type)
    ctx.lineWidth = 0.75;
    const edgeGroups = new Map();
    for (const edgeIndex of state.filtered) {
      const row = state.edges[edgeIndex];
      const typeIndex = state.nodes[row[1]][2];
      let bucket = edgeGroups.get(typeIndex);
      if (!bucket) { bucket = []; edgeGroups.set(typeIndex, bucket); }
      bucket.push(row);
    }
    for (const [typeIndex, rows] of edgeGroups) {
      ctx.strokeStyle = hexToRgba(state.meta.types[typeIndex].color, 0.13);
      ctx.beginPath();
      for (const row of rows) {
        const subject = state.nodes[row[1]];
        const object = state.nodes[row[2]];
        const x1 = subject[8] * scale + state.viewport.tx;
        const y1 = subject[9] * scale + state.viewport.ty;
        const x2 = object[8] * scale + state.viewport.tx;
        const y2 = object[9] * scale + state.viewport.ty;
        if ((x1 < -50 && x2 < -50) || (x1 > width + 50 && x2 > width + 50)
            || (y1 < -50 && y2 < -50) || (y1 > height + 50 && y2 > height + 50)) continue;
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
      }
      ctx.stroke();
    }

    // nodes
    for (const nodeIndex of used) {
      const node = state.nodes[nodeIndex];
      const [x, y] = toScreen(node[8], node[9]);
      state.screen[nodeIndex * 2] = x;
      state.screen[nodeIndex * 2 + 1] = y;
      if (x < -8 || y < -8 || x > width + 8 || y > height + 8) continue;
      const radius = 1.7 + Math.min(4.2, Math.log1p(node[6]) * 0.75);
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fillStyle = state.nodeColor[nodeIndex];
      ctx.globalAlpha = node[3] === "clean" ? 0.92 : 0.55;
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    // labels: region titles first, then the busiest hubs, then community patches
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const placed = [];
    const overlaps = (rect) => placed.some((other) =>
      rect.x < other.x + other.w && rect.x + rect.w > other.x
      && rect.y < other.y + other.h && rect.y + rect.h > other.y);
    const paintLabel = (text, color, size, cx, cy, strong, alpha) => {
      ctx.font = (strong ? "600 " : "500 ") + size + "px 'Segoe UI', 'Microsoft YaHei', sans-serif";
      const w = ctx.measureText(text).width + 12;
      const h = size + 7;
      const rect = { x: cx - w / 2, y: cy - h / 2, w, h };
      if (overlaps(rect)) return false;
      placed.push(rect);
      ctx.fillStyle = "rgba(255,255,255," + (alpha == null ? 0.92 : alpha) + ")";
      roundRect(ctx, rect.x, rect.y, w, h, 5);
      ctx.fill();
      ctx.strokeStyle = hexToRgba(color, 0.28);
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = color;
      ctx.fillText(text, cx, cy);
      return true;
    };
    for (const region of state.regions) {
      const [x, y] = toScreen(region.cx, region.cy);
      const label = (lang === "zh" ? region.label_zh : region.label_en) + " " + fmt(region.count);
      const size = Math.max(12, Math.min(19, 10 + region.r * scale * 0.055));
      const top = Math.max(size + 8, y - region.r * scale - 24);
      paintLabel(label, region.color, size, x, top, true, 0.94);
    }
    // a few community patches as topical anchors, even at full-map zoom
    const patches = state.patches.slice().sort((a, b) => b.size - a.size);
    const patchLimit = scale > 0.3 ? 22 : 12;
    let patchDrawn = 0;
    for (const patch of patches) {
      if (patchDrawn >= patchLimit) break;
      if (patch.size < (scale > 0.3 ? 80 : 150)) continue;
      const [x, y] = toScreen(patch.cx, patch.cy);
      if (x < 30 || y < 30 || x > width - 30 || y > height - 30) continue;
      if (paintLabel(short(patch.label, 20), patch.color, 10.5, x, y, false, 0.78)) patchDrawn += 1;
    }
    const hubs = [];
    for (const nodeIndex of used) {
      if (state.nodes[nodeIndex][6] >= 4) hubs.push(nodeIndex);
    }
    hubs.sort((a, b) => state.nodes[b][6] - state.nodes[a][6]);
    const hubLimit = scale > 0.35 ? 80 : 16;
    for (const nodeIndex of hubs.slice(0, hubLimit)) {
      const node = state.nodes[nodeIndex];
      const [x, y] = toScreen(node[8], node[9]);
      if (x < 40 || y < 20 || x > width - 40 || y > height - 20) continue;
      paintLabel(short(node[1], 26), "#24313f", 10.5, x, y - 11, false, 0.66);
    }
    if (state.exportMode) {
      ctx.textAlign = "left";
      ctx.textBaseline = "alphabetic";
      ctx.fillStyle = "#16202b";
      ctx.font = "700 30px 'Segoe UI', 'Microsoft YaHei', sans-serif";
      ctx.fillText(lang === "zh" ? "材料专业术语知识图谱" : "Materials Terminology Knowledge Graph", 36, 58);
      ctx.font = "400 15px 'Segoe UI', 'Microsoft YaHei', sans-serif";
      ctx.fillStyle = "#5b6877";
      ctx.fillText(`${fmt(state.meta.papers)} ${lang === "zh" ? "篇论文" : "papers"} · ` +
        `${fmt(state.meta.concepts)} ${lang === "zh" ? "个概念" : "concepts"} · ` +
        `${fmt(state.meta.relations)} ${lang === "zh" ? "条关系" : "relations"} · ${state.meta.generated}`, 36, 86);
      let legendX = 36;
      const legendY = height - 26;
      ctx.font = "600 12px 'Segoe UI', 'Microsoft YaHei', sans-serif";
      ctx.fillStyle = "#8b96a3";
      const legendTitle = lang === "zh" ? "社区" : "Communities";
      ctx.fillText(legendTitle, legendX, legendY);
      legendX += ctx.measureText(legendTitle).width + 16;
      ctx.font = "500 12.5px 'Segoe UI', 'Microsoft YaHei', sans-serif";
      for (const community of state.communities.slice(0, 12)) {
        const label = short(community.label, 18);
        ctx.fillStyle = community.color;
        ctx.beginPath();
        ctx.arc(legendX, legendY - 4, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#33475b";
        ctx.fillText(label, legendX + 9, legendY);
        legendX += ctx.measureText(label).width + 26;
      }
    }
    state.drawn = state.filtered.length;
    $("count-drawn").textContent = fmt(state.drawn);
    $("count-filtered").textContent = fmt(state.filtered.length);
    updateViewLabel();
  }

  function roundRect(ctx, x, y, w, h, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + w - radius, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    ctx.lineTo(x + w, y + h - radius);
    ctx.quadraticCurveTo(x + w, y + h, x + w - radius, y + h);
    ctx.lineTo(x + radius, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
  }

  function hexToRgba(hex, alpha) {
    const value = String(hex || "#888888").replace("#", "");
    const r = parseInt(value.slice(0, 2), 16);
    const g = parseInt(value.slice(2, 4), 16);
    const b = parseInt(value.slice(4, 6), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  function short(text, limit) {
    const value = String(text == null ? "" : text);
    return value.length > limit ? value.slice(0, limit - 1) + "…" : value;
  }

  // ------------------------------------------------------------------ hover & interaction
  function nodeAt(screenX, screenY) {
    if (!state.used) return -1;
    const scale = state.viewport.scale;
    const threshold = Math.max(6, Math.min(14, 7 / Math.max(0.15, scale)));
    let best = -1, bestDistance = threshold * threshold;
    for (const nodeIndex of state.used) {
      const x = state.screen[nodeIndex * 2], y = state.screen[nodeIndex * 2 + 1];
      if (!isFinite(x)) continue;
      const dx = x - screenX, dy = y - screenY;
      const distance = dx * dx + dy * dy;
      if (distance < bestDistance) { bestDistance = distance; best = nodeIndex; }
    }
    return best;
  }

  function drawOverlay() {
    const { ctx, width, height } = canvasSize($("overlay-canvas"));
    ctx.clearRect(0, 0, width, height);
    const tooltip = $("tooltip");
    if (state.hover < 0) { tooltip.classList.add("hidden"); return; }
    const nodeIndex = state.hover;
    const node = state.nodes[nodeIndex];
    const scale = state.viewport.scale;
    const [x, y] = toScreen(node[8], node[9]);
    const neighbours = state.adjacency[nodeIndex] || [];
    ctx.fillStyle = "rgba(247,249,253,0.78)";
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = "rgba(47,111,219,0.55)";
    ctx.lineWidth = 1.1;
    for (const [relIndex, other] of neighbours) {
      const otherNode = state.nodes[other];
      const [ox, oy] = toScreen(otherNode[8], otherNode[9]);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(ox, oy);
      ctx.stroke();
    }
    for (const [, other] of neighbours) {
      const otherNode = state.nodes[other];
      const [ox, oy] = toScreen(otherNode[8], otherNode[9]);
      ctx.beginPath();
      ctx.arc(ox, oy, 3.2, 0, Math.PI * 2);
      ctx.fillStyle = state.nodeColor[other];
      ctx.fill();
    }
    ctx.beginPath();
    ctx.arc(x, y, 7, 0, Math.PI * 2);
    ctx.fillStyle = state.nodeColor[nodeIndex];
    ctx.fill();
    ctx.strokeStyle = "#16202b";
    ctx.lineWidth = 2;
    ctx.stroke();

    const zh = node[11] ? ` · ${node[11]}` : "";
    tooltip.innerHTML = `<div class="tt-title">${esc(node[1])}</div>
      <div class="tt-meta">${esc(typeLabel(node[2]))} · ${fmt(node[6])} ${
        lang === "zh" ? "条关系" : "relations"} · ${fmt(node[4])} ${lang === "zh" ? "篇论文" : "papers"}${esc(zh)}</div>`;
    tooltip.classList.remove("hidden");
    const wrapRect = $("graph-canvas").parentElement.getBoundingClientRect();
    const event = state.pointer || { clientX: wrapRect.left + x, clientY: wrapRect.top + y };
    let left = event.clientX - wrapRect.left + 16;
    let top = event.clientY - wrapRect.top + 16;
    if (left + 320 > wrapRect.width) left = event.clientX - wrapRect.left - 320;
    if (top + 90 > wrapRect.height) top = event.clientY - wrapRect.top - 90;
    tooltip.style.left = Math.max(8, left) + "px";
    tooltip.style.top = Math.max(8, top) + "px";
  }

  function bindEvents() {
    $("btn-graph").onclick = () => showGraph(true);
    $("btn-full").onclick = () => { state.view = "graph"; setView("graph"); state.filtered = computeFiltered(); fitView(); renderGraph(); updateViewLabel(); };
    $("btn-type").onclick = showTypeView;
    $("btn-png").onclick = exportPng;
    $("btn-lang").onclick = () => {
      lang = lang === "zh" ? "en" : "zh";
      localStorage.setItem(LANG_KEY, lang);
      applyLanguage();
      buildSidebar();
      if (state.view === "graph") renderGraph();
      if (state.view === "type") drawTypeOverview();
      if (state.selected) {
        if (state.selected.kind === "node") renderNodePanel(state.selected.index);
        else if (state.selected.kind === "edge") selectEdge(state.selected.index);
      }
      setHint(state.view === "graph" ? t("graphHint") : state.view === "type" ? t("typeHint") : t("nbHint"));
    };
    $("panel-close").onclick = () => {
      $("panel-body").innerHTML = `<p class="muted">${esc(t("panelHint"))}</p>`;
      state.selected = null;
      if (state.view === "graph") { state.hover = -1; drawOverlay(); }
      if (state.network) state.network.unselectAll();
    };
    $("family-select").onchange = () => {
      state.filters.family = $("family-select").value;
      state.view = "graph"; setView("graph"); state.filtered = computeFiltered(); fitView(); renderGraph();
    };
    $("paper-select").onchange = () => {
      state.filters.paper = $("paper-select").value;
      state.view = "graph"; setView("graph"); state.filtered = computeFiltered(); fitView(); renderGraph();
    };
    $("anomaly-toggle").onchange = () => {
      state.filters.anomalies = $("anomaly-toggle").checked;
      state.view = "graph"; setView("graph"); state.filtered = computeFiltered(); fitView(); renderGraph();
    };
    $("btn-clear").onclick = () => showGraph(true);

    const input = $("search-input");
    let timer = null;
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => renderSearchResults(input.value), 130);
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        const first = document.querySelector("#search-results .item");
        if (first) selectSearchResult(Number(first.dataset.index));
      } else if (event.key === "Escape") {
        $("search-results").classList.add("hidden");
      }
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".searchbox")) $("search-results").classList.add("hidden");
    });
    $("search-results").addEventListener("click", (event) => {
      const item = event.target.closest(".item");
      if (item) selectSearchResult(Number(item.dataset.index));
    });

    const canvas = $("graph-canvas");
    let dragging = false, moved = false, lastX = 0, lastY = 0;
    canvas.addEventListener("mousedown", (event) => {
      dragging = true; moved = false; lastX = event.clientX; lastY = event.clientY;
      canvas.style.cursor = "grabbing";
    });
    window.addEventListener("mouseup", () => { dragging = false; canvas.style.cursor = "grab"; });
    window.addEventListener("mousemove", (event) => {
      if (!dragging) return;
      const dx = event.clientX - lastX, dy = event.clientY - lastY;
      if (Math.abs(dx) + Math.abs(dy) > 1) moved = true;
      lastX = event.clientX; lastY = event.clientY;
      state.viewport.tx += dx;
      state.viewport.ty += dy;
      if (state.view === "graph") {
        cancelAnimationFrame(state.raf);
        state.raf = requestAnimationFrame(() => { renderGraph(); drawOverlay(); });
      }
    });
    canvas.addEventListener("mousemove", (event) => {
      if (dragging || state.view !== "graph") return;
      state.pointer = event;
      const rect = canvas.getBoundingClientRect();
      const nodeIndex = nodeAt(event.clientX - rect.left, event.clientY - rect.top);
      if (nodeIndex !== state.hover) {
        state.hover = nodeIndex;
        cancelAnimationFrame(state.raf);
        state.raf = requestAnimationFrame(drawOverlay);
      } else if (nodeIndex >= 0) {
        cancelAnimationFrame(state.raf);
        state.raf = requestAnimationFrame(drawOverlay);
      }
      canvas.style.cursor = nodeIndex >= 0 ? "pointer" : "grab";
    });
    canvas.addEventListener("mouseleave", () => {
      state.hover = -1;
      drawOverlay();
    });
    canvas.addEventListener("click", (event) => {
      if (moved || state.view !== "graph") return;
      const rect = canvas.getBoundingClientRect();
      const nodeIndex = nodeAt(event.clientX - rect.left, event.clientY - rect.top);
      if (nodeIndex >= 0) selectNode(nodeIndex);
    });
    canvas.addEventListener("dblclick", (event) => {
      if (state.view !== "graph") return;
      const rect = canvas.getBoundingClientRect();
      const nodeIndex = nodeAt(event.clientX - rect.left, event.clientY - rect.top);
      if (nodeIndex >= 0) startNeighbourhood(nodeIndex);
    });
    canvas.addEventListener("wheel", (event) => {
      if (state.view !== "graph") return;
      event.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left, y = event.clientY - rect.top;
      const factor = event.deltaY < 0 ? 1.16 : 1 / 1.16;
      const next = Math.max(0.04, Math.min(4, state.viewport.scale * factor));
      const ratio = next / state.viewport.scale;
      state.viewport.tx = x - (x - state.viewport.tx) * ratio;
      state.viewport.ty = y - (y - state.viewport.ty) * ratio;
      state.viewport.scale = next;
      cancelAnimationFrame(state.raf);
      state.raf = requestAnimationFrame(() => { renderGraph(); drawOverlay(); });
    }, { passive: false });

    $("overview-canvas").addEventListener("click", (event) => {
      const geometry = state.overviewGeometry;
      if (!geometry) return;
      const rect = $("overview-canvas").getBoundingClientRect();
      const x = event.clientX - rect.left, y = event.clientY - rect.top;
      for (const type of geometry.types) {
        if (Math.hypot(x - type.sx, y - type.sy) <= type.radius + 4) {
          state.filters.types = new Set([type.type]);
          state.filters.community = -1;
          showGraph(false);
          buildSidebar();
          return;
        }
      }
    });

    window.addEventListener("resize", () => {
      if (state.view === "graph") { fitView(); renderGraph(); drawOverlay(); }
      if (state.view === "type") drawTypeOverview();
      if (state.view === "neighbourhood" && state.network) state.network.redraw();
    });
    window.addEventListener("error", (event) => {
      const footer = $("footer-meta");
      if (footer) footer.textContent = "script error: " + (event.message || "unknown");
    });
    window.addEventListener("keydown", (event) => {
      if (event.target.tagName === "INPUT" || event.target.tagName === "SELECT") return;
      if (event.key === "1") showGraph(true);
      if (event.key === "2") { state.view = "graph"; setView("graph"); state.filtered = computeFiltered(); fitView(); renderGraph(); }
      if (event.key === "/") { event.preventDefault(); $("search-input").focus(); }
    });
  }

  // ------------------------------------------------------------------ search
  function searchCandidates(query, limit) {
    const key = searchKey(query);
    if (!key) return [];
    const found = new Map();
    const add = (nodeIndex, kind) => {
      if (nodeIndex == null) return;
      const current = found.get(nodeIndex);
      const score = kind === "exact" ? 3 : kind === "prefix" ? 2 : 1;
      if (!current || current.score < score) found.set(nodeIndex, { index: nodeIndex, score, kind });
    };
    if (state.searchKeys[key]) for (const nodeIndex of state.searchKeys[key]) add(nodeIndex, "exact");
    if (found.size < limit * 2) {
      for (const candidate of Object.keys(state.searchKeys)) {
        if (candidate !== key && candidate.startsWith(key)) {
          for (const nodeIndex of state.searchKeys[candidate]) add(nodeIndex, "prefix");
          if (found.size >= limit * 2) break;
        }
      }
    }
    if (found.size < limit && key.length >= 2) {
      for (const candidate of Object.keys(state.searchKeys)) {
        if (!candidate.startsWith(key) && candidate.includes(key)) {
          for (const nodeIndex of state.searchKeys[candidate]) add(nodeIndex, "substring");
          if (found.size >= limit * 3) break;
        }
      }
    }
    return Array.from(found.values())
      .sort((a, b) => (b.score - a.score) || (state.nodes[b.index][6] - state.nodes[a.index][6]))
      .slice(0, limit);
  }

  function renderSearchResults(query) {
    const box = $("search-results");
    if (!query || !query.trim()) { box.classList.add("hidden"); box.innerHTML = ""; return; }
    const results = searchCandidates(query, 24);
    if (!results.length) {
      box.innerHTML = `<div class="empty">${esc(t("searchEmpty", { q: query }))}</div>`;
      box.classList.remove("hidden");
      return;
    }
    box.innerHTML = results.map((result) => {
      const node = state.nodes[result.index];
      const zh = node[11] ? ` · ${esc(node[11])}` : "";
      const flags = node[3] !== "clean" ? ` · ${esc(node[3])}` : "";
      return `<div class="item" data-index="${result.index}">
        <div class="name">${esc(node[1])}</div>
        <div class="meta">${esc(typeLabel(node[2]))} · ${fmt(node[4])} ${
          lang === "zh" ? "篇论文" : "papers"} · ${fmt(node[6])} ${lang === "zh" ? "条关系" : "relations"}${zh}${flags}</div>
      </div>`;
    }).join("");
    box.classList.remove("hidden");
  }

  function selectSearchResult(nodeIndex) {
    $("search-results").classList.add("hidden");
    state.selected = { kind: "node", index: nodeIndex };
    startNeighbourhood(nodeIndex);
  }

  // ------------------------------------------------------------------ panel
  async function evidenceFor(paper, relationId) {
    if (!state.evidenceCache.has(paper)) {
      const safe = paper.replace(/[<>:"/\\|?*]/g, "_");
      try {
        state.evidenceCache.set(paper, await fetchJSON(`data/evidence/${encodeURIComponent(safe)}.json`));
      } catch (error) {
        state.evidenceCache.set(paper, {});
      }
    }
    return (state.evidenceCache.get(paper) || {})[relationId] || null;
  }

  function edgeView(relIndex) {
    const row = state.edges[relIndex];
    return {
      relIdx: relIndex, relationId: state.relids[row[0]],
      subject: state.nodes[row[1]], object: state.nodes[row[2]],
      subjectIdx: row[1], objectIdx: row[2],
      predicate: state.meta.predicates[row[3]], family: state.meta.families[row[4]],
      paper: state.meta.paper_ids[row[5]], flags: row[6],
    };
  }

  function relationRows(nodeIndex) {
    return (state.adjacency[nodeIndex] || []).map(([relIdx, other, direction]) => ({ relIdx, other, direction }));
  }

  function paperTitle(id) {
    const meta = state.meta.papers_meta[id];
    return (meta && meta.title) || id;
  }
  function paperLink(id) {
    const meta = state.meta.papers_meta[id];
    return (meta && meta.md) || "";
  }

  function renderNodePanel(nodeIndex) {
    const node = state.nodes[nodeIndex];
    const rows = relationRows(nodeIndex);
    const outgoing = rows.filter((row) => row.direction > 0);
    const incoming = rows.filter((row) => row.direction < 0);
    const aliases = Array.from(new Set((node[12] || []).concat(node[13] || []))).filter(Boolean);
    const community = node[10] >= 0 ? state.communities.find((item) => item.id === node[10]) : null;
    const body = `
      <div class="card-title">${esc(node[1])}</div>
      <div class="chips">
        <span class="chip type" style="background:${esc(state.meta.types[node[2]].color)}">${esc(typeLabel(node[2]))}</span>
        <span class="chip">${node[7] ? (lang === "zh" ? "关系节点" : "in graph") : t("onlySearch")}</span>
        ${node[3] !== "clean" ? `<span class="chip warn">${esc(node[3])}</span>` : ""}
        ${node[11] ? `<span class="chip">${esc(t("zhLabel"))}: ${esc(node[11])}</span>` : ""}
        ${community ? `<span class="chip">${esc(t("community"))}: ${esc(community.label)}</span>` : ""}
      </div>
      <dl class="kv">
        <dt>${esc(t("nodeId"))}</dt><dd>${esc(node[0])}</dd>
        <dt>${esc(t("papers"))}</dt><dd>${fmt(node[4])}</dd>
        <dt>${esc(t("relations"))}</dt><dd>${fmt(node[6])}</dd>
        <dt>${esc(t("mentions"))}</dt><dd>${fmt(node[5])}</dd>
        ${node[14] ? `<dt>${esc(t("instanceMember"))}</dt><dd>${esc(paperTitle(node[14]))}</dd>` : ""}
      </dl>
      ${aliases.length ? `<div class="section"><h3>${esc(t("aliases"))}</h3><div class="aliases">${
        aliases.slice(0, 24).map((alias) => `<span>${esc(alias)}</span>`).join("")}</div></div>` : ""}
      <div class="section actions-row">
        <button class="mini" id="btn-start-nb">${esc(t("expandHere"))}</button>
        <button class="mini" id="btn-more-nb">${esc(t("expandMore"))}</button>
        <button class="mini" id="btn-locate-full">${esc(t("locateFull"))}</button>
      </div>
      <div class="section"><h3>${esc(t("outEdges"))} (${outgoing.length})</h3><div class="rel-list">${
        outgoing.slice(0, 40).map(relRowHtml).join("") || `<p class="muted">${esc(t("noRelations"))}</p>`}</div></div>
      <div class="section"><h3>${esc(t("inEdges"))} (${incoming.length})</h3><div class="rel-list">${
        incoming.slice(0, 40).map(relRowHtml).join("") || `<p class="muted">${esc(t("noRelations"))}</p>`}</div></div>
    `;
    $("panel-body").innerHTML = body;
    $("btn-start-nb").onclick = () => startNeighbourhood(nodeIndex);
    $("btn-more-nb").onclick = () => {
      state.nbNodes = Math.min(600, state.nbNodes + 80);
      state.nbEdges = Math.min(1600, state.nbEdges + 160);
      startNeighbourhood(state.nbStart != null ? state.nbStart : nodeIndex);
    };
    $("btn-locate-full").onclick = () => {
      state.filters = { types: new Set(state.meta.types.map((type) => type.id)),
        family: "", paper: "", anomalies: true, community: -1 };
      buildSidebar();
      showGraph(false);
      // centre on the node
      const scale = Math.max(state.viewport.scale, 0.6);
      state.viewport.scale = scale;
      state.viewport.tx = $("graph-canvas").clientWidth / 2 - node[8] * scale;
      state.viewport.ty = $("graph-canvas").clientHeight / 2 - node[9] * scale;
      state.selected = { kind: "node", index: nodeIndex };
      renderGraph();
      drawOverlay();
    };
    document.querySelectorAll("#panel-body .rel").forEach((element) => {
      element.onclick = () => selectEdge(Number(element.dataset.rel));
    });
  }

  function relRowHtml(row) {
    const view = edgeView(row.relIdx);
    const flags = [];
    if (view.flags & 1) flags.push(t("directionFlag"));
    if (view.flags & 2) flags.push(t("noLineFlag"));
    return `<div class="rel" data-rel="${row.relIdx}">
      <div>${esc(short(view.subject[1], 26))} <span class="pred">→ ${esc(view.predicate)} →</span> ${esc(short(view.object[1], 26))}</div>
      <div class="mini-meta">${esc(view.paper.slice(0, 3))} · ${esc(familyLabel(view.family))}${
        flags.length ? " · " + flags.join(" / ") : ""}</div>
    </div>`;
  }

  async function selectEdge(relIndex) {
    const view = edgeView(relIndex);
    state.selected = { kind: "edge", index: relIndex };
    const flags = [];
    if (view.flags & 1) flags.push(`<span class="flag">${esc(t("directionFlag"))}</span>`);
    if (view.flags & 2) flags.push(`<span class="flag">${esc(t("noLineFlag"))}</span>`);
    $("panel-body").innerHTML = `
      <div class="card-title">${esc(view.subject[1])}</div>
      <div class="chips"><span class="chip">${esc(t("relationDetail"))}</span>${flags.join(" ")}</div>
      <dl class="kv">
        <dt>${esc(t("predicate"))}</dt><dd><b>${esc(view.predicate)}</b>（${esc(familyLabel(view.family))}）</dd>
        <dt>${esc(t("direction"))}</dt><dd>${esc(view.subject[1])} → ${esc(view.object[1])}</dd>
        <dt>${esc(t("typesEnds"))}</dt><dd>${esc(typeLabel(view.subject[2]))} → ${esc(typeLabel(view.object[2]))}</dd>
        <dt>${esc(t("paperField"))}</dt><dd>${esc(paperTitle(view.paper))}<br><span class="muted">${esc(view.paper)}</span></dd>
        <dt>relation_id</dt><dd>${esc(view.relationId)}</dd>
      </dl>
      <div class="section"><h3>${esc(t("evidence"))}</h3><div id="evidence-box" class="evidence">${esc(t("loading"))}</div></div>
      <div class="section actions-row">
        <button class="mini" id="btn-edge-subject">${esc(t("subject"))}</button>
        <button class="mini" id="btn-edge-object">${esc(t("object"))}</button>
        ${paperLink(view.paper) ? `<a class="button mini" href="${esc(paperLink(view.paper))}" target="_blank" rel="noopener">${esc(t("openPaper"))}</a>` : ""}
      </div>
    `;
    $("btn-edge-subject").onclick = () => startNeighbourhood(view.subjectIdx);
    $("btn-edge-object").onclick = () => startNeighbourhood(view.objectIdx);
    const evidence = await evidenceFor(view.paper, view.relationId);
    const box = $("evidence-box");
    if (!evidence) {
      box.innerHTML = `<span class="muted">${esc(t("noEvidence"))}</span>`;
      return;
    }
    const [text, line, context] = evidence;
    box.innerHTML = `
      <div class="quote">“${esc(text || t("quoteEmpty"))}”</div>
      <div class="loc">${esc(paperTitle(view.paper))} · ${esc(view.paper)} · ${
        line ? `${lang === "zh" ? "第" : "line "}${line}${lang === "zh" ? "行" : ""}`
             : `<span class="flag">${esc(t("locateMissing"))}</span>`}</div>
      ${context ? `<div class="context">${esc(t("context"))}: ${esc(context)}</div>` : ""}
    `;
  }

  function selectNode(nodeIndex) {
    state.selected = { kind: "node", index: nodeIndex };
    renderNodePanel(nodeIndex);
  }

  // ------------------------------------------------------------------ type overview
  function showTypeView() {
    state.view = "type";
    setView("type");
    drawTypeOverview();
    $("view-label").textContent = t("typeLabel");
    $("btn-type").classList.add("primary");
    $("btn-graph").classList.remove("primary");
    setHint(t("typeHint"));
  }

  function drawTypeOverview() {
    const canvas = $("overview-canvas");
    const { ctx, width, height } = canvasSize(canvas);
    ctx.clearRect(0, 0, width, height);
    const types = state.overview.types;
    const scale = Math.min(width, height) / 1150;
    const cx = width / 2, cy = height / 2;
    const nodes = types.map((type) => ({
      ...type,
      sx: cx + type.x * scale * 1.28,
      sy: cy + type.y * scale * 1.28,
      radius: Math.max(28, Math.min(92, (16 + Math.sqrt(Math.max(1, type.count)) * 0.78) * Math.max(0.8, scale))),
    }));
    const byType = new Map(nodes.map((node) => [node.type, node]));
    const edges = state.overview.edges.map((edge) => ({
      ...edge, a: byType.get(edge.s), b: byType.get(edge.o),
    })).filter((edge) => edge.a && edge.b);
    const maxCount = Math.max(...edges.map((edge) => edge.count), 1);
    for (const edge of edges) {
      const { a, b } = edge;
      const angleA = Math.atan2(a.sy - cy, a.sx - cx);
      let angleDiff = Math.atan2(b.sy - cy, b.sx - cx) - angleA;
      while (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
      while (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;
      const midAngle = angleA + angleDiff / 2;
      const ringDistance = Math.hypot(a.sx - cx, a.sy - cy) || 1;
      const controlRadius = ringDistance * 1.1;
      const mx = cx + Math.cos(midAngle) * controlRadius;
      const my = cy + Math.sin(midAngle) * controlRadius;
      ctx.beginPath();
      ctx.moveTo(a.sx, a.sy);
      ctx.quadraticCurveTo(mx, my, b.sx, b.sy);
      const sourceType = state.meta.types.findIndex((item) => item.id === edge.s);
      ctx.strokeStyle = hexToRgba(sourceType >= 0 ? state.meta.types[sourceType].color : "#8b96a3", 0.2);
      ctx.lineWidth = 0.8 + 2.6 * Math.sqrt(edge.count / maxCount);
      ctx.stroke();
    }
    for (const node of nodes) {
      ctx.beginPath();
      ctx.arc(node.sx, node.sy, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = node.color;
      ctx.globalAlpha = 0.92;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2.5;
      ctx.stroke();
      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const zh = lang === "zh" ? node.label : typeLabel(state.meta.types.findIndex((item) => item.id === node.type));
      ctx.font = `600 ${Math.max(10, Math.min(17, node.radius / 3.4))}px 'Segoe UI', 'Microsoft YaHei', sans-serif`;
      ctx.fillText(zh, node.sx, node.sy - node.radius * 0.2);
      ctx.font = `${Math.max(9, Math.min(14, node.radius / 4.6))}px 'Segoe UI', sans-serif`;
      ctx.fillText(fmt(node.count), node.sx, node.sy + node.radius * 0.34);
    }
    state.overviewGeometry = { types: nodes };
  }

  // ------------------------------------------------------------------ neighbourhood
  function ensureNetwork() {
    if (state.network) return;
    state.visNodes = new vis.DataSet([]);
    state.visEdges = new vis.DataSet([]);
    state.network = new vis.Network($("network"), { nodes: state.visNodes, edges: state.visEdges }, {
      physics: false, layout: { improvedLayout: false },
      interaction: { hover: true, tooltipDelay: 240, multiselect: false },
      nodes: {
        shape: "dot", borderWidth: 1.5,
        font: { size: 13, face: "Segoe UI, Microsoft YaHei, sans-serif", color: "#16202b" },
        chosen: { node: (values) => { values.borderWidth = 3; values.borderColor = "#2f6fdb"; } },
      },
      edges: {
        arrows: { to: { enabled: true, scaleFactor: 0.55 } },
        smooth: false, width: 1.2, selectionWidth: 2.4,
        color: { color: "rgba(130,140,155,0.45)", highlight: "#2f6fdb", hover: "#2f6fdb" },
        font: { size: 10, color: "#6b7785", strokeWidth: 3, strokeColor: "#fbfcfe" },
      },
    });
    state.network.on("click", (params) => {
      if (params.nodes.length) selectNode(params.nodes[0]);
      else if (params.edges.length) selectEdge(params.edges[0]);
    });
    state.network.on("doubleClick", (params) => {
      if (params.nodes.length) startNeighbourhood(params.nodes[0]);
    });
  }

  function neighbourhoodData(startIndex, maxNodes, maxEdges) {
    const queue = [[startIndex, 0]];
    const distance = new Map([[startIndex, 0]]);
    const nodeSet = new Set([startIndex]);
    const edgeSet = [];
    while (queue.length && nodeSet.size < maxNodes && edgeSet.length < maxEdges) {
      const [current, depth] = queue.shift();
      const neighbours = state.adjacency[current] || [];
      for (const [relIndex, other] of neighbours) {
        if (edgeSet.length >= maxEdges) break;
        if (!edgeSet.includes(relIndex)) edgeSet.push(relIndex);
        if (!nodeSet.has(other) && nodeSet.size < maxNodes) {
          nodeSet.add(other);
          distance.set(other, depth + 1);
          if (depth < 2) queue.push([other, depth + 1]);
        }
      }
    }
    return { nodeSet, edgeSet, distance };
  }

  function startNeighbourhood(nodeIndex, maxNodes, maxEdges) {
    ensureNetwork();
    state.view = "neighbourhood";
    setView("neighbourhood");
    const limits = { nodes: maxNodes || state.nbNodes, edges: maxEdges || state.nbEdges };
    state.nbNodes = limits.nodes;
    state.nbEdges = limits.edges;
    state.nbStart = nodeIndex;
    const { nodeSet, edgeSet, distance } = neighbourhoodData(nodeIndex, limits.nodes, limits.edges);
    state.filtered = edgeSet;
    state.selected = { kind: "node", index: nodeIndex };

    const centre = state.nodes[nodeIndex];
    const ring = Array.from(nodeSet).filter((index) => index !== nodeIndex);
    const typeOrder = new Map(state.meta.types.map((type, position) => [type.id, position]));
    ring.sort((a, b) => {
      const ta = typeOrder.get(state.meta.types[state.nodes[a][2]].id);
      const tb = typeOrder.get(state.meta.types[state.nodes[b][2]].id);
      return ta - tb || state.nodes[b][6] - state.nodes[a][6];
    });
    const radius = Math.max(180, Math.min(620, 80 + ring.length * 7));
    const labelled = new Set();
    if (ring.length <= 70) ring.forEach((index) => labelled.add(index));
    else ring.slice().sort((a, b) => state.nodes[b][6] - state.nodes[a][6])
      .slice(0, 45).forEach((index) => labelled.add(index));

    const visNodes = [{
      id: nodeIndex, label: centre[1], x: 0, y: 0, fixed: true,
      color: { background: state.nodeColor[nodeIndex], border: "#ffffff" },
      size: 18, font: { size: 15, bold: true },
    }];
    ring.forEach((index, position) => {
      const angle = (2 * Math.PI * position) / Math.max(1, ring.length) - Math.PI / 2;
      const node = state.nodes[index];
      const factor = (distance.get(index) || 1) >= 2 ? 1.32 : 1;
      visNodes.push({
        id: index, label: node[1], x: Math.cos(angle) * radius * factor,
        y: Math.sin(angle) * radius * factor, fixed: true,
        color: { background: state.nodeColor[index], border: "#ffffff" },
        size: 7 + Math.min(7, Math.log1p(node[6]) * 1.6),
        font: { size: labelled.has(index) ? 12 : 0 },
        title: `${node[1]}\n${typeLabel(node[2])} · ${fmt(node[6])} ${lang === "zh" ? "条关系" : "relations"}`,
      });
    });
    const visEdges = edgeSet.map((relIndex) => {
      const view = edgeView(relIndex);
      return {
        id: relIndex, from: view.subjectIdx, to: view.objectIdx,
        label: visNodes.length <= 80 ? view.predicate : "",
        title: `${view.subject[1]} -> ${view.predicate} -> ${view.object[1]}`,
        dashes: (view.flags & 1) ? [4, 3] : false,
      };
    });
    state.visNodes.clear();
    state.visNodes.add(visNodes);
    state.visEdges.clear();
    state.visEdges.add(visEdges);
    setTimeout(() => { state.network.fit({ animation: false }); }, 30);
    state.drawn = visEdges.length;
    $("count-filtered").textContent = fmt(edgeSet.length);
    $("count-drawn").textContent = fmt(visEdges.length);
    $("view-label").textContent = t("nbLabel");
    $("btn-graph").classList.remove("primary");
    $("btn-type").classList.remove("primary");
    renderNodePanel(nodeIndex);
    setHint(t("nbHint", { nodes: visNodes.length, edges: visEdges.length,
      maxNodes: limits.nodes, maxEdges: limits.edges }));
  }

  // ------------------------------------------------------------------ PNG export
  async function exportPng() {
    try {
      let canvas = null;
      if (state.view === "graph") canvas = $("graph-canvas");
      else if (state.view === "type") canvas = $("overview-canvas");
      else if (state.network) {
        const container = state.network.canvas && state.network.canvas.body
          && state.network.canvas.body.container;
        canvas = container ? container.querySelector("canvas") : null;
      }
      if (!canvas) { toast(t("exportFail", { msg: "no canvas" })); return; }
      const name = state.view === "graph" ? "materials_kg_graph.png"
        : state.view === "type" ? "materials_kg_overview.png" : "materials_kg_neighbourhood.png";
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
      if (!blob) { toast(t("exportFail", { msg: "empty blob" })); return; }
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = name;
      document.body.appendChild(link);
      link.click();
      setTimeout(() => { URL.revokeObjectURL(link.href); link.remove(); }, 2000);
      toast(t("exportTip", { name }));
    } catch (error) {
      toast(t("exportFail", { msg: error.message }));
    }
  }

  // ------------------------------------------------------------------ misc
  function setHint(text) { $("hint").textContent = text; }

  function applyHash() {
    const raw = location.hash.replace(/^#/, "");
    if (!raw) return;
    const params = new URLSearchParams(raw);
    if (params.get("anomalies") === "1") {
      state.filters.anomalies = true;
      $("anomaly-toggle").checked = true;
    }
    const type = params.get("type");
    const nodeId = params.get("node");
    const query = params.get("q");
    if (params.get("view") === "type") showTypeView();
    if (type) {
      state.filters.types = new Set([type]);
      showGraph(false);
      buildSidebar();
    }
    if (nodeId) {
      const index = state.nodes.findIndex((node) => node[0] === nodeId);
      if (index >= 0) { selectSearchResult(index); return; }
    }
    if (query) {
      const results = searchCandidates(query, 1);
      if (results.length) selectSearchResult(results[0].index);
      else toast(t("searchEmpty", { q: query }));
    }
  }

  boot();
})();
