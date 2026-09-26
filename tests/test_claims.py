"""Jede Zahl, die README, Hilfetexte und Beschriftungen nennen, ist hier belegt: das Standardnetz (Seed 1), die Presets, die Lehrnetze von Hand und die Verteilungen über feste Netze
(Seeds ab 100000: 40 Netze für die Verteilung, 20 je p der Reihe und im Ausreißer-Test).

Alle Radien und Summen sind ganze Zahlen (Zehntel-Einheiten) und auf allen Plattformen dieselben; angezeigt werden sie durch 10 geteilt. Nur die Überdeckungs-LP ist ein Gleitkommawert; sie wird als
ganzzahliger LP-Radius (kleinster Radius mit zulässiger LP) gezählt. Nie gezählt wird, welche der gleich guten Auswahlen der MILP-Löser liefert."""

import pytest

import pc_algorithms as al
import pc_constants as C
import pc_evaluation as ev
import pc_exact as ex
import pc_scenario as sc

PCT = pytest.approx


def _a(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.canonical(ev.Params(p["net"], p["points"], p["p"], p["seed"], p["start"], p["outlier"])))


@pytest.fixture(scope="module")
def dist_uniform():
    return ev.distribution(ev.Params("uniform", 50, 5, 1))


@pytest.fixture(scope="module")
def dist_cluster():
    return ev.distribution(ev.Params("cluster", 50, 4, 1))


@pytest.fixture(scope="module")
def series():
    return {r["p"]: r for r in ev.p_series(ev.Params("uniform", 50, 5, 1))}


# --- Standardnetz und Presets -------------------------------------------------------------------------------------------------------------

def test_standard_net():
    """50 Punkte, p = 5, Seed 1: Optimalradius 28,4 (LP-Radius gleich); Farthest-first ab Punkt 1: Radien 96,8 / 81,6 / 65,0 / 48,6 / 42,6 nach 1 bis 5 Mittelpunkten (1,50-fach); Swap 32,6 nach 4 Zügen (Summe 843,9),
    nur mit Radius ebenfalls 32,6 nach 2 Zügen; bester Startpunkt 25 (36,0), schlechtester 22 (48,6); p-Center-Lösung mit kleinster Summe 856,2, p-Median 795,9 mit Radius 35,3, Farthest-first-Summe 1 029,0."""
    a = _a("🗺️ Standardnetz")
    assert (a["radius"], a["lp"]) == (284, 284) and a["far"].centers == (0, 36, 40, 30, 47) and a["far"].radii == (968, 816, 650, 486, 426) and a["far"].radius / 284 == PCT(1.5, abs=0.001)
    assert (a["swap"].radius, len(a["swap"].moves), a["swap"].total) == (326, 4, 8439) and (a["swap_plain"].radius, len(a["swap_plain"].moves)) == (326, 2)
    assert (a["starts"][a["best_start"]], a["best_start"] + 1, a["starts"][a["worst_start"]], a["worst_start"] + 1) == (360, 25, 486, 22)
    assert (a["center_sum"], a["median"], a["median_radius"], a["far_sum"]) == (8562, 7959, 353, 10290)


def test_preset_gonzalez_trap():
    a = _a("🪤 Garantie 2 wird erreicht")
    assert (a["radius"], a["far"].radius, a["far"].radii) == (80, 160, (254, 160)) and a["far"].radius == 2 * a["radius"]
    assert (a["swap"].radius, len(a["swap"].moves)) == (80, 1) and a["starts"][a["best_start"]] == 80 and a["best_start"] + 1 == 6 and a["starts"][a["worst_start"]] == 160
    assert (a["center_sum"], a["median"], a["median_radius"]) == (370, 370, 80)


def test_preset_swap_stuck():
    a = _a("🧲 Swap steckt fest")
    assert (a["radius"], a["far"].radius, a["swap"].radius, len(a["swap"].moves), a["swap_plain"].radius) == (60, 100, 100, 0, 100)
    assert a["starts"][a["best_start"]] == 60 and a["best_start"] + 1 == 5 and a["starts"][a["worst_start"]] == 100


def test_preset_summe_gegen_maximum():
    """p-Center: Radius 9,2, Summe 46,8; p-Median: Summe 37,5, Radius 19,6 (mehr als das Doppelte, 2,13-fach); Farthest-first trifft das Optimum."""
    a = _a("⚖️ Summe gegen Maximum")
    assert (a["radius"], a["center_sum"], a["median"], a["median_radius"], a["far"].radius) == (92, 468, 375, 196, 92) and a["median_radius"] / a["radius"] == PCT(2.13, abs=0.01)
    assert a["center_sum"] / a["median"] == PCT(1.248, abs=0.001)


def test_preset_clusters():
    a = _a("🏘️ Vier Cluster")
    assert (a["radius"], a["far"].radius, a["swap"].radius, len(a["swap"].moves), a["swap_plain"].radius, len(a["swap_plain"].moves)) == (161, 228, 186, 4, 161, 6)
    assert a["far"].radius / a["radius"] == PCT(1.416, abs=0.001)


def test_preset_one_center():
    a = _a("🎯 Ein Mittelpunkt")
    assert (a["radius"], a["far"].radius, a["swap"].radius, len(a["swap"].moves)) == (605, 968, 605, 1) and a["far"].radius / 605 == PCT(1.6, abs=0.001)
    assert a["starts"][a["best_start"]] == 605 and a["best_start"] + 1 == 13 and a["median_radius"] == 731


def test_preset_outlier():
    a = _a("📍 Ein Ausreißer")
    assert a["inst"].n == 51 and a["inst"].pos[50] == (150, 150)
    assert (a["radius"], a["far"].radius, a["swap"].radius, a["swap_plain"].radius, a["median_radius"]) == (411, 650, 411, 474, 984)


def test_preset_large_net():
    a = _a("🏙️ Großes Netz")
    assert (a["radius"], a["far"].radius, a["swap"].radius, len(a["swap"].moves), a["starts"][a["best_start"]]) == (214, 291, 214, 8, 256)
    assert a["far"].radius / a["radius"] == PCT(1.36, abs=0.001)


# --- Verteilung über 40 feste Netze -------------------------------------------------------------------------------------------------------------

def test_uniform_distribution(dist_uniform):
    """40 gleichverteilte Netze (50 Punkte, p = 5): die Überdeckungs-LP trifft den Optimalradius in 40 von 40; Farthest-first (Start 1) im Mittel 1,415-fach (Median 1,441, schlechtestes 1,718, nie exakt), bester Start 1,199
    (schlechtestes 1,458, nie exakt), schlechtester Start 1,633 (bis 1,804); Swap 1,045 (schlechtestes 1,196, exakt in 15, im Mittel 7,1 Züge), nur mit Radius 1,120 (1,357; exakt in 8; 3,7 Züge);
    p-Median-Lösung 1,276-facher Radius (bis 1,614), p-Center-Lösung 1,079-fache Summe (bis 1,187)."""
    s = dist_uniform["summary"]
    assert s["count"] == 40 and s["lp_exact"] == 40 and s["lp"] == PCT(1.0)
    assert (s["g0"], s["g0_median"], s["g0_max"], s["g0_exact"]) == (PCT(1.415, abs=0.001), PCT(1.441, abs=0.001), PCT(1.718, abs=0.001), 0)
    assert (s["gbest"], s["gbest_max"], s["gbest_exact"], s["gworst"], s["gworst_max"]) == (PCT(1.199, abs=0.001), PCT(1.458, abs=0.001), 0, PCT(1.633, abs=0.001), PCT(1.804, abs=0.001))
    assert (s["swap"], s["swap_max"], s["swap_exact"], s["swap_moves"]) == (PCT(1.045, abs=0.001), PCT(1.196, abs=0.001), 15, PCT(7.1, abs=0.05))
    assert (s["plain"], s["plain_max"], s["plain_exact"], s["plain_moves"]) == (PCT(1.120, abs=0.001), PCT(1.357, abs=0.001), 8, PCT(3.675, abs=0.001))
    assert (s["med_radius"], s["med_radius_max"], s["center_sum"], s["center_sum_max"]) == (PCT(1.276, abs=0.001), PCT(1.614, abs=0.001), PCT(1.079, abs=0.001), PCT(1.187, abs=0.001))


def test_guarantee_two_is_never_violated_on_the_distribution(dist_uniform, dist_cluster):
    for dist in (dist_uniform, dist_cluster):
        assert all(r["g0"] <= 2.0 and r["gworst"] <= 2.0 for r in dist["rows"]) and all(r["swap"] <= r["g0"] + 1e-9 and r["plain"] <= r["g0"] + 1e-9 for r in dist["rows"])


def test_cluster_distribution(dist_cluster):
    """40 Clusternetze (50 Punkte, p = 4): LP trifft in 40 von 40; Farthest-first 1,491 (bis 1,826), bester Start 1,293, schlechtester 1,665 (bis 1,923); Swap 1,021 (exakt in 30), nur mit Radius 1,141 (exakt in 17)."""
    s = dist_cluster["summary"]
    assert s["lp_exact"] == 40 and (s["g0"], s["g0_max"], s["gbest"], s["gworst"], s["gworst_max"]) == (PCT(1.491, abs=0.001), PCT(1.826, abs=0.001), PCT(1.293, abs=0.001), PCT(1.665, abs=0.001), PCT(1.923, abs=0.001))
    assert (s["swap"], s["swap_exact"], s["plain"], s["plain_exact"]) == (PCT(1.021, abs=0.001), 30, PCT(1.141, abs=0.001), 17)


# --- Reihe über p (20 Netze je p) --------------------------------------------------------------------------------------------------------------

def test_series_over_p(series):
    """p = 1 / 2 / 3 / 5 / 8: Farthest-first (Start 1) 1,495 / 1,407 / 1,482 / 1,446 / 1,372; bester Start 1,000 / 1,151 / 1,148 / 1,215 / 1,163; Swap 1,000 / 1,031 / 1,055 / 1,044 / 1,050;
    Radius der p-Median-Lösung 1,045 / 1,185 / 1,217 / 1,271 / 1,347; Summe der p-Center-Lösung 1,008 / 1,057 / 1,049 / 1,074 / 1,073; LP-Radius exakt in 20 / 20 / 20 / 20 / 19 Netzen."""
    ps = (1, 2, 3, 5, 8)
    r = series
    assert [r[q]["g0"] for q in ps] == PCT([1.495, 1.407, 1.482, 1.446, 1.372], abs=0.001)
    assert [r[q]["gbest"] for q in ps] == PCT([1.000, 1.151, 1.148, 1.215, 1.163], abs=0.001)
    assert [r[q]["swap"] for q in ps] == PCT([1.000, 1.031, 1.055, 1.044, 1.050], abs=0.001)
    assert [r[q]["med_radius"] for q in ps] == PCT([1.045, 1.185, 1.217, 1.271, 1.347], abs=0.001)
    assert [r[q]["center_sum"] for q in ps] == PCT([1.008, 1.057, 1.049, 1.074, 1.073], abs=0.001)
    assert [r[q]["lp_exact"] for q in ps] == [20, 20, 20, 20, 19]


# --- Ausreißer und Kreis -------------------------------------------------------------------------------------------------------------------------

def test_outlier_test():
    """Ein Punkt bei (150, 150), p = 4, 20 Netze: der Optimalradius steigt im Mittel auf das 1,251-Fache (1,122 bis 1,380), die p-Median-Kosten auf das 1,120-Fache (1,097 bis 1,154)."""
    o = ev.outlier_test(ev.Params("uniform", 50, 4, 1))
    assert (o["radius"], o["radius_min"], o["radius_max"]) == (PCT(1.251, abs=0.001), PCT(1.122, abs=0.001), PCT(1.380, abs=0.001))
    assert (o["median"], o["median_min"], o["median_max"]) == (PCT(1.120, abs=0.001), PCT(1.097, abs=0.001), PCT(1.154, abs=0.001))


def test_circle_test():
    """p = 1, 40 Netze: der beste Punkt als Mittelpunkt hat im Mittel den 1,073-fachen Radius des kleinsten umschließenden Kreises (kleinstes Verhältnis 0,999 durch das Abrunden, größtes 1,171)."""
    c = ev.circle_test(ev.Params("uniform", 50, 1, 1))
    assert (c["mean"], c["min"], c["max"]) == (PCT(1.073, abs=0.001), PCT(0.999, abs=0.001), PCT(1.171, abs=0.001))


def test_help_texts_have_content():
    assert all(C.PRESET_HELP[k].strip() for k in C.PRESETS) and set(C.PRESET_HELP) == set(C.PRESETS)


def test_the_map_units_are_tenths():
    """Angezeigte Zahlen sind die ganzzahligen Radien durch 10: 284 wird 28,4."""
    assert _a("🗺️ Standardnetz")["radius"] / 10 == PCT(28.4)
