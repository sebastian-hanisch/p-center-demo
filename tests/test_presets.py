"""Presets: vollständig, in den Grenzen, und jedes Beispiel zeigt, was sein Name verspricht (die Zahlen selbst belegt test_claims.py)."""

import pytest

import pc_constants as C
import pc_evaluation as ev
import pc_presets as P

KEYS = set(P.PRESET_KEYS)


def _params(p):
    return ev.Params(p["net"], p["points"], p["p"], p["seed"], p["start"], p["outlier"])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 8
    assert all(C.PRESET_HELP[name].strip() for name in C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_values_are_inside_the_bounds(name):
    p = C.PRESETS[name]
    assert p["net"] in C.NETS and isinstance(p["outlier"], bool)
    for key, state_key in P.PRESET_KEYS.items():
        spec = P.SETTING_SPECS[state_key]
        if spec.lo is not None:
            assert spec.lo <= p[key] <= spec.hi, (name, key)


def test_setting_specs_have_room_to_move():
    """Ein Regler mit lo == hi würde Streamlit abstürzen lassen."""
    assert all(spec.lo < spec.hi for spec in P.SETTING_SPECS.values() if spec.lo is not None)


def test_presets_use_seeds_outside_the_distribution_set():
    for name, p in C.PRESETS.items():
        assert p["seed"] not in C.DIST_SEEDS, name


def test_each_preset_shows_the_effect_its_name_promises():
    a = {name: ev.analyse(ev.canonical(_params(p))) for name, p in C.PRESETS.items()}
    trap = a["🪤 Garantie 2 wird erreicht"]
    assert trap["far"].radius == 2 * trap["radius"]
    stuck = a["🧲 Swap steckt fest"]
    assert stuck["swap"].radius > stuck["radius"] and not stuck["swap"].moves
    fair = a["⚖️ Summe gegen Maximum"]
    assert fair["median_radius"] > 2 * fair["radius"] and fair["center_sum"] > fair["median"]
    assert a["📍 Ein Ausreißer"]["inst"].n == 51 and a["🎯 Ein Mittelpunkt"]["far"].radii and len(a["🎯 Ein Mittelpunkt"]["far"].centers) == 1
    assert a["🏙️ Großes Netz"]["inst"].n == 80 and a["🏘️ Vier Cluster"]["inst"].kind == "cluster"


def test_canonical_clamps_p_and_start_and_ignores_the_random_controls_of_teaching_nets():
    assert ev.canonical(ev.Params("gonzalez_trap", 20, 8, 99, 50, False)) == ev.Params("gonzalez_trap", C.DEFAULT_POINTS, 6, C.DEFAULT_SEED, 7, False)
    assert ev.canonical(ev.Params("uniform", 20, 8, 99, 50, True)).start == 21
