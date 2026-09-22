"""Jede Zahl in den Hilfetexten, Presets, Tabellen und Grenzen der App und der README ist hier über die 100 festen Karten (DIST_SEEDS) belegt.
Alles rechnet mit ganzen Zahlen und einem eigenen Zufallsgenerator - die Werte sind auf jeder Plattform dieselben; die Toleranzen decken nur die Rundung auf die im Text genannten Stellen.
Positive UND negative Aussagen: wo Blüten den Weg ändern und wo nicht, wo die Suche ohne Kontraktion verliert und wo sie richtig liegt. Mittel und Median stehen zusammen."""

import pytest

import bl_evaluation as ev


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.4f} statt {expected}"


@pytest.fixture(scope="module")
def edge():
    return ev.distribution(30, 20, 0, "edge")


@pytest.fixture(scope="module")
def empty():
    return ev.distribution(30, 20, 0, "empty")


@pytest.fixture(scope="module")
def order():
    return ev.distribution(30, 20, 0, "order")


# --- die Karte: n = 30, Reichweite 20 ------------------------------------------------------------------------------------------------

def test_the_default_map_family(edge):
    d = edge
    near(d["degree"], 2.97, 0.005)
    near(d["opt"]["mean"], 13.37, 0.005)
    assert d["opt"]["median"] == 13.0 and (d["opt"]["min"], d["opt"]["max"]) == (11, 15)
    near(d["greedy_edge"]["mean"], 12.04, 0.005)
    assert d["greedy_edge"]["median"] == 12.0
    near(d["greedy_order"]["mean"], 12.03, 0.005)
    assert (d["greedy_not_opt"], d["greedy_order_not_opt"], d["perfect"]) == (84, 81, 4)              # Greedy ist auf 84 von 100 Karten nicht optimal, ein perfektes Matching gibt es auf 4
    near(d["isolated"]["mean"], 1.77, 0.005)
    assert d["isolated"]["median"] == 1.0 and d["isolated"]["max"] == 7


def test_effort_and_paths_from_the_greedy_start(edge):
    d = edge
    near(d["augmentations"]["mean"], 1.33, 0.005)
    assert d["augmentations"]["median"] == 1.0 and d["augmentations"]["max"] == 4
    near(d["path_len"]["mean"], 4.49, 0.005)
    assert d["path_len"]["median"] == 3.0 and d["path_len"]["max"] == 15 and d["n_paths"] == 133
    near(d["contractions"]["mean"], 6.83, 0.005)
    assert d["contractions"]["median"] == 6.5 and d["contractions"]["max"] == 16
    near(d["depth"]["mean"], 2.85, 0.005)
    assert d["depth"]["median"] == 2.0 and d["depth"]["max"] == 8
    near(d["scanned"]["mean"], 52.32, 0.005)
    assert d["scanned"]["median"] == 50.0 and d["scanned"]["max"] == 97
    near(d["nc_scanned"]["mean"], 37.48, 0.005)                                                        # ohne Kontraktion sieht die Suche weniger Kanten (sie hört früher auf)


def test_the_four_step_ladder(edge):
    d = edge
    assert d["with_blossom"] == 100                                                                    # eine Blüte wird auf allen 100 Karten kontrahiert ...
    assert d["with_through"] == 64                                                                     # ... der Weg läuft nur auf 64 durch eine ...
    assert d["lost_maps"] == 18                                                                        # ... die Suche ohne Kontraktion verliert nur auf 18 ...
    near(d["lost_mean"], 0.19, 0.005)
    assert d["lost_max"] == 2
    near(d["lost_share"] * 100, 1.42, 0.005)                                                           # ... und zwar 1,4 % der Paare
    assert d["nc_optimal"] == 82 and d["nc_proof_of_optimal"] == 16                                    # auf 82 Karten liegt sie richtig, beweisen kann sie es nur auf 16
    assert d["proof"] == 100                                                                           # Blossom kann es auf allen 100


def test_the_certificate_statistics(edge):
    d = edge
    near(d["D"]["mean"], 12.45, 0.005)
    assert d["D"]["median"] == 13.0 and d["D"]["max"] == 28
    near(d["A"]["mean"], 2.09, 0.005)
    assert d["A"]["median"] == 2.0 and d["A"]["max"] == 7 and d["A_empty"] == 29                     # A ist auf 29 Karten leer
    near(d["C"]["mean"], 15.46, 0.005)
    assert d["C"]["median"] == 14.0
    near(d["comps_D"]["mean"], 5.35, 0.005)
    assert d["comps_D"]["median"] == 5.0


def test_the_empty_start(empty):
    d = empty
    near(d["augmentations"]["mean"], 13.37, 0.005)                                                     # eine Verbesserung je Paar
    near(d["contractions"]["mean"], 10.86, 0.005)
    assert d["contractions"]["median"] == 10.0
    near(d["scanned"]["mean"], 78.45, 0.005)
    assert d["scanned"]["median"] == 76.0 and d["with_through"] == 59 and d["lost_maps"] == 24 and d["nc_optimal"] == 76 and d["nc_proof_of_optimal"] == 13
    near(d["lost_mean"], 0.24, 0.005)
    near(d["lost_share"] * 100, 1.8, 0.005)


def test_the_order_start(order):
    d = order
    near(d["augmentations"]["mean"], 1.34, 0.005)
    near(d["contractions"]["mean"], 5.99, 0.005)
    near(d["scanned"]["mean"], 49.71, 0.005)
    assert d["with_blossom"] == 98 and d["with_through"] == 54 and d["lost_maps"] == 23 and d["nc_optimal"] == 77 and d["nc_proof_of_optimal"] == 14                                # ohne Blüte auf 2 Karten


def test_greedy_start_cuts_the_rounds_a_lot_but_the_scans_only_by_a_third(edge, empty):
    rounds = empty["augmentations"]["mean"] / edge["augmentations"]["mean"]
    scans = 1 - edge["scanned"]["mean"] / empty["scanned"]["mean"]
    near(rounds, 10.05, 0.05)                                                                          # Verbesserungen durch zehn
    near(scans, 0.333, 0.0005)                                                                         # angesehene Kanten nur minus 33 %
    assert rounds > 9 and scans < 0.4


# --- Nummerierung und Suchvariante -------------------------------------------------------------------------------------------------------

def test_the_loss_depends_on_the_numbering():
    num = ev.numbering_experiment(30, 20, 0, "edge")
    assert (num["maps"], num["any"], num["all"], num["k"]) == (100, 43, 0, 12)                       # 43 Karten verlieren unter mindestens einer, keine unter allen 12 Nummerierungen
    near(num["share"], 0.1575, 0.0001)                                                                 # 15,8 % der (Karte, Nummerierung)-Paare


def test_single_root_search_loses_less_than_all_roots():
    assert ev.single_root_comparison(30, 20, 0, "edge") == {"multi": 18, "single": 3}
    assert ev.single_root_comparison(30, 20, 0, "empty") == {"multi": 24, "single": 2}


# --- Reichweite und Größe -------------------------------------------------------------------------------------------------------------

def test_reach_sweep_is_a_hump():
    rows = {r["reach"]: r for r in ev.reach_sweep(30)}
    expect = {10: (0.825, 7.5, 27, 5, 3), 20: (3.035, 13.6, 40, 27, 10), 30: (6.138, 14.7, 40, 35, 1), 40: (9.983, 15.0, 36, 29, 0), 60: (17.603, 15.0, 24, 17, 0)}      # Grad, Optimum, Blüte, Weg durch Blüte, Verlust (von 40 Karten)
    for reach, (deg, opt, blossom, through, lost) in expect.items():
        r = rows[reach]
        near(r["degree"], deg, 0.0006)
        near(r["opt"], opt, 0.05)
        assert (r["with_blossom"], r["with_through"], r["lost_maps"]) == (blossom, through, lost) and r["n_valid"] == 40
    assert rows[20]["lost_maps"] > rows[10]["lost_maps"] and rows[20]["lost_maps"] > rows[30]["lost_maps"] > rows[40]["lost_maps"] == 0
    near(rows[20]["lost_mean"], 0.275, 0.0005)
    near(rows[20]["contractions"], 6.925, 0.0005)


def test_on_dense_maps_the_baseline_can_prove_its_result():
    """Nicht verallgemeinern: bei Reichweite 40 (mittlerer Grad 10) liegt die Suche ohne Kontraktion auf 99 Karten richtig und kann es auf 98 beweisen (leerer Start: 100 und 99)."""
    d = ev.distribution(30, 40, 0, "edge")
    assert (d["nc_optimal"], d["nc_proof_of_optimal"], d["lost_maps"]) == (99, 98, 1)
    e = ev.distribution(30, 40, 0, "empty")
    assert (e["nc_optimal"], e["nc_proof_of_optimal"]) == (100, 99)


def test_ballung_helps_the_baseline():
    assert ev.distribution(30, 20, 0, "edge")["lost_maps"] == 18
    assert ev.distribution(30, 20, 100, "empty")["lost_maps"] == 2 and ev.distribution(30, 20, 0, "empty")["lost_maps"] == 24                  # mehr Ballung: fast kein Verlust mehr


def test_effort_against_size():
    rows = {r["n"]: r for r in ev.scale_table()}
    assert [rows[n]["reach"] for n in (10, 20, 40, 80, 160, 320)] == [34, 24, 17, 12, 8, 6]
    expect = {10: (18.0, 10.6), 40: (124.7, 93.1), 160: (824.1, 633.6), 320: (2968.6, 2233.7)}          # angesehene Kanten: leerer Start, Greedy-Start
    for n, (e, g) in expect.items():
        near(rows[n]["empty"]["scan"], e, 0.05)
        near(rows[n]["edge"]["scan"], g, 0.05)
    near(rows[320]["edge"]["nc_scan"], 1642.9, 0.05)
    near(rows[320]["empty"]["nc_scan"], 2455.2, 0.05)
    assert all(2.5 < rows[n]["degree"] < 3.5 for n in rows)                                              # der mittlere Grad bleibt bei jeder Größe zwischen 2,6 und 3,4
    assert [rows[n]["edge"]["lost_maps"] for n in (10, 20, 40, 80, 160, 320)] == [1, 2, 2, 6, 8, 7]         # ohne Kontraktion: Karten mit Verlust (von 10)
    assert [round(rows[n]["edge"]["lost_mean"], 1) for n in (10, 20, 40, 80, 160, 320)] == [0.1, 0.2, 0.2, 0.8, 1.4, 1.8]
    near(rows[320]["edge"]["scan_per_edge"], 4.12, 0.005)
    near(rows[10]["edge"]["scan_per_edge"], 0.81, 0.005)
    assert (rows[320]["edge"]["scan"] / rows[20]["edge"]["scan"]) > 16 ** 1.2                            # etwa n^1,5: 16-fache Größe, mehr als 16^1,2-facher Aufwand
    near(1 - rows[320]["edge"]["scan"] / rows[320]["empty"]["scan"], 0.248, 0.0005)                        # bei n = 320 spart der Greedy-Start 25 % der Kanten
    near(rows[320]["empty"]["aug"] / rows[320]["edge"]["aug"], 8.66, 0.005)                             # und teilt die Verbesserungen durch 8,7


def test_complete_graphs_need_nested_blossoms():
    rows = {r["n"]: r for r in ev.complete_graph_table()}
    for n, scans in ((5, 20), (11, 110), (17, 272), (23, 506), (29, 812), (35, 1190)):
        assert rows[n]["scanned"] == [scans] and rows[n]["contractions"] == [(n - 1) // 2] and rows[n]["depth"] == [(n - 1) // 2] and rows[n]["count"] == [(n - 1) // 2] and rows[n]["nc_proof"] == 0
        assert scans == n * (n - 1)


# --- die Presets ------------------------------------------------------------------------------------------------------------------------

def test_preset_maps():
    from bl_scenario import generate
    a = ev.analyse(generate(30, 20, 0, 165), "edge", "edmonds", 165)
    _, _, d = ev.verdict(a)
    assert (d["greedy"], d["opt"], d["augmentations"], d["path_lengths"], d["contractions"], d["depth"], d["scanned"], d["events"], d["isolated"]) == (12, 13, 1, [7], 2, 1, 18, 10, 4)
    assert (d["nc_count"], d["nc_lost"], len(d["cert"]["A"]), len(d["cert"]["D"]), d["cert_holds"], d["cert_nc_holds"]) == (12, 1, 0, 4, True, False)
    b = ev.analyse(generate(30, 20, 0, 155), "edge", "edmonds", 155)
    _, _, d = ev.verdict(b)
    assert (d["greedy"], d["opt"], d["path_lengths"], d["contractions"], d["depth"], d["scanned"], d["events"]) == (13, 14, [3], 5, 2, 32, 18)
    assert (len(d["cert"]["A"]), len(d["cert"]["D"]), len(d["cert"]["C"]), d["nc_count"], d["cert"]["odd_after_A"], d["cert"]["deficiency"]) == (2, 10, 18, 13, 4, 2)
    c = ev.analyse(generate(29, 150, 0, 165), "edge", "edmonds", 165)
    _, _, d = ev.verdict(c)
    assert (d["greedy"], d["opt"], d["augmentations"], d["contractions"], d["depth"], d["scanned"], d["cert_nc_holds"]) == (14, 14, 0, 14, 14, 812, False)
