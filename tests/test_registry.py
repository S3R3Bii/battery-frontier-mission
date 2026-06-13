from battery_frontier.registry import load_registries
from battery_frontier.schemas import EvidenceClass


def test_all_registries_validate_and_cross_references_resolve() -> None:
    registries = load_registries()
    assert registries.assumptions
    assert registries.scenarios
    assert registries.chemistries
    assert registries.citations
    assert registries.data_sources
    assert registries.aircraft_systems
    assert registries.propulsion_systems
    assert registries.dataset_candidates
    assert registries.material_candidates


def test_scenarios_are_not_mislabeled_as_validated_facts() -> None:
    registries = load_registries()
    assert all(
        scenario.evidence_class == EvidenceClass.SPECULATIVE_HYPOTHESIS
        for scenario in registries.scenarios
    )


def test_no_chemistry_is_ranked_before_measurements_exist() -> None:
    registries = load_registries()
    assert all(chemistry.status == "not_scored" for chemistry in registries.chemistries)


def test_manufacturer_examples_have_source_urls_and_boundary_labels() -> None:
    registries = load_registries()

    assert all(system.source_url for system in registries.aircraft_systems)
    valid_statuses = {"official", "official_partial", "third_party", "estimated"}
    assert all(system.values_status in valid_statuses for system in registries.aircraft_systems)
    assert all(system.source_url for system in registries.propulsion_systems)
    assert all(system.values_status for system in registries.propulsion_systems)


def test_dataset_candidates_separate_measurements_from_metadata() -> None:
    registries = load_registries()
    by_id = {dataset.id: dataset for dataset in registries.dataset_candidates}

    assert by_id["dataset.cmu_evtol_battery"].license_status == "approved_cc_by_4_0"
    assert by_id["dataset.cmu_evtol_battery"].measured_performance is True
    assert by_id["dataset.materials_project_battery_materials"].metadata_only is True
    assert by_id["dataset.materials_project_battery_materials"].measured_performance is False


def test_material_candidates_are_not_audited_measurement_lane() -> None:
    registries = load_registries()

    assert all(
        not material.may_appear_in_audited_lane
        for material in registries.material_candidates
    )
    assert any(
        material.id == "material.hemp_bast_fiber_graphene_like_carbon"
        for material in registries.material_candidates
    )
