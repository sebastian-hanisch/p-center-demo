"""Szenario: p-Center (Minimax-Standortplanung): p Punkte einer Karte werden zu Mittelpunkten, jeder Punkt geht zum nächsten Mittelpunkt, gesucht ist die Auswahl mit dem kleinsten größten Abstand
(dem Radius). Standorte sind die Punkte selbst (Vertex-p-Center) - nur dafür gilt die Garantie 2 des Farthest-first-Verfahrens.

Alles ist ganzzahlig und läuft über einen eigenen Zufallsgenerator (SplitMix64 auf Python-Ints, Kopie aus `ufl_scenario.py`) statt über `numpy.random`: numpy garantiert keine über Versionen stabilen
Zufallsströme, die CI installiert aber wöchentlich die neueste Version. Abstände sind ganzzahlig (Zehntel-Einheiten), also sind alle Radien ganze Zahlen und Vergleiche exakt: Voreinstellungen, Seeds und
jede im Text genannte Zahl sind auf Windows und Linux dieselben.
"""

from dataclasses import dataclass
from math import isqrt

_MASK = (1 << 64) - 1
MAP_W = 100
CLUSTERS = 4
CLUSTER_SPREAD = 15      # Punkte eines Clusters liegen im Quadrat +- CLUSTER_SPREAD um den Clustermittelpunkt


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def below(self, n):
        """Ganzzahl in 0..n-1 (die Modulo-Verzerrung bei n <= 101 liegt um 1e-17)."""
        return self.next() % n


def distance(a, b):
    """Euklidische Entfernung in Zehntel-Einheiten, ganzzahlig (abgerundet)."""
    return isqrt(100 * ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


@dataclass(frozen=True)
class PC:
    kind: str            # "uniform", "cluster" oder "teaching"
    names: tuple
    pos: tuple           # ((x, y), ...)
    d: tuple             # Abstandsmatrix d[i][j], ganzzahlig

    @property
    def n(self):
        return len(self.pos)


def _build(kind, pos):
    n = len(pos)
    return PC(kind, tuple(f"Punkt {k + 1}" for k in range(n)), tuple(pos), tuple(tuple(distance(pos[i], pos[j]) for j in range(n)) for i in range(n)))


def generate(n, kind, seed):
    """`uniform`: gleichverteilt auf 0..99; `cluster`: vier Cluster (Mittelpunkte gleichverteilt, Punkte in einem Quadrat um sie, auf die Karte begrenzt)."""
    rng = SplitMix64(seed)
    if kind == "uniform":
        pos = [(rng.below(MAP_W), rng.below(MAP_W)) for _ in range(n)]
    elif kind == "cluster":
        centers = [(rng.below(MAP_W), rng.below(MAP_W)) for _ in range(CLUSTERS)]
        pos = []
        for _ in range(n):
            cx, cy = centers[rng.below(CLUSTERS)]
            x = min(MAP_W - 1, max(0, cx + rng.below(2 * CLUSTER_SPREAD + 1) - CLUSTER_SPREAD))
            y = min(MAP_W - 1, max(0, cy + rng.below(2 * CLUSTER_SPREAD + 1) - CLUSTER_SPREAD))
            pos.append((x, y))
    else:
        raise KeyError(kind)
    return _build(kind, pos)


def with_outlier(inst, position=(150, 150)):
    """Das Netz mit einem zusätzlichen, weit entfernten Punkt (Ausreißer-Test); der Punkt liegt außerhalb der Karte."""
    return _build(inst.kind, list(inst.pos) + [position])


def teaching(name):
    """Lehrnetze von Hand: kleine Punktmengen, an denen sich ein Effekt nachrechnen lässt."""
    if name not in TEACHING:
        raise KeyError(name)
    return _build("teaching", TEACHING[name])


# Lehrnetze (per Suche über kleine Punktmengen gefunden, hier fest eingetragen; tests/test_algorithms.py rechnet jede Aussage nach).
TEACHING = {
    # Farthest-first ab Punkt 1 mit p = 2: Radius 160, das Optimum 80 - die Garantie 2 wird genau erreicht
    "gonzalez_trap": [(20, 0), (13, 9), (1, 17), (15, 1), (20, 16), (19, 8), (18, 15)],
    # Swap-Lokalsuche ab Farthest-first mit p = 3: bleibt bei Radius 100 stehen, das Optimum ist 60
    "swap_stuck": [(7, 14), (16, 7), (1, 6), (9, 16), (12, 15), (17, 18), (18, 16), (10, 20)],
    # p = 2: die p-Median-Lösung hat den Radius 196, das p-Center-Optimum 92 - Summe und Maximum wollen Verschiedenes
    "fairness": [(16, 18), (7, 17), (20, 15), (9, 19), (8, 19), (18, 15), (0, 1), (18, 9), (11, 18)],
}
