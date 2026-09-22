"""Blossom - Paare in einem Graphen ohne zwei Seiten - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo EIN Verfahren - Edmonds' Blossom-Algorithmus - und lässt stattdessen das Beispiel wachsen.
Achtes Stück der Matching-Linie der "Konzepte"-Reihe, unabhängiger Ast unter den Verbesserungswegen: die Suche der zweiseitigen Demos in einem allgemeinen Graphen. Siehe README.

Lauffähig mit: streamlit run app.py
"""

import time

import numpy as np
import streamlit as st

import bl_constants as C
import bl_evaluation as ev
from bl_blossom import state_at
from bl_presets import (
    KEPT,
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from bl_scenario import build, generate
from bl_visualization import build_ladder, build_map, build_progress, build_reach_sweep, build_scale

st.set_page_config(page_title="Blossom – Sebastian Hanisch", layout="wide")


def _f(x, digits=1):
    return "–" if x is None else f"{x:.{digits}f}".replace(".", ",")


def _int(x):
    return f"{x:,.0f}".replace(",", " ")


def _ms(s, digits=1):
    """Mittel | Median (max)"""
    return f"{_f(s['mean'], digits)} | {_f(s['median'], digits)}"


@st.cache_resource(show_spinner=False, max_entries=16)
def _analysis(params):
    net, n, reach, ballung, seed, start, search = params
    return ev.analyse(build(net, n, reach, ballung, seed), start, search, seed)


@st.cache_data(show_spinner=False)
def _distribution(n, reach, ballung, start):
    return ev.distribution(n, reach, ballung, start)


@st.cache_data(show_spinner=False)
def _starts(n, reach, ballung):
    return ev.start_comparison(n, reach, ballung)


@st.cache_data(show_spinner=False)
def _scale():
    return ev.scale_table()


@st.cache_data(show_spinner=False)
def _numbering(n, reach, ballung, start):
    return ev.numbering_experiment(n, reach, ballung, start), ev.single_root_comparison(n, reach, ballung, start)


@st.cache_data(show_spinner=False)
def _reach_sweep(n, ballung, start):
    return ev.reach_sweep(n, ballung, start=start)


@st.cache_data(show_spinner=False)
def _complete():
    return ev.complete_graph_table()


@st.cache_data(show_spinner=False)
def _brute(reach, ballung, seed):
    return [ev.brute_proof(generate(12, reach, ballung, seed + k)) for k in range(20)]


st.title("🌸 Blossom – Paare in einem Graphen ohne zwei Seiten")
st.markdown(
    """
In den bisherigen Demos gab es **zwei Seiten**: Fahrzeuge und Aufträge. Hier gibt es nur **eine Gruppe von Fahrern**, je zwei können **zusammen fahren**, wenn sie nah genug beieinander liegen - ein allgemeiner Graph. Und in ihm gibt es **ungerade Kreise**:
drei Fahrer, die einander erreichen. Die Suche der Verbesserungswege-Demo wird dort unzuverlässig: sie kann in einem solchen Kreis nur eine Richtung sehen und meldet „kein Verbesserungsweg“, obwohl es einen gibt.
**Edmonds' Blossom-Algorithmus** zieht so einen Kreis, die **Blüte**, zu **einer** Ecke zusammen, sucht weiter und klappt den Weg am Ende wieder durch die Blüte auf - in der richtigen Richtung. Am Ende steht sogar ein **Beweis** der Optimalität.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren vergleichen, zeigt diese Demo - achtes Stück der Matching-Linie der \"Konzepte\"-Reihe, unabhängiger Ast unter den Verbesserungswegen - **ein** Verfahren an einem wachsenden Beispiel. "
    "Der Vergleich ist ehrlich gebaut: die **Baseline** ist dieselbe Suche **ohne** den Kontraktionsschritt (die wörtliche Breitensuche der zweiseitigen Demo liefert auf einem allgemeinen Graphen nicht einmal gültige Wege). "
    "Gewichte (welche Paare **billiger** sind) fehlen absichtlich: sie sind das nächste Stück, der **Gewichtete Blossom**. Nachbarn der Linie, noch nicht gebaut: Gewichteter Blossom und Stabile Mitbewohner."
)

with st.expander("So funktioniert Blossom", expanded=True):
    st.markdown(
        """
1. **Wald:** alle noch freien Fahrer sind **Wurzeln** (gerade). Von den geraden Fahrern aus wächst ein Wald: ein Nachbar, der noch nicht dabei ist, wird **ungerade**, sein Partner wieder **gerade** - so entstehen alternierende Pfade.
2. **Verbesserungsweg:** berührt eine Kante zwei gerade Fahrer **verschiedener Bäume**, ist der Weg zwischen den Wurzeln ein Verbesserungsweg: Umklappen (gewählt ⇄ nicht gewählt) gibt ein Paar mehr.
3. **Blüte:** verbindet eine Kante zwei gerade Fahrer **desselben Baums**, entsteht ein **ungerader Kreis**. Die Suche zieht ihn zu **einer** geraden Ecke zusammen (die ungeraden Mitglieder werden gerade und suchen weiter). Blüten können in Blüten liegen.
4. **Aufklappen:** beim Zurücklaufen des Weges wird jede Blüte wieder geöffnet, und zwar in der Richtung, die eine **gerade** Zahl von Kanten im Inneren hat - deshalb bleibt der Weg alternierend.
5. **Ende und Beweis:** findet die Suche keinen Weg mehr, sind die geraden Fahrer D, die ungeraden A und der Rest C. Fehlen nach Entfernen von A genau so viele ungerade Komponenten wie freie Fahrer, ist das Matching **bewiesen größtmöglich** (Tutte-Berge).
        """
    )

st.caption("🎯 Schnellstart – eine Beispielkarte laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    net_key = st.selectbox(
        "Karte", list(C.NETS), key="net_select", format_func=lambda k: C.NETS[k],
        help="Eine zufällige Karte mit Fahrern oder eine feste Lehrbuchkarte: die kleinste Blüte, eine Blüte mit Stiel, verschachtelte Blüten, die Windmühle (der ganze Graph ist eine Blüte) und der Stern.",
    )
    if net_key == "random":
        n = st.slider("Fahrer", *bounds("n_slider"), key="n_slider", help="Anzahl der Fahrer. Je zwei können zusammen fahren, wenn ihre Fahrzeit höchstens die Reichweite beträgt.")
        st.session_state[KEPT["n_slider"]] = n
        reach = st.slider("Reichweite [min]", *bounds("reach_slider"), key="reach_slider", step=5,
                          help="Wie weit zwei Fahrer höchstens auseinander liegen dürfen. Bei kleiner Reichweite ist der Graph fast ein Baum, bei großer schafft schon Greedy fast alles: Blüten spielen dazwischen die größte Rolle (n = 30: um Reichweite 20). Ab 142 kann jeder jeden erreichen.")
        st.session_state[KEPT["reach_slider"]] = reach
        ballung = st.slider("Ballung [%]", *bounds("ballung_slider"), key="ballung_slider", step=25, help="0 = Fahrer gleichmäßig verteilt, 100 = alle um drei Stadtteile gruppiert. Mehr Ballung bedeutet hier weniger Verlust ohne Kontraktion.")
        st.session_state[KEPT["ballung_slider"]] = ballung
        seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
        st.session_state[KEPT["seed_input"]] = seed
        st.button("🎲 Neue Karte generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Zufalls-Seed. Die Verteilung über 100 feste Karten weiter unten ändert sich dabei nicht.")
    else:
        n = int(st.session_state.get(KEPT["n_slider"], C.DEFAULT_N))
        reach = int(st.session_state.get(KEPT["reach_slider"], C.DEFAULT_REACH))
        ballung = int(st.session_state.get(KEPT["ballung_slider"], C.DEFAULT_BALLUNG))
        seed = int(st.session_state.get(KEPT["seed_input"], C.DEFAULT_SEED))
        st.caption("Diese Karte ist fest - es gibt nichts zu erzeugen. Zahl der Fahrer, Reichweite, Ballung und Seed gehören zur zufälligen Karte.")

fixed = net_key in C.FIXED_NETS

# --- Suche und Ablauf ---------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Suche und Ablauf")
step_col, start_col, search_col, play_col = st.columns([4, 3, 4, 2])
with start_col:
    start = st.radio("Start", list(C.START_LABELS), key="start_radio", format_func=lambda k: C.START_LABELS[k],
                     help="Womit die Suche beginnt: leer, oder mit einer Greedy-Paarung (billigste Kante zuerst / Fahrer für Fahrer). Greedy senkt die Zahl der Verbesserungen um etwa das Zehnfache, die angesehenen Kanten aber nur um ein Viertel bis ein Drittel.")
with search_col:
    search = st.radio("Suche", list(C.SEARCH_LABELS), key="search_radio", format_func=lambda k: C.SEARCH_LABELS[k],
                      help="Blossom zieht Blüten zusammen. Ohne Kontraktion ist es dieselbe Suche, aber eine Kante zwischen zwei geraden Fahrern desselben Baums wird übersprungen (wie im zweiseitigen Fall, wo es sie nicht gibt): stets gültig, aber manchmal zu klein.")
params = (net_key, int(n), int(reach), int(ballung), int(seed), start, search)
if fixed:
    params = (net_key, C.DEFAULT_N, C.DEFAULT_REACH, C.DEFAULT_BALLUNG, C.DEFAULT_SEED, start, search)
with st.spinner("Rechne..."):
    a = _analysis(params)
sc, res = a.scenario, a.result
level, code, d = ev.verdict(a)
n_events = res.n_events
if st.session_state.get("bl_step_owner") != params:
    st.session_state["bl_step"] = n_events
    st.session_state["bl_step_owner"] = params
with step_col:
    step = st.slider("Ereignis", 0, n_events, key="bl_step", help="Wie viele Ereignisse der Suche schon geschehen sind (Runde beginnt, Fahrer entdeckt, Blüte gefunden, Weg umgeklappt). Ganz rechts das Ergebnis mit dem Beweis.")
with play_col:
    auto_play = st.button("▶️ Abspielen", width="stretch")
sync_query_params({"net_select": net_key, "start_radio": start, "search_radio": search, "n_slider": int(n), "reach_slider": int(reach), "ballung_slider": int(ballung), "seed_input": int(seed)})
view_slot = st.empty()
opt = d["opt"]
lab = lambda v: f"{v + 1}"


def _event_text(k):
    if k == 0:
        free = sc.n - 2 * len(res.start)
        return f"Anfang: {C.START_LABELS[start]} - {len(res.start)} Paare, {free} Fahrer sind noch frei. Noch keine Suche."
    e = res.events[k - 1]
    if e.kind == "round":
        roots = sum(1 for x in state_at(res, k - 1)[0].match if x < 0)
        return f"Runde {e.round}: eine neue Suche beginnt. Alle {roots} freien Fahrer sind Wurzeln (gerade) und wachsen gleichzeitig; die Bäume der letzten Runde sind vergessen, ebenso ihre Blüten."
    if e.kind == "grow":
        return f"Fahrer {lab(e.v)} (gerade) erreicht {lab(e.u)}, der noch nicht im Wald ist: {lab(e.u)} wird ungerade, sein Partner {lab(e.w)} gerade."
    if e.kind == "blossom":
        blo = res.blossoms[e.blossom]
        kids = f" Sie enthält {len(blo.children)} kleinere Blüte{'n' if len(blo.children) != 1 else ''} (Tiefe {blo.depth})." if blo.children else ""
        return (f"Fahrer {lab(e.v)} und {lab(e.u)} sind beide gerade und im selben Baum: die Kante schließt einen **ungeraden Kreis**, die Blüte {e.blossom + 1} mit {len(blo.members)} Fahrern und der Basis {lab(blo.base)}. "
                f"Sie wird zu einer geraden Ecke zusammengezogen, ihre ungeraden Mitglieder werden gerade.{kids}")
    if e.kind == "augment":
        thr = ""
        if e.through:
            thr = " Der Weg läuft durch " + " und ".join(f"die Blüte {b + 1} (Eintritt {lab(i)}, Austritt {lab(o)}, {inner} Kanten im Inneren, gerade Länge)" for b, i, o, inner in e.through) + "."
        return f"Fahrer {lab(e.v)} und {lab(e.u)} liegen in **verschiedenen Bäumen**: der Weg {' - '.join(lab(x) for x in e.path)} ({len(e.path) - 1} Kanten) ist ein Verbesserungsweg.{thr} Umklappen: {state_count(k)} Paare."
    if a.search == "nocontract":
        more = f" Es fehlen {d['lost']} Paare zum Optimum ({opt}): die Suche hat sie in einer Blüte übersehen." if d["lost"] else ""
        proof = " Aus dieser Beschriftung lässt sich der Beweis nicht herleiten." if not d["cert_holds"] else " Hier lässt sich der Beweis aber herleiten."
        return f"Keine Verbesserung mehr: die Suche endet mit {res.count} Paaren.{more}{proof}"
    return f"Keine Verbesserung mehr: die Suche endet mit {res.count} Paaren - **bewiesen größtmöglich**: entfernt man die {len(d['cert']['A'])} ungeraden Fahrer, bleiben {d['cert']['odd_after_A']} ungerade Komponenten."


def state_count(k):
    return sum(1 for x in state_at(res, k)[0].match if x >= 0) // 2


def _cert_table():
    c = d["cert"]
    ok = lambda b: "✅" if b else "❌"
    rows = [("D (gerade Fahrer)", f"{len(c['D'])} Fahrer in {len(c['comps_D'])} Komponenten (Größen: {', '.join(str(x) for x in sorted(c['comps_D'], reverse=True)[:12]) or '–'})"),
            ("A (ungerade Fahrer)", f"{len(c['A'])} Fahrer: " + (", ".join(lab(v) for v in c["A"]) or "keine")),
            ("C (nicht im Wald)", f"{len(c['C'])} Fahrer in {len(c['comps_C'])} Komponenten"),
            ("Ungerade Komponenten von G − A", f"{c['odd_after_A']}"),
            ("Tutte-Berge-Gleichung", f"{ok(c['holds'])} ungerade Komponenten − |A| = {c['odd_after_A']} − {len(c['A'])} = {c['odd_after_A'] - len(c['A'])};  n − 2 · Paare = {sc.n} − {2 * res.count} = {c['deficiency']}"),
            ("Struktur (Gallai-Edmonds)", f"{ok(c['ge_ok'])} alle Komponenten von D ungerade, alle von C gerade, keine Kante zwischen D und C")]
    return {"Bestandteil": [r[0] for r in rows], "Wert": [r[1] for r in rows]}


def _render(k):
    """Zustand nach den ersten k Ereignissen: links die Karte, rechts der Verlauf; am Ende der Beweis."""
    with view_slot.container():
        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**Nach {k} von {n_events} Ereignissen** - " + _event_text(k))
        c1.plotly_chart(build_map(sc, res, k), width="stretch", key=f"bl_map_{k}")
        c2.markdown("**Verlauf**")
        c2.plotly_chart(build_progress(res, k, opt), width="stretch", key=f"bl_progress_{k}")
        snap, blossoms = state_at(res, k)
        if blossoms:
            c2.table({"Blüte": [b.id + 1 for b in blossoms], "Fahrer": [len(b.members) for b in blossoms], "Basis": [lab(b.base) for b in blossoms], "Tiefe": [b.depth for b in blossoms]})
        if k == n_events:
            st.markdown("**Beweis:** ist das Ergebnis größtmöglich?")
            st.table(_cert_table())
            if a.search == "nocontract":
                st.caption("Dies ist die Beschriftung der Suche ohne Kontraktion. Die Gleichung gilt nur, wenn die Suche zufällig alles gesehen hat; sonst fehlt der Beweis (und oft auch ein Paar).")
            else:
                st.caption("Für jede Fahrer-Menge S gilt: n − 2 · Paare ≥ ungerade Komponenten von G − S − |S| (Tutte-Berge). Gilt bei S = A Gleichheit, kann kein Matching größer sein.")


if auto_play:
    frames = sorted({int(round(x)) for x in np.linspace(0, n_events, min(n_events, 40) + 1)})
    for k in frames:
        _render(k)
        time.sleep(min(0.6, 6.0 / max(len(frames), 1)))
    step = n_events
else:
    _render(step)

st.caption("Fahrer: grün = gerade, rot = ungerade, grau = noch nicht im Wald. Blaue Linien sind gewählte Paare, dünne dunkle Linien der Wald. Eine violette Hülle ist eine kontrahierte Blüte (verschachtelt = dunkler, ein Ring markiert die Basis). "
           "Beim letzten Ereignis: grün = Fahrer neu entdeckt, violett gestrichelt = die Kante, die eine Blüte schließt, orange = der Verbesserungsweg (Stücke im Inneren einer Blüte violett).")

st.markdown("---")

# --- Wie gut? ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Wie gut ist das Ergebnis?")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Paare", f"{d['count']} von {d['opt']}", delta=(f"{d['lost']} weniger als das Optimum" if d["lost"] else "so viele wie das Optimum"), delta_color="off",
          help=f"Greedy ({C.START_LABELS['edge'].split(':')[0]}) findet {d['greedy_edge']}, Greedy (Fahrer für Fahrer) {d['greedy_order']}; das Optimum kennt Blossom.")
m2.metric("Verbesserungen", str(d["augmentations"]), delta=f"Weglängen: {', '.join(str(x) for x in d['path_lengths']) or '–'}", delta_color="off", help="Wie oft ein Verbesserungsweg umgeklappt wurde, und wie viele Kanten er hatte (3 = kürzester Weg um ein Paar).")
m3.metric("Blüten", f"{d['contractions']}", delta=f"größte Tiefe {d['depth']}, Weg durch eine Blüte: {d['through']}", delta_color="off", help="Zahl der Kontraktionen (nach jeder Verbesserung wird der Wald neu aufgebaut). Tiefe = wie tief Blüten ineinander liegen.")
m4.metric("Angesehene Kanten", _int(d["scanned"]), delta=f"ohne Kontraktion: {_int(d['nc_scanned'])}", delta_color="off", help="Aufwand in Kanten (Kopfzahl, nie Sekunden); jede Kante wird von beiden Enden gesehen. Dazu kommen die Ecken in kontrahierten Blüten: " + _int(d["contracted_vertices"]) + ".")
if code == "none":
    st.info("ℹ️ Kein einziges Paar ist möglich – die Reichweite ist zu klein. Es gibt nichts zu paaren.")
elif code == "optimal":
    st.success(f"✅ {d['count']} Paare - {'bewiesen größtmöglich' if d['cert_holds'] else 'größtmöglich'}. Greedy fand {d['greedy']}, {d['augmentations']} Verbesserung{'en' if d['augmentations'] != 1 else ''} führten zum Optimum.")
else:
    st.warning(f"Die Suche ohne Kontraktion endet mit {d['count']} von {d['opt']} möglichen Paaren: sie hat {d['lost']} Paar{'e' if d['lost'] != 1 else ''} in einer Blüte übersehen. Blossom findet {d['opt']}.")
cmp_rows = ev.compare_table(a)
st.table({"Verfahren": [r["label"] for r in cmp_rows], "Paare": [str(r["count"]) for r in cmp_rows], "Verbesserungen": [str(r["augmentations"]) if r["augmentations"] is not None else "–" for r in cmp_rows],
          "Blüten": [str(r["contractions"]) if r["contractions"] is not None else "–" for r in cmp_rows], "angesehene Kanten": [_int(r["scanned"]) if r["scanned"] is not None else "–" for r in cmp_rows],
          "Optimalität beweisbar": ["–" if r["proof"] is None else ("✅" if r["proof"] else "❌") for r in cmp_rows]})
st.caption("Die Zeilen mit Verfahren beginnen alle beim gewählten Start. „Optimalität beweisbar“ heißt: aus der Beschriftung der letzten Suche ergibt sich eine Menge A, für die die Tutte-Berge-Gleichung gilt.")

if fixed:
    st.info("Feste Karte: es gibt nur diese eine Ziehung. Für die Verteilung über viele Karten eine zufällige Karte wählen.")
elif code != "none":
    st.markdown(f"**Nicht nur diese eine Karte:** {len(C.DIST_SEEDS)} feste Karten mit denselben Einstellungen (Fahrer {n}, Reichweite {reach}, Ballung {ballung} %, Start: {C.START_LABELS[start]}), getrennt vom Seed oben.")
    dist = _distribution(int(n), int(reach), int(ballung), start)
    if dist["n_valid"] == 0:
        st.info("ℹ️ Bei dieser Reichweite gibt es auf keiner der Karten ein mögliches Paar.")
    else:
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Optimum (Mittel | Median)", _ms(dist["opt"]), delta=f"Greedy: {_ms(dist['greedy_edge'])}", delta_color="off", help=f"Greedy ist auf {dist['greedy_not_opt']} von {dist['n_valid']} Karten nicht optimal; ein perfektes Matching (alle Fahrer gepaart) gibt es auf {dist['perfect']}.")
        p2.metric("Kontraktionen (Mittel | Median)", _ms(dist["contractions"]), delta=f"Blüte auf {dist['with_blossom']} von {dist['n_valid']} Karten", delta_color="off")
        p3.metric("Angesehene Kanten (Mittel | Median)", _ms(dist["scanned"], 0), delta=f"ohne Kontraktion: {_ms(dist['nc_scanned'], 0)}", delta_color="off")
        p4.metric("Ohne Kontraktion verliert", f"{dist['lost_maps']} von {dist['n_valid']} Karten", delta=f"im Mittel {_f(dist['lost_mean'], 2)} Paare, höchstens {dist['lost_max']}", delta_color="off",
                  help="Karten, auf denen die Suche ohne Kontraktion weniger Paare findet als Blossom, und wie viele.")
        st.plotly_chart(build_ladder(ev.ladder(int(n), int(reach), int(ballung), start)), width="stretch", key="bl_ladder")
        st.caption(f"Die Leiter über {dist['n_valid']} Karten: eine Blüte entsteht fast immer; sie ändert den Weg oft; aber die Suche ohne Kontraktion verliert nur auf einem Teil der Karten ein oder zwei Paare, und auf den meisten Karten, auf denen sie richtig liegt, kann sie es nicht beweisen. Der Verlust hängt von der Nummerierung der Fahrer ab (unten).")
        srows = _starts(int(n), int(reach), int(ballung))
        st.table({"Start": [C.START_LABELS[r["start"]] for r in srows], "Verbesserungen (Mittel)": [_f(r["augmentations"], 2) for r in srows], "angesehene Kanten (Mittel)": [_f(r["scanned"], 1) for r in srows],
                  "Kontraktionen (Mittel)": [_f(r["contractions"], 1) for r in srows], "ohne Kontraktion: Karten mit Verlust": [r["lost_maps"] for r in srows]})
        st.caption("Ein Greedy-Start spart die meisten Verbesserungen (der leere Start braucht eine je Paar), aber deutlich weniger angesehene Kanten: die letzte, erfolglose Suche und die breiten frühen Suchen dominieren den Aufwand.")

st.markdown("---")

# --- Experimente auf Abruf -----------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wovon hängt es ab?")
if st.button("Aufwand gegen die Größe (n = 10 bis 320)", key="scale_start"):
    st.session_state["scale_on"] = True
if st.session_state.get("scale_on"):
    with st.spinner("Rechne 6 Größen × 10 Karten..."):
        rows = _scale()
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(build_scale(rows), width="stretch", key="bl_scale_chart")
    c2.table({"n": [r["n"] for r in rows], "Reichweite": [r["reach"] for r in rows], "leer: Kanten": [_int(r["empty"]["scan"]) for r in rows], "Greedy: Kanten": [_int(r["edge"]["scan"]) for r in rows],
              "Greedy: Kanten je Kante": [_f(r["edge"]["scan_per_edge"], 1) for r in rows], "ohne Kontraktion, Greedy": [_int(r["edge"]["nc_scan"]) for r in rows], "ohne Kontraktion: Karten mit Verlust": [f"{r['edge']['lost_maps']} von 10" for r in rows]})
    st.caption("Mittel über 10 feste Karten, Reichweite so gewählt, dass der mittlere Grad bei jeder Größe etwa 3 bleibt. Der Aufwand wächst etwa wie n^1,5. Theorie: höchstens n/2 Verbesserungen je O(Kanten) plus die Kontraktionen, die mit Mitgliederlisten O(Größe) kosten. "
               "Ohne Kontraktion ist es etwas billiger, weil die Suche früher aufhört. Der Verlust ohne Kontraktion bleibt ein fast gleicher Anteil der Paare (etwa 1 %), wird absolut aber größer.")

if not fixed:
    if st.button("Andere Nummerierung: derselbe Graph, andere Reihenfolge (12 Nummerierungen je Karte)", key="numbering_start"):
        st.session_state["numbering_on"] = (int(n), int(reach), int(ballung), start)
    if st.session_state.get("numbering_on") == (int(n), int(reach), int(ballung), start):
        with st.spinner("Rechne 12 Nummerierungen × 100 Karten..."):
            num, single = _numbering(int(n), int(reach), int(ballung), start)
        st.table({"Frage": ["Karten, die unter mindestens einer Nummerierung Paare verlieren", "Karten, die unter allen 12 Nummerierungen verlieren", "Anteil der (Karte, Nummerierung)-Paare mit Verlust",
                            "Karten mit Verlust: alle freien Fahrer als Wurzeln (wie die Vorgänger-BFS)", "Karten mit Verlust: eine Wurzel nach der anderen (Kuhn)"],
                  "Ergebnis": [f"{num['any']} von {num['maps']}", f"{num['all']} von {num['maps']}", f"{_f(100 * num['share'], 1)} %", f"{single['multi']} von {num['maps']}", f"{single['single']} von {num['maps']}"]})
        st.caption("Der Graph ist derselbe, nur die Nummerierung der Fahrer (und damit die Reihenfolge, in der die Suche ihn sieht) ist eine andere. Der Verlust ohne Kontraktion ist also zum Teil **Zufall der Nummerierung**; unter den meisten Nummerierungen findet auch die Suche ohne Kontraktion das Optimum. "
                   "Die Ein-Wurzel-Variante verliert seltener als die Alle-Wurzeln-Variante - die Demo verwendet die zweite, weil sie die Suche der Vorgänger spiegelt.")
    if st.button("Reichweiten-Sweep (40 Karten je Wert)", key="reach_start"):
        st.session_state["reach_on"] = (int(n), int(ballung), start)
    if st.session_state.get("reach_on") == (int(n), int(ballung), start):
        with st.spinner("Rechne 7 Reichweiten × 40 Karten..."):
            rrows = _reach_sweep(int(n), int(ballung), start)
        c1, c2 = st.columns([3, 2])
        c1.plotly_chart(build_reach_sweep(rrows), width="stretch", key="bl_reach_chart")
        c2.table({"Reichweite": [r["reach"] for r in rrows], "Grad": [_f(r["degree"], 1) for r in rrows], "Optimum": [_f(r["opt"], 1) for r in rrows], "Blüte": [r["with_blossom"] for r in rrows],
                  "Weg durch Blüte": [r["with_through"] for r in rrows], "Verlust": [r["lost_maps"] for r in rrows]})
        st.caption("Von n Karten. Bei kleinem Grad ist der Graph fast ein Baum (wenige Kreise), bei großem schafft schon Greedy fast alles; dazwischen ist der Verlust ohne Kontraktion am größten - ein Buckel.")

if st.button("Der vollständige Graph: der Beweis braucht n/2 verschachtelte Blüten", key="complete_start"):
    st.session_state["complete_on"] = True
if st.session_state.get("complete_on"):
    with st.spinner("Rechne..."):
        crow = _complete()
    st.table({"n (ungerade)": [r["n"] for r in crow], "Paare (Greedy = Optimum)": [", ".join(str(x) for x in r["count"]) for r in crow], "Kontraktionen": [", ".join(str(x) for x in r["contractions"]) for r in crow],
              "größte Tiefe": [", ".join(str(x) for x in r["depth"]) for r in crow], "angesehene Kanten": [", ".join(_int(x) for x in r["scanned"]) for r in crow], "ohne Kontraktion beweisbar": [f"{r['nc_proof']} von {r['maps']}" for r in crow]})
    st.caption("Alle Fahrer erreichen einander, n ungerade: Greedy findet sofort (n − 1)/2 Paare, das Optimum. Trotzdem braucht der Beweis (n − 1)/2 ineinander verschachtelte Blüten und genau n (n − 1) angesehene Kanten - auf jeder Karte, unabhängig von der Lage der Fahrer. Ohne Kontraktion lässt sich hier nichts beweisen.")

if st.button("Brute-Force-Beweis auf 20 kleinen Karten (12 Fahrer)", key="brute_start"):
    st.session_state["brute_on"] = (int(reach), int(ballung), int(seed))
if st.session_state.get("brute_on") == (int(reach), int(ballung), int(seed)):
    with st.spinner("Probiere alle Teilmengen..."):
        brows = _brute(int(reach), int(ballung), int(seed))
    st.table({"Karte": list(range(1, len(brows) + 1)), "Optimum (Brute Force)": [r["opt"] for r in brows], "Tutte-Berge: max über alle 4096 Teilmengen": [r["tutte_berge"] for r in brows],
              "n − 2 · Optimum": [r["deficiency"] for r in brows], "Blossom": [r["blossom"] for r in brows], "alles gleich": ["✅" if r["agree"] else "❌" for r in brows]})
    st.caption("12 Fahrer, Reichweite und Ballung wie in der Seitenleiste, Seeds ab dem eingestellten. Das Optimum kommt aus einer Bitmasken-Dynamik, das Tutte-Berge-Maximum aus allen 4096 Teilmengen S von odd(G − S) − |S|; beides ohne Blossom.")

st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Alle Paare sind gleich gut** | Kosten spielen keine Rolle: Blossom findet die *Zahl* der Paare, nicht die billigste Paarung. Soll auch die Fahrzeit minimal sein, braucht es Gewichte. | **Gewichteter Blossom** (nicht gebaut), im zweiseitigen Fall die **Ungarische Methode** (gebaut) |
| **Jeder kann mit jedem** (eine Gruppe) | Gibt es zwei getrennte Seiten, geht es schneller: keine Blüten, viele kürzeste Wege je Phase. | **Hopcroft–Karp** (gebaut) |
| **Größe zählt, nicht Zufriedenheit** | Haben die Fahrer Vorlieben, ist die stabile Paarung das Ziel - und in einer Gruppe muss keine existieren. | **Stabile Mitbewohner** (nicht gebaut) |
| **Alles ist vorab bekannt** | Kommen die Fahrer nacheinander und sind Zusagen bindend, ist nur Online-Matching möglich. | **Online-Matching** (gebaut) |
| **Zwei Fahrer je Fahrt** | Größere Gruppen (Kapazitäten, b-Matching) brauchen andere Verfahren. | (nicht in der Linie) |
| **Kleine bis mittlere Graphen** | Die hier gezeigte Version ist einfach; für riesige Graphen gibt es asymptotisch schnellere Verfahren (Micali–Vazirani). | (nicht in der Linie) |
"""
)
st.caption("Die Nachbarn der Matching-Linie (noch nicht gebaut): Gewichteter Blossom und Stabile Mitbewohner. Bereits gebaut: die Wurzel (Greedy-Matching), die Verbesserungswege, Hopcroft–Karp, die Ungarische Methode, der Auktionsalgorithmus, Gale–Shapley, Online-Matching und diese Demo.")

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Ungerichteter Graph $G=(V,E)$: die Fahrer $V$, eine Kante $\{u,v\}$, wenn die Fahrzeit höchstens die Reichweite beträgt. Ein Matching $M\subseteq E$ hat keine zwei Kanten mit gemeinsamer Ecke; gesucht ist ein größtmögliches, $\nu(G)=\max|M|$.

**Berge (1957).** $M$ ist genau dann größtmöglich, wenn es keinen **$M$-augmentierenden Weg** gibt: einen einfachen Weg zwischen zwei freien Ecken, dessen Kanten abwechselnd nicht in $M$ und in $M$ liegen. Umklappen erhöht $|M|$ um eins. In zweiseitigen Graphen findet eine Breitensuche solche Wege; in allgemeinen nicht.

**Blüte.** Bei der Suche im Wald aus allen freien Ecken (gerade Ecken im Abstand gerade vom Wurzel, ungerade ungerade) schließt eine Kante zwischen zwei geraden Ecken desselben Baums einen **ungeraden Kreis** $B$ aus $2k+1$ Ecken, von denen $k$ Kanten in $M$ liegen: eine *Blüte* mit Basis $b$ (der Ecke, die im Baum am nächsten an der Wurzel liegt). **Kontraktion:** $G/B$ ersetzt $B$ durch eine Ecke, $M/B$ ist ein Matching in $G/B$.

**Satz (Edmonds 1965).** $G$ hat einen $M$-augmentierenden Weg genau dann, wenn $G/B$ einen $M/B$-augmentierenden Weg hat. Der Weg lässt sich zurückverfolgen: tritt er durch die kontrahierte Ecke, wird er in $B$ in der **Richtung mit gerader Zahl von Kanten im Inneren** aufgeklappt (eine der beiden Richtungen um den Kreis hat immer gerade Länge). Blüten können ineinander liegen.

**Tutte–Berge.** $\nu(G)=\tfrac12\min_{S\subseteq V}\bigl(|V|+|S|-\operatorname{odd}(G-S)\bigr)$, äquivalent $|V|-2\nu(G)=\max_S(\operatorname{odd}(G-S)-|S|)$, wobei $\operatorname{odd}$ die Zahl der Komponenten mit ungerader Eckenzahl ist. Die Ungleichung „$\ge$“ gilt für jedes $S$ (schwache Dualität); der Algorithmus liefert am Ende ein $S=A$ mit Gleichheit.

**Gallai–Edmonds.** Nach der erfolglosen Suche sei $D$ die Menge der geraden, $A$ die der ungeraden, $C$ die der unbeschrifteten Ecken. Dann sind alle Komponenten von $G[D]$ ungerade (**faktorkritisch**), alle von $G[C]$ gerade (perfekt zu paaren), $A=N(D)\setminus D$, und jedes größtmögliche Matching paart $A$ mit verschiedenen Komponenten von $D$ und lässt in jeder Komponente von $D$ höchstens eine Ecke frei.

**Aufwand.** Höchstens $n/2$ Verbesserungen; jede Suche sieht jede Kante höchstens zweimal und macht höchstens $O(n)$ Kontraktionen von je $O(n)$ Aufwand. Mit Mitgliederlisten je Blüte ergibt das $O(n\cdot|E|)$ (die einfache Version mit Basis-Feld für alle Ecken $O(n^3)$). Im vollständigen Graphen mit ungerader Eckenzahl braucht der Beweis $(n-1)/2$ verschachtelte Kontraktionen und genau $n(n-1)$ gesehene Kanten.

**Grenzen.** (1) Keine Gewichte. (2) Eine Gruppe: bei zwei Seiten schneller. (3) Größe statt Stabilität. (4) Alles vorab bekannt. (5) Zwei Fahrer je Fahrt. (6) Nicht für riesige Graphen optimiert.

Implementiert in `bl_scenario.py` (Karten, eigener Zufallsgenerator, feste Karten), `bl_greedy.py` (Startpaarungen), `bl_blossom.py` (Wald, Kontraktion, Aufklappen, Ereignisprotokoll, Beweis), `bl_oracle.py` (Brute Force), `bl_evaluation.py` (Kennzahlen, Verteilungen, Sweeps).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
