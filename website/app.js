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
    svg.appendChild(
      textNode("text", label, {
        x: Math.min(pointX + 12, width - margin.right - 230),
        y: laneY - 12,
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
  renderEvidenceLedger(data);
  renderSourceReadiness(data);
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
