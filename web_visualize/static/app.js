const state = {
  data: null,
  dataIndexes: null,
  kpiData: null,
  hovered: null,
  selected: null,
  selectedODId: null,
  selectedRouteOptionKey: null,
  selectedStopId: null,
  layers: { zone: true, route: true, stop: true, od: false },
  hideInvalidOD: false,
  sortMode: "composite_desc",
  coverageRadiusM: 50,
  view: { scale: 1, offsetX: 0, offsetY: 0 },
  drag: { active: false, startX: 0, startY: 0, offsetX: 0, offsetY: 0 },
  devicePixelRatio: window.devicePixelRatio || 1,
};

const canvas = document.getElementById("mapCanvas");
const ctx = canvas.getContext("2d");
const tooltip = document.getElementById("tooltip");
const statusBox = document.getElementById("statusBox");
const networkSummary = document.getElementById("networkSummary");
const mapStatusPill = document.getElementById("mapStatusPill");
const detailPanel = document.getElementById("detailPanel");
const odList = document.getElementById("odList");
const datasetSelect = document.getElementById("datasetSelect");
const maxPlansInput = document.getElementById("maxPlansInput");
const gridCellSizeInput = document.getElementById("gridCellSizeInput");
const topNOdInput = document.getElementById("topNOdInput");
const coverageRadiusInput = document.getElementById("coverageRadiusInput");
const backendUrlInput = document.getElementById("backendUrlInput");
const sortSelect = document.getElementById("sortSelect");
const hideInvalidToggle = document.getElementById("hideInvalidToggle");

const layerInputs = {
  zone: document.getElementById("layerZone"),
  route: document.getElementById("layerRoute"),
  stop: document.getElementById("layerStop"),
  od: document.getElementById("layerOd"),
};

function setStatus(message, tone = "default") {
  statusBox.className = "status-line";
  if (tone === "error") statusBox.classList.add("error-line");
  if (tone === "success") statusBox.classList.add("success-line");
  statusBox.innerHTML = message;
}

function setMapPill(label, tone = "default") {
  mapStatusPill.textContent = label;
  mapStatusPill.className = "pill";
  if (tone === "error") mapStatusPill.classList.add("invalid");
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return String(value);
  if (Math.abs(numeric - Math.round(numeric)) < 1e-9) return String(Math.round(numeric));
  return numeric.toFixed(2);
}

function formatCoord(value) {
  return Number(value).toFixed(6);
}

function parseMaxPlans() {
  const raw = maxPlansInput.value.trim();
  if (!raw || raw.toLowerCase() === "none") return null;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseTopNOd() {
  const raw = topNOdInput.value.trim();
  if (!raw || raw.toLowerCase() === "none") return null;
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function buildNetworkUrl() {
  const params = new URLSearchParams();
  params.set("dataset", datasetSelect.value);
  const maxPlans = parseMaxPlans();
  params.set("max_plans", maxPlans === null ? "None" : String(maxPlans));
  params.set("grid_cell_size_m", gridCellSizeInput.value || "500");
  const topNOd = parseTopNOd();
  if (topNOd !== null) params.set("top_n_od_pairs", String(topNOd));
  return `/data/network?${params.toString()}`;
}

function buildIndexes(data) {
  const zonesById = new Map(data.zones.map((zone) => [zone.id, zone]));
  const stopsById = new Map(data.stops.map((stop) => [stop.id, stop]));
  const routesById = new Map(data.routes.map((route) => [route.id, route]));
  const odById = new Map(data.od_pairs.map((od) => [od.id, od]));
  const zoneOdCounts = new Map();
  for (const od of data.od_pairs) {
    zoneOdCounts.set(od.origin_zone_id, (zoneOdCounts.get(od.origin_zone_id) || 0) + 1);
    zoneOdCounts.set(od.destination_zone_id, (zoneOdCounts.get(od.destination_zone_id) || 0) + 1);
  }
  return { zonesById, stopsById, routesById, odById, zoneOdCounts };
}

function updateNetworkSummary() {
  if (!state.data) {
    networkSummary.textContent = "Load a dataset to inspect zones, routes, stops and OD pairs.";
    return;
  }
  const meta = state.data.meta;
  const maxPlansText = meta.max_plans === null ? "all" : meta.max_plans;
  networkSummary.textContent = `${meta.dataset} | ${meta.stop_count} stops | ${meta.route_count} routes | ${meta.zone_count} zones | ${meta.od_pair_count} OD pairs | grid ${meta.grid_cell_size_m}m | max plans ${maxPlansText}`;
}

async function loadNetwork() {
  setStatus("<strong>State:</strong> Loading network data...");
  setMapPill("Loading");
  try {
    const response = await fetch(buildNetworkUrl());
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Cannot load network data");
    state.data = payload;
    state.dataIndexes = buildIndexes(payload);
    state.kpiData = null;
    state.selected = null;
    state.selectedODId = null;
    state.selectedRouteOptionKey = null;
    state.selectedStopId = null;
    state.coverageRadiusM = Number.parseFloat(coverageRadiusInput.value) || 50;
    updateNetworkSummary();
    fitToData();
    render();
    renderDetails();
    renderOdList();
    setStatus("<strong>State:</strong> Network data loaded.", "success");
    setMapPill("Ready");
  } catch (err) {
    setStatus(`<strong>State:</strong> ${err.message}`, "error");
    setMapPill("Error", "error");
  }
}

async function calculateKpi() {
  setStatus("<strong>State:</strong> Calling KPI backend...");
  setMapPill("KPI");
  try {
    const response = await fetch("/data/kpi/calculate-all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset: datasetSelect.value, max_plans: maxPlansInput.value.trim(), grid_cell_size_m: gridCellSizeInput.value || "500", backend_url: backendUrlInput.value.trim(), use_backend_proxy: false }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Cannot calculate KPI");
    state.kpiData = payload;
    renderOdList();
    renderDetails();
    render();
    setStatus("<strong>State:</strong> KPI results loaded into sidebar.", "success");
    setMapPill("KPI Ready");
  } catch (err) {
    setStatus(`<strong>State:</strong> ${err.message}`, "error");
    setMapPill("KPI Error", "error");
  }
}

function getKpiMap() {
  if (!state.kpiData || !Array.isArray(state.kpiData.data)) return new Map();
  return new Map(state.kpiData.data.map((item) => [item.od_pair_id, item]));
}

function compareNullable(a, b) {
  const aMissing = a === null || a === undefined;
  const bMissing = b === null || b === undefined;
  if (aMissing && bMissing) return 0;
  if (aMissing) return 1;
  if (bMissing) return -1;
  return a - b;
}

function compareText(a, b) {
  return String(a).localeCompare(String(b));
}

function getVisibleOdEntries() {
  if (!state.data) return [];
  const kpiMap = getKpiMap();
  const odEntries = state.data.od_pairs.map((od) => {
    const kpi = kpiMap.get(od.id) || null;
    const summary = kpi ? kpi.summary : null;
    return { od, kpi, summary, demand: od.demand, composite: summary && summary.scores ? summary.scores.composite : null, isValid: summary ? summary.is_valid : null };
  });
  let filtered = odEntries;
  if (state.hideInvalidOD) filtered = filtered.filter((entry) => entry.isValid === true);
  const sorters = {
    composite_desc: (a, b) => compareNullable(b.composite, a.composite) || compareText(a.od.id, b.od.id),
    composite_asc: (a, b) => compareNullable(a.composite, b.composite) || compareText(a.od.id, b.od.id),
    demand_desc: (a, b) => compareNullable(b.demand, a.demand) || compareText(a.od.id, b.od.id),
    demand_asc: (a, b) => compareNullable(a.demand, b.demand) || compareText(a.od.id, b.od.id),
    id_asc: (a, b) => compareText(a.od.id, b.od.id),
  };
  return filtered.sort(sorters[state.sortMode] || sorters.composite_desc);
}

function renderOdList() {
  const entries = getVisibleOdEntries();
  if (!state.kpiData) {
    odList.innerHTML = '<div class="hint">Run KPI calculation to populate sortable OD results.</div>';
    return;
  }
  if (!entries.length) {
    odList.innerHTML = '<div class="hint">No OD entries match the active filter.</div>';
    return;
  }
  odList.innerHTML = entries.map((entry) => {
    const summary = entry.summary;
    const isActive = state.selectedODId === entry.od.id;
    const validClass = summary && summary.is_valid === false ? "pill invalid" : "pill";
    const validityLabel = summary ? (summary.is_valid ? "Valid" : "Invalid") : "No KPI";
    return `
      <div class="od-item ${isActive ? "active" : ""}" data-od-id="${entry.od.id}">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
          <strong class="mono">${entry.od.id}</strong>
          <span class="${validClass}">${validityLabel}</span>
        </div>
        <div class="status-line"><strong>O:</strong> ${entry.od.origin_zone_id} &nbsp; <strong>D:</strong> ${entry.od.destination_zone_id}</div>
        <div class="metric-grid">
          <div class="metric-card"><small>Demand</small><strong>${formatNumber(entry.demand)}</strong></div>
          <div class="metric-card"><small>Composite</small><strong>${formatNumber(entry.composite)}</strong></div>
        </div>
      </div>`;
  }).join("");
  for (const element of odList.querySelectorAll(".od-item")) {
    element.addEventListener("click", () => {
      const odId = element.dataset.odId;
      state.selectedODId = odId;
      state.selected = { type: "od", id: odId };
      state.selectedRouteOptionKey = null;
      renderOdList();
      renderDetails();
      render();
    });
  }
}

function getSelectedOd() {
  if (!state.selectedODId || !state.dataIndexes) return null;
  return state.dataIndexes.odById.get(state.selectedODId) || null;
}

function getSelectedRouteOption() {
  if (!state.selectedODId || !state.selectedRouteOptionKey || !state.kpiData) return null;
  const kpi = getKpiMap().get(state.selectedODId);
  if (!kpi || !Array.isArray(kpi.route_options)) return null;
  return kpi.route_options.find((option) => `${state.selectedODId}::${option.option_id}` === state.selectedRouteOptionKey) || null;
}

function renderDetails() {
  if (!state.data) {
    detailPanel.innerHTML = '<div class="hint">Load network data first.</div>';
    return;
  }
  const indexes = state.dataIndexes;
  const selected = state.selected;
  if (selected && selected.type === "zone") {
    const zone = indexes.zonesById.get(selected.id);
    const related = indexes.zoneOdCounts.get(selected.id) || 0;
    detailPanel.innerHTML = `<div class="detail-block"><h3>Zone ${zone.id}</h3><div class="status-line">Centroid: <span class="mono">${formatCoord(zone.centroid.lat)}, ${formatCoord(zone.centroid.lon)}</span></div><div class="status-line">Boundary points: <strong>${zone.boundary.length}</strong></div><div class="status-line">Related OD count: <strong>${related}</strong></div></div>`;
    return;
  }
  if (selected && selected.type === "route") {
    const route = indexes.routesById.get(selected.id);
    detailPanel.innerHTML = `<div class="detail-block"><h3>Route ${route.id}</h3><div class="status-line">Stops on route: <strong>${route.stops_seq.length}</strong></div><div class="status-line">Start: <span class="mono">${route.start_stop_id}</span></div><div class="status-line">End: <span class="mono">${route.end_stop_id}</span></div><div class="status-line">Stop sequence:</div><div class="mono">${route.stops_seq.join(" -> ")}</div></div>`;
    return;
  }
  if (selected && selected.type === "stop") {
    const stop = indexes.stopsById.get(selected.id);
    detailPanel.innerHTML = `<div class="detail-block"><h3>Stop ${stop.id}</h3><div class="status-line">Coordinates: <span class="mono">${formatCoord(stop.lat)}, ${formatCoord(stop.lon)}</span></div><div class="status-line">Routes through stop: <strong>${stop.route_ids.length}</strong></div><div class="mono">${stop.route_ids.join(", ") || "None"}</div><div class="status-line" style="margin-top:10px;">Coverage radius on click: <strong>${formatNumber(state.coverageRadiusM)}m</strong></div></div>`;
    return;
  }
  if (state.selectedODId) {
    const od = indexes.odById.get(state.selectedODId);
    const kpi = getKpiMap().get(state.selectedODId) || null;
    const routeOptions = kpi && Array.isArray(kpi.route_options) ? kpi.route_options : [];
    const summaryHtml = kpi ? `<div class="metric-grid"><div class="metric-card"><small>Composite</small><strong>${formatNumber(kpi.summary.scores.composite)}</strong></div><div class="metric-card"><small>Transfer</small><strong>${formatNumber(kpi.summary.scores.transfer)}</strong></div><div class="metric-card"><small>Circuity</small><strong>${formatNumber(kpi.summary.scores.circuity)}</strong></div><div class="metric-card"><small>Coverage</small><strong>${formatNumber(kpi.summary.scores.spatial_coverage)}</strong></div></div>` : '<div class="hint">No KPI payload matched this OD. Check dataset/back-end alignment.</div>';
    const optionsHtml = routeOptions.length ? routeOptions.map((option) => {
      const optionKey = `${od.id}::${option.option_id}`;
      const active = state.selectedRouteOptionKey === optionKey;
      return `<div class="route-option-item ${active ? "active" : ""}" data-route-option-key="${optionKey}"><strong>${option.option_id}</strong><div class="status-line">Routes: <span class="mono">${(option.path.route_sequence || []).join(" -> ") || "None"}</span></div><div class="status-line">Stops: <span class="mono">${(option.path.stop_sequence || []).join(" -> ") || "None"}</span></div><div class="metric-grid"><div class="metric-card"><small>Composite</small><strong>${formatNumber(option.metrics.composite_score)}</strong></div><div class="metric-card"><small>Transfer</small><strong>${formatNumber(option.metrics.transfer_count)}</strong></div><div class="metric-card"><small>Circuity</small><strong>${formatNumber(option.metrics.circuity_index)}</strong></div><div class="metric-card"><small>Coverage</small><strong>${formatNumber(option.metrics.coverage_ratio)}</strong></div></div></div>`;
    }).join("") : '<div class="hint">No route options available.</div>';
    detailPanel.innerHTML = `<div class="detail-block"><h3>OD ${od.id}</h3><div class="status-line"><strong>Origin:</strong> <span class="mono">${od.origin_zone_id}</span></div><div class="status-line"><strong>Destination:</strong> <span class="mono">${od.destination_zone_id}</span></div><div class="status-line"><strong>Demand:</strong> ${formatNumber(od.demand)}</div>${summaryHtml}</div><div class="detail-block"><h3>Route Options</h3>${optionsHtml}</div>`;
    for (const element of detailPanel.querySelectorAll(".route-option-item")) {
      element.addEventListener("click", () => {
        const key = element.dataset.routeOptionKey;
        state.selectedRouteOptionKey = state.selectedRouteOptionKey === key ? null : key;
        renderDetails();
        render();
      });
    }
    return;
  }
  detailPanel.innerHTML = '<div class="hint">Hover or click a zone, route, stop or OD to inspect its details.</div>';
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const dpr = state.devicePixelRatio;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  render();
}

function fitToData() {
  if (!state.data || !state.data.meta || !state.data.meta.bbox) return;
  const bbox = state.data.meta.bbox;
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(1, rect.width);
  const height = Math.max(1, rect.height);
  const lonSpan = Math.max(bbox.max_lon - bbox.min_lon, 1e-9);
  const latSpan = Math.max(bbox.max_lat - bbox.min_lat, 1e-9);
  const padding = 40;
  const scale = Math.min((width - padding * 2) / lonSpan, (height - padding * 2) / latSpan);
  const centerLon = (bbox.min_lon + bbox.max_lon) / 2;
  const centerLat = (bbox.min_lat + bbox.max_lat) / 2;
  state.view.scale = scale;
  state.view.offsetX = width / 2 - centerLon * scale;
  state.view.offsetY = height / 2 + centerLat * scale;
  render();
}

function worldToScreen(point) {
  return { x: point.lon * state.view.scale + state.view.offsetX, y: -point.lat * state.view.scale + state.view.offsetY };
}

function screenToWorld(x, y) {
  return { lon: (x - state.view.offsetX) / state.view.scale, lat: -(y - state.view.offsetY) / state.view.scale };
}

function routeColor(routeId) {
  const palette = ["#d7263d", "#007ea7", "#f4a261", "#2a9d8f", "#6a4c93", "#ffb703", "#3a86ff", "#ff006e", "#1982c4", "#588157"];
  let hash = 0;
  for (const ch of routeId) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return palette[hash % palette.length];
}

function getHighlightedRouteIds() {
  const ids = new Set();
  const option = getSelectedRouteOption();
  if (!option || !option.path || !Array.isArray(option.path.route_sequence)) return ids;
  for (const routeId of option.path.route_sequence) ids.add(routeId);
  return ids;
}

function getHighlightedStopIds() {
  const ids = new Set();
  const option = getSelectedRouteOption();
  if (!option || !option.path || !Array.isArray(option.path.stop_sequence)) return ids;
  for (const stopId of option.path.stop_sequence) ids.add(stopId);
  return ids;
}

function render() {
  const rect = canvas.getBoundingClientRect();
  const width = rect.width;
  const height = rect.height;
  ctx.clearRect(0, 0, width, height);
  if (!state.data) {
    ctx.save();
    ctx.fillStyle = "rgba(31, 35, 40, 0.72)";
    ctx.font = "600 18px Segoe UI";
    ctx.textAlign = "center";
    ctx.fillText("Load network data to start exploring.", width / 2, height / 2);
    ctx.restore();
    return;
  }
  drawBackgroundGrid(width, height);
  if (state.layers.zone) drawZones();
  if (state.layers.route) drawRoutes();
  if (state.layers.od) drawOds();
  if (state.layers.stop) drawStops();
  drawSelectionHighlights();
}

function drawBackgroundGrid(width, height) {
  ctx.save();
  ctx.strokeStyle = "rgba(0,0,0,0.04)";
  ctx.lineWidth = 1;
  for (let x = 0; x <= width; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke(); }
  for (let y = 0; y <= height; y += 80) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke(); }
  ctx.restore();
}

function drawZones() {
  for (const zone of state.data.zones) {
    const boundary = zone.boundary.map(worldToScreen);
    const isSelected = state.selected && state.selected.type === "zone" && state.selected.id === zone.id;
    const currentOD = getSelectedOd();
    const isHighlighted = currentOD && (zone.id === currentOD.origin_zone_id || zone.id === currentOD.destination_zone_id);
    ctx.save();
    ctx.beginPath();
    boundary.forEach((point, index) => { if (index === 0) ctx.moveTo(point.x, point.y); else ctx.lineTo(point.x, point.y); });
    ctx.closePath();
    ctx.fillStyle = isHighlighted ? "rgba(255, 183, 3, 0.18)" : "rgba(0, 78, 100, 0.08)";
    ctx.strokeStyle = isSelected || isHighlighted ? "rgba(247, 111, 0, 0.9)" : "rgba(0, 78, 100, 0.35)";
    ctx.lineWidth = isSelected || isHighlighted ? 2.6 : 1.2;
    ctx.fill();
    ctx.stroke();
    const centroid = worldToScreen(zone.centroid);
    ctx.fillStyle = "rgba(31,35,40,0.78)";
    ctx.font = "11px Consolas";
    ctx.fillText(zone.id, centroid.x + 6, centroid.y - 6);
    ctx.restore();
  }
}

function drawRoutes() {
  const highlightedRoutes = getHighlightedRouteIds();
  for (const route of state.data.routes) {
    const points = route.shape.map(worldToScreen);
    if (points.length < 2) continue;
    const highlighted = highlightedRoutes.has(route.id) || (state.selected && state.selected.type === "route" && state.selected.id === route.id);
    ctx.save();
    ctx.beginPath();
    points.forEach((point, index) => { if (index === 0) ctx.moveTo(point.x, point.y); else ctx.lineTo(point.x, point.y); });
    ctx.strokeStyle = routeColor(route.id);
    ctx.lineWidth = highlighted ? 4.5 : 2.2;
    ctx.globalAlpha = highlighted || !state.selectedRouteOptionKey ? 0.9 : 0.18;
    ctx.stroke();
    ctx.restore();
  }
}

function drawStops() {
  const highlightedStops = getHighlightedStopIds();
  for (const stop of state.data.stops) {
    const point = worldToScreen(stop);
    const highlighted = highlightedStops.has(stop.id) || stop.id === state.selectedStopId || (state.selected && state.selected.type === "stop" && state.selected.id === stop.id);
    ctx.save();
    ctx.beginPath();
    ctx.arc(point.x, point.y, highlighted ? 5.2 : 3.2, 0, Math.PI * 2);
    ctx.fillStyle = highlighted ? "#ffb703" : "#111111";
    ctx.globalAlpha = highlighted || !state.selectedRouteOptionKey ? 0.95 : 0.24;
    ctx.fill();
    ctx.restore();
  }
  drawCoverageCircle();
}

function drawCoverageCircle() {
  if (!state.selectedStopId || !state.dataIndexes) return;
  const stop = state.dataIndexes.stopsById.get(state.selectedStopId);
  if (!stop) return;
  const center = worldToScreen(stop);
  const latRadiusDeg = state.coverageRadiusM / 111320;
  const lonRadiusDeg = state.coverageRadiusM / (111320 * Math.max(Math.cos(stop.lat * Math.PI / 180), 1e-6));
  const edgeX = worldToScreen({ lat: stop.lat, lon: stop.lon + lonRadiusDeg });
  const edgeY = worldToScreen({ lat: stop.lat + latRadiusDeg, lon: stop.lon });
  ctx.save();
  ctx.beginPath();
  ctx.ellipse(center.x, center.y, Math.abs(edgeX.x - center.x), Math.abs(edgeY.y - center.y), 0, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(247, 111, 0, 0.10)";
  ctx.strokeStyle = "rgba(247, 111, 0, 0.65)";
  ctx.lineWidth = 1.6;
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

function buildOdCurve(origin, destination, seed) {
  const dx = destination.x - origin.x;
  const dy = destination.y - origin.y;
  const distance = Math.hypot(dx, dy) || 1;
  const nx = -dy / distance;
  const ny = dx / distance;
  let hash = 0;
  for (const ch of seed) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  const direction = hash % 2 === 0 ? 1 : -1;
  const magnitude = Math.min(34, Math.max(12, distance * 0.18));
  return {
    start: origin,
    end: destination,
    control: { x: (origin.x + destination.x) / 2 + nx * magnitude * direction, y: (origin.y + destination.y) / 2 + ny * magnitude * direction },
  };
}

function quadraticPoint(p0, p1, p2, t) {
  const mt = 1 - t;
  return { x: mt * mt * p0.x + 2 * mt * t * p1.x + t * t * p2.x, y: mt * mt * p0.y + 2 * mt * t * p1.y + t * t * p2.y };
}

function quadraticTangent(p0, p1, p2, t) {
  return { x: 2 * (1 - t) * (p1.x - p0.x) + 2 * t * (p2.x - p1.x), y: 2 * (1 - t) * (p1.y - p0.y) + 2 * t * (p2.y - p1.y) };
}

function drawArrowHead(curve, alpha) {
  const t = 0.92;
  const point = quadraticPoint(curve.start, curve.control, curve.end, t);
  const tangent = quadraticTangent(curve.start, curve.control, curve.end, t);
  const angle = Math.atan2(tangent.y, tangent.x);
  const size = 8;
  ctx.save();
  ctx.translate(point.x, point.y);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-size, size / 2);
  ctx.lineTo(-size, -size / 2);
  ctx.closePath();
  ctx.fillStyle = `rgba(183, 35, 24, ${alpha})`;
  ctx.fill();
  ctx.restore();
}

function drawOds() {
  for (const od of state.data.od_pairs) {
    const originZone = state.dataIndexes.zonesById.get(od.origin_zone_id);
    const destinationZone = state.dataIndexes.zonesById.get(od.destination_zone_id);
    if (!originZone || !destinationZone) continue;
    const curve = buildOdCurve(worldToScreen(originZone.centroid), worldToScreen(destinationZone.centroid), od.id);
    const isSelected = state.selectedODId === od.id || (state.selected && state.selected.type === "od" && state.selected.id === od.id);
    const demandWidth = Math.max(1.5, Math.min(6.5, 1.2 + Math.log10(Math.max(od.demand, 1)) * 1.8));
    const alpha = isSelected ? 0.95 : 0.35;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(curve.start.x, curve.start.y);
    ctx.quadraticCurveTo(curve.control.x, curve.control.y, curve.end.x, curve.end.y);
    ctx.strokeStyle = isSelected ? "rgba(183, 35, 24, 0.95)" : "rgba(214, 39, 40, 0.35)";
    ctx.lineWidth = isSelected ? demandWidth + 1.5 : demandWidth;
    ctx.stroke();
    drawArrowHead(curve, alpha);
    ctx.restore();
  }
}

function drawSelectionHighlights() {
  const od = getSelectedOd();
  if (!od) return;
  const originZone = state.dataIndexes.zonesById.get(od.origin_zone_id);
  const destinationZone = state.dataIndexes.zonesById.get(od.destination_zone_id);
  [originZone, destinationZone].forEach((zone) => {
    if (!zone) return;
    const centroid = worldToScreen(zone.centroid);
    ctx.save();
    ctx.beginPath();
    ctx.arc(centroid.x, centroid.y, 8, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(247, 111, 0, 0.9)";
    ctx.lineWidth = 2.2;
    ctx.stroke();
    ctx.restore();
  });
}

function buildTooltipHtml(hit) {
  if (hit.type === "zone") {
    const zone = state.dataIndexes.zonesById.get(hit.id);
    const count = state.dataIndexes.zoneOdCounts.get(hit.id) || 0;
    return `<strong>Zone ${zone.id}</strong><br>Centroid: ${formatCoord(zone.centroid.lat)}, ${formatCoord(zone.centroid.lon)}<br>Related OD: ${count}`;
  }
  if (hit.type === "route") {
    const route = state.dataIndexes.routesById.get(hit.id);
    return `<strong>Route ${route.id}</strong><br>Stops: ${route.stops_seq.length}<br>Start: ${route.start_stop_id}<br>End: ${route.end_stop_id}`;
  }
  if (hit.type === "stop") {
    const stop = state.dataIndexes.stopsById.get(hit.id);
    return `<strong>Stop ${stop.id}</strong><br>Lat/Lon: ${formatCoord(stop.lat)}, ${formatCoord(stop.lon)}<br>Routes: ${stop.route_ids.join(", ") || "None"}`;
  }
  if (hit.type === "od") {
    const od = state.dataIndexes.odById.get(hit.id);
    return `<strong>${od.id}</strong><br>O: ${od.origin_zone_id}<br>D: ${od.destination_zone_id}<br>Demand: ${formatNumber(od.demand)}`;
  }
  return "";
}

function updateTooltip(event, hit) {
  if (!hit) {
    tooltip.style.opacity = "0";
    return;
  }
  tooltip.style.opacity = "1";
  tooltip.style.left = `${event.offsetX}px`;
  tooltip.style.top = `${event.offsetY}px`;
  tooltip.innerHTML = buildTooltipHtml(hit);
}

function distanceToSegment(point, start, end) {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const lengthSquared = dx * dx + dy * dy;
  if (!lengthSquared) return Math.hypot(point.x - start.x, point.y - start.y);
  let t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / lengthSquared;
  t = Math.max(0, Math.min(1, t));
  const projection = { x: start.x + t * dx, y: start.y + t * dy };
  return Math.hypot(point.x - projection.x, point.y - projection.y);
}

function pointInPolygon(point, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x, yi = polygon[i].y;
    const xj = polygon[j].x, yj = polygon[j].y;
    const intersect = ((yi > point.y) !== (yj > point.y)) && (point.x < ((xj - xi) * (point.y - yi)) / ((yj - yi) || 1e-9) + xi);
    if (intersect) inside = !inside;
  }
  return inside;
}

function findNearestStop(mouseX, mouseY, thresholdPx) {
  let best = null;
  let bestDistance = thresholdPx;
  for (const stop of state.data.stops) {
    const point = worldToScreen(stop);
    const distance = Math.hypot(point.x - mouseX, point.y - mouseY);
    if (distance <= bestDistance) {
      bestDistance = distance;
      best = { type: "stop", id: stop.id };
    }
  }
  return best;
}

function findNearestRoute(mouseX, mouseY, thresholdPx) {
  let best = null;
  let bestDistance = thresholdPx;
  for (const route of state.data.routes) {
    const points = route.shape.map(worldToScreen);
    for (let index = 0; index < points.length - 1; index += 1) {
      const distance = distanceToSegment({ x: mouseX, y: mouseY }, points[index], points[index + 1]);
      if (distance <= bestDistance) {
        bestDistance = distance;
        best = { type: "route", id: route.id };
      }
    }
  }
  return best;
}

function findNearestOd(mouseX, mouseY, thresholdPx) {
  let best = null;
  let bestDistance = thresholdPx;
  for (const od of state.data.od_pairs) {
    const originZone = state.dataIndexes.zonesById.get(od.origin_zone_id);
    const destinationZone = state.dataIndexes.zonesById.get(od.destination_zone_id);
    if (!originZone || !destinationZone) continue;
    const curve = buildOdCurve(worldToScreen(originZone.centroid), worldToScreen(destinationZone.centroid), od.id);
    let previous = curve.start;
    for (let step = 1; step <= 24; step += 1) {
      const point = quadraticPoint(curve.start, curve.control, curve.end, step / 24);
      const distance = distanceToSegment({ x: mouseX, y: mouseY }, previous, point);
      if (distance <= bestDistance) {
        bestDistance = distance;
        best = { type: "od", id: od.id };
      }
      previous = point;
    }
  }
  return best;
}

function findZoneAtPoint(mouseX, mouseY) {
  for (const zone of state.data.zones) {
    const polygon = zone.boundary.map(worldToScreen);
    if (pointInPolygon({ x: mouseX, y: mouseY }, polygon)) return { type: "zone", id: zone.id };
  }
  return null;
}

function hitTest(mouseX, mouseY) {
  if (!state.data) return null;
  if (state.layers.stop) {
    const stopHit = findNearestStop(mouseX, mouseY, 8);
    if (stopHit) return stopHit;
  }
  if (state.layers.od) {
    const odHit = findNearestOd(mouseX, mouseY, 8);
    if (odHit) return odHit;
  }
  if (state.layers.route) {
    const routeHit = findNearestRoute(mouseX, mouseY, 6);
    if (routeHit) return routeHit;
  }
  if (state.layers.zone) {
    const zoneHit = findZoneAtPoint(mouseX, mouseY);
    if (zoneHit) return zoneHit;
  }
  return null;
}

function handleCanvasMove(event) {
  if (state.drag.active) {
    state.view.offsetX = state.drag.offsetX + (event.offsetX - state.drag.startX);
    state.view.offsetY = state.drag.offsetY + (event.offsetY - state.drag.startY);
    render();
    return;
  }
  const hit = hitTest(event.offsetX, event.offsetY);
  state.hovered = hit;
  updateTooltip(event, hit);
  canvas.style.cursor = hit ? "pointer" : "crosshair";
  render();
}

function handleCanvasClick(event) {
  const hit = hitTest(event.offsetX, event.offsetY);
  state.selected = hit;
  if (!hit) {
    state.selectedODId = null;
    state.selectedRouteOptionKey = null;
    state.selectedStopId = null;
    renderDetails();
    renderOdList();
    render();
    return;
  }
  if (hit.type === "od") {
    state.selectedODId = hit.id;
    state.selectedRouteOptionKey = null;
  } else if (hit.type === "stop") {
    state.selectedStopId = hit.id;
  } else {
    state.selectedStopId = null;
  }
  renderDetails();
  renderOdList();
  render();
}

function handleWheel(event) {
  event.preventDefault();
  const zoomFactor = event.deltaY < 0 ? 1.12 : 0.89;
  const worldBefore = screenToWorld(event.offsetX, event.offsetY);
  state.view.scale *= zoomFactor;
  state.view.offsetX = event.offsetX - worldBefore.lon * state.view.scale;
  state.view.offsetY = event.offsetY + worldBefore.lat * state.view.scale;
  render();
}

canvas.addEventListener("mousemove", handleCanvasMove);
canvas.addEventListener("mouseleave", () => {
  state.hovered = null;
  tooltip.style.opacity = "0";
  canvas.style.cursor = "crosshair";
  render();
});
canvas.addEventListener("click", handleCanvasClick);
canvas.addEventListener("mousedown", (event) => {
  state.drag.active = true;
  state.drag.startX = event.offsetX;
  state.drag.startY = event.offsetY;
  state.drag.offsetX = state.view.offsetX;
  state.drag.offsetY = state.view.offsetY;
});
window.addEventListener("mouseup", () => {
  state.drag.active = false;
});
canvas.addEventListener("wheel", handleWheel, { passive: false });

document.getElementById("loadButton").addEventListener("click", loadNetwork);
document.getElementById("calculateKpiButton").addEventListener("click", calculateKpi);
document.getElementById("fitButton").addEventListener("click", fitToData);
coverageRadiusInput.addEventListener("change", () => {
  state.coverageRadiusM = Number.parseFloat(coverageRadiusInput.value) || 50;
  renderDetails();
  render();
});
sortSelect.addEventListener("change", () => {
  state.sortMode = sortSelect.value;
  renderOdList();
});
hideInvalidToggle.addEventListener("change", () => {
  state.hideInvalidOD = hideInvalidToggle.checked;
  renderOdList();
});
for (const [key, input] of Object.entries(layerInputs)) {
  input.addEventListener("change", () => {
    state.layers[key] = input.checked;
    render();
  });
}
window.addEventListener("resize", resizeCanvas);
resizeCanvas();
loadNetwork();

