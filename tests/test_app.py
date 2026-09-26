"""Rauchtests der Streamlit-Oberfläche per AppTest: Standard, jedes Preset, jedes Netz, Randgrößen, Schritt-Regler, ausgeblendete Regler, Permalink, Experimente auf Abruf."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import pc_constants as C
from pc_presets import PRESET_KEYS

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"


def _run(setup=None, timeout=300):
    at = AppTest.from_file(str(APP), default_timeout=timeout)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    if setup is not None:
        setup(at)
        at.run()
        assert not at.exception, [e.value for e in at.exception]
    return at


def _apply(at, p):
    for key, state_key in PRESET_KEYS.items():
        at.session_state[state_key] = p[key]


def _metric(at, label):
    return [m.value for m in at.metric if m.label == label]


def _step_slider(at):
    found = [s for s in at.slider if s.key == "pc_step"]
    return found[0] if found else None


def _texts(at):
    return [e.value for e in list(at.success) + list(at.warning) + list(at.info) + list(at.error)]


def test_default_renders_without_exception():
    at = _run()
    assert _metric(at, "Optimalradius") == ["28,4"] and _metric(at, "Radius nach diesem Schritt") == ["42,6"] and _step_slider(at).value == 5 and _step_slider(at).max == 5
    assert any("das ist das 1,50-Fache des Optimums (28,4)" in t for t in _texts(at))


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_renders(name):
    at = _run(lambda a: _apply(a, C.PRESETS[name]))
    assert not at.error and _metric(at, "Optimalradius")


@pytest.mark.parametrize("net", list(C.NETS))
@pytest.mark.parametrize("p", (1, 3, 8))
def test_every_net_and_p_renders(net, p):
    def setup(at):
        at.session_state["net_select"] = net
        at.session_state["p_slider"] = p
    at = _run(setup)
    assert not at.error and _metric(at, "Optimalradius")


def test_guarantee_warning_for_the_trap():
    at = _run(lambda a: _apply(a, C.PRESETS["🪤 Garantie 2 wird erreicht"]))
    assert any("genau das Doppelte" in t for t in _texts(at))


def test_exact_hit_shows_success():
    at = _run(lambda a: _apply(a, C.PRESETS["⚖️ Summe gegen Maximum"]))
    assert any("trifft das Optimum (9,2)" in t for t in _texts(at))


def test_extreme_sizes_render():
    for vals in ((("points_slider", C.POINTS_MIN), ("p_slider", C.P_MIN), ("start_slider", 1)),
                 (("points_slider", C.POINTS_MAX), ("p_slider", C.P_MAX), ("start_slider", C.POINTS_MAX))):
        def setup(at, vals=vals):
            for key, value in vals:
                at.session_state[key] = value
        at = _run(setup)
        assert not at.error and _metric(at, "Optimalradius")


def test_step_slider_moves_through_frames():
    at = _run()
    for value in (1, 2, 3, 5):
        _step_slider(at).set_value(value)
        at.run()
        assert not at.exception and _step_slider(at).value == value


def test_p_equals_one_has_no_step_slider():
    at = _run(lambda a: _apply(a, C.PRESETS["🎯 Ein Mittelpunkt"]))
    assert _step_slider(at) is None and _metric(at, "Radius nach diesem Schritt") == ["96,8"]


def test_selection_is_limited_to_p_and_the_empty_selection_shows_a_notice():
    at = _run()
    at.multiselect(key="pick_multi").set_value([])
    at.run()
    assert not at.exception and any("Wählen Sie mindestens einen Punkt" in t for t in _texts(at))
    at.multiselect(key="pick_multi").set_value([0, 1, 2, 3, 4])
    at.run()
    assert not at.exception and _metric(at, "Radius")


def test_hidden_controls_keep_their_values_across_a_net_switch():
    at = _run()
    at.sidebar.slider(key="points_slider").set_value(30)
    at.run()
    at.sidebar.selectbox(key="net_select").set_value("gonzalez_trap")
    at.run()
    assert not at.exception and not [w for w in at.sidebar.slider if w.key == "points_slider"]
    at.sidebar.selectbox(key="net_select").set_value("uniform")
    at.run()
    assert at.sidebar.slider(key="points_slider").value == 30 and not at.exception


def test_start_slider_follows_the_number_of_points():
    at = _run()
    at.sidebar.slider(key="start_slider").set_value(50)
    at.run()
    at.sidebar.slider(key="points_slider").set_value(20)
    at.run()
    assert not at.exception and at.sidebar.slider(key="start_slider").value <= 20


def test_permalink_settings_are_loaded_and_clamped():
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.query_params["net"] = "cluster"
    at.query_params["points"] = "999"
    at.query_params["p"] = "3"
    at.query_params["start"] = "2"
    at.query_params["outlier"] = "1"
    at.run()
    assert not at.exception
    assert at.sidebar.slider(key="points_slider").value == C.POINTS_MAX and at.sidebar.slider(key="p_slider").value == 3 and at.sidebar.checkbox(key="outlier_box").value is True


def test_invalid_permalink_values_fall_back_to_the_defaults():
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.query_params["net"] = "nirgendwo"
    at.query_params["outlier"] = "vielleicht"
    at.run()
    assert not at.exception and at.sidebar.selectbox(key="net_select").value == C.DEFAULT_NET and at.sidebar.checkbox(key="outlier_box").value is False


def test_experiments_run_on_demand(monkeypatch):
    import pc_evaluation as ev
    d_o, s_o, o_o, c_o = ev.distribution, ev.p_series, ev.outlier_test, ev.circle_test
    monkeypatch.setattr(ev, "distribution", lambda p: d_o(p, seeds=C.SWEEP_SEEDS[:3]))
    monkeypatch.setattr(ev, "p_series", lambda p: s_o(p, seeds=C.SERIES_SEEDS[:2], ps=(1, 3)))
    monkeypatch.setattr(ev, "outlier_test", lambda p: o_o(p, seeds=C.SERIES_SEEDS[:2]))
    monkeypatch.setattr(ev, "circle_test", lambda p: c_o(p, seeds=C.SWEEP_SEEDS[:3]))
    at = _run()
    for key in ("dist_start", "series_start", "outlier_start", "circle_start"):
        next(b for b in at.button if b.key == key).click().run()
        assert not at.exception, key
    assert any("Die Überdeckungs-LP liefert den Optimalradius in" in c.value for c in at.caption)


def test_source_has_explicit_chart_keys_and_locked_axes():
    app = APP.read_text(encoding="utf-8")
    assert all(re.search(r"plotly_chart\(.*key=", line) for line in app.splitlines() if "st.plotly_chart(" in line)
    viz = (ROOT / "pc_visualization.py").read_text(encoding="utf-8")
    assert viz.count("return _base(fig") >= 5 and "def lock_axes" in viz
