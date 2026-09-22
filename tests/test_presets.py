"""Presets: vollständig, in den Grenzen, und jede Beispielkarte zeigt, was ihr Hilfetext behauptet."""

import pytest

import bl_constants as C
import bl_evaluation as ev
import bl_presets as P
from bl_scenario import build

KEYS = set(P.PRESET_KEYS)


def _a(p):
    return ev.analyse(build(p["net"], p["n"], p["reach"], p["ballung"], p["seed"]), p["start"], p["search"], p["seed"])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 8
    assert all(C.PRESET_HELP[name].strip() for name in C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_preset_values_are_inside_the_bounds_and_on_the_step_grid(name):
    p = C.PRESETS[name]
    assert p["net"] in C.NETS and p["start"] in C.START_LABELS and p["search"] in C.SEARCH_LABELS
    for key, state_key in P.PRESET_KEYS.items():
        spec = P.SETTING_SPECS[state_key]
        if spec.lo is not None:
            assert spec.lo <= p[key] <= spec.hi, (name, key)
    assert (p["reach"] - C.REACH_MIN) % 5 == 0 and p["ballung"] % 25 == 0


def test_setting_specs_have_room_to_move():
    """Ein Regler mit lo == hi würde Streamlit abstürzen lassen."""
    assert all(spec.lo < spec.hi for spec in P.SETTING_SPECS.values() if spec.lo is not None)
    assert set(P.KEPT) <= set(P.SETTING_SPECS)


def test_presets_use_seeds_outside_the_distribution_set():
    for name, p in C.PRESETS.items():
        assert p["seed"] not in C.DIST_SEEDS, name


def test_the_default_map_is_the_medium_preset_and_shows_a_lost_pair_for_greedy():
    p = C.PRESETS["🗺️ Mittlere Karte"]
    assert (p["n"], p["reach"], p["ballung"], p["seed"], p["start"], p["search"]) == (30, 20, 0, C.DEFAULT_SEED, "edge", "edmonds")
    level, code, d = ev.verdict(_a(p))
    assert (level, code) == ("success", ev.OPTIMAL) and (d["greedy"], d["opt"]) == (12, 13)


def test_the_presets_show_what_their_help_says():
    v = {name: ev.verdict(_a(p))[2] for name, p in C.PRESETS.items()}
    assert (v["🔺 Dreieck mit Anhängsel"]["greedy"], v["🔺 Dreieck mit Anhängsel"]["opt"], v["🔺 Dreieck mit Anhängsel"]["nc_count"]) == (1, 2, 1)
    assert (v["🌸 Blüte mit Stiel"]["greedy"], v["🌸 Blüte mit Stiel"]["opt"], v["🌸 Blüte mit Stiel"]["nc_count"], v["🌸 Blüte mit Stiel"]["path_lengths"]) == (4, 5, 4, [9])
    assert (v["🪆 Verschachtelte Blüten"]["greedy"], v["🪆 Verschachtelte Blüten"]["opt"], v["🪆 Verschachtelte Blüten"]["nc_count"], v["🪆 Verschachtelte Blüten"]["depth"]) == (4, 5, 4, 2)
    wind = v["🌀 Windmühle"]
    assert (wind["greedy"], wind["opt"], wind["depth"], wind["scanned"], len(wind["cert"]["A"])) == (4, 4, 4, 24, 0)
    med = v["🗺️ Mittlere Karte"]
    assert (med["greedy"], med["opt"], med["path_lengths"], med["contractions"], med["scanned"]) == (12, 13, [7], 2, 18)
    nc = v["🚫 Ohne Kontraktion"]
    assert (nc["count"], nc["opt"], nc["lost"], nc["cert_holds"]) == (12, 13, 1, False)
    proof = v["🧾 Beweis"]
    assert (proof["greedy"], proof["opt"], len(proof["cert"]["A"]), len(proof["cert"]["D"]), len(proof["cert"]["C"]), proof["cert"]["odd_after_A"]) == (13, 14, 2, 10, 18, 4)
    full = v["🌐 Alles erreichbar"]
    assert (full["greedy"], full["opt"], full["contractions"], full["scanned"]) == (14, 14, 14, 812)


def test_the_medium_preset_is_a_typical_draw():
    """Die gezeigte Karte liegt nahe dem Median der 100 festen Karten (Greedy 12, Optimum 13, Kontraktionen 2 bis 16)."""
    d = ev.distribution(30, 20, 0, "edge")
    a = ev.verdict(_a(C.PRESETS["🗺️ Mittlere Karte"]))[2]
    assert abs(a["opt"] - d["opt"]["median"]) <= 1 and abs(a["greedy"] - d["greedy_edge"]["median"]) <= 1
    assert d["contractions"]["min"] <= a["contractions"] <= d["contractions"]["max"] and d["scanned"]["min"] <= a["scanned"] <= d["scanned"]["max"]


def test_fixed_presets_hide_the_random_controls():
    assert {n for n, p in C.PRESETS.items() if p["net"] in C.FIXED_NETS} == {"🔺 Dreieck mit Anhängsel", "🌸 Blüte mit Stiel", "🪆 Verschachtelte Blüten", "🌀 Windmühle"}
