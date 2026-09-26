"""p-Center - wie weit ist der Weiteste noch weg? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo EIN Modell - das p-Center-Problem (Minimax-Standortplanung) - und lässt stattdessen das Beispiel wachsen.
Neues Stück der Standortplanungs-Linie der "Konzepte"-Reihe, Kind des Standortproblems ohne Kapazität (Wurzel): dieselbe Standortwahl, aber das Ziel ist der größte Abstand statt der Summe.
Siehe README für die Einordnung.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import pc_algorithms as al
import pc_constants as C
import pc_evaluation as ev
import pc_scenario as sc
from pc_presets import (
    KEPT,
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    seed_widget,
    sync_query_params,
)
from pc_visualization import build_bounds, build_dist, build_map, build_radius_curve, build_series

st.set_page_config(page_title="p-Center – Sebastian Hanisch", layout="wide")


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _int(x):
    return "–" if x is None else f"{int(round(x)):,}".replace(",", " ")


def _d(x):
    """Abstände sind in Zehntel-Einheiten gerechnet: Anzeige in Karteneinheiten mit einer Nachkommastelle."""
    return "–" if x is None else f"{x / 10:,.1f}".replace(",", " ").replace(".", ",")


def _q(a, b):
    """Quotient, auch wenn der Nenner 0 ist (Optimalradius 0, wenn jeder Punkt Mittelpunkt ist): 0 / 0 = 1."""
    if b:
        return a / b
    return 1.0 if a == 0 else float("inf")


def _pct(x, digits=0):
    return "–" if x is None else f"{x:.{digits}f} %".replace(".", ",")


@st.cache_resource(show_spinner=False, max_entries=32)
def _analysis(p):
    return ev.analyse(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _dist(p):
    return ev.distribution(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _series(p):
    return ev.p_series(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _outlier(p):
    return ev.outlier_test(p)


@st.cache_resource(show_spinner=False, max_entries=8)
def _circle(p):
    return ev.circle_test(p)


st.title("🎯 p-Center – wie weit ist der Weiteste noch weg?")
st.markdown(
    """
Bisher war das Ziel der Standortwahl eine **Summe** (Fixkosten plus Wege). Beim **p-Center-Problem** zählt nur der **Weiteste**: von $n$ Punkten werden $p$ zu Mittelpunkten, jeder Punkt geht zum nächsten, und gesucht ist die Auswahl,
bei der der **größte Abstand** möglichst klein ist („niemand ist weiter als $r$ entfernt“, wie bei Notdiensten oder Filialen mit Erreichbarkeitsgarantie). Das genaue Optimum ist hier leicht zu berechnen (Binärsuche über den Radius mit einer Überdeckungsrechnung);
das klassische einfache Verfahren, **Farthest-first** (Gonzalez), hat eine **Garantie**: nie mehr als das Doppelte des Optimums. Die Demo zeigt, was von dieser Garantie in der Praxis übrig bleibt, wie stark der **Startpunkt** wirkt,
wie die **Swap-Lokalsuche** nachbessert und was der **Preis der Fairness** gegenüber der Summen-Lösung (p-Median) ist.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren vergleichen, zeigt diese Demo - ein Stück der Standortplanungs-Linie der \"Konzepte\"-Reihe - **ein** Modell an einem wachsenden Beispiel. "
    "Verwandt: das Standortproblem ohne Kapazität (Summe statt Maximum), die k-Means-Demo (p-Median ist dort nur k-Medoids) und die Rettungsdienst-Demo (Überdeckung mit Verfügbarkeit)."
)

with st.expander("So funktioniert das p-Center-Problem", expanded=True):
    st.markdown(
        r"""
1. **Modell:** $n$ Punkte, Abstände $d_{ij}$; wähle $p$ Punkte als Mittelpunkte $S$, sodass der **Radius** $\max_j\min_{i\in S}d_{ij}$ minimal ist. Die Mittelpunkte sind hier Punkte der Menge (Vertex-p-Center).
2. **Farthest-first:** Startpunkt wählen, dann immer den Punkt zum Mittelpunkt machen, der von allen bisherigen am weitesten entfernt ist. **Garantie:** nach $p$ Schritten sind $p+1$ Punkte paarweise mindestens $r$ voneinander entfernt (der weiteste Punkt und die $p$ Mittelpunkte); zwei davon müssen im Optimum denselben Mittelpunkt haben, also ist der Optimalradius mindestens $r/2$.
3. **Exakt:** der Optimalradius ist einer der Abstände. Für einen Radius $r$ fragt man, wie viele Mittelpunkte man mindestens braucht, damit jeder Punkt höchstens $r$ von einem entfernt ist (Überdeckungsproblem); reichen $p$, ist $r$ zulässig. Eine Binärsuche über die sortierten Abstände findet den kleinsten.
4. **Swap-Lokalsuche:** einen Mittelpunkt gegen einen anderen Punkt tauschen, solange (Radius, Summe) lexikografisch sinkt. Ohne den zweiten Schlüssel bleibt sie auf Plateaus stehen, auf denen viele Tausche den Radius nicht ändern.
        """
    )

st.caption("🎯 Schnellstart – ein Beispiel laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    net_key = st.selectbox("Netz", list(C.NETS), key="net_select", format_func=lambda k: C.NETS[k],
                           help="Ein Zufallsnetz (gleichverteilt oder in vier Clustern) oder ein kleines Lehrnetz, an dem sich ein Effekt von Hand nachrechnen lässt.")
    if net_key in C.FIXED_NETS:
        points = int(st.session_state.get(KEPT["points_slider"], C.DEFAULT_POINTS))
        seed = int(st.session_state.get(KEPT["seed_input"], C.DEFAULT_SEED))
        st.caption("Dieses Netz ist fest - Punktzahl und Seed gehören zu den Zufallsnetzen.")
    else:
        seed_widget("points_slider")
        points = st.slider("Punkte", *bounds("points_slider"), key="points_slider")
        st.session_state[KEPT["points_slider"]] = points
        seed_widget("seed_input")
        seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
        st.session_state[KEPT["seed_input"]] = seed
        st.button("🎲 Neues Netz generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Zufalls-Seed. Die Verteilungen über feste Netze weiter unten ändern sich dabei nicht.")
    outlier = st.checkbox("Ausreißer hinzufügen", key="outlier_box", help="Fügt einen weit entfernten Punkt außerhalb der Karte hinzu und zeigt, wie stark er den Radius und die Summe treibt.")
    n_now = (len(sc.TEACHING[net_key]) if net_key in C.FIXED_NETS else int(points)) + (1 if outlier else 0)
    p_val = st.slider("Zahl der Mittelpunkte p", *bounds("p_slider"), key="p_slider", help="Wie viele Punkte zu Mittelpunkten werden (höchstens so viele wie Punkte).")
    st.session_state["start_slider"] = max(1, min(int(st.session_state.get("start_slider", 1)), n_now))
    start = st.slider("Startpunkt von Farthest-first", 1, n_now, key="start_slider", help="Der erste Mittelpunkt. Der Startpunkt entscheidet stark über das Ergebnis; weiter unten stehen der beste und der schlechteste.")

sync_query_params({"net_select": net_key, "points_slider": int(points), "p_slider": int(p_val), "start_slider": int(start), "outlier_box": int(bool(outlier)), "seed_input": int(seed)})

params = ev.canonical(ev.Params(net_key, int(points), int(p_val), int(seed), int(start), bool(outlier)))
with st.spinner("Rechne..."):
    a = _analysis(params)
inst, opt, far = a["inst"], a["radius"], a["far"]
p = params.p
out_idx = inst.n - 1 if params.outlier else None

st.markdown(f"Das Netz hat **{inst.n} Punkte**, gesucht sind **{p}** Mittelpunkte. Der **Optimalradius** ist **{_d(opt)}**; die einfachste Überdeckungsrechnung (LP) sagt {_d(a['lp'])} voraus"
            + (" - sie trifft das Optimum." if a["lp"] == opt else " - eine Untergrenze."))

# --- Selbst probieren ---------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Selbst probieren: welche Punkte werden Mittelpunkte?")
if st.session_state.get("pc_pick_owner") != params:
    st.session_state["pick_multi"] = list(range(p))
    st.session_state["pc_pick_owner"] = params
chosen = st.multiselect("Mittelpunkte", list(range(inst.n)), key="pick_multi", format_func=lambda i: inst.names[i], max_selections=p,
                        help="Voreingestellt sind die ersten Punkte. Jeder Punkt geht zum nächsten Mittelpunkt; der engste Punkt ist rot umrandet.")
cl, cr = st.columns([3, 2])
with cl:
    st.plotly_chart(build_map(inst, chosen, height=460, outlier=out_idx), width="stretch", key="pick_map")
with cr:
    if chosen:
        tr = ev.try_centers(inst, chosen)
        m1, m2 = st.columns(2)
        m1.metric("Radius", _d(tr["radius"]), delta=f"{_pct(100 * _q(tr['radius'], opt) - 100)} über dem Optimum" if tr["radius"] > opt else "Optimum", delta_color="off" if tr["radius"] == opt else "inverse")
        m2.metric("Optimalradius", _d(opt))
        m3, m4 = st.columns(2)
        m3.metric("Summe der Abstände", _d(tr["total"]), help="Summe der Abstände aller Punkte zum nächsten Mittelpunkt (das Ziel des p-Median-Problems).")
        m4.metric("Engster Punkt", inst.names[tr["bottleneck"]].replace("Punkt ", "P"), help="Der Punkt mit dem größten Abstand zu seinem Mittelpunkt: er bestimmt den Radius.")
        if len(chosen) < p:
            st.caption(f"Erst {len(chosen)} von {p} Mittelpunkten gewählt.")
    else:
        st.info("Wählen Sie mindestens einen Punkt.")
st.caption("Grün: Mittelpunkte mit ihrem Überdeckungskreis (Radius = größter Abstand der Auswahl); rot umrandet: der engste Punkt. Abstände in Karteneinheiten.")

st.markdown("---")

# --- Farthest-first Schritt für Schritt ------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Farthest-first Schritt für Schritt")
owner = (params,)
if st.session_state.get("pc_step_owner") != owner:
    st.session_state["pc_step"] = p
    st.session_state["pc_step_owner"] = owner
view_slot = st.empty()
if p > 1:
    step_col, play_col = st.columns([5, 2])
    with step_col:
        step = st.slider("Schritt", 1, p, key="pc_step", help="Nach k Schritten sind k Mittelpunkte gesetzt; der Diamant zeigt den Punkt, der als Nächstes gewählt wird (der weiteste).")
    with play_col:
        auto_play = st.button("▶️ Abspielen", width="stretch")
else:
    step, auto_play = 1, False


def _render(k):
    with view_slot.container():
        c1, c2 = st.columns([3, 2])
        with c1:
            nxt = far.centers[k] if k < p else None
            st.plotly_chart(build_map(inst, far.centers[:k], next_center=nxt, height=460, outlier=out_idx), width="stretch", key=f"far_map_{k}")
        with c2:
            st.plotly_chart(build_radius_curve(far.radii, opt, current=k, height=380), width="stretch", key=f"far_curve_{k}")
        m1, m2 = st.columns(2)
        m1.metric("Radius nach diesem Schritt", _d(far.radii[k - 1]))
        m2.metric("Verhältnis zum Optimum von p", _f(_q(far.radii[k - 1], opt), 2), help="Radius geteilt durch den Optimalradius für p Mittelpunkte. Garantiert ist nach p Schritten höchstens 2.")


if auto_play:
    for k in range(1, p + 1):
        _render(k)
        time.sleep(min(0.5, 6.0 / max(p, 1)))
else:
    _render(step)
ratio = _q(far.radius, opt)
if ratio >= 1.999:
    st.warning(f"⚠️ Farthest-first ab Punkt {far.first + 1} endet bei {_d(far.radius)}: **genau das Doppelte** des Optimums ({_d(opt)}). Die Garantie ist erreicht, nicht übertroffen.")
elif far.radius == opt:
    st.success(f"✅ Farthest-first ab Punkt {far.first + 1} trifft das Optimum ({_d(opt)}).")
else:
    st.info(f"Farthest-first ab Punkt {far.first + 1} endet bei {_d(far.radius)}, das ist das {_f(ratio, 2)}-Fache des Optimums ({_d(opt)}); die Garantie erlaubt bis zum Doppelten.")

st.markdown("---")

# --- Wie gut ist das? ---------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Wie gut ist das? Startpunkt und Swap-Lokalsuche")
rows = ev.bound_rows(a)
st.plotly_chart(build_bounds(rows), width="stretch", key="bounds_chart")
sw = a["swap"]
st.table({"Verfahren": ["Optimum (billigste Auswahl mit optimalem Radius)", "Swap-Lokalsuche (ab gewähltem Start)", "Farthest-first, gewählter Start", "Farthest-first, bester Start", "Farthest-first, schlechtester Start", "p-Median-Lösung (Summe minimal)"],
          "Radius": [_d(opt), _d(sw.radius), _d(far.radius), _d(a["starts"][a["best_start"]]), _d(a["starts"][a["worst_start"]]), _d(a["median_radius"])],
          "Summe der Abstände": [_d(a["center_sum"]), _d(sw.total), _d(a["far_sum"]), "–", "–", _d(a["median"])]})
st.caption(f"Swap-Lokalsuche: {len(sw.moves)} Züge, {_int(sw.evals)} bewertete Tausche; ohne den zweiten Schlüssel (nur der Radius) endet sie bei {_d(a['swap_plain'].radius)} nach {len(a['swap_plain'].moves)} Zügen. "
           f"Farthest-first von jedem der {inst.n} Startpunkte aus liefert Radien zwischen {_d(a['starts'][a['best_start']])} und {_d(a['starts'][a['worst_start']])}.")

st.markdown("---")

# --- Preis der Fairness ---------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Preis der Fairness: Maximum gegen Summe")
f1, f2 = st.columns(2)
with f1:
    st.markdown("**p-Center** (größter Abstand minimal; unter den Optima die kleinste Summe)")
    st.plotly_chart(build_map(inst, a["center_set"], height=380, outlier=out_idx), width="stretch", key="fair_center")
    st.metric("Radius / Summe", f"{_d(opt)} / {_d(a['center_sum'])}")
with f2:
    st.markdown("**p-Median** (Summe der Abstände minimal)")
    st.plotly_chart(build_map(inst, a["median_set"], height=380, outlier=out_idx), width="stretch", key="fair_median")
    st.metric("Radius / Summe", f"{_d(a['median_radius'])} / {_d(a['median'])}")
st.caption(f"Die p-Median-Lösung hat einen {_f(_q(a['median_radius'], opt), 2)}-fachen Radius, die p-Center-Lösung eine {_f(_q(a['center_sum'], a['median']), 2)}-fache Summe: wer das Maximum drückt, zahlt in der Summe, und umgekehrt. "
           "Wie viel, hängt vom Netz ab; die Experimente unten messen es über 40 Netze.")

st.markdown("---")

# --- Experimente ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Gilt das in jedem Netz?")
st.caption("40 feste Netze mit der gewählten Punktzahl und p: Farthest-first (Start 1 und bester Start), Swap-Lokalsuche mit und ohne Summe als zweiten Schlüssel, p-Median.")
if st.button("40 Netze durchrechnen (dauert einige Sekunden)", key="dist_start"):
    st.session_state["dist_on"] = True
if st.session_state.get("dist_on"):
    with st.spinner("Rechne 40 Netze..."):
        dist = _dist(params)
    s = dist["summary"]
    st.plotly_chart(build_dist(dist), width="stretch", key="dist_chart")
    st.table({"Verfahren": ["Farthest-first (Start 1)", "Farthest-first (bester Start)", "Farthest-first (schlechtester Start)", "Swap (Radius, Summe)", "Swap (nur Radius)", "p-Median-Lösung"],
              "Radius / Optimum (Mittel)": [_f(s[k], 3) for k in ("g0", "gbest", "gworst", "swap", "plain", "med_radius")],
              "schlechtestes Netz": [_f(s[k + "_max"], 2) for k in ("g0", "gbest", "gworst", "swap", "plain", "med_radius")],
              "exakt in": [f"{s[k + '_exact']} von {s['count']}" if k in ("g0", "gbest", "swap", "plain") else "–" for k in ("g0", "gbest", "gworst", "swap", "plain", "med_radius")]})
    st.caption(f"Die Überdeckungs-LP liefert den Optimalradius in {s['lp_exact']} von {s['count']} Netzen (im Mittel {_f(s['lp'], 3)}, schlechtestes {_f(s['lp_min'], 3)}). "
               f"Die p-Center-Lösung mit der kleinsten Summe kostet im Mittel das {_f(s['center_sum'], 3)}-Fache des Summen-Optimums (schlechtestes Netz {_f(s['center_sum_max'], 2)}).")

st.subheader("🔬 Wovon hängt es von p ab?")
st.caption("Verhältnisse zum Optimalradius gegen die Zahl der Mittelpunkte (Mittel über 20 feste Netze).")
if st.button("Reihe über p durchrechnen (dauert einige Sekunden)", key="series_start"):
    st.session_state["series_on"] = True
if st.session_state.get("series_on"):
    with st.spinner("Rechne 5 Werte von p × 20 Netze..."):
        series = _series(params)
    st.plotly_chart(build_series(series), width="stretch", key="series_chart")
    st.table({"p": [str(r["p"]) for r in series], "Farthest-first Start 1 / bester Start": [f"{_f(r['g0'], 3)} / {_f(r['gbest'], 3)}" for r in series],
              "Swap / p-Median-Radius": [f"{_f(r['swap'], 3)} / {_f(r['med_radius'], 3)}" for r in series], "p-Center-Summe / Summen-Optimum": [_f(r["center_sum"], 3) for r in series]})

st.subheader("🔬 Ein Ausreißer")
st.caption("Ein zusätzlicher Punkt bei (150, 150), weit außerhalb der Karte: wie stark treibt er den Optimalradius und die p-Median-Kosten (20 feste Netze, p wie eingestellt)?")
if st.button("Ausreißer-Test durchrechnen", key="outlier_start"):
    st.session_state["outlier_on"] = True
if st.session_state.get("outlier_on"):
    with st.spinner("Rechne 20 Netze mit und ohne Ausreißer..."):
        ot = _outlier(params)
    st.table({"Größe": ["Optimalradius", "p-Median-Kosten"], "Faktor (Mittel)": [_f(ot["radius"], 2), _f(ot["median"], 2)], "kleinster / größter Faktor": [f"{_f(ot['radius_min'], 2)} / {_f(ot['radius_max'], 2)}", f"{_f(ot['median_min'], 2)} / {_f(ot['median_max'], 2)}"]})
    st.caption("Man erwartet, dass das Maximum viel empfindlicher auf einen Ausreißer reagiert als die Summe. Gemessen: der Radius steigt stärker, weil der Ausreißer ihn direkt bestimmt; der Unterschied ist da, aber keine Größenordnung.")

st.subheader("🔬 Muss der Mittelpunkt ein Punkt sein?")
st.caption("Für p = 1: Radius des besten Punkts als Mittelpunkt gegen den kleinsten umschließenden Kreis (Mittelpunkt frei, 40 feste Netze).")
if st.button("Kreis-Vergleich durchrechnen", key="circle_start"):
    st.session_state["circle_on"] = True
if st.session_state.get("circle_on"):
    ct = _circle(params)
    st.table({"Verhältnis Punkt-Mittelpunkt / Kreis": ["Mittel", "kleinstes", "größtes"], "Wert": [_f(ct["mean"], 3), _f(ct["min"], 3), _f(ct["max"], 3)]})
    st.caption("Dass der Mittelpunkt ein Punkt sein muss, kostet für p = 1 im Mittel einige Prozent des Radius (Werte unter 1,000 entstehen nur durch das Abrunden der Abstände auf Zehntel).")

st.markdown("---")

# --- Grenzen ----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist - und wer ansetzt |
|---|---|
| **Mittelpunkte sind Punkte der Menge** | Sind Mittelpunkte frei wählbar (kontinuierliches p-Center), sind Radien kleiner und die Garantie 2 gilt in anderer Form; für p = 1 zeigt die Demo den kleinsten umschließenden Kreis, für größere p ist es nicht gebaut. |
| **Keine Kapazität, keine Gewichte** | Mit Nachfragen (gewichtetes p-Center) und Kapazitäten ist das Problem schwerer; die Kapazität behandelt das Stück „kapazitierte Standortplanung“ mit der Lagrange-Relaxation für die Summe. |
| **Luftlinie, ganzzahlige Abstände** | Abstände sind auf Zehntel abgerundet (damit alle Radien ganze Zahlen sind und Vergleiche exakt); Straßennetze und Fahrzeiten sind nicht gebaut. |
| **Ein Mittelpunkt fällt nie aus** | Mit Verfügbarkeit (Notdienste, Hypercube-Modell) ändert sich die Standortwahl, siehe die Rettungsdienst-Demo. |
| **Exakter Löser** | Das Überdeckungs-MILP löst bei den Reglergrenzen der Demo in Sekundenbruchteilen; größere Netze brauchen spezialisierte Verfahren (Dominierende-Menge-Reduktionen). |
| **Erzeugte Netze** | Gleichverteilte oder geclusterte Punkte, keine Fremddaten; die Lehrnetze sind Konstruktionen. |
"""
)
st.caption("Die Standortplanungs-Linie ist als Ganzes geplant: das Standortproblem ohne Kapazität als Wurzel, danach die kapazitierte Standortplanung mit Lagrange-Relaxation, dieses Stück (Maximum statt Summe), Hub-Standorte, Wettbewerbsstandort und Standort mit Bestand.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Punkte $V$, $|V|=n$, Abstände $d_{ij}$. Für $S\subseteq V$ mit $|S|=p$ ist der Radius $r(S)=\max_{j\in V}\min_{i\in S}d_{ij}$; gesucht $r^*=\min_Sr(S)$.

**Überdeckung.** Für einen Radius $r$ ist $N_r(j)=\{i:d_{ij}\le r\}$. Die kleinste Zahl $k(r)$ von Mittelpunkten mit Radius $\le r$ ist
$$k(r)=\min\Big\{\sum_iy_i:\ \sum_{i\in N_r(j)}y_i\ge1\ \forall j,\ y\in\{0,1\}^V\Big\}.$$
$k(r)$ fällt mit wachsendem $r$, und $r^*=\min\{r:k(r)\le p\}$ ist einer der Abstände: Binärsuche über die sortierten Abstände. Ersetzt man $y\in\{0,1\}$ durch $y\in[0,1]$, ergibt sich die LP-Untergrenze des Radius.

**Farthest-first (Gonzalez 1985).** $S_1=\{s\}$, $S_{k+1}=S_k\cup\{\arg\max_jd(j,S_k)\}$. Ist $r_p=r(S_p)$ und $j$ der weiteste Punkt, dann sind $S_p\cup\{j\}$ ($p+1$ Punkte) paarweise mindestens $r_p$ voneinander entfernt. Im Optimum teilen sich zwei davon einen Mittelpunkt, also $2r^*\ge r_p$. Unter $P\ne NP$ ist keine bessere Näherung als $2$ möglich (Hsu und Nemhauser 1979).

**Swap-Lokalsuche.** Nachbarschaft: einen Mittelpunkt gegen einen Nichtmittelpunkt tauschen; bewertet wird $(r(S),\sum_jd(j,S))$ lexikografisch, Gleichstand: kleinster Index.

**p-Median** zum Vergleich: $\min_S\sum_j\min_{i\in S}d_{ij}$. Der Preis der Fairness ist $r(S_{\text{Median}})/r^*$ und $\text{Summe}(S_{\text{Center}})/\text{Summe}^*$.

**Kleinster umschließender Kreis** (kontinuierliches 1-Center): Mittelpunkt und Radius aus zwei oder drei Punkten des Randes (Welzl 1991).

Implementiert in `pc_scenario.py` (Netze, Lehrnetze, Zufallsgenerator), `pc_algorithms.py` (Farthest-first, Swap), `pc_exact.py` (Binärsuche und Überdeckung, LP, p-Median, HiGHS), `pc_circle.py` (Kreis), `pc_evaluation.py` (Vergleiche, Reihen, Verteilungen).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
