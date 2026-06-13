from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_dashboard_core_phase_pages_render() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(project_root / "dashboard" / "app.py"))
    app.run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "Battery Frontier Mission Control"

    app.sidebar.radio[0].set_value("Aviation Mission Simulator")
    app.run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "Phase 3 Aviation Mission Simulator"
    assert any(metric.label == "Battery mass" for metric in app.metric)

    app.sidebar.radio[0].set_value("Physics Workbench")
    app.run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "Phase 2 Physics Workbench"
    assert any(metric.label == "Theoretical capacity" for metric in app.metric)

    app.sidebar.radio[0].set_value("Energy Density Frontier")
    app.run(timeout=20)

    assert not app.exception
    assert app.title[0].value == "Energy Density Frontier Map"


def test_dashboard_evidence_and_artifact_pages_render() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(project_root / "dashboard" / "app.py"))
    app.run(timeout=30)

    app.sidebar.radio[0].set_value("Evidence & Sources")
    app.run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Evidence, Sources, and Audit Status"

    app.sidebar.radio[0].set_value("Methods & Artifacts")
    app.run(timeout=30)
    assert not app.exception
    assert app.title[0].value == "Methods, Provenance, and Downloads"
