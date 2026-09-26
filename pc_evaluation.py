"""Auswertung: alles, was die Oberfläche zu einem Netz zeigt, und die Experimente über feste Netze (Verteilung, Reihe über p, Ausreißer, Kreis)."""

import statistics
from dataclasses import dataclass

import pc_algorithms as al
import pc_circle as ci
import pc_constants as C
import pc_exact as ex
import pc_scenario as sc


@dataclass(frozen=True)
class Params:
    net: str
    points: int
    p: int
    seed: int
    start: int = 1                 # Startpunkt von Farthest-first, 1-basiert
    outlier: bool = False


def build(p):
    if p.net in C.FIXED_NETS:
        inst = sc.teaching(p.net)
    else:
        inst = sc.generate(p.points, p.net, p.seed)
    return sc.with_outlier(inst, C.OUTLIER_POSITION) if p.outlier else inst


def canonical(p):
    """Feste Lehrnetze rechnen unabhängig von Punktzahl und Seed: gleiche Netze unter demselben Schlüssel; p und Startpunkt werden auf das Netz begrenzt."""
    n = build(p).n if p.net not in C.FIXED_NETS else sc.teaching(p.net).n + (1 if p.outlier else 0)
    points, seed = (p.points, p.seed) if p.net not in C.FIXED_NETS else (C.DEFAULT_POINTS, C.DEFAULT_SEED)
    return Params(p.net, points, min(p.p, n - 1), seed, min(max(1, p.start), n), p.outlier)


def analyse(p):
    """Netz, Optimum, LP-Radius, Farthest-first (mit dem gewählten Startpunkt, bestem und schlechtestem), Swap, p-Median und die billigste Auswahl mit optimalem Radius."""
    inst = build(p)
    d = inst.d
    r = ex.exact_radius(d, p.p)
    lp = ex.lp_radius(d, p.p)
    far = al.farthest_first(d, p.p, p.start - 1)
    starts = al.all_starts(d, p.p)
    best_start = min(range(inst.n), key=lambda f: (starts[f], f))
    worst_start = max(range(inst.n), key=lambda f: (starts[f], -f))
    swap = al.swap_search(d, far.centers, "sum")
    swap_plain = al.swap_search(d, far.centers, "none")
    csum, ccenters = ex.best_sum_at_radius(d, p.p, r)
    med, mcenters = ex.solve_pmedian(d, p.p)
    return dict(inst=inst, radius=r, lp=lp, far=far, starts=starts, best_start=best_start, worst_start=worst_start, swap=swap, swap_plain=swap_plain,
                center_sum=csum, center_set=ccenters, median=med, median_set=mcenters, median_radius=al.radius(d, mcenters), far_sum=al.total(d, far.centers))


def bound_rows(a):
    """Radien in Prozent des Optimalradius: (Name, Radius, Prozent, Art)."""
    r = a["radius"]
    rows = [("LP-Radius (Untergrenze)", a["lp"], "untere Schranke"),
            ("Optimum (exakt)", r, "Optimum"),
            ("Swap-Lokalsuche", a["swap"].radius, "Lösung"),
            (f"Farthest-first, bester Start (Punkt {a['best_start'] + 1})", a["starts"][a["best_start"]], "Lösung"),
            (f"Farthest-first, gewählter Start (Punkt {a['far'].first + 1})", a["far"].radius, "Lösung"),
            (f"Farthest-first, schlechtester Start (Punkt {a['worst_start'] + 1})", a["starts"][a["worst_start"]], "Lösung")]
    return [(name, v, 100.0 * v / r if r else 100.0, kind) for name, v, kind in rows]


def try_centers(inst, chosen):
    """Radius, Summe, engster Punkt und Zuordnung einer gewählten Auswahl."""
    chosen = tuple(sorted(chosen))
    far_idx, far_d = al.bottleneck(inst.d, chosen)
    return dict(radius=far_d, total=al.total(inst.d, chosen), bottleneck=far_idx, assign=al.assignment(inst.d, chosen))


def ratio(a, b):
    return a / b


def _row(inst, p):
    d = inst.d
    r = ex.exact_radius(d, p)
    lp = ex.lp_radius(d, p)
    far0 = al.farthest_first(d, p, 0)
    starts = al.all_starts(d, p)
    swap = al.swap_search(d, far0.centers, "sum")
    plain = al.swap_search(d, far0.centers, "none")
    csum, _cs = ex.best_sum_at_radius(d, p, r)
    med, ms = ex.solve_pmedian(d, p)
    return dict(r=r, lp=lp / r, g0=far0.radius / r, gbest=min(starts) / r, gworst=max(starts) / r, swap=swap.radius / r, plain=plain.radius / r,
                swap_moves=len(swap.moves), plain_moves=len(plain.moves), med_radius=al.radius(d, ms) / r, center_sum=csum / med, median=med)


def summary(rows):
    def mean(k):
        return statistics.fmean(r[k] for r in rows)

    out = {"count": len(rows)}
    for k in ("lp", "g0", "gbest", "gworst", "swap", "plain", "swap_moves", "plain_moves", "med_radius", "center_sum"):
        out[k] = mean(k)
    for k in ("g0", "gbest", "gworst", "swap", "plain", "med_radius", "center_sum"):
        out[k + "_max"] = max(r[k] for r in rows)
    out["g0_median"] = statistics.median(r["g0"] for r in rows)
    out["lp_min"] = min(r["lp"] for r in rows)
    out["lp_exact"] = sum(1 for r in rows if r["lp"] >= 1 - 1e-9)
    for k in ("g0", "gbest", "swap", "plain"):
        out[k + "_exact"] = sum(1 for r in rows if r[k] <= 1)
    return out


def distribution(p, seeds=C.SWEEP_SEEDS):
    kind = p.net if p.net in ("uniform", "cluster") else "uniform"
    rows = [_row(sc.generate(p.points, kind, s), p.p) for s in seeds]
    return dict(rows=rows, summary=summary(rows))


def p_series(p, seeds=C.SERIES_SEEDS, ps=C.SERIES_P):
    kind = p.net if p.net in ("uniform", "cluster") else "uniform"
    out = []
    for q in ps:
        rows = [_row(sc.generate(p.points, kind, s), q) for s in seeds]
        out.append(dict(p=q, **summary(rows)))
    return out


def outlier_test(p, seeds=C.SERIES_SEEDS):
    """Ein zusätzlicher ferner Punkt: Faktor des Optimalradius und der p-Median-Kosten, Zahl der geänderten Mittelpunkte des p-Median."""
    kind = p.net if p.net in ("uniform", "cluster") else "uniform"
    rows = []
    for s in seeds:
        inst = sc.generate(p.points, kind, s)
        out = sc.with_outlier(inst, C.OUTLIER_POSITION)
        r0, r1 = ex.exact_radius(inst.d, p.p), ex.exact_radius(out.d, p.p)
        m0, s0 = ex.solve_pmedian(inst.d, p.p)
        m1, s1 = ex.solve_pmedian(out.d, p.p)
        rows.append(dict(radius=r1 / r0, median=m1 / m0, radius_up=r1 - r0, changed=len(set(s1) - set(s0))))
    return dict(rows=rows, radius=statistics.fmean(r["radius"] for r in rows), median=statistics.fmean(r["median"] for r in rows),
                radius_min=min(r["radius"] for r in rows), radius_max=max(r["radius"] for r in rows), median_min=min(r["median"] for r in rows), median_max=max(r["median"] for r in rows))


def circle_test(p, seeds=C.SWEEP_SEEDS):
    """p = 1: Radius des Vertex-1-Centers gegen den des kleinsten umschließenden Kreises (Mittelpunkt frei)."""
    kind = p.net if p.net in ("uniform", "cluster") else "uniform"
    ratios = []
    for s in seeds:
        inst = sc.generate(p.points, kind, s)
        c = ci.smallest_enclosing_circle(inst.pos)
        ratios.append(ex.exact_radius(inst.d, 1) / 10 / c[2])
    return dict(ratios=ratios, mean=statistics.fmean(ratios), max=max(ratios), min=min(ratios))
