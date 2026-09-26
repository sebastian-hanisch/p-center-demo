"""Exakte Rechnung: Optimalradius per Binärsuche gegen Brute Force, LP-Radius, billigste Auswahl bei optimalem Radius, p-Median-MILP gegen Brute Force."""

from itertools import combinations

import pytest

import pc_algorithms as al
import pc_exact as ex
import pc_scenario as sc
from tests.helpers import tiny


@pytest.mark.parametrize("seed", range(25))
def test_exact_radius_equals_brute_force(seed):
    inst = tiny(seed, 10)
    for p in (1, 2, 3, 4):
        opt, sets = ex.brute_force_center(inst.d, p)
        assert ex.exact_radius(inst.d, p) == opt
        assert ex.lp_radius(inst.d, p) <= opt


@pytest.mark.parametrize("seed", range(20))
def test_min_cover_is_minimal_and_lp_is_below(seed):
    inst = tiny(seed, 9)
    for r in sorted({v for row in inst.d for v in row})[::7]:
        k, s = ex.min_cover(inst.d, r)
        assert len(s) == k and al.radius(inst.d, s) <= r
        if k > 1:
            assert not any(al.radius(inst.d, c) <= r for c in combinations(range(inst.n), k - 1))
        lp, _ = ex.min_cover(inst.d, r, integer=False)
        assert lp <= k + 1e-9


@pytest.mark.parametrize("seed", range(15))
def test_best_sum_at_optimal_radius_equals_brute_force(seed):
    inst = tiny(seed, 9)
    for p in (2, 3):
        r, sets = ex.brute_force_center(inst.d, p)
        best = min(al.total(inst.d, s) for s in sets)
        value, chosen = ex.best_sum_at_radius(inst.d, p, r)
        assert value == best and al.radius(inst.d, chosen) <= r and len(chosen) <= p


@pytest.mark.parametrize("seed", range(15))
def test_pmedian_milp_equals_brute_force(seed):
    inst = tiny(seed, 9)
    for p in (1, 2, 3):
        value, sets = ex.brute_force_median(inst.d, p)
        milp_value, chosen = ex.solve_pmedian(inst.d, p)
        assert milp_value == value and al.total(inst.d, chosen) == value and len(chosen) == p


def test_exact_on_a_map_net_and_p_larger_than_needed():
    inst = sc.generate(40, "uniform", 4)
    r = [ex.exact_radius(inst.d, p) for p in range(1, 7)]
    assert all(b <= a for a, b in zip(r, r[1:])) and ex.exact_radius(inst.d, inst.n) == 0


def test_lp_radius_is_a_lower_bound_on_map_nets():
    for seed in range(100000, 100006):
        inst = sc.generate(40, "cluster", seed)
        for p in (2, 4):
            assert ex.lp_radius(inst.d, p) <= ex.exact_radius(inst.d, p)
