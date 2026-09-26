"""Exakte Rechnung (HiGHS über scipy): das Optimum des p-Center-Problems per Binärsuche über den Radius, die Überdeckungs-LP, das p-Median-Optimum für den Vergleich, Brute Force für Kleinstnetze.

p-Center exakt: der Optimalradius ist einer der Abstände. Für einen Radius r fragt man: wie viele Mittelpunkte braucht man mindestens, damit jeder Punkt höchstens r von einem entfernt ist (Überdeckungsproblem,
kleinstes Mengenüberdeckungs-MILP)? Reichen p, ist r zulässig. Die Zahl der nötigen Mittelpunkte sinkt mit wachsendem Radius, deshalb genügt eine Binärsuche über die sortierten Abstände.
Der Radius ist ganzzahlig, die Rechnung liefert sein Ergebnis exakt; nur die Auswahl der Mittelpunkte ist bei mehreren gleich guten nicht eindeutig.
"""

from itertools import combinations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix

from pc_algorithms import radius, total

EPS = 1e-6


def _cover_matrix(d, r):
    n = len(d)
    return np.array([[1.0 if d[j][i] <= r else 0.0 for i in range(n)] for j in range(n)])


def min_cover(d, r, integer=True):
    """Kleinste Zahl von Mittelpunkten, sodass jeder Punkt höchstens r von einem entfernt ist: (Anzahl bzw. LP-Wert, Auswahl oder ())."""
    n = len(d)
    a = _cover_matrix(d, r)
    if integer:
        res = milp(np.ones(n), constraints=LinearConstraint(a, np.ones(n), np.inf), integrality=np.ones(n), bounds=Bounds(0, 1))
        if res.status != 0:
            raise RuntimeError("Überdeckung nicht lösbar: " + str(res.message))
        return int(round(res.fun)), tuple(int(i) for i in np.flatnonzero(res.x > 0.5))
    res = linprog(np.ones(n), A_ub=-a, b_ub=-np.ones(n), bounds=(0, 1), method="highs")
    if res.status != 0:
        raise RuntimeError("Überdeckungs-LP nicht lösbar: " + str(res.message))
    return float(res.fun), ()


def _bottleneck_search(d, p, integer):
    values = sorted({v for row in d for v in row})
    lo, hi = 0, len(values) - 1                                  # bei größtem Abstand genügt ein Mittelpunkt
    while lo < hi:
        mid = (lo + hi) // 2
        k, _s = min_cover(d, values[mid], integer)
        if k <= p + EPS:
            hi = mid
        else:
            lo = mid + 1
    return values[lo]


def exact_radius(d, p):
    """Optimalradius (ganzzahlig)."""
    return _bottleneck_search(d, p, True)


def lp_radius(d, p):
    """Kleinster Radius, für den die Überdeckungs-LP mit p Mittelpunkten zulässig ist: eine untere Schranke des Optimalradius (ganzzahlig, da nur Abstände in Frage kommen)."""
    return _bottleneck_search(d, p, False)


def best_sum_at_radius(d, p, r):
    """Unter allen Auswahlen mit höchstens p Mittelpunkten und Radius <= r diejenige mit der kleinsten Summe der Abstände: (Summe, Auswahl). Zeigt, wie 'billig' ein p-Center-Optimum sein kann."""
    n = len(d)
    nv = n + n * n                                               # y_i, dann x_ji (Punkt j wird von i bedient), nur mit d <= r
    cost = np.concatenate([np.zeros(n), np.array(d, dtype=float).ravel()])
    rows, cols, vals, lo, hi = [], [], [], [], []
    k = 0
    for j in range(n):
        for i in range(n):
            rows.append(k); cols.append(n + j * n + i); vals.append(1.0)
        lo.append(1.0); hi.append(1.0); k += 1
    for j in range(n):
        for i in range(n):
            rows += [k, k]; cols += [n + j * n + i, i]; vals += [1.0, -1.0]
            lo.append(-np.inf); hi.append(0.0); k += 1
    for i in range(n):
        rows.append(k); cols.append(i); vals.append(1.0)
    lo.append(0.0); hi.append(float(p)); k += 1
    ub = np.ones(nv)
    for j in range(n):
        for i in range(n):
            if d[j][i] > r:
                ub[n + j * n + i] = 0.0
    a = coo_matrix((vals, (rows, cols)), shape=(k, nv)).tocsr()
    integ = np.concatenate([np.ones(n), np.zeros(n * n)])
    res = milp(cost, constraints=LinearConstraint(a, np.array(lo), np.array(hi)), integrality=integ, bounds=Bounds(np.zeros(nv), ub), options={"time_limit": 60.0, "mip_rel_gap": 0.0})
    if res.status != 0:
        raise RuntimeError("Summe bei festem Radius nicht lösbar: " + str(res.message))
    return int(round(res.fun)), tuple(int(i) for i in range(n) if res.x[i] > 0.5)


def solve_pmedian(d, p):
    """p-Median (Summe der Abstände zum nächsten Mittelpunkt): (Optimum, Auswahl); bei mehreren gleich guten Auswahlen nicht eindeutig."""
    n = len(d)
    nv = n + n * n
    cost = np.concatenate([np.zeros(n), np.array(d, dtype=float).ravel()])
    rows, cols, vals, lo, hi = [], [], [], [], []
    k = 0
    for j in range(n):
        for i in range(n):
            rows.append(k); cols.append(n + j * n + i); vals.append(1.0)
        lo.append(1.0); hi.append(1.0); k += 1
    for j in range(n):
        for i in range(n):
            rows += [k, k]; cols += [n + j * n + i, i]; vals += [1.0, -1.0]
            lo.append(-np.inf); hi.append(0.0); k += 1
    for i in range(n):
        rows.append(k); cols.append(i); vals.append(1.0)
    lo.append(float(p)); hi.append(float(p)); k += 1
    a = coo_matrix((vals, (rows, cols)), shape=(k, nv)).tocsr()
    integ = np.concatenate([np.ones(n), np.zeros(n * n)])
    res = milp(cost, constraints=LinearConstraint(a, np.array(lo), np.array(hi)), integrality=integ, bounds=Bounds(0, 1), options={"time_limit": 60.0, "mip_rel_gap": 0.0})
    if res.status != 0:
        raise RuntimeError("p-Median nicht lösbar: " + str(res.message))
    return int(round(res.fun)), tuple(int(i) for i in range(n) if res.x[i] > 0.5)


def brute_force_center(d, p):
    """Alle Auswahlen mit p Mittelpunkten (nur Kleinstnetze): (Optimalradius, Liste der optimalen Auswahlen)."""
    n = len(d)
    best, sets = None, []
    for s in combinations(range(n), min(p, n)):
        r = radius(d, s)
        if best is None or r < best:
            best, sets = r, [s]
        elif r == best:
            sets.append(s)
    return best, sets


def brute_force_median(d, p):
    n = len(d)
    best, sets = None, []
    for s in combinations(range(n), min(p, n)):
        v = total(d, s)
        if best is None or v < best:
            best, sets = v, [s]
        elif v == best:
            sets.append(s)
    return best, sets
