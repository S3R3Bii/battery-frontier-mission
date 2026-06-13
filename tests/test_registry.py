from battery_frontier.registry import load_registries
from battery_frontier.schemas import EvidenceClass


def test_all_registries_validate_and_cross_references_resolve() -> None:
    registries = load_registries()
    assert registries.assumptions
    assert registries.scenarios
    assert registries.chemistries
    assert registries.citations
    assert registries.data_sources


def test_scenarios_are_not_mislabeled_as_validated_facts() -> None:
    registries = load_registries()
    assert all(
        scenario.evidence_class == EvidenceClass.SPECULATIVE_HYPOTHESIS
        for scenario in registries.scenarios
    )


def test_no_chemistry_is_ranked_before_measurements_exist() -> None:
    registries = load_registries()
    assert all(chemistry.status == "not_scored" for chemistry in registries.chemistries)

