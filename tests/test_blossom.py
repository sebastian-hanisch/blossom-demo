"""Blossom gegen unabhängige Prüfer, networkx, Brute Force, Tutte-Berge, feste Karten, Negativkontrollen und die Baseline ohne Kontraktion."""

import itertools
import random

import networkx as nx
import numpy as np
import pytest

import bl_blossom as B
import bl_constants as C
import bl_greedy as G
import bl_oracle as O
import bl_scenario as S

STARTS = list(G.STARTS)


def graph_scenario(adj):
    """Ein Scenario aus einer reinen Adjazenz (nicht geometrisch) - für Zufallsgraphen G(n, p) und zweiseitige Graphen."""
    n = len(adj)
    return S.Scenario(tuple((i, 0) for i in range(n)), 0, np.ones((n, n), dtype=np.int64), tuple(tuple(sorted(a)) for a in adj))


def gnp(n, p, rng):
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].append(j)
                adj[j].append(i)
    return graph_scenario(adj)


def nx_size(sc):
    g = nx.Graph()
    g.add_nodes_from(range(sc.n))
    g.add_edges_from((i, j) for i in range(sc.n) for j in sc.adj[i] if i < j)
    return len(nx.max_weight_matching(g, maxcardinality=True))


def is_matching(sc, pairs):
    used = set()
    for i, j in pairs:
        if j not in sc.adj[i] or i in used or j in used:
            return False
        used |= {i, j}
    return True


# --- unabhängiger Prüfer je Verbesserung -----------------------------------------------------------------------------------------

def check_augmentations(sc, res):
    """Jede Verbesserung: einfacher Weg, alternierend, echte Kanten, beide Enden frei, danach ein gültiges Matching mit einem Paar mehr. Nur aus den Schnappschüssen, ohne Code des Algorithmus."""
    for k, e in enumerate(res.events, start=1):
        if e.kind != "augment":
            continue
        before, after = res.snapshots[k - 1].match, res.snapshots[k].match
        path = e.path
        assert len(path) % 2 == 0 and len(set(path)) == len(path)
        assert before[path[0]] < 0 and before[path[-1]] < 0
        for t in range(len(path) - 1):
            a, b = path[t], path[t + 1]
            assert b in sc.adj[a]
            assert (before[a] == b) == (t % 2 == 1)
        pb = {(i, j) for i, j in enumerate(before) if j > i}
        pa = {(i, j) for i, j in enumerate(after) if j > i}
        assert is_matching(sc, pa) and len(pa) == len(pb) + 1
    assert is_matching(sc, res.pairs)


@pytest.mark.parametrize("start", STARTS)
def test_every_augmentation_is_valid_on_geometric_maps(start):
    for sd in C.DIST_SEEDS[:40]:
        for n, reach in ((12, 25), (30, 20), (40, 20)):
            sc = S.generate(n, reach, 0, sd)
            res = B.run(sc, start)
            assert not res.error
            check_augmentations(sc, res)
            assert res.snapshots[0].match == tuple(G.start_matching(sc, start))
            assert res.snapshots[-1].match == tuple(res.match_list(sc.n))


# --- networkx und Brute Force -------------------------------------------------------------------------------------------------------

def test_size_equals_networkx_on_geometric_and_random_graphs_for_all_starts():
    runs = 0
    for sd in C.DIST_SEEDS[:40]:
        for n, reach in ((10, 30), (20, 25), (30, 20), (40, 20), (30, 40)):
            sc = S.generate(n, reach, 25 * (sd % 3), sd)
            opt = nx_size(sc)
            for start in STARTS:
                assert B.run(sc, start, record=False).count == opt
                runs += 1
    rng = random.Random(12345)
    for _ in range(300):
        n = rng.randint(2, 80)
        sc = gnp(n, rng.choice((0.02, 0.05, 0.1, 0.3)), rng)
        opt = nx_size(sc)
        for start in STARTS:
            res = B.run(sc, start, record=False)
            assert res.count == opt and not res.error
            runs += 1
    assert runs >= 1500


def test_size_equals_brute_force_up_to_14_vertices():
    rng = random.Random(7)
    for _ in range(300):
        n = rng.randint(2, 14)
        sc = gnp(n, rng.choice((0.15, 0.25, 0.4)), rng)
        for start in STARTS:
            assert B.run(sc, start, record=False).count == O.max_matching_size(sc.adj)
    for sd in range(200, 230):
        sc = S.generate(14, 25, 0, sd)
        assert B.run(sc, "edge", record=False).count == O.max_matching_size(sc.adj)


def test_greedy_starts_are_valid_maximal_matchings():
    for sd in C.DIST_SEEDS[:30]:
        sc = S.generate(30, 20, 0, sd)
        for start in STARTS:
            m = G.start_matching(sc, start)
            pairs = G.pairs_of(m)
            assert is_matching(sc, pairs)
            if start != "empty":
                assert not any(m[i] < 0 and m[j] < 0 for i in range(sc.n) for j in sc.adj[i])           # maximal: keine Kante mit zwei freien Enden


# --- Zertifikat: Tutte-Berge / Gallai-Edmonds ----------------------------------------------------------------------------------------

def independent_odd_components(adj, removed):
    """Union-Find, ohne Code des Algorithmus und des Orakels."""
    n = len(adj)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    keep = [v for v in range(n) if v not in removed]
    for v in keep:
        for u in adj[v]:
            if u not in removed:
                parent[find(v)] = find(u)
    sizes = {}
    for v in keep:
        sizes[find(v)] = sizes.get(find(v), 0) + 1
    return sum(1 for s in sizes.values() if s % 2)


def test_the_certificate_proves_maximality_by_an_independent_check():
    for sd in C.DIST_SEEDS[:60]:
        for n, reach in ((30, 20), (20, 25), (40, 20)):
            sc = S.generate(n, reach, 0, sd)
            for start in STARTS:
                res = B.run(sc, start, record=False)
                cert = B.certificate(sc, res.pairs, res.label)
                A = set(cert["A"])
                assert independent_odd_components(sc.adj, A) - len(A) == sc.n - 2 * res.count            # Tutte-Berge mit Gleichheit: bewiesen größtmöglich
                assert cert["holds"] and cert["ge_ok"] and cert["odd_after_A"] == independent_odd_components(sc.adj, A)


def test_tutte_berge_formula_by_brute_force_over_all_subsets():
    for sd in range(300, 360):
        sc = S.generate(11, 25, 0, sd)
        opt = O.max_matching_size(sc.adj)
        assert O.tutte_berge(sc.adj) == sc.n - 2 * opt
        res = B.run(sc, "edge", record=False)
        assert res.count == opt


def test_gallai_edmonds_sets_equal_the_brute_force_definition():
    """D = Ecken, die von mindestens einem größtmöglichen Matching nicht überdeckt werden (opt(G - v) = opt(G)); A = Nachbarn von D außerhalb von D."""
    checked = 0
    for sd in range(400, 470):
        for n, reach in ((12, 25), (10, 30), (14, 20)):
            sc = S.generate(n, reach, 0, sd)
            opt = O.max_matching_size(sc.adj)
            brute_d = []
            for v in range(n):
                keep = [u for u in range(n) if u != v]
                ix = {u: i for i, u in enumerate(keep)}
                sub = [[ix[w] for w in sc.adj[u] if w != v] for u in keep]
                if O.max_matching_size(sub) == opt:
                    brute_d.append(v)
            for start in ("empty", "edge"):
                res = B.run(sc, start, record=False)
                cert = B.certificate(sc, res.pairs, res.label)
                assert list(cert["D"]) == brute_d
                assert list(cert["A"]) == sorted({w for v in brute_d for w in sc.adj[v]} - set(brute_d))
                checked += 1
    assert checked >= 400


def test_weak_duality_holds_for_every_subset_and_equality_needs_the_right_set():
    """Für jede Menge S gilt odd(G - S) - |S| <= n - 2|M| (Tutte-Berge, schwache Dualität); die Gleichheit erreicht nur eine passende Menge wie A. Eine manipulierte Menge (A plus eine Ecke aus D) beweist auf 96 von 100 Karten nichts."""
    rng = random.Random(3)
    for sd in C.DIST_SEEDS[:40]:
        sc = S.generate(30, 20, 0, sd)
        res = B.run(sc, "edge", record=False)
        deficiency = sc.n - 2 * res.count
        for _ in range(60):
            sub = set(rng.sample(range(sc.n), rng.randint(0, 8)))
            assert independent_odd_components(sc.adj, sub) - len(sub) <= deficiency
    fails = total = 0
    for sd in C.DIST_SEEDS:
        sc = S.generate(30, 20, 0, sd)
        res = B.run(sc, "edge", record=False)
        cert = B.certificate(sc, res.pairs, res.label)
        if not cert["D"]:
            continue
        total += 1
        tampered = set(cert["A"]) | {cert["D"][0]}                                                     # eine Ecke aus D zusätzlich in A: der Beweis bricht
        fails += independent_odd_components(sc.adj, tampered) - len(tampered) != sc.n - 2 * res.count
    assert (total, fails) == (96, 96) or (total, fails) == (100, 96)


# --- feste Karten ---------------------------------------------------------------------------------------------------------------------

EXPECTED_EDGES = {
    "dreieck": {(0, 1), (0, 2), (1, 2), (1, 3)},
    "bluete": {(0, 1), (1, 2), (2, 3), (2, 6), (3, 4), (3, 7), (4, 5), (5, 6), (7, 8), (8, 9)},
    "verschachtelt": {(0, 1), (0, 5), (1, 2), (2, 3), (2, 4), (3, 4), (3, 6), (5, 6), (5, 7), (7, 8), (8, 9)},
    "windmuehle": {(0, k) for k in range(1, 9)} | {(1, 2), (3, 4), (5, 6), (7, 8)},
    "stern": {(0, 1), (0, 2), (0, 3)},
}


@pytest.mark.parametrize("net", list(S.NETS))
def test_fixed_maps_have_exactly_the_intended_graph(net):
    sc = S.NETS[net]()
    edges = {(i, j) for i in range(sc.n) for j in sc.adj[i] if i < j}
    assert edges == EXPECTED_EDGES[net]
    assert O.max_matching_size(sc.adj) == B.run(sc, "edge", record=False).count == nx_size(sc)


def test_fixed_maps_pinned_results():
    expect = {"dreieck": (2, 1, 1, 1, 3), "bluete": (5, 4, 1, 1, 14), "verschachtelt": (5, 4, 2, 2, 9), "windmuehle": (4, 4, 4, 4, 24), "stern": (1, 1, 0, 0, 3)}         # opt, greedy, Kontraktionen, Tiefe, angesehene Kanten
    for net, (opt, greedy, contr, depth, scans) in expect.items():
        res = B.run(S.NETS[net](), "edge")
        assert (res.count, len(res.start), res.contractions, res.max_depth, res.scanned_total) == (opt, greedy, contr, depth, scans), net


def test_the_path_through_the_flower_takes_the_long_way_round():
    """B: der Weg A B C G F E D H I J hat 9 Kanten, 4 davon im Inneren der Blüte {C,D,E,F,G}: die Richtung mit gerader Länge."""
    res = B.run(S.flower_stem(), "edge")
    aug = [e for e in res.events if e.kind == "augment"][0]
    assert len(aug.path) - 1 == 9 and aug.path in ((0, 1, 2, 6, 5, 4, 3, 7, 8, 9), (9, 8, 7, 3, 4, 5, 6, 2, 1, 0))
    assert len(aug.through) == 1 and aug.through[0][3] == 4
    blo = res.blossoms[aug.through[0][0]]
    assert blo.base == 2 and blo.members == (2, 3, 4, 5, 6) and len(blo.cycle) == 5 and blo.depth == 1


def test_nested_blossoms_and_the_windmill():
    res = B.run(S.nested_flowers(), "edge")
    aug = [e for e in res.events if e.kind == "augment"][0]
    assert len(aug.path) - 1 == 9 and res.max_depth == 2 and len(aug.through) == 2
    inner, outer = res.blossoms[0], res.blossoms[1]
    assert inner.members == (2, 3, 4) and outer.members == (0, 1, 2, 3, 4, 5, 6) and outer.children == (inner.id,) and outer.depth == 2
    wind = B.run(S.windmill(), "edge")
    assert wind.augmentations == 0 and wind.max_depth == 4 and wind.contractions == 4 and wind.scanned_total == 24
    cert = B.certificate(S.windmill(), wind.pairs, wind.label)
    assert len(cert["D"]) == 9 and cert["A"] == () and cert["odd_after_A"] == 1 and cert["deficiency"] == 1                      # der ganze Graph ist eine Blüte


def test_the_star_has_the_textbook_certificate():
    sc = S.star()
    res = B.run(sc, "edge")
    cert = B.certificate(sc, res.pairs, res.label)
    assert cert["A"] == (0,) and cert["D"] == (1, 2, 3) and cert["comps_D"] == (1, 1, 1) and cert["odd_after_A"] == 3 and cert["deficiency"] == 2 and cert["holds"]


def test_complete_graphs_need_nested_contractions_and_n_times_n_minus_one_scans():
    for n in (5, 11, 17, 23, 29, 35):
        for sd in (1, 2, 3):
            res = B.run(S.generate(n, 150, 0, sd), "edge")
            assert (res.contractions, res.max_depth, res.scanned_total, res.count) == ((n - 1) // 2, (n - 1) // 2, n * (n - 1), (n - 1) // 2)
    for n in (6, 12, 30):
        res = B.run(S.generate(n, 150, 0, 1), "edge")
        assert res.scanned_total == 0 and res.count == n // 2 and res.augmentations == 0 and res.contractions == 0


# --- Baseline ohne Kontraktion und Negativkontrollen ----------------------------------------------------------------------------------------

def test_without_contraction_the_search_misses_the_path_on_the_flower_maps():
    for net, opt in (("dreieck", 2), ("bluete", 5), ("verschachtelt", 5)):
        sc = S.NETS[net]()
        nc = B.run(sc, "edge", B.SEARCH_NOCONTRACT)
        assert (nc.count, B.run(sc, "edge").count) == (opt - 1, opt), net                           # (1, 4, 4) gegen (2, 5, 5)
        assert not nc.error and is_matching(sc, nc.pairs)


def test_only_the_nested_map_traps_the_baseline_under_every_numbering():
    """Ehrlicher Befund: die Falle hängt von der Nummerierung ab. Unter 300 zufälligen Nummerierungen (Greedy-Start) verliert die Suche ohne Kontraktion auf A 70-mal, auf B 133-mal und nur auf C
    (verschachtelte Blüten) jedes Mal; Blossom findet stets das Optimum."""
    lost = {}
    for net, opt in (("dreieck", 2), ("bluete", 5), ("verschachtelt", 5)):
        sc = S.NETS[net]()
        lost[net] = 0
        for j in range(300):
            sc2 = S.relabel(sc, S.perm(sc.n, 5000 + j))
            lost[net] += B.run(sc2, "edge", B.SEARCH_NOCONTRACT, record=False).count < opt
            assert B.run(sc2, "edge", record=False).count == opt
    assert lost == {"dreieck": 70, "bluete": 133, "verschachtelt": 300}


def test_the_baseline_is_sound_and_optimal_on_bipartite_graphs():
    rng = random.Random(99)
    for _ in range(400):
        a, b = rng.randint(1, 12), rng.randint(1, 12)
        adj = [[] for _ in range(a + b)]
        for i in range(a):
            for j in range(b):
                if rng.random() < 0.25:
                    adj[i].append(a + j)
                    adj[a + j].append(i)
        sc = graph_scenario(adj)
        g = nx.Graph()
        g.add_nodes_from(range(a + b))
        g.add_edges_from((i, w) for i in range(a) for w in adj[i])
        opt = len(nx.bipartite.maximum_matching(g, top_nodes=range(a))) // 2 if g.number_of_edges() else 0
        for start in STARTS:
            nc = B.run(sc, start, B.SEARCH_NOCONTRACT, record=False)
            assert nc.count == opt == B.run(sc, start, record=False).count and is_matching(sc, nc.pairs)
            assert nc.contractions == 0


def test_the_baseline_is_always_valid_on_general_graphs_and_sometimes_too_small():
    rng = random.Random(4)
    short = total = 0
    for _ in range(400):
        sc = gnp(rng.randint(4, 40), rng.choice((0.08, 0.15)), rng)
        opt = nx_size(sc)
        nc = B.run(sc, "edge", B.SEARCH_NOCONTRACT, record=False)
        assert is_matching(sc, nc.pairs) and not nc.error
        short += nc.count < opt
        total += 1
    assert 0 < short < total // 4


def test_negative_control_without_lifting_gives_invalid_paths():
    """Ohne das Umsetzen der Vorgänger bei der Kontraktion läuft der Weg falsch um die Blüte (oder gar nicht): auf 52 von 100 Karten (n = 30, Reichweite 20, Greedy-Start) ungültig, mit Aufklappen auf keiner."""
    bad = sum(1 for sd in C.DIST_SEEDS if B.run(S.generate(30, 20, 0, sd), "edge", record=False, lift=False).error)
    good = sum(1 for sd in C.DIST_SEEDS if B.run(S.generate(30, 20, 0, sd), "edge", record=False, lift=True).error)
    assert (bad, good) == (52, 0)
    res = B.run(S.flower_stem(), "edge", lift=False)
    assert res.error == "invalid_path" or res.count < 5


def test_the_literal_bipartite_bfs_is_no_baseline_it_does_not_even_give_simple_paths():
    """Die Breitensuche der Zweiseiten-Demo, wörtlich auf die symmetrische Adjazenz angewandt: von 100 Karten liefert sie auf 98 (n = 30, Reichweite 20, Greedy-Start) einen Weg mit doppelter Ecke."""
    from collections import deque

    def literal(sc, start):
        n, adj = sc.n, sc.adj
        match = G.start_matching(sc, start)
        for _ in range(400):
            parent, seen, found = {}, set(), None
            queue = deque(i for i in range(n) if match[i] < 0)
            while queue and found is None:
                i = queue.popleft()
                for j in adj[i]:
                    if j in seen:
                        continue
                    seen.add(j)
                    parent[j] = i
                    if match[j] < 0:
                        cv, co, cur, guard = [], [], j, 0
                        while True:
                            v = parent[cur]
                            cv.append(v)
                            co.append(cur)
                            if match[v] < 0:
                                break
                            cur = match[v]
                            guard += 1
                            if guard > 4 * n:
                                return "loop"
                        found = (cv[::-1], co[::-1])
                        break
                    queue.append(match[j])
            if found is None:
                return "done"
            cv, co = found
            walk = [x for a, b in zip(cv, co) for x in (a, b)]
            if len(set(walk)) != len(walk):
                return "nonsimple"
            for a, b in zip(cv, co):
                match[a], match[b] = b, a
        return "cap"
    outcomes = [literal(S.generate(30, 20, 0, sd), "edge") for sd in C.DIST_SEEDS]
    assert outcomes.count("nonsimple") == 98 and outcomes.count("done") == 2


# --- Ablauf, Wiedergabe, Aufwand ------------------------------------------------------------------------------------------------------

def test_replay_is_deterministic_and_events_are_consistent():
    sc = S.generate(30, 20, 0, 100003)
    a, b = B.run(sc, "edge"), B.run(sc, "edge")
    assert a == b
    assert a.snapshots[0].blossoms == () and len(a.snapshots) == len(a.events) + 1
    assert a.events[0].kind == "round" and a.events[-1].kind == "fail"
    scans = [e.scanned for e in a.events]
    assert scans == sorted(scans) and scans[-1] == a.scanned_total
    seen_blossoms = 0
    for k, e in enumerate(a.events, start=1):
        snap, blossoms = B.state_at(a, k)
        assert len(snap.match) == sc.n and all(len(b.cycle) % 2 == 1 for b in blossoms)
        if e.kind == "blossom":
            blo = a.blossoms[e.blossom]
            assert blo.id == seen_blossoms and e.blossom in snap.blossoms and blo.round == e.round
            assert set(blo.members) >= set(blo.cycle) and all(a.blossoms[c].depth < blo.depth for c in blo.children)
            seen_blossoms += 1
        if e.kind == "grow":
            assert snap.label[e.u] == B.ODD and snap.label[e.w] == B.EVEN and snap.parent[e.u] == e.v
    assert sum(len(r.path) > 0 for r in a.rounds) == a.augmentations and a.rounds[-1].path == ()
    assert sum(r.scanned for r in a.rounds) == a.scanned_total and sum(r.contractions for r in a.rounds) == a.contractions == seen_blossoms


def test_blossoms_are_reset_after_every_augmentation():
    sc = S.generate(30, 20, 0, 100005)
    res = B.run(sc, "empty")
    for k, e in enumerate(res.events, start=1):
        if e.kind == "round":
            assert res.snapshots[k].blossoms == ()
        if e.kind == "blossom":
            assert all(res.blossoms[i].round == e.round for i in res.snapshots[k].blossoms)


def test_recording_does_not_change_the_result_or_the_counters():
    for sd in C.DIST_SEEDS[:20]:
        sc = S.generate(30, 20, 0, sd)
        for start in STARTS:
            a, b = B.run(sc, start, record=True), B.run(sc, start, record=False)
            assert (a.pairs, a.scanned_total, a.contractions, a.contracted_vertices, a.augmentations, a.max_depth, a.through_paths) == (b.pairs, b.scanned_total, b.contractions, b.contracted_vertices, b.augmentations, b.max_depth, b.through_paths)


def test_isolated_and_tiny_maps():
    sc = graph_scenario([[], [], []])
    res = B.run(sc, "edge")
    assert res.count == 0 and res.scanned_total == 0 and res.events[-1].kind == "fail"
    sc = graph_scenario([[1], [0]])
    assert B.run(sc, "empty").count == 1 and B.run(sc, "edge").count == 1
    sc = graph_scenario([[1, 2], [0, 2], [0, 1]])
    res = B.run(sc, "edge")
    assert res.count == 1 and res.augmentations == 0 and res.contractions == 1                                    # ein Dreieck allein: Greedy nimmt eine Kante, die dritte Ecke bleibt übrig; die Suche findet das Dreieck (eine Blüte), aber keinen Weg
