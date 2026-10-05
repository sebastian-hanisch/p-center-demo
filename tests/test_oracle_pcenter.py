"""Orakel-Test: Farthest-first, Swap-Lokalsuche, Abstände und Summe bei optimalem Radius gegen unabhängige, naive Neuberechnungen (Brute Force über alle Auswahlen)."""

from itertools import combinations
from math import isqrt

import pytest

import pc_algorithms as al
import pc_exact as ex
import pc_scenario as sc
from tests.helpers import tiny


def _near(d, cs):
    return [min(d[j][i] for i in cs) for j in range(len(d))]


def _farthest(d, p, first):
    cs = [first]
    while len(cs) < p:
        nd = _near(d, cs)
        cs.append(min(i for i in range(len(d)) if nd[i] == max(nd)))
    return cs


def _swap(d, start, tie):
    n, cur = len(d), sorted(start)

    def key(cs):
        nd = _near(d, cs)
        return (max(nd), sum(nd)) if tie == "sum" else (max(nd), 0)

    ck, moves, evals = key(cur), 0, 0
    while True:
        best = None
        for a in cur:
            for b in range(n):
                if b in cur:
                    continue
                c2 = sorted([x for x in cur if x != a] + [b])
                evals += 1
                if best is None or key(c2) < best[0]:
                    best = (key(c2), c2)
        if best is None or best[0] >= ck:
            return tuple(cur), moves, evals
        ck, cur, moves = best[0], best[1], moves + 1


@pytest.mark.parametrize("seed", range(12))
def test_farthest_first_and_swap_equal_naive_reimplementation(seed):
    inst = tiny(seed, 9, 5 if seed % 2 else 30)                 # enges Gitter: viele Gleichstände
    d = inst.d
    for p in (2, 3, 4):
        best_r = min(max(_near(d, s)) for s in combinations(range(inst.n), p))
        for f in range(inst.n):
            ff = al.farthest_first(d, p, f)
            assert list(ff.centers) == _farthest(d, p, f)
            assert ff.radius <= 2 * best_r
        far0 = al.farthest_first(d, p, 0)
        for tie in ("sum", "none"):
            sw = al.swap_search(d, far0.centers, tie)
            centers, moves, evals = _swap(d, far0.centers, tie)
            assert (sw.centers, len(sw.moves), sw.evals) == (centers, moves, evals)


@pytest.mark.parametrize("seed", range(8))
def test_distance_is_floor_of_ten_times_euclid_and_cheapest_optimum_equals_brute_force(seed):
    rng = sc.SplitMix64(seed)
    a, b = (rng.below(100), rng.below(100)), (rng.below(100), rng.below(100))
    s = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    k = sc.distance(a, b)
    assert k * k <= 100 * s < (k + 1) ** 2 and k == isqrt(100 * s)
    inst = tiny(seed, 9, 6)
    for p in (2, 3):
        r = min(max(_near(inst.d, c)) for c in combinations(range(inst.n), p))
        cheapest = min(sum(_near(inst.d, c)) for c in combinations(range(inst.n), p) if max(_near(inst.d, c)) <= r)
        assert ex.best_sum_at_radius(inst.d, p, r)[0] == cheapest
