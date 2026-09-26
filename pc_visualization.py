"""Plotly-Abbildungen: Karte mit Mittelpunkten, Überdeckungskreisen und engstem Punkt, Radiusverlauf von Farthest-first, Radien in Prozent des Optimums, Experimente (Verteilung, Reihe über p).
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen. Karten haben gleichen Maßstab (scaleanchor) mit automatischem Bereich; der Rand kommt über zwei unsichtbare Punkte
(ein fest vorgegebener Bereich wird beim ersten Zeichnen in schmaler Breite eingefroren). Abstände sind in Zehntel-Einheiten, Kreise in Karteneinheiten (Radius / 10)."""

import plotly.graph_objects as go

import pc_algorithms as al
import pc_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.22), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, centers=(), circles=True, next_center=None, height=480, outlier=None):
    """Punkte (blau), Mittelpunkte (grün, mit Kreis vom Radius der Auswahl), der engste Punkt (rot umrandet), Linien zum nächsten Mittelpunkt. `next_center`: der als Nächstes gewählte Punkt (Farthest-first)."""
    fig = go.Figure()
    centers = tuple(sorted(centers))
    far_idx = None
    if centers:
        far_idx, r = al.bottleneck(inst.d, centers)
        assign = al.assignment(inst.d, centers)
        xs, ys = [], []
        for j, i in enumerate(assign):
            if j == i:
                continue
            xs += [inst.pos[j][0], inst.pos[i][0], None]
            ys += [inst.pos[j][1], inst.pos[i][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLORS["line"], width=1), hoverinfo="skip", showlegend=False))
        if circles:
            for i in centers:
                fig.add_shape(type="circle", xref="x", yref="y", x0=inst.pos[i][0] - r / 10, x1=inst.pos[i][0] + r / 10, y0=inst.pos[i][1] - r / 10, y1=inst.pos[i][1] + r / 10,
                              line=dict(color=C.COLORS["circle"], width=1.5, dash="dot"), fillcolor="rgba(44,160,44,0.06)")
    others = [j for j in range(inst.n) if j not in centers]
    fig.add_trace(go.Scatter(x=[inst.pos[j][0] for j in others], y=[inst.pos[j][1] for j in others], mode="markers", name="Punkt",
                             marker=dict(color=C.COLORS["point"], size=8, opacity=0.8), text=[f"{inst.names[j]}" for j in others], hoverinfo="text"))
    if outlier is not None:
        fig.add_trace(go.Scatter(x=[inst.pos[outlier][0]], y=[inst.pos[outlier][1]], mode="markers", name="Ausreißer", marker=dict(color=C.COLORS["outlier"], size=11, symbol="x"),
                                 text=[inst.names[outlier]], hoverinfo="text"))
    if far_idx is not None:
        fig.add_trace(go.Scatter(x=[inst.pos[far_idx][0]], y=[inst.pos[far_idx][1]], mode="markers", name="engster Punkt", marker=dict(color="rgba(0,0,0,0)", size=17, line=dict(color=C.COLORS["far"], width=2.5)),
                                 text=[f"{inst.names[far_idx]}: Abstand {r / 10:.1f}".replace(".", ",")], hoverinfo="text"))
    if next_center is not None:
        fig.add_trace(go.Scatter(x=[inst.pos[next_center][0]], y=[inst.pos[next_center][1]], mode="markers", name="nächster Mittelpunkt", marker=dict(color="rgba(0,0,0,0)", size=20, symbol="diamond-open", line=dict(color="#111111", width=2)),
                                 text=[inst.names[next_center]], hoverinfo="text"))
    if centers:
        fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in centers], y=[inst.pos[i][1] for i in centers], mode="markers+text", name="Mittelpunkt",
                                 marker=dict(symbol="square", color=C.COLORS["center"], size=14, line=dict(color="#111111", width=1)),
                                 text=[str(i + 1) for i in centers], textposition="top center", textfont=dict(size=10), hovertext=[inst.names[i] for i in centers], hoverinfo="text"))
    xs = [p[0] for p in inst.pos]
    ys_ = [p[1] for p in inst.pos]
    pad = 6
    if centers and circles:
        rr = al.radius(inst.d, centers) / 10
        xs += [inst.pos[i][0] - rr for i in centers] + [inst.pos[i][0] + rr for i in centers]
        ys_ += [inst.pos[i][1] - rr for i in centers] + [inst.pos[i][1] + rr for i in centers]
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys_) - pad, max(ys_) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    return _base(fig, height)


def build_radius_curve(radii, opt, current=None, height=340):
    """Radius nach 1, 2, ..., p Mittelpunkten; Linien für das Optimum und das Doppelte des Optimums (die Garantie)."""
    ks = list(range(1, len(radii) + 1))
    fig = go.Figure(go.Scatter(x=ks, y=[v / 10 for v in radii], mode="lines+markers", name="Farthest-first", line=dict(color=C.COLORS["gonzalez"], width=2)))
    if current is not None and 1 <= current <= len(radii):
        fig.add_trace(go.Scatter(x=[current], y=[radii[current - 1] / 10], mode="markers", marker=dict(color=C.COLORS["center"], size=13, symbol="diamond"), name="aktueller Schritt"))
    fig.add_hline(y=opt / 10, line=dict(color=C.COLORS["exact"], dash="dash"), annotation_text="Optimum (p Mittelpunkte)", annotation_position="top right")
    fig.add_hline(y=2 * opt / 10, line=dict(color=C.COLORS["lp"], dash="dot"), annotation_text="Garantie: 2 × Optimum", annotation_position="top right")
    fig.update_xaxes(title="Zahl der Mittelpunkte", dtick=1)
    fig.update_yaxes(title="Radius", rangemode="tozero")
    return _base(fig, height)


def build_bounds(rows, height=340):
    """Radien in Prozent des Optimalradius (Linie bei 100)."""
    colors = {"untere Schranke": C.COLORS["lp"], "Optimum": C.COLORS["exact"], "Lösung": C.COLORS["gonzalez"]}
    labels = [r[0] for r in rows][::-1]
    vals = [r[2] for r in rows][::-1]
    cols = [colors[r[3]] for r in rows][::-1]
    fig = go.Figure(go.Bar(y=labels, x=vals, orientation="h", marker=dict(color=cols), text=[f"{v:.0f} %" for v in vals], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}: %{x:.1f} % des Optimalradius<extra></extra>"))
    fig.update_xaxes(range=[0, max(vals) + 20], title="Prozent des Optimalradius (100 = Optimum, 200 = Garantie)")
    fig.add_vline(x=100, line=dict(color=C.COLORS["exact"], dash="dash"))
    fig.add_vline(x=200, line=dict(color=C.COLORS["lp"], dash="dot"))
    return _base(fig, height)


def build_series(series, height=420):
    """Verhältnisse zum Optimum gegen p (Mittel über feste Netze)."""
    xs = [r["p"] for r in series]
    fig = go.Figure()
    for key, name, color in (("g0", "Farthest-first, Start Punkt 1", C.COLORS["gonzalez"]), ("gbest", "Farthest-first, bester Start", C.COLORS["best"]), ("swap", "Swap-Lokalsuche", C.COLORS["swap"]),
                             ("med_radius", "Radius der p-Median-Lösung", C.COLORS["median"])):
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in series], mode="lines+markers", name=name, line=dict(color=color, width=2)))
    fig.update_xaxes(title="Zahl der Mittelpunkte p", dtick=1)
    fig.update_yaxes(title="Radius / Optimalradius (Mittel)")
    return _base(fig, height)


def build_dist(dist, height=420):
    rows = dist["rows"]
    fig = go.Figure()
    for key, name, color in (("g0", "Farthest-first (Start 1)", C.COLORS["gonzalez"]), ("gbest", "Farthest-first (bester Start)", C.COLORS["best"]), ("swap", "Swap (Radius, Summe)", C.COLORS["swap"]),
                             ("plain", "Swap (nur Radius)", C.COLORS["median"]), ("med_radius", "p-Median-Lösung", "#7f7f7f")):
        fig.add_trace(go.Box(y=[r[key] for r in rows], name=name, marker_color=color, boxpoints="all", jitter=0.4, pointpos=0))
    fig.update_yaxes(title="Radius / Optimalradius")
    return _base(fig, height)
