"""Kleinster umschließender Kreis (p = 1 mit frei wählbarem Mittelpunkt) gegen das Vertex-1-Center.

Im p-Center-Problem dieser Demo sind Mittelpunkte Punkte der Menge. Darf der Mittelpunkt irgendwo liegen (kontinuierliches Problem), ist der Radius für p = 1 der des kleinsten Kreises, der alle Punkte enthält
(Welzl 1991; hier die einfache Fassung mit drei Schleifen und fester Reihenfolge, damit sie deterministisch ist). Für p = 1 ist das Vertex-1-Center nie besser als der Kreis und höchstens doppelt so weit.
"""

from math import hypot


def _circle_two(a, b):
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return cx, cy, hypot(a[0] - b[0], a[1] - b[1]) / 2


def _circle_three(a, b, c):
    ax, ay = a
    bx, by = b
    cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if d == 0:                                    # kollinear: der Kreis über den beiden entferntesten
        pairs = [(a, b), (a, c), (b, c)]
        return max((_circle_two(p, q) for p, q in pairs), key=lambda t: t[2])
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy, hypot(ax - ux, ay - uy)


def _inside(circle, p, eps=1e-9):
    return hypot(p[0] - circle[0], p[1] - circle[1]) <= circle[2] + eps


def smallest_enclosing_circle(points):
    """(Mittelpunkt x, Mittelpunkt y, Radius) des kleinsten Kreises um alle Punkte."""
    pts = list(points)
    if not pts:
        raise ValueError("keine Punkte")
    circle = (pts[0][0], pts[0][1], 0.0)
    for i, p in enumerate(pts):
        if _inside(circle, p):
            continue
        circle = (p[0], p[1], 0.0)
        for j in range(i):
            q = pts[j]
            if _inside(circle, q):
                continue
            circle = _circle_two(p, q)
            for k in range(j):
                r = pts[k]
                if not _inside(circle, r):
                    circle = _circle_three(p, q, r)
    return circle
