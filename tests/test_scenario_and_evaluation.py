"""Karten, Zufallsströme, Wächter der kopierten Bausteine und die Plumbing der Auswertung (Verdict, Tabellen, Verteilungen, Sweeps, Experimente)."""

import pytest

import bl_blossom as B
import bl_constants as C
import bl_evaluation as ev
import bl_greedy as G
import bl_scenario as S


def test_splitmix_vector_and_a_pinned_point_list():
    rng = S.SplitMix64(0)
    assert [rng.next() for _ in range(2)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4]
    sc = S.generate(30, 20, 0, 100000)
    assert sc.pts[:3] == ((8, 69), (86, 39), (66, 62)) and sc.m == 46 and sc.degrees()[:8] == (1, 7, 3, 5, 5, 2, 4, 2)          # Wächter: der Einpunkt-Generator rechnet auf jeder Plattform gleich
    assert S.generate(6, 50, 0, 1).pts == ((17, 80), (38, 86), (61, 20), (82, 44), (9, 0), (100, 31))


def test_travel_cost_rounds_up_and_reach_is_a_closed_bound():
    assert S.travel_cost(3, 4) == (5, 25) and S.travel_cost(1, 1) == (2, 2) and S.travel_cost(0, 0) == (0, 0)
    sc = S.from_points([(0, 0), (10, 0), (0, 11)], 10)
    assert sc.adj == ((1,), (0,), ()) and sc.m == 1                                                # Entfernung genau gleich der Reichweite zählt


def test_graph_is_symmetric_and_edges_are_sorted_by_cost_then_index():
    sc = S.generate(30, 25, 0, 7)
    for i in range(sc.n):
        assert list(sc.adj[i]) == sorted(sc.adj[i]) and i not in sc.adj[i]
        assert all(i in sc.adj[j] for j in sc.adj[i])
    edges = sc.edges()
    assert len(edges) == sc.m and edges == sorted(edges) and all(i < j for _c, i, j in edges)


def test_relabel_keeps_the_graph_but_not_the_numbering():
    sc = S.generate(30, 20, 0, 100003)
    p = S.perm(sc.n, 5)
    sc2 = S.relabel(sc, p)
    assert sorted(sc.degrees()) == sorted(sc2.degrees()) and sc.m == sc2.m
    assert sc2.pts == tuple(sc.pts[k] for k in p) and sorted(p) == list(range(sc.n)) and p == S.perm(sc.n, 5) != S.perm(sc.n, 6)
    assert B.run(sc, "edge", record=False).count == B.run(sc2, "edge", record=False).count


def test_build_fixed_nets_ignore_random_parameters():
    a, b = S.build("windmuehle", 5, 99, 100, 123), S.build("windmuehle", 40, 10, 0, 1)
    assert a.pts == b.pts and a.n == 9
    assert S.build("random", 7, 40, 0, 3).n == 7 and set(S.NETS) == set(C.FIXED_NETS)


def test_greedy_rules_on_the_smallest_flower():
    sc = S.triangle_pendant()
    assert G.pairs_of(G.greedy_edge(sc)) == ((1, 2),)                                           # billigste Kante B-C: das Anhängsel und A bleiben frei
    assert G.pairs_of(G.greedy_order(sc)) == ((0, 1),)
    assert G.start_matching(sc, "empty") == [-1] * 4
    with pytest.raises(ValueError):
        G.start_matching(sc, "no-such-start")


def test_verdict_of_the_fixed_maps():
    for net, opt in (("dreieck", 2), ("bluete", 5), ("verschachtelt", 5), ("windmuehle", 4), ("stern", 1)):
        level, code, d = ev.verdict(ev.analyse(S.NETS[net](), "edge", "edmonds"))
        assert (level, code) == ("success", ev.OPTIMAL) and d["count"] == d["opt"] == opt and d["cert_holds"] and d["cert_ge"] and d["error"] == ""
    level, code, d = ev.verdict(ev.analyse(S.triangle_pendant(), "edge", "nocontract"))
    assert (level, code) == ("warning", ev.SHORT) and (d["count"], d["opt"], d["lost"]) == (1, 2, 1) and not d["cert_holds"]


def test_verdict_none_without_any_feasible_edge():
    sc = S.from_points([(0, 0), (90, 90), (0, 90)], 10)
    level, code, d = ev.verdict(ev.analyse(sc, "edge", "edmonds"))
    assert (level, code) == ("info", ev.NONE) and d["count"] == 0 and d["isolated"] == 3


def test_compare_table_rows():
    a = ev.analyse(S.generate(30, 20, 0, 165), "edge", "edmonds", 165)
    rows = ev.compare_table(a)
    assert [r["label"] for r in rows] == ["Greedy: billigste Kante zuerst", "Greedy: Fahrer für Fahrer", "Blossom (mit Kontraktion)", "Ohne Kontraktion"]
    assert rows[2]["count"] == 13 and rows[3]["count"] == 12 and rows[2]["proof"] is True and rows[3]["proof"] is False and rows[0]["proof"] is None


def test_distribution_fields_and_shapes():
    d = ev.distribution(30, 20, 0, "edge")
    assert d["n_seeds"] == 100 == d["n_valid"] and d["opt"]["min"] <= d["opt"]["median"] <= d["opt"]["max"] and d["with_blossom"] <= d["n_valid"]
    lad = ev.ladder(30, 20, 0, "edge")
    assert set(lad) == {"n_valid", "blossom", "through", "lost", "nc_optimal", "nc_proof"} and lad["nc_optimal"] + lad["lost"] == lad["n_valid"] and lad["nc_proof"] <= lad["nc_optimal"]


def test_distribution_is_repeatable_and_without_feasible_pairs():
    assert ev.distribution(20, 25, 25, "empty") == ev.distribution(20, 25, 25, "empty")
    assert ev.distribution(4, 10, 0, "edge", seeds=tuple(range(5)))["n_valid"] >= 0
    lonely = tuple(s for s in range(200) if S.generate(4, 10, 0, s).m == 0)
    assert len(lonely) >= 3
    assert ev.distribution(4, 10, 0, "edge", seeds=lonely)["n_valid"] == 0


def test_cell_rows_are_plain_numbers():
    rows = ev.cell_rows(20, 25, 0, tuple(C.SWEEP_SEEDS[:4]))
    for row in rows:
        assert isinstance(row["greedy_edge"], int) and isinstance(row["edges"], int)
        for start in G.STARTS:
            x = row[start]
            assert all(isinstance(x[k], int) for k in ("count", "scanned", "contractions", "augmentations", "depth", "nc_count", "D", "A", "C"))


def test_start_comparison_and_reach_sweep_shape():
    rows = ev.start_comparison(20, 25, 0, seeds=C.SWEEP_SEEDS[:10])
    assert [r["start"] for r in rows] == list(G.STARTS)
    by = {r["start"]: r for r in rows}
    assert by["empty"]["augmentations"] > by["edge"]["augmentations"]
    sw = ev.reach_sweep(20, 0, seeds=C.SWEEP_SEEDS[:6], reaches=(15, 25))
    assert [r["reach"] for r in sw] == [15, 25] and all(r["n_valid"] > 0 for r in sw)


def test_numbering_experiment_and_single_root():
    num = ev.numbering_experiment(20, 25, 0, seeds=C.SWEEP_SEEDS[:8], k=3)
    assert num["k"] == 3 and 0 <= num["all"] <= num["any"] <= num["maps"] and 0 <= num["share"] <= 1
    single = ev.single_root_comparison(20, 25, 0, seeds=C.SWEEP_SEEDS[:8])
    assert set(single) == {"multi", "single"}


def test_scale_table_and_complete_graph_shapes():
    rows = ev.scale_table(ns=(10, 20), seeds=C.SCALE_SEEDS[:3])
    assert [r["n"] for r in rows] == [10, 20] and [r["reach"] for r in rows] == [34, 24] and rows[0]["edge"]["aug"] < rows[0]["empty"]["aug"]
    crow = ev.complete_graph_table(ns=(5, 6), seeds=C.SWEEP_SEEDS[:2])
    assert crow[0]["contractions"] == [2] and crow[0]["scanned"] == [20] and crow[1]["scanned"] == [0] and crow[0]["nc_proof"] == 0


def test_brute_proof_agrees_and_rejects_large_maps():
    for sd in range(20):
        r = ev.brute_proof(S.generate(12, 25, 0, sd))
        assert r["agree"] and r["tutte_berge"] == r["deficiency"] == 12 - 2 * r["opt"]
    with pytest.raises(ValueError):
        ev.brute_proof(S.generate(20, 25, 0, 1))
