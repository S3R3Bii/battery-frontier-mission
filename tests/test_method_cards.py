import json

from battery_frontier.reporting.method_cards import generate_dashboard_artifacts


def test_method_cards_and_dashboard_manifest_are_generated(tmp_path) -> None:
    manifest_path, artifacts = generate_dashboard_artifacts(output_dir=tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["phase"] == "4"
    assert manifest["experimental_measurements"] == 0
    assert manifest["chemistry_ranking_enabled"] is False
    assert len(artifacts) == 4
    assert all(artifact.path.exists() for artifact in artifacts)
    assert all(artifact.sha256 for artifact in artifacts)

