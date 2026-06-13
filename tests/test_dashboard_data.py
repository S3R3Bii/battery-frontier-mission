from battery_frontier.dashboards.data import (
    chemistry_readiness_frame,
    evidence_ledger_frame,
    load_dashboard_bundle,
    phase_readiness_frame,
    physics_boundary_frame,
    source_readiness_frame,
    verify_dashboard_artifacts,
)
from battery_frontier.registry import load_registries


def test_dashboard_bundle_and_artifact_hashes_are_traceable() -> None:
    bundle = load_dashboard_bundle()
    verification = verify_dashboard_artifacts(bundle)

    assert bundle.manifest["phase"] == "4"
    assert bundle.manifest["chemistry_ranking_enabled"] is False
    assert not verification.empty
    assert verification["exists"].all()
    assert verification["hash_matches"].all()


def test_stale_dashboard_artifact_hash_is_detected() -> None:
    bundle = load_dashboard_bundle()
    tampered_manifest = {
        **bundle.manifest,
        "artifacts": [
            {
                **bundle.manifest["artifacts"][0],
                "sha256": "0" * 64,
            },
            *bundle.manifest["artifacts"][1:],
        ],
    }
    tampered = type(bundle)(
        manifest=tampered_manifest,
        physics=bundle.physics,
        aviation=bundle.aviation,
        manifest_path=bundle.manifest_path,
    )
    verification = verify_dashboard_artifacts(tampered)

    assert verification["hash_matches"].sum() == len(verification) - 1


def test_dashboard_frames_preserve_evidence_boundaries() -> None:
    registries = load_registries()
    bundle = load_dashboard_bundle()

    phases = phase_readiness_frame(registries)
    ledger = evidence_ledger_frame(bundle)
    boundaries = physics_boundary_frame(bundle)
    chemistry = chemistry_readiness_frame(registries)
    sources = source_readiness_frame(registries)

    assert set(boundaries["boundary"]) == {
        "active reactants",
        "complete cell",
        "complete pack",
    }
    assert "speculative_hypothesis" in set(ledger["evidence class"])
    assert (chemistry["ranking status"] == "not_scored").all()
    assert "prototype active" in set(phases["status"])
    assert (sources["license status"] != "approved").all()


def test_fixture_data_does_not_appear_as_audited_measurement() -> None:
    bundle = load_dashboard_bundle()
    ledger = evidence_ledger_frame(bundle)

    assert "known_experimental" not in set(ledger["evidence class"])
