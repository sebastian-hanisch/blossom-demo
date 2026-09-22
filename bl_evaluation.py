"""Auswertung: eine Karte (`analyse`, `verdict`, `compare_table`), viele Karten (`distribution`, die Vier-Stufen-Leiter), Nummerierungs- und Suchvarianten-Experiment, Reichweiten-Sweep, Aufwand gegen
Größe, der vollständige Graph und der Brute-Force-Beweis. Alles ganzzahlig und deterministisch; nur die Anzeige-Statistiken (Anteile, Mittel, Mediane) sind Gleitkomma.

Die Baseline ("ohne Kontraktion") ist Edmonds' Waldsuche mit dem Kontraktionsschritt weggelassen - nicht die wörtliche Breitensuche der Vorgänger, die auf einem allgemeinen Graphen nicht einmal
gültige Wege liefert. Sie ist stets gültig, auf zweiseitigen Graphen optimal und auf allgemeinen manchmal zu klein. Der Vergleich ist eine Leiter mit vier Stufen: (1) es gibt eine Blüte, (2) der Weg läuft
durch eine, (3) die Suche ohne Kontraktion verliert Paare, (4) sie kann auch ein richtiges Ergebnis nicht beweisen.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import bl_constants as C
import bl_oracle as O
from bl_blossom import SEARCH_EDMONDS, SEARCH_NOCONTRACT, certificate, run, run_single_root
from bl_greedy import START_EDGE, START_EMPTY, START_ORDER, STARTS, greedy_edge, greedy_order
from bl_scenario import build, generate, perm, relabel

OPTIMAL, SHORT, NONE = "optimal", "short", "none"


@dataclass
class Analysis:
    scenario: object
    start: str
    search: str
    seed: int
    result: object        # gewählte Suche
    edmonds: object       # Blossom
    nocontract: object    # Baseline
    greedy_edge: int
    greedy_order: int
    cert: dict            # Beweis der gewählten Suche
    cert_nc: dict         # Beweis, der sich aus der Suche ohne Kontraktion herleiten ließe


def analyse(sc, start=C.DEFAULT_START, search=C.DEFAULT_SEARCH, seed=0):
    ed = run(sc, start, SEARCH_EDMONDS)
    nc = run(sc, start, SEARCH_NOCONTRACT)
    chosen = ed if search == SEARCH_EDMONDS else nc
    return Analysis(sc, start, search, seed, chosen, ed, nc, sum(1 for x in greedy_edge(sc) if x >= 0) // 2, sum(1 for x in greedy_order(sc) if x >= 0) // 2,
                    certificate(sc, ed.pairs, ed.label), certificate(sc, nc.pairs, nc.label))


def path_lengths(res):
    """Kanten der gefundenen Verbesserungswege."""
    return [len(r.path) - 1 for r in res.rounds if r.path]


def verdict(a):
    """(Stufe, Code, Zahlen) für die Anzeige; `Zahlen` enthält jede Zahl, die der Text nennt."""
    sc, r, ed, nc = a.scenario, a.result, a.edmonds, a.nocontract
    opt = ed.count
    code = NONE if sc.m == 0 else (OPTIMAL if r.count == opt else SHORT)
    cert = a.cert if a.search == SEARCH_EDMONDS else a.cert_nc
    lengths = path_lengths(r)
    data = {"n": sc.n, "edges": sc.m, "count": r.count, "opt": opt, "lost": opt - r.count, "greedy": len(r.start), "greedy_edge": a.greedy_edge, "greedy_order": a.greedy_order,
            "augmentations": r.augmentations, "contractions": r.contractions, "depth": r.max_depth, "scanned": r.scanned_total, "contracted_vertices": r.contracted_vertices,
            "events": r.n_events, "through": r.through_paths, "path_lengths": lengths, "error": r.error, "isolated": sum(1 for d in sc.degrees() if d == 0),
            "nc_count": nc.count, "nc_lost": opt - nc.count, "nc_scanned": nc.scanned_total, "cert": cert, "cert_holds": cert["holds"], "cert_ge": cert["ge_ok"],
            "cert_nc_holds": a.cert_nc["holds"], "opt_scanned": ed.scanned_total}
    level = {NONE: "info", OPTIMAL: "success", SHORT: "warning"}[code]
    return level, code, data


def compare_table(a):
    sc = a.scenario
    rows = [{"label": "Greedy: billigste Kante zuerst", "count": a.greedy_edge, "augmentations": None, "scanned": None, "contractions": None, "proof": None},
            {"label": "Greedy: Fahrer für Fahrer", "count": a.greedy_order, "augmentations": None, "scanned": None, "contractions": None, "proof": None}]
    for label, res, cert in (("Blossom (mit Kontraktion)", a.edmonds, a.cert), ("Ohne Kontraktion", a.nocontract, a.cert_nc)):
        rows.append({"label": label, "count": res.count, "augmentations": res.augmentations, "scanned": res.scanned_total, "contractions": res.contractions, "proof": cert["holds"]})
    return rows


# --- viele Karten --------------------------------------------------------------------------------------------------------------

def _row(sc):
    rec = {"n": sc.n, "edges": sc.m, "degree": sum(sc.degrees()) / sc.n, "isolated": sum(1 for d in sc.degrees() if d == 0),
           "greedy_edge": sum(1 for x in greedy_edge(sc) if x >= 0) // 2, "greedy_order": sum(1 for x in greedy_order(sc) if x >= 0) // 2}
    for start in STARTS:
        ed = run(sc, start, SEARCH_EDMONDS, record=False)
        nc = run(sc, start, SEARCH_NOCONTRACT, record=False)
        cert = certificate(sc, ed.pairs, ed.label)
        cert_nc = certificate(sc, nc.pairs, nc.label)
        rec[start] = {"count": ed.count, "scanned": ed.scanned_total, "contractions": ed.contractions, "contracted_vertices": ed.contracted_vertices, "augmentations": ed.augmentations,
                      "depth": ed.max_depth, "through": ed.through_paths, "lengths": tuple(len(r.path) - 1 for r in ed.rounds if r.path),
                      "nc_count": nc.count, "nc_scanned": nc.scanned_total, "nc_holds": cert_nc["holds"], "holds": cert["holds"],
                      "D": len(cert["D"]), "A": len(cert["A"]), "C": len(cert["C"]), "comps_D": len(cert["comps_D"]), "n_rounds": len(ed.rounds)}
    return rec


@lru_cache(maxsize=64)
def cell_rows(n, reach, ballung, seeds):
    return tuple(_row(generate(n, reach, ballung, sd)) for sd in seeds)


def _mean(v):
    return float(np.mean(v)) if len(v) else None


def _med(v):
    return float(np.median(v)) if len(v) else None


def _stat(values):
    return {"mean": _mean(values), "median": _med(values), "min": min(values) if len(values) else None, "max": max(values) if len(values) else None}


def distribution(n, reach, ballung, start=C.DEFAULT_START, seeds=C.DIST_SEEDS):
    """Verteilung über viele Karten für einen Start: Optimum, Greedy, Aufwand, die Vier-Stufen-Leiter und der Beweis (Mittel, Median, Maximum)."""
    rows = cell_rows(n, reach, ballung, tuple(seeds))
    rows = [r for r in rows if r["edges"] > 0]
    if not rows:
        return {"n_seeds": len(seeds), "n_valid": 0}
    s = [r[start] for r in rows]
    lost = [x["count"] - x["nc_count"] for x in s]
    lengths = [k for x in s for k in x["lengths"]]
    d = {"n_seeds": len(seeds), "n_valid": len(rows), "opt": _stat([x["count"] for x in s]), "greedy_edge": _stat([r["greedy_edge"] for r in rows]), "greedy_order": _stat([r["greedy_order"] for r in rows]),
         "greedy_not_opt": sum(1 for r, x in zip(rows, s) if r["greedy_edge"] < x["count"]), "greedy_order_not_opt": sum(1 for r, x in zip(rows, s) if r["greedy_order"] < x["count"]),
         "perfect": sum(1 for r, x in zip(rows, s) if 2 * x["count"] == r["n"]), "isolated": _stat([r["isolated"] for r in rows]), "degree": _mean([r["degree"] for r in rows]),
         "augmentations": _stat([x["augmentations"] for x in s]), "path_len": _stat(lengths) if lengths else {"mean": None, "median": None, "min": None, "max": None}, "n_paths": len(lengths),
         "contractions": _stat([x["contractions"] for x in s]), "contracted_vertices": _stat([x["contracted_vertices"] for x in s]), "depth": _stat([x["depth"] for x in s]),
         "scanned": _stat([x["scanned"] for x in s]), "nc_scanned": _stat([x["nc_scanned"] for x in s]), "rounds": _stat([x["n_rounds"] for x in s]),
         "with_blossom": sum(1 for x in s if x["contractions"] > 0), "with_through": sum(1 for x in s if x["through"] > 0),
         "lost_maps": sum(1 for v in lost if v > 0), "lost_mean": _mean(lost), "lost_max": max(lost), "lost_share": (sum(lost) / sum(x["count"] for x in s)),
         "nc_optimal": sum(1 for v in lost if v == 0), "nc_proof_of_optimal": sum(1 for x, v in zip(s, lost) if v == 0 and x["nc_holds"]),
         "proof": sum(1 for x in s if x["holds"]), "D": _stat([x["D"] for x in s]), "A": _stat([x["A"] for x in s]), "C": _stat([x["C"] for x in s]), "comps_D": _stat([x["comps_D"] for x in s]),
         "A_empty": sum(1 for x in s if x["A"] == 0)}
    return d


def ladder(n, reach, ballung, start=C.DEFAULT_START, seeds=C.DIST_SEEDS):
    """Die vier Stufen als Zahl der Karten: Blüte kontrahiert / Weg durch eine Blüte / Suche ohne Kontraktion verliert Paare / ...und kann bei richtigem Ergebnis nicht beweisen."""
    d = distribution(n, reach, ballung, start, seeds)
    if d["n_valid"] == 0:
        return d
    return {"n_valid": d["n_valid"], "blossom": d["with_blossom"], "through": d["with_through"], "lost": d["lost_maps"], "nc_optimal": d["nc_optimal"], "nc_proof": d["nc_proof_of_optimal"]}


def start_comparison(n, reach, ballung, seeds=C.DIST_SEEDS):
    """Alle drei Starts: Runden, Verbesserungen, angesehene Kanten, Verlust ohne Kontraktion (Mittel)."""
    out = []
    for start in STARTS:
        d = distribution(n, reach, ballung, start, seeds)
        out.append({"start": start, "augmentations": d["augmentations"]["mean"], "scanned": d["scanned"]["mean"], "nc_scanned": d["nc_scanned"]["mean"], "contractions": d["contractions"]["mean"],
                    "lost_maps": d["lost_maps"], "lost_mean": d["lost_mean"], "events": None})
    return out


def numbering_experiment(n, reach, ballung, start=C.DEFAULT_START, seeds=C.DIST_SEEDS, k=C.NUMBERINGS):
    """Dieselben Karten unter k zufälligen Nummerierungen: der Graph ist derselbe, nur die Reihenfolge der Suche ist anders. Wie viele Karten verlieren Paare unter mindestens einer / allen Nummerierungen,
    und welcher Anteil aller (Karte, Nummerierung)-Paare verliert."""
    any_lost = all_lost = total = lost_total = 0
    for sd in seeds:
        sc = generate(n, reach, ballung, sd)
        if sc.m == 0:
            continue
        opt = run(sc, start, SEARCH_EDMONDS, record=False).count
        losses = []
        for j in range(k):
            sc2 = relabel(sc, perm(sc.n, sd * 1009 + j * 31 + 7))
            losses.append(run(sc2, start, SEARCH_NOCONTRACT, record=False).count < opt)
        total += k
        lost_total += sum(losses)
        any_lost += any(losses)
        all_lost += all(losses)
    return {"maps": len([1 for sd in seeds if generate(n, reach, ballung, sd).m > 0]), "any": any_lost, "all": all_lost, "share": lost_total / total if total else None, "k": k}


def single_root_comparison(n, reach, ballung, start=C.DEFAULT_START, seeds=C.DIST_SEEDS):
    """Suchvarianten ohne Kontraktion: alle freien Fahrer als Wurzeln zugleich (wie die Vorgänger-BFS) gegen eine Wurzel nach der anderen (Kuhn): Karten mit Verlust."""
    multi = single = 0
    for sd in seeds:
        sc = generate(n, reach, ballung, sd)
        if sc.m == 0:
            continue
        opt = run(sc, start, SEARCH_EDMONDS, record=False).count
        multi += run(sc, start, SEARCH_NOCONTRACT, record=False).count < opt
        single += len(run_single_root(sc, start, contract=False)[0]) < opt
    return {"multi": multi, "single": single}


def reach_sweep(n, ballung=0, seeds=C.SWEEP_SEEDS, reaches=C.REACH_SWEEP, start=C.DEFAULT_START):
    """Gegen die Reichweite: mittlerer Grad, Optimum, Karten mit Blüte / Weg durch Blüte / Verlust ohne Kontraktion, mittlerer Verlust, Kontraktionen."""
    out = []
    for r in reaches:
        d = distribution(n, r, ballung, start, seeds)
        if d["n_valid"] == 0:
            continue
        out.append({"reach": r, "degree": d["degree"], "opt": d["opt"]["mean"], "with_blossom": d["with_blossom"], "with_through": d["with_through"], "lost_maps": d["lost_maps"], "lost_mean": d["lost_mean"],
                    "contractions": d["contractions"]["mean"], "n_valid": d["n_valid"]})
    return out


@lru_cache(maxsize=8)
def scale_table(ns=C.SCALE_NS, seeds=C.SCALE_SEEDS):
    """Angesehene Kanten, Verbesserungen und Kontraktionen gegen die Größe (Reichweite so, dass der mittlere Grad etwa gleich bleibt), leerer und Greedy-Start; dazu der Verlust ohne Kontraktion."""
    out = []
    for n in ns:
        reach = max(3, math.isqrt(C.SCALE_DEGREE_AREA // n))
        acc = {s: {"aug": [], "scan": [], "contr": [], "nc_scan": [], "lost": []} for s in (START_EMPTY, START_EDGE)}
        edges, deg = [], []
        for sd in seeds:
            sc = generate(n, reach, 0, sd)
            edges.append(sc.m)
            deg.append(sum(sc.degrees()) / n)
            for s in (START_EMPTY, START_EDGE):
                ed = run(sc, s, SEARCH_EDMONDS, record=False)
                nc = run(sc, s, SEARCH_NOCONTRACT, record=False)
                acc[s]["aug"].append(ed.augmentations)
                acc[s]["scan"].append(ed.scanned_total)
                acc[s]["contr"].append(ed.contractions)
                acc[s]["nc_scan"].append(nc.scanned_total)
                acc[s]["lost"].append(ed.count - nc.count)
        row = {"n": n, "reach": reach, "edges": _mean(edges), "degree": _mean(deg)}
        for s in acc:
            row[s] = {"aug": _mean(acc[s]["aug"]), "scan": _mean(acc[s]["scan"]), "contr": _mean(acc[s]["contr"]), "nc_scan": _mean(acc[s]["nc_scan"]),
                      "lost_maps": sum(1 for v in acc[s]["lost"] if v > 0), "lost_mean": _mean(acc[s]["lost"]), "scan_per_edge": _mean(acc[s]["scan"]) / max(_mean(edges), 1)}
        out.append(row)
    return tuple(out)


def complete_graph_table(ns=C.COMPLETE_NS, seeds=C.SWEEP_SEEDS):
    """Vollständiger Graph (jeder erreicht jeden), ungerade n: Greedy ist schon optimal, aber der Beweis braucht (n-1)/2 verschachtelte Kontraktionen und n (n-1) angesehene Kanten - auf jeder Karte.
    Gerade n: perfektes Matching schon durch Greedy, keine einzige angesehene Kante."""
    out = []
    for n in ns:
        rows = []
        for sd in seeds:
            sc = generate(n, 150, 0, sd)
            ed = run(sc, START_EDGE, SEARCH_EDMONDS, record=False)
            nc = run(sc, START_EDGE, SEARCH_NOCONTRACT, record=False)
            cert_nc = certificate(sc, nc.pairs, nc.label)
            rows.append((ed.contractions, ed.max_depth, ed.scanned_total, ed.count, cert_nc["holds"]))
        out.append({"n": n, "contractions": sorted({r[0] for r in rows}), "depth": sorted({r[1] for r in rows}), "scanned": sorted({r[2] for r in rows}), "count": sorted({r[3] for r in rows}),
                    "nc_proof": sum(1 for r in rows if r[4]), "maps": len(rows)})
    return out


def brute_proof(sc):
    """Brute-Force-Beweis auf einer kleinen Karte (n <= 14): Optimum per Bitmasken-Dynamik, Tutte-Berge-Maximum über alle Teilmengen, Blossom daneben."""
    if sc.n > C.BRUTE_MAX_N:
        raise ValueError(sc.n)
    opt = O.max_matching_size(sc.adj)
    tb = O.tutte_berge(sc.adj)
    ed = run(sc, START_EDGE, SEARCH_EDMONDS, record=False)
    return {"n": sc.n, "opt": opt, "tutte_berge": tb, "deficiency": sc.n - 2 * opt, "blossom": ed.count, "agree": tb == sc.n - 2 * opt and ed.count == opt}


def scenario_from_settings(net, n, reach, ballung, seed):
    return build(net, n, reach, ballung, seed)
