from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from battery_frontier.dashboards.data import (  # noqa: E402
    chemistry_readiness_frame,
    citation_readiness_frame,
    evidence_ledger_frame,
    load_dashboard_bundle,
    phase_readiness_frame,
    physics_boundary_frame,
    source_readiness_frame,
    verify_dashboard_artifacts,
)
from battery_frontier.physics.electrochemistry import (  # noqa: E402
    theoretical_specific_capacity_mAh_g,
    theoretical_specific_energy_Wh_kg,
)
from battery_frontier.physics.system_metrics import (  # noqa: E402
    gravimetric_to_volumetric_energy_Wh_l,
)
from battery_frontier.registry import load_registries  # noqa: E402
from battery_frontier.reporting.daily import generate_daily_report  # noqa: E402
from battery_frontier.reporting.method_cards import (  # noqa: E402
    generate_dashboard_artifacts,
)
from battery_frontier.scientific_audit import (  # noqa: E402
    REQUIRED_RANKING_FIELDS,
    evaluate_ranking_gate,
)

st.set_page_config(
    page_title="Battery Frontier Mission Control",
    page_icon="BF",
    layout="wide",
)

st.markdown(
    """
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
[data-testid="stMetric"] {
    border: 1px solid rgba(120, 120, 120, 0.25);
    border-radius: 0.55rem;
    padding: 0.65rem;
}
.evidence-note {
    border-left: 4px solid #4c78a8;
    padding: 0.55rem 0.8rem;
    background: rgba(76, 120, 168, 0.08);
    margin-bottom: 0.8rem;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def registries():
    return load_registries()


@st.cache_data
def dashboard_bundle():
    return load_dashboard_bundle()


def evidence_note(text: str) -> None:
    st.markdown(f'<div class="evidence-note">{text}</div>', unsafe_allow_html=True)


def result_downloads(prefix: str) -> None:
    bundle = dashboard_bundle()
    artifact_ids = {
        "physics": ("artifact.phase2.results", "artifact.phase2.method_card"),
        "aviation": ("artifact.phase3.results", "artifact.phase3.method_card"),
    }
    selected = artifact_ids[prefix]
    records = {
        artifact["artifact_id"]: artifact for artifact in bundle.manifest["artifacts"]
    }
    columns = st.columns(2)
    for column, artifact_id in zip(columns, selected, strict=True):
        artifact = records[artifact_id]
        path = PROJECT_ROOT / artifact["path"]
        column.download_button(
            label=f"Download {artifact['title']}",
            data=path.read_bytes(),
            file_name=path.name,
            mime="application/json" if path.suffix == ".json" else "text/markdown",
            key=f"download-{artifact_id}",
        )


def mission_control() -> None:
    data = registries()
    bundle = dashboard_bundle()
    gate = evaluate_ranking_gate([])
    st.title("Battery Frontier Mission Control")
    st.caption("Phase 4 prototype: traceable charts, evidence gates, and public artifacts")
    st.warning(
        "No experimental performance dataset has been ingested. "
        "Chemistry ranking is disabled."
    )

    columns = st.columns(6)
    metrics = [
        ("Scientific assumptions", len(data.assumptions)),
        ("Chemistry families", len(data.chemistries)),
        ("Citations", len(data.citations)),
        ("Physics fixtures", len(data.physics_reference_cases)),
        ("Mission fixtures", len(data.segmented_mission_cases)),
        ("Audited measurements", 0),
    ]
    for column, (label, value) in zip(columns, metrics, strict=True):
        column.metric(label, value)

    readiness = phase_readiness_frame(data)
    status_score = {
        "complete": 1.0,
        "foundation complete": 0.8,
        "local foundation complete": 0.75,
        "prototype active": 0.65,
        "not started": 0.0,
    }
    readiness["progress"] = readiness["status"].map(status_score)
    phase_chart = px.bar(
        readiness,
        x="progress",
        y="component",
        color="status",
        orientation="h",
        hover_data=["phase", "evidence gate"],
        range_x=[0, 1],
        title="Program Readiness by Phase",
    )
    phase_chart.update_layout(
        xaxis_title="Local implementation progress, not scientific validation",
        yaxis_title=None,
        legend_title="Status",
    )
    st.plotly_chart(phase_chart, width="stretch")
    evidence_note(
        "Progress indicates implemented software and documentation. It does not "
        "indicate validated chemistry or aircraft readiness."
    )

    st.subheader("Evidence Ledger")
    st.dataframe(
        evidence_ledger_frame(bundle),
        width="stretch",
        hide_index=True,
    )

    verification = verify_dashboard_artifacts(bundle)
    verified_count = int(verification["hash_matches"].sum())
    st.subheader("Reproducible Artifacts")
    left, right = st.columns([1, 3])
    left.metric("Verified artifact hashes", f"{verified_count}/{len(verification)}")
    right.dataframe(
        verification[
            ["artifact", "type", "hash_matches", "evidence status", "claim boundary"]
        ],
        width="stretch",
        hide_index=True,
    )
    st.error(gate.reason)

    st.subheader("Top blockers")
    st.markdown(
        """
1. Dataset-level license review and immutable source snapshots
2. Audited experimental values with conditions and uncertainty
3. Comparable cell/pack boundaries across chemistry families
4. Safety, cycle-life, manufacturing, and supply-chain evidence
5. Aviation-model validation against published studies
"""
    )


def physics_workbench() -> None:
    bundle = dashboard_bundle()
    st.title("Phase 2 Physics Workbench")
    st.warning(
        "Reference cases are mathematical or illustrative fixtures. "
        "They are not experimental benchmarks or candidate rankings."
    )
    results = bundle.physics["cases"]
    selected_name = st.selectbox("Reference calculation", [item["name"] for item in results])
    result = next(item for item in results if item["name"] == selected_name)

    st.code(result["reaction_equation"])
    st.caption(f"Mass basis: {result['mass_basis_description']}")
    columns = st.columns(4)
    columns[0].metric(
        "Reaction mass basis",
        f"{result['reaction_mass_basis_g_mol']:,.3f} g/mol",
    )
    columns[1].metric(
        "Theoretical capacity",
        f"{result['theoretical_specific_capacity_mAh_g']:,.1f} mAh/g",
    )
    columns[2].metric(
        "Active specific energy",
        (
            f"{result['active_specific_energy_Wh_kg']:,.0f} Wh/kg"
            if "active_specific_energy_Wh_kg" in result
            else "not defined"
        ),
    )
    columns[3].metric(
        "Pack specific energy",
        (
            f"{result['pack']['specific_energy_Wh_kg']:,.0f} Wh/kg"
            if "pack" in result
            else "not defined"
        ),
    )

    boundary_rows = [
        {
            "boundary": "reaction mass basis",
            "specific energy (Wh/kg)": result.get("active_specific_energy_Wh_kg"),
            "status": result.get(
                "active_specific_energy_evidence_class",
                result["evidence_class"],
            ),
        }
    ]
    if "cell" in result:
        boundary_rows.append(
            {
                "boundary": "complete illustrative cell",
                "specific energy (Wh/kg)": result["cell"]["specific_energy_Wh_kg"],
                "status": result["cell"]["evidence_class"],
            }
        )
    if "pack" in result:
        boundary_rows.append(
            {
                "boundary": "complete illustrative pack",
                "specific energy (Wh/kg)": result["pack"]["specific_energy_Wh_kg"],
                "status": result["pack"]["evidence_class"],
            }
        )
    st.dataframe(pd.DataFrame(boundary_rows), width="stretch", hide_index=True)
    if len(boundary_rows) > 1:
        boundary_frame = pd.DataFrame(boundary_rows)
        boundary_chart = px.bar(
            boundary_frame,
            x="boundary",
            y="specific energy (Wh/kg)",
            color="boundary",
            text_auto=".0f",
            title="Specific Energy Across Declared System Boundaries",
        )
        boundary_chart.update_layout(showlegend=False)
        st.plotly_chart(boundary_chart, width="stretch")

    if "cell" in result:
        cell_tab, pack_tab, uncertainty_tab = st.tabs(
            ["Cell bill of materials", "Pack bill of materials", "Uncertainty"]
        )
        with cell_tab:
            cell_mass = pd.DataFrame(
                [
                    {"component": name, "mass fraction": fraction}
                    for name, fraction in result["cell"]["mass_fractions"].items()
                ]
            )
            st.plotly_chart(
                px.pie(
                    cell_mass,
                    names="component",
                    values="mass fraction",
                    title="Illustrative Cell Mass Allocation",
                ),
                width="stretch",
            )
            st.dataframe(cell_mass, width="stretch", hide_index=True)
        with pack_tab:
            pack_mass = pd.DataFrame(
                [
                    {"component": name, "mass fraction": fraction}
                    for name, fraction in result["pack"]["mass_fractions"].items()
                ]
            )
            st.plotly_chart(
                px.pie(
                    pack_mass,
                    names="component",
                    values="mass fraction",
                    title="Illustrative Pack Mass Allocation",
                ),
                width="stretch",
            )
            st.dataframe(pack_mass, width="stretch", hide_index=True)
        with uncertainty_tab:
            st.json(
                {
                    "capacity": result.get("capacity_interval_mAh_g"),
                    "active specific energy": result.get(
                        "active_specific_energy_interval_Wh_kg"
                    ),
                    "note": result["uncertainty_note"],
                }
            )
    else:
        st.info(result["uncertainty_note"])
    result_downloads("physics")


def frontier_map() -> None:
    data = registries()
    bundle = dashboard_bundle()
    st.title("Energy Density Frontier Map")
    st.warning(
        "No audited cross-chemistry frontier exists yet. The chart below shows "
        "only one illustrative reaction-to-pack boundary path."
    )
    boundary = physics_boundary_frame(bundle)
    figure = px.scatter(
        boundary,
        x="volumetric energy (Wh/L)",
        y="specific energy (Wh/kg)",
        color="boundary",
        symbol="boundary",
        hover_data=["case", "evidence"],
        title="Illustrative System-Boundary Energy Map",
    )
    figure.update_traces(
        marker={"size": 18, "line": {"width": 1, "color": "black"}}
    )
    st.plotly_chart(figure, width="stretch")
    evidence_note(
        "These points belong to one speculative Li-S calculation fixture. They "
        "must not be interpreted as demonstrated chemistry-family performance."
    )

    st.subheader("Chemistry Evidence Readiness")
    chemistry = chemistry_readiness_frame(data)
    st.dataframe(chemistry, width="stretch", hide_index=True)
    st.caption(
        "Readiness counts describe registered metadata only. They are not a "
        "performance score or ranking."
    )


def leaderboard() -> None:
    data = registries()
    st.title("Candidate Evidence Gate")
    gate = evaluate_ranking_gate([])
    st.error(gate.reason)
    st.write(
        "A public ranking will appear only after every included candidate has "
        "comparable system boundaries, uncertainty, safety, life, manufacturing, "
        "and source-lineage fields."
    )
    readiness = chemistry_readiness_frame(data)
    st.dataframe(readiness, width="stretch", hide_index=True)
    requirements = pd.DataFrame(
        [{"required ranking field": field} for field in sorted(REQUIRED_RANKING_FIELDS)]
    )
    st.subheader("Minimum Fields Required Before Ranking")
    st.dataframe(requirements, width="stretch", hide_index=True)


def aircraft_simulator() -> None:
    bundle = dashboard_bundle()
    st.title("Phase 3 Aviation Mission Simulator")
    st.warning(
        "These are simulation estimates from speculative design-study inputs. "
        "They are not aircraft feasibility, performance, or certification findings."
    )
    results = bundle.aviation["cases"]
    selected_name = st.selectbox("Segmented design study", [item["name"] for item in results])
    result = next(item for item in results if item["name"] == selected_name)

    if result["feasible"]:
        st.success("This fixture closes within its configured mass and power constraints.")
    else:
        st.error("This fixture is infeasible under its configured assumptions.")
        for reason in result["reasons"]:
            st.write(f"- {reason}")

    columns = st.columns(5)
    battery_label = "Battery mass" if result["converged"] else "Last solver iterate"
    columns[0].metric(battery_label, f"{result['battery_mass_kg']:,.0f} kg")
    columns[1].metric("Takeoff mass", f"{result['takeoff_mass_kg']:,.0f} kg")
    columns[2].metric("Battery fraction", f"{result['battery_mass_fraction']:.1%}")
    columns[3].metric(
        "Nominal battery energy",
        f"{result['nominal_battery_energy_Wh'] / 1e6:,.2f} MWh",
    )
    columns[4].metric(
        "Peak electrical power",
        f"{result['peak_electrical_power_W'] / 1e6:,.2f} MW",
    )
    st.caption(
        f"Limiting sizing constraint: {result['limiting_constraint']}. "
        f"Closure iterations: {result['iterations']}. "
        f"{result['battery_mass_interpretation']}."
    )

    segment_tab, sizing_tab, range_tab, sensitivity_tab = st.tabs(
        ["Mission segments", "Sizing constraints", "Payload-range", "Sensitivity"]
    )
    with segment_tab:
        segment_rows = [
            {
                "segment": segment["name"],
                "duration (min)": segment["duration_min"],
                "distance (km)": segment["horizontal_distance_km"],
                "electrical energy (kWh)": segment["electrical_energy_Wh"] / 1000,
                "average power (kW)": segment["average_electrical_power_W"] / 1000,
            }
            for segment in result["segments"]
        ]
        segment_frame = pd.DataFrame(segment_rows)
        energy_chart = px.bar(
            segment_frame,
            x="segment",
            y="electrical energy (kWh)",
            color="segment",
            text_auto=".0f",
            title="Electrical Energy by Mission Segment",
        )
        energy_chart.update_layout(showlegend=False)
        st.plotly_chart(energy_chart, width="stretch")
        power_chart = px.line(
            segment_frame,
            x="segment",
            y="average power (kW)",
            markers=True,
            title="Segment-Average Electrical Power",
        )
        st.plotly_chart(power_chart, width="stretch")
        st.dataframe(segment_frame, width="stretch", hide_index=True)
    with sizing_tab:
        sizing = pd.DataFrame(
            [
                {
                    "constraint": "energy",
                    "required battery mass (kg)": result["energy_limited_mass_kg"],
                },
                {
                    "constraint": "specific power",
                    "required battery mass (kg)": result[
                        "specific_power_limited_mass_kg"
                    ],
                },
                {
                    "constraint": "continuous C-rate",
                    "required battery mass (kg)": result["c_rate_limited_mass_kg"],
                },
            ]
        )
        sizing_chart = px.bar(
            sizing,
            x="constraint",
            y="required battery mass (kg)",
            color="constraint",
            text_auto=".0f",
            title="Battery Mass Required by Independent Constraint",
        )
        sizing_chart.update_layout(showlegend=False)
        st.plotly_chart(sizing_chart, width="stretch")
        st.dataframe(sizing, width="stretch", hide_index=True)
    with range_tab:
        curve = pd.DataFrame(result["payload_range_curve"])
        range_chart = px.line(
            curve,
            x="payload_kg",
            y="maximum_range_km",
            markers=True,
            title="Payload-Range Envelope Under Configured Constraints",
        )
        st.plotly_chart(range_chart, width="stretch")
        st.dataframe(curve, width="stretch", hide_index=True)
    with sensitivity_tab:
        sensitivity = pd.DataFrame(result["sensitivity"])
        sensitivity["battery mass change (%)"] = (
            sensitivity["change_from_baseline_fraction"] * 100
        )
        valid_sensitivity = sensitivity[
            (sensitivity["case"] != "baseline") & sensitivity["comparison_valid"]
        ]
        if valid_sensitivity.empty:
            st.warning(
                "Sensitivity percentages are suppressed because the baseline or "
                "perturbed mass closure did not converge."
            )
        else:
            sensitivity_chart = px.bar(
                valid_sensitivity,
                x="case",
                y="battery mass change (%)",
                color="feasible",
                title="One-at-a-Time Battery Mass Sensitivity",
            )
            sensitivity_chart.add_hline(y=0, line_color="black", line_width=1)
            st.plotly_chart(sensitivity_chart, width="stretch")
        st.dataframe(sensitivity, width="stretch", hide_index=True)
    st.caption(result["uncertainty_note"])
    result_downloads("aviation")


def evidence_and_sources() -> None:
    data = registries()
    bundle = dashboard_bundle()
    st.title("Evidence, Sources, and Audit Status")
    evidence_note(
        "This page reports provenance readiness and missing evidence. Reliability "
        "ratings and metadata counts are not chemistry performance scores."
    )

    source_tab, citation_tab, ledger_tab = st.tabs(
        ["Data sources", "Citation audit", "Evidence ledger"]
    )
    with source_tab:
        sources = source_readiness_frame(data)
        status_counts = (
            sources.groupby(["license status", "ingestion status"])
            .size()
            .reset_index(name="source count")
        )
        st.plotly_chart(
            px.bar(
                status_counts,
                x="license status",
                y="source count",
                color="ingestion status",
                title="Source Readiness by License and Ingestion State",
            ),
            width="stretch",
        )
        st.dataframe(sources, width="stretch", hide_index=True)
    with citation_tab:
        citations = citation_readiness_frame(data)
        citation_counts = (
            citations.groupby(["metadata status", "peer reviewed"])
            .size()
            .reset_index(name="citation count")
        )
        st.plotly_chart(
            px.bar(
                citation_counts,
                x="metadata status",
                y="citation count",
                color="peer reviewed",
                title="Citation Metadata Audit Status",
            ),
            width="stretch",
        )
        st.dataframe(citations, width="stretch", hide_index=True)
    with ledger_tab:
        st.dataframe(evidence_ledger_frame(bundle), width="stretch", hide_index=True)


def methods_and_artifacts() -> None:
    bundle = dashboard_bundle()
    st.title("Methods, Provenance, and Downloads")
    if st.button("Regenerate hashed dashboard artifacts"):
        generate_dashboard_artifacts()
        dashboard_bundle.clear()
        st.success("Dashboard artifacts regenerated. Refresh to load the new manifest.")
    verification = verify_dashboard_artifacts(bundle)
    if verification["hash_matches"].all():
        st.success("All dashboard result and method-card hashes match the manifest.")
    else:
        st.error("One or more dashboard artifacts fail hash verification.")
    st.dataframe(verification, width="stretch", hide_index=True)

    manifest_bytes = bundle.manifest_path.read_bytes()
    st.download_button(
        "Download Phase 4 dashboard manifest",
        data=manifest_bytes,
        file_name=bundle.manifest_path.name,
        mime="application/json",
        key="download-dashboard-manifest",
    )

    st.subheader("Method Cards")
    for artifact in bundle.manifest["artifacts"]:
        if artifact["artifact_type"] != "method_card":
            continue
        path = PROJECT_ROOT / artifact["path"]
        with st.expander(artifact["title"]):
            st.markdown(path.read_text(encoding="utf-8"))
            st.download_button(
                f"Download {artifact['title']}",
                data=path.read_bytes(),
                file_name=path.name,
                mime="text/markdown",
                key=f"method-card-{artifact['artifact_id']}",
            )


def methods_and_assumptions() -> None:
    data = registries()
    st.title("Methods and Assumptions")
    tab_equations, tab_volume, tab_assumptions, tab_sources = st.tabs(
        [
            "Equation calculator",
            "Density conversion",
            "Assumptions registry",
            "Source registry",
        ]
    )
    with tab_equations:
        electrons = st.number_input("Electrons transferred", min_value=0.001, value=1.0)
        molar_mass = st.number_input(
            "Reaction-basis molar mass (g/mol)",
            min_value=0.001,
            value=6.94,
        )
        voltage = st.number_input("Average discharge voltage (V)", min_value=0.0, value=3.0)
        capacity = theoretical_specific_capacity_mAh_g(electrons, molar_mass)
        energy = theoretical_specific_energy_Wh_kg(capacity, voltage)
        st.metric("Theoretical specific capacity", f"{capacity:,.1f} mAh/g")
        st.metric("Theoretical specific energy", f"{energy:,.1f} Wh/kg")
        st.caption(
            "Output is a theoretical limit on the declared reaction-mass basis, "
            "not complete-cell or pack performance."
        )
    with tab_volume:
        gravimetric = st.number_input(
            "Specific energy (Wh/kg)",
            min_value=0.0,
            value=250.0,
        )
        density = st.number_input(
            "Material density (kg/L)",
            min_value=0.001,
            value=2.0,
        )
        packing = st.slider("Packing fraction", min_value=0.01, max_value=1.0, value=0.65)
        volumetric = gravimetric_to_volumetric_energy_Wh_l(
            gravimetric,
            density,
            packing,
        )
        st.metric("Packed volumetric energy", f"{volumetric:,.1f} Wh/L")
        st.caption(
            "The density and packing fraction must match the same declared "
            "material or electrode boundary as the gravimetric value."
        )
    with tab_assumptions:
        st.dataframe(
            pd.DataFrame([item.model_dump(mode="json") for item in data.assumptions]),
            width="stretch",
            hide_index=True,
        )
    with tab_sources:
        st.dataframe(
            pd.DataFrame([item.model_dump(mode="json") for item in data.data_sources]),
            width="stretch",
            hide_index=True,
        )


def notebook_library() -> None:
    st.title("Research Notebook Library")
    st.info("Notebook execution begins after immutable input snapshots exist.")
    st.code(
        "\n".join(
            [
                "00_problem_framing.ipynb",
                "01_data_audit.ipynb",
                "02_energy_density_baselines.ipynb",
                "03_aviation_mission_simulator.ipynb",
                "04_material_screening.ipynb",
                "05_pareto_frontier.ipynb",
            ]
        )
    )


def daily_report() -> None:
    st.title("Daily Mission Report")
    if st.button("Generate current report"):
        report_path, _ = generate_daily_report()
        st.success(f"Generated {report_path.name}")
    reports = sorted((PROJECT_ROOT / "reports" / "daily").glob("*-mission-report.md"))
    if not reports:
        st.info("No generated report exists yet.")
        return
    latest = reports[-1]
    st.caption(f"Showing {latest.name}")
    st.markdown(latest.read_text(encoding="utf-8"))
    st.download_button(
        "Download latest daily report",
        data=latest.read_bytes(),
        file_name=latest.name,
        mime="text/markdown",
        key="download-latest-daily-report",
    )


def contribution_portal() -> None:
    st.title("Open-Source Contribution Portal")
    st.markdown(
        """
- Review `docs/contribution_guide.md` before adding quantitative claims.
- Keep licensed raw data out of Git.
- Include evidence class, system boundary, uncertainty, and source lineage.
- Add tests for equations and transforms.
- Publish failed hypotheses and null results with the same provenance as successes.
"""
    )


PAGES = {
    "Mission Control": mission_control,
    "Physics Workbench": physics_workbench,
    "Energy Density Frontier": frontier_map,
    "Candidate Evidence Gate": leaderboard,
    "Aviation Mission Simulator": aircraft_simulator,
    "Evidence & Sources": evidence_and_sources,
    "Methods & Assumptions": methods_and_assumptions,
    "Methods & Artifacts": methods_and_artifacts,
    "Notebook Library": notebook_library,
    "Daily Mission Report": daily_report,
    "Contribution Portal": contribution_portal,
}

selection = st.sidebar.radio("Mission page", list(PAGES))
st.sidebar.caption("Public scientific dashboard prototype | v0.4.0")
PAGES[selection]()
