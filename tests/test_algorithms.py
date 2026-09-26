"""Farthest-first und Swap-Lokalsuche: Handbeispiele, Garantie 2, Lehrnetze, Invarianten der Züge."""

import pytest

import pc_algorithms as al
import pc_exact as ex
import pc_scenario as sc
from tests.helpers import tiny


def _line():
    """Vier Punkte auf einer Geraden im Abstand 10 (Zehntel: 100, 200, 300)."""
    return sc._build("teaching", [(0, 0), (10, 0), (20, 0), (30, 0)])


def test_farthest_first_by_hand():
    """Start Punkt 1: Radius 300 (Punkt 4 am weitesten); Punkt 4 wird Mittelpunkt: Radius 100 (Punkt 2 zu 1, Punkt 3 zu 4)."""
    inst = _line()
    far = al.farthest_first(inst.d, 2, 0)
    assert far.centers == (0, 3) and far.radii == (300, 100) and far.radius == 100
    assert [(s.center, s.radius_before, s.radius_after) for s in far.steps] == [(0, 0, 300), (3, 300, 100)]
    assert al.farthest_first(inst.d, 1, 2).radii == (200,) and al.farthest_first(inst.d, 4, 0).radius == 0


def test_radius_total_assignment_bottleneck_by_hand():
    inst = _line()
    assert al.radius(inst.d, (0, 3)) == 100 and al.total(inst.d, (0, 3)) == 200
    assert al.assignment(inst.d, (0, 3)) == (0, 0, 3, 3)                  # Gleichstand: der kleinere Index
    assert al.bottleneck(inst.d, (0, 3)) == (1, 100)                      # Punkt 2 (Index 1) vor Punkt 3


@pytest.mark.parametrize("seed", range(40))
def test_the_guarantee_two_holds_for_every_start_and_p(seed):
    """Radius von Farthest-first <= 2 mal Optimalradius, von jedem Startpunkt aus (die Garantie von Gonzalez)."""
    inst = tiny(seed, 9)
    for p in (1, 2, 3, 4):
        opt, _sets = ex.brute_force_center(inst.d, p)
        for first in range(inst.n):
            assert al.farthest_first(inst.d, p, first).radius <= 2 * opt


@pytest.mark.parametrize("seed", range(20))
def test_farthest_first_radii_never_increase_and_start_is_the_first_center(seed):
    inst = tiny(seed, 12)
    far = al.farthest_first(inst.d, 5, seed % inst.n)
    assert far.centers[0] == seed % inst.n and len(set(far.centers)) == 5
    assert all(b <= a for a, b in zip(far.radii, far.radii[1:])) and far.radius == al.radius(inst.d, far.centers) == far.radii[-1]
    assert all(s.radius_after == al.radius(inst.d, far.centers[:k + 1]) for k, s in enumerate(far.steps))


def test_gonzalez_trap_reaches_the_guarantee_exactly():
    """Lehrnetz: Farthest-first ab Punkt 1 mit p = 2 endet bei 160, das Optimum {Punkt 3, Punkt 6} hat den Radius 80: genau das Doppelte."""
    inst = sc.teaching("gonzalez_trap")
    assert ex.brute_force_center(inst.d, 2) == (80, [(2, 5)])
    far = al.farthest_first(inst.d, 2, 0)
    assert (far.centers, far.radius) == ((0, 2), 160) and far.radius == 2 * 80
    assert min(al.all_starts(inst.d, 2)) == 80 and max(al.all_starts(inst.d, 2)) == 160


def test_swap_stuck_teaching_net():
    """Lehrnetz: Farthest-first ab Punkt 1 mit p = 3 endet bei 100, die Swap-Lokalsuche findet keinen besseren Tausch; das Optimum {2, 3, 5} hat den Radius 60."""
    inst = sc.teaching("swap_stuck")
    assert ex.brute_force_center(inst.d, 3) == (60, [(1, 2, 4)])
    far = al.farthest_first(inst.d, 3, 0)
    sw = al.swap_search(inst.d, far.centers)
    assert far.radius == 100 and sw.radius == 100 and sw.moves == () and sw.centers == tuple(sorted(far.centers))


def test_fairness_teaching_net():
    """Lehrnetz: das p-Median-Optimum {5, 6} (Summe 375) hat den Radius 196, das p-Center-Optimum {1, 7} den Radius 92 bei der Summe 468."""
    inst = sc.teaching("fairness")
    assert ex.brute_force_center(inst.d, 2) == (92, [(0, 6)])
    med, sets = ex.brute_force_median(inst.d, 2)
    assert (med, sets) == (375, [(4, 5)]) and al.radius(inst.d, sets[0]) == 196 and al.total(inst.d, (0, 6)) == 468


@pytest.mark.parametrize("seed", range(20))
def test_swap_search_is_valid_monotone_and_deterministic(seed):
    inst = tiny(seed, 12)
    far = al.farthest_first(inst.d, 3, 0)
    for tie in ("sum", "none"):
        sw = al.swap_search(inst.d, far.centers, tie)
        assert sw.radius == al.radius(inst.d, sw.centers) and sw.total == al.total(inst.d, sw.centers) and len(sw.centers) == 3
        assert sw.radius <= far.radius and sw == al.swap_search(inst.d, far.centers, tie)
        radii = [m.radius_after for m in sw.moves]
        assert all(b <= a for a, b in zip(radii, radii[1:]))


def test_swap_with_and_without_the_second_key_differ_on_a_map_net():
    """Zweig-Test: das Summen-Kriterium ändert das Ergebnis auf mindestens einem Netz (keine Nullspalte), und zwar zum Besseren."""
    better = 0
    for seed in range(100000, 100012):
        inst = sc.generate(40, "uniform", seed)
        far = al.farthest_first(inst.d, 4, 0)
        a, b = al.swap_search(inst.d, far.centers, "sum"), al.swap_search(inst.d, far.centers, "none")
        better += a.radius < b.radius
    assert better >= 1
