"""Rauchtests der Streamlit-Oberfläche per AppTest: Standard, jedes Preset, alle Kombinationen aus Start und Suche (auch beim Abspielen auf mehrbildrigen Karten),
Randgrößen, Schritt-Zustand, ausgeblendete Regler, Permalink, Experimente auf Abruf, Schlüssel und Achsensperre, Blüten-Hüllen."""

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import bl_constants as C
from bl_presets import PRESET_KEYS

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app.py"

# Anfang der Meldung zur gezeigten Karte (Streamlit legt das führende Emoji in `icon`, nicht in `value`)
EXPECTED = {
    "🔺 Dreieck mit Anhängsel": "2 Paare - bewiesen größtmöglich. Greedy fand 1",
    "🌸 Blüte mit Stiel": "5 Paare - bewiesen größtmöglich. Greedy fand 4",
    "🪆 Verschachtelte Blüten": "5 Paare - bewiesen größtmöglich. Greedy fand 4",
    "🌀 Windmühle": "4 Paare - bewiesen größtmöglich. Greedy fand 4, 0 Verbesserungen",
    "🗺️ Mittlere Karte": "13 Paare - bewiesen größtmöglich. Greedy fand 12",
    "🚫 Ohne Kontraktion": "Die Suche ohne Kontraktion endet mit 12 von 13 möglichen Paaren",
    "🧾 Beweis": "14 Paare - bewiesen größtmöglich. Greedy fand 13",
    "🌐 Alles erreichbar": "14 Paare - bewiesen größtmöglich. Greedy fand 14, 0 Verbesserungen",
}
COMBOS = [(start, search) for start in C.START_LABELS for search in C.SEARCH_LABELS]


def _run(setup=None, timeout=600):
    at = AppTest.from_file(str(APP), default_timeout=timeout)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    if setup is not None:
        setup(at)
        at.run()
        assert not at.exception, [e.value for e in at.exception]
    return at


def _apply(at, p):
    for key, state_key in PRESET_KEYS.items():
        at.session_state[state_key] = p[key]


def _set(**kw):
    def setup(at):
        for k, v in kw.items():
            at.session_state[k] = v
    return setup


def _labels(at):
    return {w.label for w in list(at.sidebar.slider) + list(at.sidebar.selectbox) + list(at.sidebar.number_input) + list(at.sidebar.radio)}


def _texts(at):
    return [e.value for e in list(at.success) + list(at.warning) + list(at.info)]


def _has(at, prefix):
    return any(t.startswith(prefix) for t in _texts(at))


def _step(at):
    found = [s for s in at.slider if s.key == "bl_step"]
    return found[0] if found else None


def _keys(at, kind):
    return [w.key for w in getattr(at, kind)]


def _play(at):
    [b for b in at.button if b.label == "▶️ Abspielen"][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_default_renders_without_exception():
    at = _run()
    assert any("Suche und Ablauf" in m.value for m in at.markdown)
    assert _has(at, EXPECTED["🗺️ Mittlere Karte"]) and not at.error


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_renders_with_its_verdict(name):
    at = _run(lambda a: _apply(a, C.PRESETS[name]))
    assert _has(at, EXPECTED[name]), _texts(at)
    if C.PRESETS[name]["net"] in C.FIXED_NETS:
        assert any(t.startswith("Feste Karte") for t in _texts(at))
    else:
        assert any(m.label.startswith("Optimum (Mittel") for m in at.metric)


@pytest.mark.parametrize("start,search", COMBOS)
def test_every_combination_renders_every_kind_of_step(start, search):
    at = _run(_set(start_radio=start, search_radio=search))
    assert not at.error
    last = int(_step(at).max)
    assert last > 4 and _step(at).value == last
    for k in (0, 1, 2, last // 3, last // 2, last - 1, last):
        _step(at).set_value(k)
        at.run()
        assert not at.exception, (start, search, k, [e.value for e in at.exception])


@pytest.mark.parametrize("start,search", COMBOS)
def test_play_runs_through_all_frames_without_duplicate_chart_keys(start, search):
    """Beim Abspielen entstehen in einem Lauf mehrere Diagramme mit demselben Namen - die Schlüssel tragen deshalb den Schritt (Regression: StreamlitDuplicateElementKey bei mehr als einem Bild)."""
    at = _run(_set(start_radio=start, search_radio=search))
    assert _step(at).max > 4
    _play(at)


@pytest.mark.parametrize("net", list(C.FIXED_NETS))
def test_play_on_fixed_maps(net):
    at = _run(_set(net_select=net))
    assert _step(at).max >= 2                                                                    # mindestens drei Bilder mit Diagrammen gleichen Namens
    _play(at)


def test_no_feasible_pair_renders_and_the_search_still_runs():
    from bl_scenario import generate
    seed = next(k for k in range(500) if generate(C.N_MIN, C.REACH_MIN, 0, k).m == 0)
    at = _run(_set(n_slider=C.N_MIN, reach_slider=C.REACH_MIN, seed_input=seed))
    assert any(t.startswith("Kein einziges Paar ist möglich") for t in _texts(at))
    _play(at)


def test_extreme_sizes_render():
    for n, reach in ((C.N_MIN, C.REACH_MIN), (C.N_MAX, C.REACH_MAX), (C.N_MIN, C.REACH_MAX), (C.N_MAX, C.REACH_MIN)):
        at = _run(_set(n_slider=n, reach_slider=reach))
        step = _step(at)
        assert step is not None and step.value == step.max


def test_hidden_controls_follow_the_net():
    def labels_for(net):
        return _labels(_run(_set(net_select=net)))
    random_labels, fixed = labels_for("random"), labels_for("windmuehle")
    assert {"Karte", "Fahrer", "Reichweite [min]", "Ballung [%]", "Zufalls-Seed"} <= random_labels
    assert fixed == {"Karte"}                                                                       # keine toten Regler bei festen Karten


def test_hidden_slider_values_come_back_when_the_random_map_is_shown_again():
    at = _run(_set(reach_slider=90, n_slider=24))
    at.session_state["net_select"] = "stern"
    at.run()
    at.session_state["net_select"] = "random"
    at.run()
    assert not at.exception and at.slider(key="reach_slider").value == 90 and at.slider(key="n_slider").value == 24


def test_step_slider_returns_to_the_last_step_when_the_map_or_a_mode_changes():
    at = _run()
    last = int(_step(at).max)
    assert _step(at).value == last
    _step(at).set_value(3)
    at.run()
    assert _step(at).value == 3
    at.session_state["net_select"] = "dreieck"
    at.run()
    assert not at.exception and _step(at).value == _step(at).max and _step(at).max < last
    at.session_state["net_select"] = "random"
    at.run()
    _step(at).set_value(2)
    at.run()
    at.session_state["search_radio"] = "nocontract"
    at.run()
    assert not at.exception and _step(at).value == _step(at).max


def test_first_step_shows_the_start_a_middle_step_the_forest_and_the_last_the_proof():
    at = _run()
    _step(at).set_value(0)
    at.run()
    assert not at.exception and any("Anfang: Greedy: billigste Kante zuerst - 12 Paare, 6 Fahrer sind noch frei" in m.value for m in at.markdown)
    assert not any("Tutte-Berge-Gleichung" in t.value.to_dict("list").get("Bestandteil", []) for t in at.table)          # der Beweis erst im letzten Schritt
    _step(at).set_value(3)
    at.run()
    assert not at.exception and any(m.value.startswith("**Nach 3 von") for m in at.markdown)
    _step(at).set_value(int(_step(at).max))
    at.run()
    proof = next(t.value.to_dict("list") for t in at.table if "Tutte-Berge-Gleichung" in t.value.to_dict("list").get("Bestandteil", []))
    assert len(proof["Bestandteil"]) == 6 and proof["Wert"][4].startswith("✅") and proof["Wert"][5].startswith("✅")


def test_events_of_every_kind_appear_on_the_nested_map():
    at = _run(_set(net_select="verschachtelt"))
    seen = set()
    for k in range(1, int(_step(at).max) + 1):
        _step(at).set_value(k)
        at.run()
        assert not at.exception
        text = " ".join(m.value for m in at.markdown)
        for key, marker in (("round", "eine neue Suche beginnt"), ("grow", "wird ungerade"), ("blossom", "ungeraden Kreis"), ("augment", "verschiedenen Bäumen"), ("fail", "Keine Verbesserung mehr")):
            if marker in text:
                seen.add(key)
    assert seen == {"round", "grow", "blossom", "augment", "fail"}


def test_the_baseline_ends_without_a_proof():
    at = _run(_set(net_select="verschachtelt", search_radio="nocontract"))
    assert any(w.value.startswith("Die Suche ohne Kontraktion endet mit 4 von 5") for w in at.warning)
    assert any("Aus dieser Beschriftung lässt sich der Beweis nicht herleiten" in m.value for m in at.markdown)
    table = next(t.value.to_dict("list") for t in at.table if "Optimalität beweisbar" in t.value.to_dict("list"))
    assert table["Optimalität beweisbar"] == ["–", "–", "✅", "❌"]


def test_permalink_parameters_are_clamped_and_snapped():
    at = AppTest.from_file(str(APP), default_timeout=600)
    at.query_params["reach"] = "9999"
    at.query_params["ballung"] = "abc"
    at.query_params["n"] = "-5"
    at.run()
    assert not at.exception
    assert at.slider(key="reach_slider").value == C.REACH_MAX and at.slider(key="ballung_slider").value == C.DEFAULT_BALLUNG and at.slider(key="n_slider").value == C.N_MIN
    at = AppTest.from_file(str(APP), default_timeout=600)
    at.query_params["reach"] = "42"
    at.query_params["ballung"] = "60"
    at.run()
    assert at.slider(key="reach_slider").value == 40 and at.slider(key="ballung_slider").value == 50


def test_permalink_keeps_valid_modes_and_falls_back_for_unknown_ones():
    at = AppTest.from_file(str(APP), default_timeout=600)
    at.query_params["start"] = "empty"
    at.query_params["search"] = "nocontract"
    at.run()
    assert not at.exception and at.radio(key="start_radio").value == "empty" and at.radio(key="search_radio").value == "nocontract"
    at = AppTest.from_file(str(APP), default_timeout=600)
    at.query_params["net"] = "ring"
    at.query_params["start"] = "chaos"
    at.query_params["search"] = "X"
    at.run()
    assert not at.exception and at.selectbox(key="net_select").value == C.DEFAULT_NET
    assert at.radio(key="start_radio").value == C.DEFAULT_START and at.radio(key="search_radio").value == C.DEFAULT_SEARCH


def test_randomize_moves_the_seed_but_not_the_distribution():
    at = _run()
    before = {m.label: m.value for m in at.metric if m.label.endswith(("(Mittel | Median)", "verliert"))}
    seed_before = at.number_input(key="seed_input").value
    [b for b in at.sidebar.button if "Neue Karte" in b.label][0].click()
    at.run()
    assert not at.exception and at.number_input(key="seed_input").value != seed_before
    after = {m.label: m.value for m in at.metric if m.label.endswith(("(Mittel | Median)", "verliert"))}
    assert before and before == after


def test_experiments_run_on_demand():
    at = _run()
    markers = ("Der Aufwand wächst etwa wie n^1,5", "Die Ein-Wurzel-Variante verliert seltener", "ein Buckel", "Alle Fahrer erreichen einander, n ungerade", "Das Optimum kommt aus einer Bitmasken-Dynamik")
    assert not any(any(m in c.value for m in markers) for c in at.caption)
    for key in ("scale_start", "numbering_start", "reach_start", "complete_start", "brute_start"):
        at.button(key=key).click()
        at.run()
        assert not at.exception, [e.value for e in at.exception]
    text = " ".join(c.value for c in at.caption)
    assert all(m in text for m in markers)


def test_experiments_on_a_fixed_map():
    at = _run(_set(net_select="bluete"))
    assert "numbering_start" not in _keys(at, "button") and "reach_start" not in _keys(at, "button")
    for key in ("scale_start", "complete_start", "brute_start"):
        at.button(key=key).click()
        at.run()
        assert not at.exception, [e.value for e in at.exception]


def _calls(src, name):
    """Der Text jedes Aufrufs `name(...)` einschließlich verschachtelter Klammern."""
    out = []
    for m in re.finditer(re.escape(name) + r"\(", src):
        depth, i = 1, m.end()
        while depth:
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        out.append(src[m.start():i])
    return out


def test_every_plotly_chart_has_an_explicit_key_and_the_play_loop_keys_carry_the_step():
    calls = _calls(APP.read_text(encoding="utf-8"), "plotly_chart")
    assert len(calls) == 5 and all(re.search(r'key=f?"[a-z_]+(_\{\w+\})?"', c) for c in calls), calls
    keys = [re.search(r'key=f?"([a-z_]+?)(?:_\{\w+\})?"', c).group(1) for c in calls]
    stepped = [c for c in calls if 'key=f"' in c]
    assert len(stepped) == 2 and {re.search(r'key=f"([a-z_]+?)_\{', c).group(1) for c in stepped} == {"bl_map", "bl_progress"}         # die Karte und der Verlauf tragen den Schritt
    unstepped = [k for c, k in zip(calls, keys) if 'key=f"' not in c]
    assert len(set(unstepped)) == len(unstepped) == 3, unstepped                                  # jeder feste Schlüssel nur einmal
    viz = (ROOT / "bl_visualization.py").read_text(encoding="utf-8")
    bodies = [b for b in viz.split(chr(10) + "def ") if b.startswith("build_")]
    assert "fixedrange=True" in viz and len(bodies) == 5 and all("_base(" in b or "_map_layout(" in b for b in bodies)


def test_maps_show_blossoms_as_hulls_have_no_legend_and_keep_equal_scale_inside_the_domain():
    import bl_blossom as B
    import bl_scenario as S
    import bl_visualization as V
    sc = S.nested_flowers()
    res = B.run(sc, "edge")
    hulls = []
    for k in range(res.n_events + 1):
        fig = V.build_map(sc, res, k)
        assert fig.layout.showlegend is False and fig.layout.xaxis.constrain == "domain" and fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
        hulls.append(sum(1 for t in fig.data if t.fill == "toself"))
    assert max(hulls) == 2 and hulls[0] == 0 and hulls[-1] == 0                                    # zwei verschachtelte Hüllen, davor und nach dem Neuaufbau des Waldes keine
    wind = S.windmill()
    wres = B.run(wind, "edge")
    assert max(sum(1 for t in V.build_map(wind, wres, k).data if t.fill == "toself") for k in range(wres.n_events + 1)) == 4          # die Windmühle: vier verschachtelte Hüllen


def test_hull_helper_handles_degenerate_point_sets():
    import bl_visualization as V
    assert V._hull([(0, 0)]) == [(0, 0)] and V._hull([(0, 0), (0, 0)]) == [(0, 0)]
    assert V._hull([(0, 0), (1, 1), (2, 2)]) == [(0, 0), (2, 2)]                                   # kollinear: nur die Enden
    assert set(V._hull([(0, 0), (4, 0), (4, 4), (0, 4), (2, 2)])) == {(0, 0), (4, 0), (4, 4), (0, 4)}


def test_app_text_has_no_links_to_repository_files():
    assert not re.search(r"\]\(\w+\.py\)", APP.read_text(encoding="utf-8"))


def test_footer_is_verbatim():
    src = APP.read_text(encoding="utf-8")
    assert "https://sebastianhanisch.net/kontakt.html" in src and "Interesse an einer maßgeschneiderten Lösung für" in src and "Operations Research und Machine Learning" in src


def test_runtime_needs_only_numpy_pandas_plotly_streamlit():
    """Konvention der Konzepte-Wurzeln und -Stücke: Referenzbibliotheken (scipy, networkx) nur als Testorakel."""
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "scipy" not in req and "networkx" not in req
    for path in ROOT.glob("*.py"):
        assert not re.search(r"^\s*(import|from)\s+(scipy|networkx)\b", path.read_text(encoding="utf-8"), re.M), path.name
