"""Plotly-Abbildungen des Blossom-Algorithmus: Karte nach k Ereignissen (Wald, Blüten als durchscheinende Hüllen, Verbesserungsweg), Verlauf, Verteilung, die Vier-Stufen-Leiter, Aufwand gegen Größe
und der Reichweiten-Sweep. Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen. Karten haben keine Legende (sie würde in schmalen Spalten die Zeichenfläche auf fast null
drücken) und `constrain="domain"`; die Farben stehen in der Erklärung unter der Karte.

Eine Blüte wird nicht zu einem Punkt zusammengezogen (das würde die Karte zerstören, die hier das Szenario ist), sondern als durchscheinende konvexe Hülle über ihren Mitgliedern gezeichnet; verschachtelte
Blüten stapeln sich und werden dunkler. Nur die Blüten, die im gezeigten Schritt gerade kontrahiert sind (nach jeder Verbesserung wird der Wald neu aufgebaut).
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import bl_constants as C
from bl_blossom import EVEN, ODD, state_at


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.08), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _hull(points):
    """Konvexe Hülle (Andrew, ganzzahlig) der Punkte, gegen den Uhrzeigersinn; weniger als drei Ecken bei Doppelpunkten oder einer Geraden."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _segments(sc, pairs):
    x, y = [], []
    for i, j in pairs:
        x += [sc.pts[i][0], sc.pts[j][0], None]
        y += [sc.pts[i][1], sc.pts[j][1], None]
    return x, y


def _map_layout(fig, sc, height):
    xs, ys = [p[0] for p in sc.pts], [p[1] for p in sc.pts]
    pad = 10
    fig.update_xaxes(visible=False, range=[min(xs) - pad, max(xs) + pad], scaleanchor="y", scaleratio=1, constrain="domain")
    fig.update_yaxes(visible=False, range=[min(ys) - pad, max(ys) + pad], constrain="domain")
    fig = _base(fig, height)
    fig.update_layout(showlegend=False)
    return fig


def build_map(sc, res, k, height=460):
    """Karte nach k Ereignissen. Fahrer: grün = gerade, rot = ungerade, grau = noch nicht im Wald; blaue Linien = gewählte Paare; dünne dunkle Linien = Kanten des Waldes; violette Hüllen = kontrahierte Blüten
    (Basis mit Ring); das letzte Ereignis: grüne Linie = neu entdeckt, violett gestrichelt = die Kante, die eine Blüte schließt, orange = der Verbesserungsweg (Stücke im Inneren einer Blüte violett)."""
    snap, blossoms = state_at(res, k)
    ev = res.events[k - 1] if k else None
    fig = go.Figure()
    faint = [(i, j) for i in range(sc.n) for j in sc.adj[i] if i < j]
    fx, fy = _segments(sc, faint)
    fig.add_trace(go.Scatter(x=fx, y=fy, mode="lines", line=dict(color="rgba(150,150,150,0.22)", width=1), hoverinfo="skip"))
    for b in blossoms:                                                     # verschachtelte Hüllen stapeln sich und werden dunkler
        pts = _hull([sc.pts[v] for v in b.members])
        if len(pts) >= 3:
            fig.add_trace(go.Scatter(x=[p[0] for p in pts] + [pts[0][0]], y=[p[1] for p in pts] + [pts[0][1]], mode="lines", fill="toself", fillcolor="rgba(148,103,189,0.16)",
                                     line=dict(color="rgba(106,61,154,0.75)", width=1.5), hoverinfo="text", hovertext=f"Blüte {b.id + 1}: Fahrer " + ", ".join(str(v + 1) for v in b.members) + f" (Basis {b.base + 1})"))
        else:
            fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color="rgba(148,103,189,0.35)", width=22), hoverinfo="text",
                                     hovertext=f"Blüte {b.id + 1}: Fahrer " + ", ".join(str(v + 1) for v in b.members)))
    tree = [(v, snap.parent[v]) for v in range(sc.n) if snap.parent[v] >= 0 and snap.label[v] != 0]
    tx, ty = _segments(sc, tree)
    fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color="rgba(70,70,70,0.7)", width=1.5), hoverinfo="skip"))
    pairs = [(i, j) for i, j in enumerate(snap.match) if j > i]
    px, py = _segments(sc, pairs)
    fig.add_trace(go.Scatter(x=px, y=py, mode="lines", line=dict(color=C.COLORS["matched"], width=3.5), hoverinfo="skip"))
    if ev is not None and ev.kind == "grow":
        gx, gy = _segments(sc, [(ev.v, ev.u)])
        fig.add_trace(go.Scatter(x=gx, y=gy, mode="lines", line=dict(color=C.COLORS["even"], width=5), hoverinfo="skip"))
    if ev is not None and ev.kind == "blossom":
        bx, by = _segments(sc, [(ev.v, ev.u)])
        fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=C.COLORS["inner"], width=5, dash="dash"), hoverinfo="skip"))
    if ev is not None and ev.kind == "augment":
        inner, outer = [], []
        member_sets = [set(b.members) for b in blossoms]
        for a, c in zip(ev.path, ev.path[1:]):
            (inner if any(a in m and c in m for m in member_sets) else outer).append((a, c))
        for links, color in ((outer, C.COLORS["path"]), (inner, C.COLORS["inner"])):
            if links:
                ax, ay = _segments(sc, links)
                fig.add_trace(go.Scatter(x=ax, y=ay, mode="lines", line=dict(color=color, width=6), hoverinfo="skip"))
    small = sc.n <= 24
    colors = [C.COLORS["even"] if snap.label[v] == EVEN else (C.COLORS["odd"] if snap.label[v] == ODD else C.COLORS["none"]) for v in range(sc.n)]
    fig.add_trace(go.Scatter(x=[p[0] for p in sc.pts], y=[p[1] for p in sc.pts], mode="markers+text" if small else "markers", text=[str(v + 1) for v in range(sc.n)] if small else None,
                             textposition="top center", hovertext=[f"Fahrer {v + 1}" for v in range(sc.n)], hoverinfo="text",
                             marker=dict(symbol="circle", size=13, color=colors, line=dict(width=1.5, color="#222"))))
    bases = [b.base for b in blossoms]
    if bases:
        fig.add_trace(go.Scatter(x=[sc.pts[v][0] for v in bases], y=[sc.pts[v][1] for v in bases], mode="markers", hoverinfo="skip",
                                 marker=dict(symbol="circle-open", size=24, color="rgba(106,61,154,0.95)", line=dict(width=3, color="rgba(106,61,154,0.95)"))))
    return _map_layout(fig, sc, height)


def build_progress(res, k, opt, height=240):
    """Über die Ereignisse: Zahl der Paare (Treppe) gegen das Optimum (gepunktet); senkrecht der aktuelle Schritt."""
    counts = [sum(1 for x in s.match if x >= 0) // 2 for s in res.snapshots]
    xs = list(range(len(counts)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, len(counts) - 1], y=[opt, opt], mode="lines", name="Optimum", line=dict(color=C.COLORS["odd"], dash="dot")))
    fig.add_trace(go.Scatter(x=xs, y=counts, mode="lines", name="Paare", line=dict(color=C.COLORS["even"], shape="hv")))
    fig.add_vline(x=k, line=dict(color="#333", width=2))
    fig.update_xaxes(title="Ereignis Nr.")
    fig.update_yaxes(title="Paare", rangemode="tozero")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.45))
    return fig


def build_ladder(ladder, height=300):
    """Die vier Stufen als Zahl der Karten (von n): Blüte kontrahiert / Weg durch eine Blüte / Suche ohne Kontraktion verliert Paare / ...und kann ein richtiges Ergebnis nicht beweisen."""
    n = ladder["n_valid"]
    names = ["Blüte kontrahiert", "Weg durch eine Blüte", "ohne Kontraktion: Paare verloren", "ohne Kontraktion: richtig, aber nicht beweisbar"]
    values = [ladder["blossom"], ladder["through"], ladder["lost"], ladder["nc_optimal"] - ladder["nc_proof"]]
    fig = go.Figure(go.Bar(x=names, y=values, marker_color=[C.COLORS["inner"], C.COLORS["path"], C.COLORS["odd"], C.COLORS["blossom"]], text=[f"{v} von {n}" for v in values], textposition="outside"))
    fig.update_yaxes(title=f"Karten (von {n})", range=[0, n * 1.12])
    fig.update_xaxes(tickangle=-15)
    fig = _base(fig, height)
    fig.update_layout(height=height + 60)
    return fig


def build_scale(rows, height=340):
    """Angesehene Kanten gegen die Größe n (doppelt logarithmisch): Blossom vom leeren und vom Greedy-Start, dazu die Suche ohne Kontraktion vom Greedy-Start."""
    fig = go.Figure()
    ns = [r["n"] for r in rows]
    fig.add_trace(go.Scatter(x=ns, y=[r["empty"]["scan"] for r in rows], mode="lines+markers", name="Blossom, leerer Start", line=dict(color=C.COLORS["odd"])))
    fig.add_trace(go.Scatter(x=ns, y=[r["edge"]["scan"] for r in rows], mode="lines+markers", name="Blossom, Greedy-Start", line=dict(color=C.COLORS["even"])))
    fig.add_trace(go.Scatter(x=ns, y=[r["edge"]["nc_scan"] for r in rows], mode="lines+markers", name="ohne Kontraktion, Greedy-Start", line=dict(color=C.COLORS["blossom"], dash="dot")))
    fig.update_xaxes(title="Fahrer n (mittlerer Grad etwa konstant)", type="log")
    fig.update_yaxes(title="angesehene Kanten", type="log")
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.3), height=height + 40)
    return fig


def build_reach_sweep(rows, height=340):
    """Gegen die Reichweite: Karten mit Blüte, mit Weg durch eine Blüte und mit Verlust ohne Kontraktion (von n Karten); rechts der mittlere Grad."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    rs = [r["reach"] for r in rows]
    fig.add_trace(go.Scatter(x=rs, y=[r["with_blossom"] for r in rows], mode="lines+markers", name="Blüte kontrahiert", line=dict(color=C.COLORS["inner"])), secondary_y=False)
    fig.add_trace(go.Scatter(x=rs, y=[r["with_through"] for r in rows], mode="lines+markers", name="Weg durch eine Blüte", line=dict(color=C.COLORS["path"])), secondary_y=False)
    fig.add_trace(go.Scatter(x=rs, y=[r["lost_maps"] for r in rows], mode="lines+markers", name="ohne Kontraktion: Paare verloren", line=dict(color=C.COLORS["odd"])), secondary_y=False)
    fig.add_trace(go.Scatter(x=rs, y=[r["degree"] for r in rows], mode="lines", name="mittlerer Grad", line=dict(color="#555", dash="dot")), secondary_y=True)
    fig.update_xaxes(title="Reichweite [min]")
    fig.update_yaxes(title="Karten", secondary_y=False, rangemode="tozero")
    fig.update_yaxes(title="mittlerer Grad", secondary_y=True, rangemode="tozero", showgrid=False)
    fig = _base(fig, height)
    fig.update_layout(legend=dict(orientation="h", y=-0.35), height=height + 50)
    return fig
