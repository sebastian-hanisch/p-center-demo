"""Kleinster umschließender Kreis: Handbeispiele und Vergleich mit Brute Force; Punkt-Mittelpunkt nie kleiner als der Kreis."""

from itertools import combinations
from math import hypot

import pytest

import pc_circle as ci
import pc_exact as ex
import pc_scenario as sc
from tests.helpers import tiny


def test_square_corners():
    cx, cy, r = ci.smallest_enclosing_circle([(0, 0), (10, 0), (0, 10), (10, 10)])
    assert (cx, cy) == pytest.approx((5, 5)) and r == pytest.approx(50 ** 0.5)


def test_two_points_and_one_point_and_collinear():
    assert ci.smallest_enclosing_circle([(0, 0), (6, 8)]) == pytest.approx((3, 4, 5))
    assert ci.smallest_enclosing_circle([(4, 4)]) == (4, 4, 0.0)
    assert ci.smallest_enclosing_circle([(0, 0), (2, 0), (10, 0)]) == pytest.approx((5, 0, 5))


def test_interior_points_do_not_change_the_circle():
    base = [(0, 0), (20, 0), (10, 17)]
    assert ci.smallest_enclosing_circle(base + [(10, 5), (9, 8)]) == pytest.approx(ci.smallest_enclosing_circle(base))


def _brute(points):
    best = None
    cands = [ci._circle_two(a, b) for a, b in combinations(points, 2)] + [ci._circle_three(a, b, c) for a, b, c in combinations(points, 3)]
    for c in cands:
        if all(hypot(p[0] - c[0], p[1] - c[1]) <= c[2] + 1e-7 for p in points) and (best is None or c[2] < best[2]):
            best = c
    return best


@pytest.mark.parametrize("seed", range(30))
def test_welzl_equals_brute_force(seed):
    pts = list(tiny(seed, 9).pos)
    assert ci.smallest_enclosing_circle(pts)[2] == pytest.approx(_brute(pts)[2], abs=1e-6)


@pytest.mark.parametrize("seed", range(15))
def test_vertex_center_is_never_better_than_the_circle_and_at_most_twice_as_far(seed):
    inst = tiny(seed, 12, 40)
    circle = ci.smallest_enclosing_circle(inst.pos)[2]
    vertex = ex.exact_radius(inst.d, 1) / 10
    assert circle - 0.11 <= vertex <= 2 * circle + 0.11         # Abstände sind auf Zehntel abgerundet
