"""Heuristiken für das p-Center-Problem: Farthest-first (Gonzalez 1985, Garantie 2) und die Swap-Lokalsuche.

Farthest-first: mit einem beliebigen Startpunkt beginnen, dann jeweils den Punkt zum Mittelpunkt machen, der von allen bisherigen Mittelpunkten am weitesten entfernt ist (Gleichstand: kleinster Index).
Garantie: liegt der weiteste Punkt nach k Mittelpunkten bei Abstand r, sind die k + 1 Mittelpunkte paarweise mindestens r auseinander - zwei davon müssten im Optimum denselben Mittelpunkt teilen, also ist
der Optimalradius mindestens r / 2. Nach p Mittelpunkten ist der Radius damit höchstens doppelt so groß wie das Optimum.

Swap-Lokalsuche: jeweils den besten Tausch eines Mittelpunkts gegen einen anderen Punkt ausführen; bewertet wird lexikografisch (Radius, Summe der Abstände zum nächsten Mittelpunkt), Gleichstand: kleinster
Index. Ohne den zweiten Schlüssel (`tie="none"`) bleibt die Suche auf den Plateaus stehen, auf denen viele Tausche den Radius nicht ändern.
Alles ganzzahlig und deterministisch.
"""

from dataclasses import dataclass


def nearest_distances(d, centers):
    """Abstand jedes Punkts zum nächsten Mittelpunkt."""
    return [min(d[j][i] for i in centers) for j in range(len(d))]


def radius(d, centers):
    return max(nearest_distances(d, centers))


def total(d, centers):
    return sum(nearest_distances(d, centers))


def assignment(d, centers):
    """Mittelpunkt je Punkt (der nächste; Gleichstand: der kleinste Index)."""
    cs = sorted(centers)
    return tuple(min(cs, key=lambda i: (d[j][i], i)) for j in range(len(d)))


def bottleneck(d, centers):
    """Der engste Punkt: (Index, Abstand) des Punkts, dessen Abstand zum nächsten Mittelpunkt der größte ist (Gleichstand: kleinster Index)."""
    nd = nearest_distances(d, centers)
    r = max(nd)
    return nd.index(r), r


@dataclass(frozen=True)
class Step:
    center: int          # neuer Mittelpunkt in diesem Schritt
    radius_before: int   # Radius der bisherigen Mittelpunkte (Abstand des neuen Mittelpunkts zu ihnen); beim Start 0
    radius_after: int    # Radius mit dem neuen Mittelpunkt


@dataclass(frozen=True)
class Farthest:
    first: int
    centers: tuple       # in der Reihenfolge des Öffnens
    steps: tuple
    radius: int
    radii: tuple         # Radius nach 1, 2, ..., p Mittelpunkten


def farthest_first(d, p, first=0):
    """Farthest-first mit p Mittelpunkten ab dem Startpunkt `first`."""
    n = len(d)
    centers = [first]
    near = list(d[first])
    steps = [Step(first, 0, max(near))]
    while len(centers) < min(p, n):
        r_before = max(near)
        j = near.index(r_before)
        centers.append(j)
        near = [min(near[k], d[j][k]) for k in range(n)]
        steps.append(Step(j, r_before, max(near)))
    return Farthest(first, tuple(centers), tuple(steps), max(near), tuple(s.radius_after for s in steps))


def all_starts(d, p):
    """Farthest-first von jedem Startpunkt aus: Radius je Startpunkt."""
    return [farthest_first(d, p, f).radius for f in range(len(d))]


@dataclass(frozen=True)
class Move:
    out: int
    into: int
    radius_after: int
    total_after: int
    evals: int


@dataclass(frozen=True)
class Swap:
    start: tuple
    centers: tuple
    radius: int
    total: int
    moves: tuple
    evals: int


def swap_search(d, start, tie="sum", max_moves=200):
    """Swap-Lokalsuche ab `start`. `tie="sum"`: lexikografisch (Radius, Summe); `tie="none"`: nur der Radius."""
    n = len(d)
    cur = set(start)

    def key(centers):
        nd = nearest_distances(d, centers)
        return (max(nd), sum(nd)) if tie == "sum" else (max(nd),)

    cur_key = key(cur)
    moves = []
    evals = 0
    while len(moves) < max_moves:
        best = None
        for a in sorted(cur):
            for b in range(n):
                if b in cur:
                    continue
                k = key((cur - {a}) | {b})
                evals += 1
                if best is None or k < best[0]:
                    best = (k, a, b)
        if best is None or best[0] >= cur_key:
            break
        cur_key, a, b = best[0], best[1], best[2]
        cur = (cur - {a}) | {b}
        moves.append(Move(a, b, radius(d, cur), total(d, cur), evals))
    return Swap(tuple(sorted(start)), tuple(sorted(cur)), radius(d, cur), total(d, cur), tuple(moves), evals)
