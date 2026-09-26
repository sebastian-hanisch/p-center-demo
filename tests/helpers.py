"""Gemeinsame Hilfen der Tests: kleine Zufallsnetze für Brute-Force-Vergleiche."""

import pc_scenario as sc


def tiny(seed, n=9, grid=30):
    """Kleines Netz mit verschiedenen Punkten auf einem Gitter 0..grid."""
    rng = sc.SplitMix64(seed)
    pos = []
    while len(pos) < n:
        q = (rng.below(grid + 1), rng.below(grid + 1))
        if q not in pos:
            pos.append(q)
    return sc._build("teaching", pos)
