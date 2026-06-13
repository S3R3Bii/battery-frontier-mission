import pytest

from battery_frontier.physics.derating import (
    CellDerating,
    InstalledUseDerating,
    PackDerating,
)


def test_derating_is_explicit_and_monotonic() -> None:
    active = 1000.0
    cell = CellDerating(0.6, 0.85, 0.9).apply(active)
    pack = PackDerating(0.7, 0.96).apply(cell)
    useful = InstalledUseDerating(0.9, 0.8, 0.8, 0.95, 0.2, 0.85).apply(pack)

    assert active > cell > pack > useful > 0
    assert cell == pytest.approx(459.0)


def test_reserve_cannot_consume_all_energy() -> None:
    with pytest.raises(ValueError):
        InstalledUseDerating(0.9, 0.8, 0.8, 0.95, 1.0, 0.85)

