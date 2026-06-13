const DATA_URL = "mission-control-data.json";
const SVG_NS = "http://www.w3.org/2000/svg";
const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

function fmt(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "unavailable";
  }
  return `${numberFormat.format(Number(value))}${suffix}`;
}

function textNode(tag, value, attrs = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  node.textContent = value;
  Object.entries(attrs).forEach(([key, val]) => node.setAttribute(key, val));
  return node;
}

function svgNode(tag, attrs = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs).forEach(([key, val]) => node.setAttribute(key, val));
  return node;
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
}

function renderMetrics(data) {
  const metrics = [
    ["Audited measurements", data.audited_measurements],
    ["Verified artifacts", `${data.metrics.verified_artifacts}/${data.metrics.total_artifacts}`],
    ["Sources registered", data.metrics.data_sources],
    ["Chemistry families", data.metrics.chemistry_families],
    ["Candidate dossiers", data.metrics.candidate_dossiers],
    ["Physics fixtures", data.metrics.physics_fixtures],
    ["Mission fixtures", data.metrics.mission_fixtures],
  ];
  const grid = document.getElementById("metricsGrid");
  grid.innerHTML = "";
  metrics.forEach(([name, value]) => {
    const tile = document.createElement("div");
    tile.className = "metric";
    tile.innerHTML = `<p class="value">${value}</p><p class="name">${name}</p>`;
    grid.appendChild(tile);
  });
}

function renderFrontierChart(data) {
  const container = document.getElementById("frontierChart");
  container.innerHTML = "";
  const width = 1120;
  const height = 430;
  const margin = { top: 36, right: 56, bottom: 54, left: 190 };
  const lanes = ["audited measurements", "local calculation fixture", "mission pack input"];
  const values = data.frontier.points
    .map((point) => point.specific_energy_Wh_kg)
    .filter((value) => value !== null && value !== undefined);
  const maxValue = Math.max(1000, ...values) * 1.12;
  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;
  const laneGap = chartHeight / (lanes.length - 1);
  const x = (value) => margin.left + (Number(value) / maxValue) * chartWidth;
  const y = (lane) => margin.top + lanes.indexOf(lane) * laneGap;

  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    "aria-label": data.frontier.title,
  });
  const unknownStart = x(data.frontier.max_configured_mission_input_Wh_kg || maxValue * 0.72);
  svg.appendChild(
    svgNode("rect", {
      x: unknownStart,
      y: margin.top - 20,
      width: width - margin.right - unknownStart,
      height: chartHeight + 38,
      fill: "rgba(255, 107, 107, 0.08)",
    }),
  );
  svg.appendChild(
    textNode("text", "unknown / unvalidated region", {
      x: unknownStart + 12,
      y: margin.top - 4,
      class: "chart-note",
    }),
  );

  const tickCount = 5;
  for (let index = 0; index <= tickCount; index += 1) {
    const value = (maxValue / tickCount) * index;
    const tickX = x(value);
    svg.appendChild(
      svgNode("line", {
        x1: tickX,
        x2: tickX,
        y1: margin.top - 10,
        y2: height - margin.bottom + 8,
        stroke: "#1c2634",
        "stroke-width": index === 0 ? 2 : 1,
      }),
    );
    svg.appendChild(
      textNode("text", fmt(value), {
        x: tickX,
        y: height - 22,
        "text-anchor": "middle",
        class: "axis-label",
      }),
    );
  }

  lanes.forEach((lane) => {
    const laneY = y(lane);
    svg.appendChild(
      svgNode("line", {
        x1: margin.left,
        x2: width - margin.right,
        y1: laneY,
        y2: laneY,
        stroke: "#273242",
        "stroke-width": 1,
      }),
    );
    svg.appendChild(
      textNode("text", lane, {
        x: 22,
        y: laneY + 4,
        class: "chart-label",
      }),
    );
  });

  const laneLabelCounts = {};
  data.frontier.points.forEach((point) => {
    const laneY = y(point.lane);
    const value = point.specific_energy_Wh_kg;
    if (value === null || value === undefined) {
      svg.appendChild(
        svgNode("circle", {
          cx: margin.left,
          cy: laneY,
          r: 8,
          fill: "transparent",
          stroke: "#ff6b6b",
          "stroke-width": 2,
        }),
      );
      svg.appendChild(
        textNode("text", "no audited pack/cell records", {
          x: margin.left + 18,
          y: laneY + 5,
          class: "chart-note",
        }),
      );
      return;
    }

    const pointX = x(value);
    const color = point.lane === "mission pack input" ? "#f0b84c" : "#4fd8ff";
    const laneIndex = laneLabelCounts[point.lane] || 0;
    laneLabelCounts[point.lane] = laneIndex + 1;
    if (point.lane === "mission pack input") {
      svg.appendChild(
        svgNode("line", {
          x1: pointX,
          x2: pointX,
          y1: laneY - 28,
          y2: laneY + 28,
          stroke: color,
          "stroke-width": 2,
        }),
      );
    }
    svg.appendChild(
      svgNode("circle", {
        cx: pointX,
        cy: laneY,
        r: point.boundary === "complete pack" ? 8 : 6,
        fill: color,
        stroke: "#05070a",
        "stroke-width": 2,
      }),
    );
    const label = `${point.boundary}: ${fmt(value, " Wh/kg")}`;
    let labelY = laneY - 12;
    if (point.lane === "mission pack input") {
      labelY = laneY + (laneIndex % 2 === 0 ? -18 : 25);
    } else if (point.boundary === "complete pack") {
      labelY = laneY - 30;
    } else if (point.boundary === "complete cell") {
      labelY = laneY + 25;
    }
    svg.appendChild(
      textNode("text", label, {
        x: Math.min(pointX + 12, width - margin.right - 230),
        y: labelY,
        class: "chart-note",
      }),
    );
  });

  svg.appendChild(
    textNode("text", "Pack specific energy (Wh/kg)", {
      x: margin.left + chartWidth / 2,
      y: height - 4,
      "text-anchor": "middle",
      class: "axis-label",
    }),
  );
  container.appendChild(svg);
}

function renderMissionBands(data) {
  const root = document.getElementById("missionBands");
  root.innerHTML = "";
  data.frontier.mission_bands.forEach((band) => {
    const item = document.createElement("article");
    item.className = "band";
    const statusClass = band.feasible ? "ok" : "blocked";
    item.innerHTML = `
      <p class="name">${band.label}</p>
      <p class="value">${fmt(band.pack_specific_energy_Wh_kg, " Wh/kg")}</p>
      <span class="status ${statusClass}">${band.feasible ? "feasible fixture" : "infeasible fixture"}</span>
      <p class="detail">${band.claim_boundary}</p>
    `;
    root.appendChild(item);
  });
}

function renderEvidenceLedger(data) {
  const body = document.getElementById("evidenceLedger");
  body.innerHTML = "";
  data.evidence_ledger.slice(0, 10).forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.record}</td>
      <td>${row.domain}</td>
      <td>${row["evidence class"]}</td>
      <td>${row.status}</td>
    `;
    body.appendChild(tr);
  });
}

function renderSourceReadiness(data) {
  const root = document.getElementById("sourceReadiness");
  root.innerHTML = "";
  data.connector_readiness.forEach((source) => {
    const item = document.createElement("article");
    item.className = "source-item";
    const blocked = source.trusted_publication_allowed ? "" : "blocked";
    item.innerHTML = `
      <div>
        <p class="name">${source.source}</p>
        <p class="detail">${source.readiness}</p>
      </div>
      <span class="status ${blocked}">${source.license_status}</span>
    `;
    root.appendChild(item);
  });
}

function renderCandidateDossiers(data) {
  const root = document.getElementById("candidateDossiers");
  root.innerHTML = "";
  const summary = data.candidate_dossier_summary;
  setText(
    "candidateSummary",
    `${summary.candidate_count} dossiers | ${summary.audited_measurement_count} audited measurements | ranking blocked`,
  );
  const ordered = [...data.candidate_dossiers].sort((left, right) => {
    if (left.id.includes("hemp")) return -1;
    if (right.id.includes("hemp")) return 1;
    return left.display_name.localeCompare(right.display_name);
  });
  ordered.forEach((candidate) => {
    const item = document.createElement("article");
    item.className = `candidate-card ${candidate.id.includes("hemp") ? "focus" : ""}`;
    const blockers = candidate.ranking_blockers.slice(0, 4);
    const materialCount = candidate.materials_project_material_ids.length;
    item.innerHTML = `
      <div class="candidate-card-head">
        <div>
          <p class="name">${candidate.display_name}</p>
          <p class="detail">${candidate.candidate_type}</p>
        </div>
        <span class="status blocked">unranked</span>
      </div>
      <p class="candidate-boundary">${candidate.system_boundary}</p>
      <div class="candidate-data-row">
        <span>${candidate.audited_measurement_count} audited records</span>
        <span>${materialCount} MP metadata ids</span>
        <span>${candidate.fixture_reference_ids.length} local fixtures</span>
      </div>
      <p class="label">Missing proof</p>
      <ul>${blockers.map((field) => `<li>${field}</li>`).join("")}</ul>
    `;
    root.appendChild(item);
  });
}

function renderMaterialsProjectAppendix(data) {
  const root = document.getElementById("mpAppendix");
  const appendix = data.materials_project_appendix;
  root.innerHTML = "";
  setText(
    "mpSummary",
    `${appendix.query_count} queries | ${appendix.record_count} metadata records | ranking evidence: no`,
  );
  appendix.queries.forEach((query) => {
    const item = document.createElement("article");
    item.className = "source-item";
    const stateClass = query.status === "fetched" ? "ok" : "blocked";
    const ids =
      query.material_ids.length > 0
        ? query.material_ids.slice(0, 4).join(", ")
        : query.error_message || "no published metadata";
    item.innerHTML = `
      <div>
        <p class="name">${query.label}</p>
        <p class="detail">${query.query} | ${ids}</p>
      </div>
      <span class="status ${stateClass}">${query.status}</span>
    `;
    root.appendChild(item);
  });
}

function renderTargetBlueprint(data) {
  const root = document.getElementById("targetBlueprint");
  root.innerHTML = "";
  const system = data.conceptual_target_system;
  setText("blueprintBoundary", system.claim_boundary);
  const svg = svgNode("svg", {
    viewBox: "0 0 920 360",
    "aria-label": system.title,
  });
  svg.appendChild(
    svgNode("rect", {
      x: 18,
      y: 18,
      width: 884,
      height: 324,
      rx: 8,
      fill: "#060a10",
      stroke: "#273242",
    }),
  );
  svg.appendChild(
    svgNode("path", {
      d: "M106 214 C214 174 345 158 508 158 L734 158 C790 158 836 180 868 218 C802 210 742 204 688 202 L496 198 C344 195 214 202 106 214 Z",
      fill: "rgba(79, 216, 255, 0.10)",
      stroke: "#4fd8ff",
      "stroke-width": 2,
    }),
  );
  svg.appendChild(
    svgNode("path", {
      d: "M282 166 L94 82 L520 160 Z",
      fill: "rgba(173, 140, 255, 0.14)",
      stroke: "#ad8cff",
      "stroke-width": 2,
    }),
  );
  svg.appendChild(
    svgNode("path", {
      d: "M346 198 L118 300 L574 200 Z",
      fill: "rgba(85, 216, 139, 0.12)",
      stroke: "#55d88b",
      "stroke-width": 2,
    }),
  );
  svg.appendChild(
    svgNode("rect", {
      x: 320,
      y: 175,
      width: 248,
      height: 24,
      rx: 4,
      fill: "rgba(240, 184, 76, 0.18)",
      stroke: "#f0b84c",
    }),
  );
  svg.appendChild(
    svgNode("path", {
      d: "M604 163 C632 126 678 109 731 118 C694 144 665 162 630 181 Z",
      fill: "rgba(79, 216, 255, 0.08)",
      stroke: "#4fd8ff",
      "stroke-width": 2,
    }),
  );
  const propulsors = [
    [210, 152],
    [300, 166],
    [610, 166],
    [752, 181],
    [258, 225],
    [602, 214],
  ];
  propulsors.forEach(([cx, cy]) => {
    svg.appendChild(
      svgNode("circle", {
        cx,
        cy,
        r: 13,
        fill: "#05070a",
        stroke: "#4fd8ff",
        "stroke-width": 2,
      }),
    );
    svg.appendChild(
      svgNode("circle", {
        cx,
        cy,
        r: 4,
        fill: "#4fd8ff",
      }),
    );
  });
  const callouts = [
    ["Battery pack corridor", 330, 142, 420, 170],
    ["Thermal loop", 574, 250, 548, 202],
    ["Payload + reserve margin", 648, 82, 620, 156],
    ["Distributed propulsion", 92, 58, 205, 150],
    ["Structural option", 126, 320, 304, 232],
  ];
  callouts.forEach(([label, x1, y1, x2, y2]) => {
    svg.appendChild(
      svgNode("line", {
        x1,
        y1,
        x2,
        y2,
        stroke: "#566172",
        "stroke-width": 1,
      }),
    );
    svg.appendChild(
      textNode("text", label, {
        x: x1,
        y: y1 - 6,
        class: "chart-note",
      }),
    );
  });
  svg.appendChild(
    textNode("text", "CONCEPTUAL TARGET - NOT A DESIGN CLAIM", {
      x: 458,
      y: 40,
      "text-anchor": "middle",
      class: "axis-label",
    }),
  );
  root.appendChild(svg);

  const labels = document.getElementById("blueprintLabels");
  labels.innerHTML = "";
  system.labels.forEach((label) => {
    const item = document.createElement("article");
    item.className = "system-label";
    item.innerHTML = `<p class="name">${label.name}</p><p class="detail">${label.status}</p>`;
    labels.appendChild(item);
  });
}

function renderArtifacts(data) {
  const root = document.getElementById("artifactList");
  root.innerHTML = "";
  data.artifact_verification.forEach((artifact) => {
    const item = document.createElement("article");
    item.className = "artifact-item";
    item.innerHTML = `
      <p class="name">${artifact.artifact}</p>
      <p class="detail">${artifact.type} | ${artifact.hash_matches ? "hash verified" : "hash mismatch"}</p>
      <code>${artifact.sha256}</code>
    `;
    root.appendChild(item);
  });
}

function render(data) {
  setText("phaseBadge", `Phase ${data.phase}`);
  setText("rankingGate", data.ranking_gate_reason);
  setText("generatedAt", `Generated ${new Date(data.generated_at_utc).toLocaleString()}`);
  setText("frontierNote", data.frontier.unknown_region_note);
  renderMetrics(data);
  renderFrontierChart(data);
  renderMissionBands(data);
  renderCandidateDossiers(data);
  renderTargetBlueprint(data);
  renderEvidenceLedger(data);
  renderSourceReadiness(data);
  renderMaterialsProjectAppendix(data);
  renderArtifacts(data);
}

fetch(DATA_URL, { cache: "no-store" })
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Unable to load ${DATA_URL}: ${response.status}`);
    }
    return response.json();
  })
  .then(render)
  .catch((error) => {
    setText("generatedAt", "Data load failed");
    document.getElementById("frontierChart").innerHTML =
      `<div class="guardrail">${error.message}</div>`;
  });
