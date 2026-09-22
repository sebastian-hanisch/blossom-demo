"""Konstanten, Regler-Grenzen, Presets und feste Seed-Mengen der Demo "Blossom"."""

# --- Regler (wie in den Vorgängerdemos) ---------------------------------------------------------------------------------
N_MIN, N_MAX, DEFAULT_N = 4, 40, 30          # Fahrer
REACH_MIN, REACH_MAX, DEFAULT_REACH = 10, 150, 20   # Reichweite in Minuten; ab 142 kann jeder jeden erreichen (vollständiger Graph)
BALLUNG_MIN, BALLUNG_MAX, DEFAULT_BALLUNG = 0, 100, 0   # ganze Prozent, Schritt 25
DEFAULT_SEED = 165
SEED_MAX = 2_000_000_000

NETS = {"random": "Zufällige Karte", "dreieck": "Dreieck mit Anhängsel (4)", "bluete": "Blüte mit Stiel (10)", "verschachtelt": "Verschachtelte Blüten (10)", "windmuehle": "Windmühle (9)", "stern": "Stern (4)"}
DEFAULT_NET = "random"
FIXED_NETS = ("dreieck", "bluete", "verschachtelt", "windmuehle", "stern")

START_LABELS = {"edge": "Greedy: billigste Kante zuerst", "order": "Greedy: Fahrer für Fahrer", "empty": "Leer"}
DEFAULT_START = "edge"
SEARCH_LABELS = {"edmonds": "Blossom (mit Kontraktion)", "nocontract": "Ohne Kontraktion (wie im zweiseitigen Fall)"}
DEFAULT_SEARCH = "edmonds"

# --- feste Seed-Mengen (dieselben wie in den Vorgängerdemos; unabhängig vom Nutzer-Seed) --------------------------------------------
DIST_SEEDS = tuple(range(100000, 100100))
SWEEP_SEEDS = DIST_SEEDS[:40]
SCALE_NS = (10, 20, 40, 80, 160, 320)
SCALE_SEEDS = DIST_SEEDS[:10]
SCALE_DEGREE_AREA = 12000                   # reach = isqrt(SCALE_DEGREE_AREA // n): etwa gleich viele Nachbarn je Fahrer bei jeder Größe
REACH_SWEEP = (10, 15, 20, 25, 30, 40, 60)
NUMBERINGS = 12                             # wie viele Umnummerierungen jeder Karte im Nummerierungs-Experiment
COMPLETE_NS = (5, 11, 17, 23, 29, 35)
BRUTE_MAX_N = 14

COLORS = {"matched": "#1f77b4", "even": "#2ca02c", "odd": "#d62728", "none": "#c8c8c8", "path": "#ff7f0e", "inner": "#9467bd", "blossom": "#7f7f7f", "tree": "#555555", "driver": "#111111"}

# --- Presets ------------------------------------------------------------------------------------------------------------------
_BASE = dict(net="random", start=DEFAULT_START, search=DEFAULT_SEARCH, n=DEFAULT_N, reach=DEFAULT_REACH, ballung=DEFAULT_BALLUNG, seed=DEFAULT_SEED)
PRESETS = {
    "🔺 Dreieck mit Anhängsel": {**_BASE, "net": "dreieck"},
    "🌸 Blüte mit Stiel": {**_BASE, "net": "bluete"},
    "🪆 Verschachtelte Blüten": {**_BASE, "net": "verschachtelt"},
    "🌀 Windmühle": {**_BASE, "net": "windmuehle"},
    "🗺️ Mittlere Karte": {**_BASE},
    "🚫 Ohne Kontraktion": {**_BASE, "search": "nocontract"},
    "🧾 Beweis": {**_BASE, "seed": 155},
    "🌐 Alles erreichbar": {**_BASE, "n": 29, "reach": 150},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py und tests/test_blossom.py belegt
PRESET_HELP = {
    "🔺 Dreieck mit Anhängsel": "Vier Fahrer: A, B und C erreichen einander (ein Dreieck), D nur B. Greedy nimmt die billigste Kante B–C und findet 1 Paar, das Optimum sind 2 (A–C und B–D). Der Weg D–B=C–A führt durch das Dreieck: die kleinste Blüte. Ohne Kontraktion bleibt die Suche bei 1 - aber nur bei manchen Nummerierungen (unter 70 von 300 zufälligen).",
    "🌸 Blüte mit Stiel": "Zehn Fahrer: ein Stiel A–B, eine Blüte aus fünf Fahrern (C bis G) und ein Ausgang D–H, danach H=I–J. Greedy findet 4 Paare, das Optimum 5. Der Weg hat 9 Kanten, 4 davon im Inneren der Blüte: er geht auf der Seite um die Blüte herum, die eine gerade Zahl von Kanten hat. Ohne Kontraktion bleibt die Suche bei 4 (unter 133 von 300 Nummerierungen).",
    "🪆 Verschachtelte Blüten": "Eine Blüte aus drei Fahrern liegt in einer größeren aus sieben (Tiefe 2), und der Verbesserungsweg mit 9 Kanten läuft durch beide. Greedy findet 4 Paare, das Optimum 5, die Suche ohne Kontraktion bleibt bei 4 - unter jeder der 300 getesteten Nummerierungen.",
    "🌀 Windmühle": "Neun Fahrer: der mittlere erreicht alle acht äußeren, die äußeren sind paarweise verbunden. Greedy findet schon das Optimum (4 Paare), aber der Beweis braucht vier ineinander verschachtelte Blüten (24 angesehene Kanten): der ganze Graph ist eine einzige Blüte, A ist leer.",
    "🗺️ Mittlere Karte": "30 Fahrer, Reichweite 20, Seed 165: Greedy findet 12 Paare, das Optimum sind 13. Eine Verbesserung mit 7 Kanten läuft durch Blüten (2 Kontraktionen, 18 angesehene Kanten). Über 100 Karten: Optimum im Mittel 13,4 (Median 13), Greedy 12,0; eine Blüte entsteht auf allen 100 Karten, der Weg läuft auf 64 durch eine.",
    "🚫 Ohne Kontraktion": "Dieselbe Karte, aber die Suche überspringt jede Kante zwischen zwei geraden Fahrern desselben Baums: sie endet bei 12 von 13 Paaren und übersieht den Weg in einer Blüte. Über 100 Karten verliert sie auf 18 (vom leeren Start auf 24), im Mittel 0,19 Paare, höchstens 2 - und auf den 82 Karten, auf denen sie richtig liegt, kann sie es nur auf 16 beweisen.",
    "🧾 Beweis": "Seed 155: Greedy findet 13 Paare, das Optimum sind 14. Nach der letzten Suche sind 2 Fahrer ungerade (A), 10 gerade (D) und 18 nicht im Wald (C). Entfernt man A, bleiben 4 ungerade Komponenten: 4 − 2 = 2 = 30 − 2 · 14. Das beweist, dass kein Matching mehr als 14 Paare hat.",
    "🌐 Alles erreichbar": "29 Fahrer, jeder erreicht jeden: Greedy findet sofort die 14 Paare des Optimums, und trotzdem braucht der Beweis 14 ineinander verschachtelte Blüten und genau 29 · 28 = 812 angesehene Kanten - auf jeder Karte. Ohne Kontraktion lässt sich hier auf keiner der 40 getesteten Karten etwas beweisen.",
}
