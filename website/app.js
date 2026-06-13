const DATA_URL = "mission-control-data.json";
const SVG_NS = "http://www.w3.org/2000/svg";
const numberFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

function fmt(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "unavailable";
  }
  return `${numberFormat.format(Number(value))}${suffix}`;
}

function fmtBytes(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "unavailable";
  }
  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = Number(value);
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
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
    ["Simulation rows", data.metrics.simulation_rows],
    ["Aircraft systems", data.metrics.aircraft_systems],
    ["Material candidates", data.metrics.material_candidates],
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

function renderMeasurementPipeline(data) {
  const pipeline = data.measurement_pipeline;
  setText(
    "measurementPipelineSummary",
    `${pipeline.approved_source.name} | ${pipeline.approved_source.license} | ${pipeline.approved_source.system_boundary}`,
  );
  const root = document.getElementById("measurementPipeline");
  root.innerHTML = "";
  const raw = pipeline.raw_snapshot;
  const quality = pipeline.quality_report;
  [
    ["Approved source", pipeline.approved_source.doi, "ok"],
    ["Raw manifest", pipeline.raw_manifest_present ? "present" : "missing", pipeline.raw_manifest_present ? "ok" : "blocked"],
    ["Selected raw size", fmtBytes(raw.selected_size_bytes), "neutral"],
    ["Downloaded raw size", fmtBytes(raw.downloaded_size_bytes), raw.downloaded_size_bytes > 0 ? "ok" : "blocked"],
    ["Parser status", quality ? quality.quality_status : "not parsed", quality ? "ok" : "blocked"],
    ["Pack evidence", pipeline.pack_level_evidence ? "yes" : "no", "blocked"],
  ].forEach(([label, value, state]) => {
    const item = document.createElement("article");
    item.className = "pipeline-step";
    item.innerHTML = `
      <p class="name">${label}</p>
      <p class="value">${value}</p>
      <span class="status ${state === "ok" ? "ok" : state === "blocked" ? "blocked" : ""}">${state}</span>
    `;
    root.appendChild(item);
  });
  setText("measurementBoundary", pipeline.claim_boundary);
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

function renderAviationRequirementMap(data) {
  const root = document.getElementById("aviationRequirementMap");
  root.innerHTML = "";
  const rows = data.aviation_requirement_map.rows;
  const focus =
    rows.filter(
      (row) =>
        row.base_case_id === "mission.regional_demonstrator" &&
        row.profile === "baseline" &&
        Number(row.payload_fraction) === 0.6,
    ) ||
    [];
  const sourceRows = focus.length > 0 ? focus : rows.slice(0, 15);
  const routes = [...new Set(sourceRows.map((row) => Number(row.route_distance_km)))].sort(
    (left, right) => left - right,
  );
  const energies = [
    ...new Set(sourceRows.map((row) => Number(row.pack_specific_energy_Wh_kg))),
  ].sort((left, right) => left - right);
  const width = 760;
  const height = 330;
  const margin = { top: 42, right: 24, bottom: 58, left: 86 };
  const cellW = (width - margin.left - margin.right) / routes.length;
  const cellH = (height - margin.top - margin.bottom) / energies.length;
  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    "aria-label": "Aviation requirement feasibility heatmap",
  });

  energies.forEach((energy, energyIndex) => {
    routes.forEach((route, routeIndex) => {
      const row = sourceRows.find(
        (candidate) =>
          Number(candidate.route_distance_km) === route &&
          Number(candidate.pack_specific_energy_Wh_kg) === energy,
      );
      const feasible = row && row.feasible;
      const rectX = margin.left + routeIndex * cellW;
      const rectY = margin.top + (energies.length - energyIndex - 1) * cellH;
      svg.appendChild(
        svgNode("rect", {
          x: rectX,
          y: rectY,
          width: Math.max(cellW - 4, 12),
          height: Math.max(cellH - 4, 12),
          rx: 4,
          fill: feasible ? "rgba(85, 216, 139, 0.55)" : "rgba(255, 107, 107, 0.34)",
          stroke: feasible ? "#55d88b" : "#ff6b6b",
        }),
      );
      if (row) {
        svg.appendChild(
          textNode("text", feasible ? "OK" : "NO", {
            x: rectX + cellW / 2,
            y: rectY + cellH / 2 + 4,
            "text-anchor": "middle",
            class: "heatmap-cell-label",
          }),
        );
      }
    });
  });

  routes.forEach((route, index) => {
    svg.appendChild(
      textNode("text", `${fmt(route)} km`, {
        x: margin.left + index * cellW + cellW / 2,
        y: height - 26,
        "text-anchor": "middle",
        class: "axis-label",
      }),
    );
  });
  energies.forEach((energy, index) => {
    svg.appendChild(
      textNode("text", fmt(energy), {
        x: margin.left - 12,
        y: margin.top + (energies.length - index - 0.5) * cellH + 4,
        "text-anchor": "end",
        class: "axis-label",
      }),
    );
  });
  svg.appendChild(
    textNode("text", "Regional demonstrator baseline payload sweep", {
      x: margin.left,
      y: 24,
      class: "chart-label",
    }),
  );
  svg.appendChild(
    textNode("text", "Pack specific energy (Wh/kg)", {
      x: 18,
      y: margin.top + 4,
      class: "axis-label",
    }),
  );
  svg.appendChild(
    textNode("text", "Route distance", {
      x: margin.left + (width - margin.left - margin.right) / 2,
      y: height - 4,
      "text-anchor": "middle",
      class: "axis-label",
    }),
  );
  root.appendChild(svg);
}

function renderLongHaulFeasibility(data) {
  const root = document.getElementById("longHaulTable");
  root.innerHTML = "";
  data.long_haul_feasibility.rows.forEach((row) => {
    const tr = document.createElement("tr");
    const reasons =
      row.infeasibility_reasons.length > 0
        ? row.infeasibility_reasons.slice(0, 2).join("; ")
        : "diagnostic assumptions pass";
    tr.innerHTML = `
      <td>${row.name}</td>
      <td>${fmt(row.distance_km, " km")}</td>
      <td>${fmt(row.required_pack_specific_energy_Wh_kg, " Wh/kg")}</td>
      <td>${fmt(row.battery_mass_fraction_at_500Whkg_pack * 100, "%")}</td>
      <td><span class="status ${row.feasible ? "ok" : "blocked"}">${row.feasibility_status}</span></td>
      <td>${reasons}</td>
    `;
    root.appendChild(tr);
  });
  setText("longHaulBoundary", data.long_haul_feasibility.claim_boundary);
}

function renderSimulationCampaign(data) {
  const summary = data.simulation_campaign_summary;
  setText(
    "simulationSummary",
    `${summary.aviation_requirement_grid_rows} aviation rows | ${summary.pack_trade_space_rows} pack rows | evidence: simulation only`,
  );
  renderAviationRequirementMap(data);

  const stats = document.getElementById("simulationStats");
  stats.innerHTML = "";
  [
    ["Feasible rows", summary.aviation_feasible_count],
    ["Infeasible rows", summary.aviation_infeasible_count],
    ["Bounded requirements", summary.bounded_requirement_count],
    ["Candidate envelopes", summary.candidate_envelope_count],
    ["Long-haul cases", summary.long_haul_study_count],
    ["Long-haul infeasible", summary.long_haul_infeasible_count],
  ].forEach(([label, value]) => {
    const item = document.createElement("article");
    item.className = "simulation-stat";
    item.innerHTML = `<p class="value">${fmt(value)}</p><p class="name">${label}</p>`;
    stats.appendChild(item);
  });
  renderLongHaulFeasibility(data);

  const truthList = document.getElementById("truthList");
  truthList.innerHTML = "";
  data.what_would_need_to_be_true.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    truthList.appendChild(li);
  });
}

function renderManufacturerExamples(data) {
  const aircraft = document.getElementById("aircraftExamples");
  const propulsion = document.getElementById("propulsionExamples");
  aircraft.innerHTML = "";
  propulsion.innerHTML = "";
  data.manufacturer_examples.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.manufacturer}</td>
      <td>${row.vehicle_name}</td>
      <td>${row.aircraft_class}</td>
      <td>${fmt(row.range_km, " km")}</td>
      <td>${fmt(row.passenger_capacity)}</td>
      <td><span class="status">${row.values_status}</span></td>
    `;
    aircraft.appendChild(tr);
  });
  data.propulsion_examples.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.manufacturer}</td>
      <td>${row.system_name}</td>
      <td>${row.system_type}</td>
      <td>${fmt(row.propulsor_count)}</td>
      <td><span class="status">${row.values_status}</span></td>
    `;
    propulsion.appendChild(tr);
  });
}

function renderDatasetCandidates(data) {
  const root = document.getElementById("datasetCandidates");
  root.innerHTML = "";
  data.dataset_candidates.forEach((dataset) => {
    const item = document.createElement("article");
    item.className = "source-item";
    const state = dataset.license_status.includes("approved") ? "ok" : "blocked";
    item.innerHTML = `
      <div>
        <p class="name">${dataset.name}</p>
        <p class="detail">${dataset.category} | ${dataset.system_boundary}</p>
      </div>
      <span class="status ${state}">${dataset.license_status}</span>
    `;
    root.appendChild(item);
  });
}

function renderPartnerDossiers(data) {
  const root = document.getElementById("partnerDossiers");
  root.innerHTML = "";
  const manifest = data.partner_dossiers;
  if (!manifest) {
    root.innerHTML = '<div class="guardrail">Partner dossiers have not been generated.</div>';
    return;
  }
  Object.entries(manifest.written_artifacts).forEach(([id, artifacts]) => {
    const item = document.createElement("article");
    item.className = "source-item";
    const mdPath = artifacts.markdown.path;
    item.innerHTML = `
      <div>
        <p class="name">${id.replaceAll("_", " ")}</p>
        <p class="detail">${mdPath}</p>
      </div>
      <span class="status ok">latest</span>
    `;
    root.appendChild(item);
  });
  setText(
    "partnerSummary",
    `${manifest.dossier_count} dossiers | archive: ${manifest.archive_created ? "created" : "unchanged"} | signature ${manifest.input_signature_sha256.slice(0, 10)}`,
  );
}

function renderPackSensitivity(data) {
  const root = document.getElementById("packSensitivity");
  root.innerHTML = "";
  data.pack_trade_space_summary.sensitivity.slice(0, 6).forEach((item) => {
    const row = document.createElement("article");
    row.className = "sensitivity-row";
    row.innerHTML = `
      <div>
        <p class="name">${item.variable.replaceAll("_", " ")}</p>
        <p class="detail">Spread: ${fmt(item.mean_required_cell_energy_spread_Wh_kg, " Wh/kg")}</p>
      </div>
      <span class="status">architecture</span>
    `;
    root.appendChild(row);
  });
}

function renderInfeasibleLedger(data) {
  const root = document.getElementById("infeasibleLedger");
  root.innerHTML = "";
  data.infeasible_region_ledger.slice(0, 8).forEach((row) => {
    const item = document.createElement("article");
    item.className = "source-item";
    item.innerHTML = `
      <div>
        <p class="name">${row.base_case_id} | ${row.profile}</p>
        <p class="detail">${fmt(row.route_distance_km, " km")} | ${fmt(row.pack_specific_energy_Wh_kg, " Wh/kg")} | ${row.reasons}</p>
      </div>
      <span class="status blocked">${row.limiting_constraint}</span>
    `;
    root.appendChild(item);
  });
}

function renderCandidateEnvelopes(data) {
  const root = document.getElementById("candidateEnvelopeConsole");
  root.innerHTML = "";
  const ordered = [...data.candidate_envelopes].sort((left, right) => {
    if (left.candidate_id.includes("hemp")) return -1;
    if (right.candidate_id.includes("hemp")) return 1;
    return left.display_name.localeCompare(right.display_name);
  });
  ordered.slice(0, 8).forEach((candidate) => {
    const item = document.createElement("article");
    item.className = `envelope-card ${
      candidate.candidate_id.includes("hemp") ? "focus" : ""
    }`;
    const projection = candidate.envelopes.find(
      (entry) => entry.mode === "theoretical_projection",
    );
    const optimistic = candidate.envelopes.find((entry) => entry.mode === "optimistic");
    item.innerHTML = `
      <p class="name">${candidate.display_name}</p>
      <p class="detail">${candidate.basis}</p>
      <div class="candidate-data-row">
        <span>Optimistic ${fmt(optimistic.full_cell_specific_energy_Wh_kg, " Wh/kg")}</span>
        <span>Projection ${fmt(projection.full_cell_specific_energy_Wh_kg, " Wh/kg")}</span>
        <span>Ranking no</span>
      </div>
      <p class="detail">${candidate.hemp_specific_guardrail || "Envelope only; audit required."}</p>
    `;
    root.appendChild(item);
  });
}

function renderMaterialHypothesisFrontier(data) {
  const summary = data.materials_campaign_summary;
  setText(
    "materialSummary",
    `${summary.material_candidate_count} materials | ${summary.energy_estimated_candidate_count} estimated | ${summary.energy_blocked_candidate_count} blocked`,
  );
  setText(
    "materialBoundary",
    "Material screening is simulation-only. No material card is an audited measurement, DFT proof, pack proof, or candidate ranking.",
  );

  const chart = document.getElementById("materialFrontierChart");
  chart.innerHTML = "";
  const estimated = data.material_candidate_cards
    .filter((card) => card.engineering_bounded_pack_Wh_kg !== null)
    .sort(
      (left, right) =>
        Number(right.engineering_bounded_pack_Wh_kg) -
        Number(left.engineering_bounded_pack_Wh_kg),
    )
    .slice(0, 8);
  const requirements = data.material_mission_requirements;
  const values = [
    ...estimated.flatMap((card) => [
      card.theoretical_only_pack_Wh_kg,
      card.engineering_bounded_pack_Wh_kg,
    ]),
    ...requirements.map((row) => row.required_pack_specific_energy_Wh_kg),
  ].filter((value) => value !== null && value !== undefined);
  const maxValue = Math.max(1000, ...values) * 1.08;
  const width = 1120;
  const height = 460;
  const margin = { top: 44, right: 42, bottom: 52, left: 260 };
  const rowHeight = (height - margin.top - margin.bottom) / Math.max(estimated.length, 1);
  const x = (value) => margin.left + (Number(value) / maxValue) * (width - margin.left - margin.right);
  const svg = svgNode("svg", {
    viewBox: `0 0 ${width} ${height}`,
    "aria-label": "Material hypothesis frontier",
  });

  svg.appendChild(
    svgNode("rect", {
      x: x(1000),
      y: margin.top - 18,
      width: width - margin.right - x(1000),
      height: height - margin.top - margin.bottom + 34,
      fill: "rgba(255, 107, 107, 0.07)",
    }),
  );
  svg.appendChild(
    textNode("text", "unknown / unvalidated aviation region", {
      x: x(1000) + 12,
      y: margin.top - 3,
      class: "chart-note",
    }),
  );

  for (let index = 0; index <= 5; index += 1) {
    const value = (maxValue / 5) * index;
    const tickX = x(value);
    svg.appendChild(
      svgNode("line", {
        x1: tickX,
        x2: tickX,
        y1: margin.top - 10,
        y2: height - margin.bottom + 8,
        stroke: "#1c2634",
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

  requirements.forEach((requirement, index) => {
    const reqX = x(requirement.required_pack_specific_energy_Wh_kg);
    svg.appendChild(
      svgNode("line", {
        x1: reqX,
        x2: reqX,
        y1: margin.top - 8,
        y2: height - margin.bottom + 8,
        stroke: index < 2 ? "#55d88b" : "#f0b84c",
        "stroke-width": 1.4,
        "stroke-dasharray": "5 6",
      }),
    );
    svg.appendChild(
      textNode("text", requirement.name.replace(" stress test", ""), {
        x: Math.min(reqX + 6, width - margin.right - 130),
        y: margin.top + 13 + index * 16,
        class: "chart-note",
      }),
    );
  });

  estimated.forEach((card, index) => {
    const y = margin.top + index * rowHeight + rowHeight / 2;
    svg.appendChild(
      textNode("text", card.display_name, {
        x: 22,
        y: y + 4,
        class: "chart-label",
      }),
    );
    svg.appendChild(
      svgNode("line", {
        x1: margin.left,
        x2: x(card.theoretical_only_pack_Wh_kg),
        y1: y - 7,
        y2: y - 7,
        stroke: "#f0b84c",
        "stroke-width": 9,
        "stroke-linecap": "round",
      }),
    );
    svg.appendChild(
      svgNode("line", {
        x1: margin.left,
        x2: x(card.engineering_bounded_pack_Wh_kg),
        y1: y + 8,
        y2: y + 8,
        stroke: "#4fd8ff",
        "stroke-width": 9,
        "stroke-linecap": "round",
      }),
    );
    svg.appendChild(
      textNode("text", `eng ${fmt(card.engineering_bounded_pack_Wh_kg, " Wh/kg")}`, {
        x: Math.min(x(card.engineering_bounded_pack_Wh_kg) + 10, width - margin.right - 90),
        y: y + 13,
        class: "chart-note",
      }),
    );
  });

  svg.appendChild(
    textNode("text", "theoretical-only pack proxy", {
      x: margin.left,
      y: 24,
      class: "chart-note",
    }),
  );
  svg.appendChild(
    textNode("text", "engineering-bounded pack proxy", {
      x: margin.left + 190,
      y: 24,
      class: "chart-note",
    }),
  );
  svg.appendChild(
    textNode("text", "Pack specific energy proxy (Wh/kg)", {
      x: margin.left + (width - margin.left - margin.right) / 2,
      y: height - 4,
      "text-anchor": "middle",
      class: "axis-label",
    }),
  );
  chart.appendChild(svg);

  const cards = document.getElementById("materialCards");
  cards.innerHTML = "";
  const featured = [...data.material_candidate_cards]
    .sort((left, right) => {
      if (left.material_id.includes("hemp")) return -1;
      if (right.material_id.includes("hemp")) return 1;
      return left.display_name.localeCompare(right.display_name);
    })
    .slice(0, 10);
  featured.forEach((card) => {
    const item = document.createElement("article");
    item.className = `material-card ${card.material_id.includes("hemp") ? "focus" : ""}`;
    const blocked = card.energy_estimate_status.startsWith("blocked");
    item.innerHTML = `
      <div class="candidate-card-head">
        <div>
          <p class="name">${card.display_name}</p>
          <p class="detail">${card.role} | ${card.evidence_level}</p>
        </div>
        <span class="status ${blocked ? "blocked" : "ok"}">${blocked ? "blocked" : "estimated"}</span>
      </div>
      <p class="candidate-boundary">${card.system_boundary}</p>
      <div class="candidate-data-row">
        <span>Theoretical ${fmt(card.theoretical_only_pack_Wh_kg, " Wh/kg")}</span>
        <span>Engineered ${fmt(card.engineering_bounded_pack_Wh_kg, " Wh/kg")}</span>
        <span>Ranking no</span>
      </div>
      <p class="detail">${card.hemp_bast_fiber_guardrail || card.claim_boundary}</p>
    `;
    cards.appendChild(item);
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
  renderMeasurementPipeline(data);
  renderMissionBands(data);
  renderSimulationCampaign(data);
  renderManufacturerExamples(data);
  renderPackSensitivity(data);
  renderInfeasibleLedger(data);
  renderCandidateEnvelopes(data);
  renderMaterialHypothesisFrontier(data);
  renderCandidateDossiers(data);
  renderDatasetCandidates(data);
  renderPartnerDossiers(data);
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
