"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "p-Center: wie weit ist der Weiteste noch weg?"."""

# --- Regler ---------------------------------------------------------------------------------------------------------------------
POINTS_MIN, POINTS_MAX, DEFAULT_POINTS = 15, 80, 50
P_MIN, P_MAX, DEFAULT_P = 1, 8, 5
START_MIN, START_MAX, DEFAULT_START = 1, 80, 1
DEFAULT_SEED = 1
SEED_MAX = 2_000_000_000

NETS = {
    "uniform": "Zufallsnetz, gleichverteilt",
    "cluster": "Zufallsnetz mit vier Clustern",
    "gonzalez_trap": "Lehrnetz: Farthest-first erreicht die Garantie 2 (7 Punkte)",
    "swap_stuck": "Lehrnetz: Swap-Lokalsuche steckt fest (8 Punkte)",
    "fairness": "Lehrnetz: Summe und Maximum wollen Verschiedenes (9 Punkte)",
}
DEFAULT_NET = "uniform"
FIXED_NETS = ("gonzalez_trap", "swap_stuck", "fairness")
OUTLIER_POSITION = (150, 150)

# --- feste Seed-Mengen (dieselben wie in den Flussdemos; unabhängig vom Nutzer-Seed) ---------------------------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
SERIES_SEEDS = DIST_SEEDS[:20]
SERIES_P = (1, 2, 3, 5, 8)

COLORS = {"center": "#2ca02c", "point": "#1f77b4", "far": "#d62728", "circle": "#2ca02c", "line": "#7f8c8d", "median": "#9467bd", "outlier": "#d62728",
          "gonzalez": "#ff7f0e", "best": "#8c564b", "swap": "#1f77b4", "exact": "#111111", "lp": "#d62728"}

# --- Presets -----------------------------------------------------------------------------------------------------------------
_BASE = dict(net=DEFAULT_NET, points=DEFAULT_POINTS, p=DEFAULT_P, start=DEFAULT_START, seed=DEFAULT_SEED, outlier=False)
PRESETS = {
    "🗺️ Standardnetz": {**_BASE},
    "🪤 Garantie 2 wird erreicht": {**_BASE, "net": "gonzalez_trap", "p": 2},
    "🧲 Swap steckt fest": {**_BASE, "net": "swap_stuck", "p": 3},
    "⚖️ Summe gegen Maximum": {**_BASE, "net": "fairness", "p": 2},
    "🏘️ Vier Cluster": {**_BASE, "net": "cluster", "p": 4},
    "🎯 Ein Mittelpunkt": {**_BASE, "p": 1},
    "📍 Ein Ausreißer": {**_BASE, "p": 4, "outlier": True},
    "🏙️ Großes Netz": {**_BASE, "points": 80, "p": 8},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py belegt.
PRESET_HELP = {
    "🗺️ Standardnetz": "50 Punkte, p = 5: Optimalradius 28,4 (die Überdeckungs-LP trifft ihn). Farthest-first ab Punkt 1 endet bei 42,6 (das 1,50-Fache), die Swap-Lokalsuche bei 32,6; der beste Startpunkt liefert 36,0, der schlechteste 48,6. Die p-Median-Lösung hat den Radius 35,3.",
    "🪤 Garantie 2 wird erreicht": "7 Punkte, p = 2: Optimalradius 8,0, Farthest-first ab Punkt 1 endet bei 16,0 - genau das Doppelte. Der beste Startpunkt (Punkt 6) trifft das Optimum, die Swap-Lokalsuche findet es nach einem Zug.",
    "🧲 Swap steckt fest": "8 Punkte, p = 3: Optimalradius 6,0; Farthest-first ab Punkt 1 endet bei 10,0, und kein einzelner Tausch senkt Radius oder Summe: die Swap-Lokalsuche bleibt bei 10,0. Der beste Startpunkt (Punkt 5) trifft das Optimum.",
    "⚖️ Summe gegen Maximum": "9 Punkte, p = 2: das p-Center-Optimum hat den Radius 9,2 bei der Summe 46,8; das p-Median-Optimum hat die Summe 37,5, aber den Radius 19,6 - mehr als das Doppelte.",
    "🏘️ Vier Cluster": "50 Punkte in vier Clustern, p = 4: Optimalradius 16,1; Farthest-first 22,8 (1,42-fach). Die Swap-Lokalsuche mit der Summe als zweitem Kriterium endet bei 18,6, nur mit dem Radius bei 16,1 (dem Optimum).",
    "🎯 Ein Mittelpunkt": "p = 1: Optimalradius 60,5; Farthest-first ab Punkt 1 endet bei 96,8 (1,60-fach), der beste Startpunkt (Punkt 13) trifft das Optimum, die Swap-Lokalsuche findet es nach einem Zug.",
    "📍 Ein Ausreißer": "51 Punkte (einer bei (150, 150), weit außerhalb der Karte), p = 4: Optimalradius 41,1; Farthest-first 65,0; die Swap-Lokalsuche mit Summe erreicht das Optimum, nur mit dem Radius bleibt sie bei 47,4.",
    "🏙️ Großes Netz": "80 Punkte, p = 8: Optimalradius 21,4; Farthest-first 29,1 (1,36-fach); die Swap-Lokalsuche erreicht das Optimum nach 8 Zügen, der beste Startpunkt liefert 25,6.",
}
