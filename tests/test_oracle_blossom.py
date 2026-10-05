"""Orakel-Test: Suche ohne Kontraktion und Blüten-Struktur gegen eine unabhängige Zweitumsetzung bzw. networkx.

Die Zahlen "Karten mit Verlust ohne Kontraktion" und "beweisbar ohne Kontraktion" der README hängen an der Baseline; hier wird sie in einer eigenen,
kurzen Fassung (Dictionaries, keine Basis-/Blütenfelder) nachgebaut und mit Paaren, Beschriftung und Beweis verglichen. Jede kontrahierte Blüte muss
faktor-kritisch sein (ohne irgendeine ihrer Ecken gibt es ein perfektes Matching der übrigen), die Zahl der Ecken in Blüten und der Wege durch Blüten
wird aus den Schnappschüssen neu gezählt.
"""

import math
import random

import numpy as np
import pytest

import bl_blossom as B
import bl_greedy as G
import bl_scenario as S

nx = pytest.importorskip("networkx")


def _scenario(adj):
    n = len(adj)
    return S.Scenario(tuple((i, 0) for i in range(n)), 0, np.ones((n, n), dtype=np.int64), tuple(tuple(sorted(a)) for a in adj))


def _gnp(n, p, rng):
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].append(j)
                adj[j].append(i)
    return _scenario(adj)


def _graph(sc):
    g = nx.Graph()
    g.add_nodes_from(range(sc.n))
    g.add_edges_from((i, j) for i in range(sc.n) for j in sc.adj[i] if i < j)
    return g


def _opt(g):
    return len(nx.max_weight_matching(g, maxcardinality=True))


def _odd_components(g, removed):
    h = g.copy()
    h.remove_nodes_from(removed)
    return sum(1 for c in nx.connected_components(h) if len(c) % 2)


def _nocontract(sc, match):
    """Waldsuche aus allen freien Ecken ohne Kontraktion, eine Verbesserung je Runde (FIFO, Indexreihenfolge). Rückgabe (match, Beschriftung)."""
    match = list(match)
    while True:
        lab, par, root, queue = {}, {}, {}, []
        for v in range(sc.n):
            if match[v] < 0:
                lab[v], root[v] = "E", v
                queue.append(v)
        found, qi = None, 0
        while qi < len(queue) and found is None:
            v = queue[qi]
            qi += 1
            for u in sc.adj[v]:
                if match[v] == u:
                    continue
                if lab.get(u) == "E":
                    if root[u] != root[v]:
                        found = (v, u)
                        break
                elif u not in lab:
                    lab[u], par[u], root[u] = "O", v, root[v]
                    w = match[u]
                    lab[w], root[w] = "E", root[v]
                    queue.append(w)
        if found is None:
            return match, lab

        def up(x):
            seq = [x]
            while match[x] >= 0:
                y = match[x]
                x = par[y]
                seq += [y, x]
            return seq
        path = up(found[0])[::-1] + up(found[1])
        for k in range(0, len(path) - 1, 2):
            match[path[k]], match[path[k + 1]] = path[k + 1], path[k]


def test_search_without_contraction_equals_an_independent_reimplementation():
    rng = random.Random(11)
    for t in range(60):
        sc = _gnp(rng.randint(2, 24), rng.choice((0.08, 0.15, 0.3)), rng) if t % 2 else S.generate(rng.choice((8, 16, 30)), rng.choice((15, 20, 30)), 25 * (t % 3), 1000 + t)
        g = _graph(sc)
        for start in G.STARTS:
            nc = B.run(sc, start, B.SEARCH_NOCONTRACT, record=False)
            match, lab = _nocontract(sc, G.start_matching(sc, start))
            assert nc.pairs == B.pairs_of(match)
            cert = B.certificate(sc, nc.pairs, nc.label)
            assert list(cert["A"]) == [v for v in range(sc.n) if lab.get(v) == "O"]
            assert list(cert["D"]) == [v for v in range(sc.n) if lab.get(v) == "E"]
            assert cert["holds"] == (_odd_components(g, cert["A"]) - len(cert["A"]) == sc.n - 2 * nc.count)


def test_every_contracted_blossom_is_factor_critical_and_counters_match_the_snapshots():
    rng = random.Random(5)
    seen = 0
    for t in range(40):
        sc = _gnp(rng.randint(3, 20), rng.choice((0.15, 0.3, 0.5)), rng) if t % 2 else S.generate(rng.choice((10, 20)), rng.choice((20, 30)), 0, 2000 + t)
        g = _graph(sc)
        res = B.run(sc, "edge")
        assert res.count == _opt(g)
        assert res.contracted_vertices == sum(len(b.members) for b in res.blossoms)
        for b in res.blossoms:
            sub = g.subgraph(b.members)
            assert len(b.members) % 2 == 1 and b.base in b.members and nx.is_connected(sub)
            for v in b.members:
                rest = sub.copy()
                rest.remove_node(v)
                assert 2 * _opt(rest) == len(b.members) - 1
            seen += 1
        through = 0
        for k, e in enumerate(res.events, start=1):
            if e.kind != "augment":
                continue
            active = [res.blossoms[i] for i in res.snapshots[k - 1].blossoms]
            through += any(a in b.members and c in b.members for b in active for a, c in zip(e.path, e.path[1:]))
        assert through == res.through_paths
    assert seen >= 20


def test_travel_cost_is_the_rounded_up_euclidean_distance():
    for dx in range(-12, 13):
        for dy in range(-12, 13):
            c, d2 = S.travel_cost(dx, dy)
            assert d2 == dx * dx + dy * dy and c == math.ceil(math.sqrt(d2))
