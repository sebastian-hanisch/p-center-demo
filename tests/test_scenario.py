"""Szenario: Zufallsnetze und Lehrnetze - ganzzahlig, deterministisch, in den erwarteten Grenzen."""

import pytest

import pc_constants as C
import pc_scenario as sc


def test_distance_is_integer_euclid_in_tenths():
    assert sc.distance((0, 0), (3, 4)) == 50 and sc.distance((5, 5), (5, 5)) == 0 and sc.distance((0, 0), (1, 1)) == 14


@pytest.mark.parametrize("kind", ["uniform", "cluster"])
def test_generate_is_deterministic_integer_and_symmetric(kind):
    a = sc.generate(30, kind, 1)
    assert a == sc.generate(30, kind, 1) and a != sc.generate(30, kind, 2)
    assert a.n == 30 and all(0 <= x < sc.MAP_W and 0 <= y < sc.MAP_W for x, y in a.pos)
    assert all(isinstance(v, int) for row in a.d for v in row)
    assert all(a.d[i][i] == 0 for i in range(a.n)) and all(a.d[i][j] == a.d[j][i] for i in range(a.n) for j in range(a.n))


def test_triangle_inequality_up_to_rounding():
    """Abstände sind auf Zehntel abgerundet: die Dreiecksungleichung gilt bis auf 1 Einheit."""
    inst = sc.generate(25, "uniform", 3)
    n = inst.n
    assert all(inst.d[i][k] <= inst.d[i][j] + inst.d[j][k] + 1 for i in range(n) for j in range(n) for k in range(n))


def test_clusters_are_more_concentrated_than_uniform_points():
    def mean_nn(inst):
        return sum(min(inst.d[i][j] for j in range(inst.n) if j != i) for i in range(inst.n)) / inst.n
    assert mean_nn(sc.generate(60, "cluster", 5)) < mean_nn(sc.generate(60, "uniform", 5))


def test_unknown_kind_raises():
    with pytest.raises(KeyError):
        sc.generate(10, "kreis", 1)
    with pytest.raises(KeyError):
        sc.teaching("gibt-es-nicht")


def test_with_outlier_adds_one_far_point():
    inst = sc.generate(20, "uniform", 1)
    out = sc.with_outlier(inst, C.OUTLIER_POSITION)
    assert out.n == 21 and out.pos[:20] == inst.pos and out.pos[20] == (150, 150)
    assert all(out.d[i][j] == inst.d[i][j] for i in range(20) for j in range(20)) and min(out.d[20][:20]) > 400


@pytest.mark.parametrize("name", list(sc.TEACHING))
def test_teaching_nets_are_well_formed(name):
    inst = sc.teaching(name)
    assert inst.kind == "teaching" and 7 <= inst.n <= 9 and len(set(inst.pos)) == inst.n


def test_every_teaching_net_in_the_constants_exists():
    assert set(C.FIXED_NETS) == set(sc.TEACHING)
