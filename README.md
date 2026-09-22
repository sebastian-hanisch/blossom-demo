# Blossom – Paare in einem Graphen ohne zwei Seiten – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-edmonds-matching-demo.streamlit.app/)**

Achtes Stück der **Matching-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", ein **unabhängiger Ast unter den Verbesserungswegen** ([augmenting-path-demo](https://github.com/sebastian-hanisch/augmenting-path-demo)):
anders als die Fall-Demos im Portfolio (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt diese Demo **ein** Verfahren – **Edmonds' Blossom-Algorithmus** – an einem wachsenden Beispiel.
In den bisherigen Stücken gab es zwei Seiten (Fahrzeuge und Aufträge). Hier gibt es **eine Gruppe von Fahrern**: je zwei können zusammen fahren (Fahrgemeinschaften), wenn ihre Fahrzeit höchstens die Reichweite beträgt – ein **allgemeiner Graph** mit **ungeraden Kreisen** („Blüten“).
Die Suche der Verbesserungswege-Demo ist dort nicht mehr korrekt; Blossom zieht jede Blüte zu einer Ecke zusammen, sucht weiter, klappt den Weg wieder auf und liefert am Ende einen **Beweis** (Tutte–Berge / Gallai–Edmonds). Gesucht ist ein größtmögliches ungewichtetes Matching; **Gewichte** (billigste Paarung) sind das nächste Stück, der Gewichtete Blossom.

**Wichtigster Befund der Vorarbeit:** die Geschichte „ohne Blüten verliert die Suche viele Paare“ ist auf realistischen Karten **schwächer, als sie klingt**. Die faire Baseline ist Edmonds' Waldsuche **ohne den Kontraktionsschritt** (die wörtliche Breitensuche der Zweiseiten-Demo liefert auf einem allgemeinen Graphen nicht einmal gültige Wege, das wäre ein Strohmann): sie verliert Paare nur auf einem Teil der Karten, meist eines, und der Verlust hängt an der Nummerierung der Fahrer. Der **stärkere Befund** ist der Beweis: ohne Kontraktion lässt sich selbst ein *richtiges* Ergebnis fast nie beweisen. Deshalb ist der Vergleich eine **Leiter mit vier Stufen**.

**Einordnung in die Reihe (die Kanten des Graphen):** dieses Stück lockert die Annahme „zwei getrennte Seiten“ der Verbesserungswege. Seine eigenen Schwächen sind die Ansatzpunkte des nächsten Stücks: keine Gewichte (**Gewichteter Blossom**: Ungarisch + Blossom).
```
greedy-matching-demo (Wurzel: eine gewählte Zuordnung bleibt)                     [gebaut]
  ├─ augmenting-path-demo (Verbesserungswege: Paare optimal, Kosten blind)        [gebaut]
  │    ├─ hopcroft-karp-demo (viele kürzeste Wege je Phase)                       [gebaut]
  │    ├─ hungarian-demo (Ungarische Methode: Paare zuerst, dann Kosten)           [gebaut]
  │    │    └─ auction-algorithm-demo (Auktionsalgorithmus: dezentral)             [gebaut]
  │    └─ blossom-demo (allgemeine Graphen: ungerade Kreise, Kontraktion)          [dieses Stück]
  │   Ungarisch + Blossom → Gewichteter Blossom (Konvergenz)                       [nicht gebaut]
  ├─ gale-shapley-demo (Vorlieben statt Kosten, stabil)                            [gebaut]
  │    └─ Stabile Mitbewohner                                                      [nicht gebaut]
  └─ online-matching-demo (Aufträge kommen nacheinander)                           [gebaut]
```

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` (und, wo es feste Karten sind, in `tests/test_blossom.py`) über die 100 festen Karten (Seeds 100000–100099) belegt: 30 Fahrer, Reichweite 20 (mittlerer Grad 2,97), Greedy-Start „billigste Kante zuerst“, wo nichts anderes steht. Aufwand = **angesehene Kanten**, nie Sekunden (jede Kante wird von beiden Enden gesehen). Mittel und Median stehen zusammen.

| Frage | Ergebnis |
|---|---|
| Die Karten | ⚠️ Optimum im Mittel **13,37** Paare (Median 13, 11 bis 15), Greedy 12,04 (Median 12). Greedy ist auf **84 von 100** Karten nicht optimal (Fahrer für Fahrer: 81), ein perfektes Matching gibt es auf 4. Im Mittel 1,77 Fahrer ohne mögliches Paar (Median 1, höchstens 7). |
| Stufe 1: es gibt eine Blüte | ✅ Auf **allen 100** Karten wird eine Blüte kontrahiert (im Mittel 6,83, Median 6,5, höchstens 16; Tiefe im Mittel 2,85, höchstens 8). |
| Stufe 2: der Weg läuft durch eine | ⚠️ Nur auf **64 von 100** Karten (Weg-Länge im Mittel 4,49 Kanten, Median 3, höchstens 15; 133 Wege). Im Mittel 1,33 Verbesserungen ab Greedy (Median 1, höchstens 4). |
| Stufe 3: ohne Kontraktion gehen Paare verloren | ❌ Nur auf **18 von 100** Karten (vom leeren Start: 24; Fahrer für Fahrer: 23), im Mittel 0,19 Paare, höchstens 2 – **1,4 % der Paare**. Auf 82 Karten findet auch die Suche ohne Kontraktion das Optimum. |
| Stufe 4: aber sie kann es nicht beweisen | ✅ Von diesen 82 richtigen Ergebnissen lässt sich das Optimum nur auf **16** beweisen (leerer Start: 13 von 76, Fahrer für Fahrer: 14 von 77). Blossom beweist es auf **allen 100**. Nicht verallgemeinern: auf dichten Karten (n = 30, Reichweite 40, mittlerer Grad 10) liegt die Suche ohne Kontraktion auf 99 Karten richtig und beweist es auf 98. |
| Es ist zum Teil Zufall der Nummerierung | ⚠️ Dieselben 100 Graphen unter 12 zufälligen Nummerierungen: **43** Karten verlieren unter mindestens einer, **keine unter allen 12**, 15,75 % der (Karte, Nummerierung)-Paare. Alle freien Fahrer als Wurzeln (wie die Vorgänger-BFS) verlieren auf 18 Karten, eine Wurzel nach der anderen (Kuhn) nur auf **3** (leerer Start: 24 gegen 2). |
| Der Beweis (Gallai–Edmonds) | ✅ Nach der letzten Suche: D (gerade) im Mittel 12,45 (Median 13, höchstens 28), A (ungerade) 2,09 (Median 2, höchstens 7; **leer auf 29 Karten**), C 15,46 (Median 14); D zerfällt im Mittel in 5,35 Komponenten. Die Tutte–Berge-Gleichung gilt auf allen 100 Karten. |
| Aufwand: Greedy-Start | ⚠️ Die Zahl der Verbesserungen geht um den Faktor **10** zurück (13,37 → 1,33), die angesehenen Kanten aber nur um **33 %** (78,45 → 52,32; Median 76 → 50); bei n = 320 nur um 25 % (Verbesserungen ÷ 8,7). Ohne Kontraktion sind es weniger Kanten (37,5), weil die Suche früher aufhört. |
| Aufwand gegen Größe | ⚠️ n = 10 / 40 / 160 / 320 (mittlerer Grad etwa 3, 10 Karten): **18 / 125 / 824 / 2 969** Kanten vom leeren Start, 11 / 93 / 634 / 2 234 vom Greedy-Start, etwa n^1,5; Kanten je Kante von 0,8 auf 4,1. Ohne Kontraktion verlieren bei n = 320 7 von 10 Karten Paare (im Mittel 1,8), bei n = 10 nur 1 (0,1). |
| Reichweite | ✅ Ein **Buckel** (n = 30, 40 Karten): bei Reichweite 10 / 20 / 30 / 40 / 60 (Grad 0,8 / 3,0 / 6,1 / 10,0 / 17,6) verliert die Suche ohne Kontraktion auf 3 / **10** / 1 / 0 / 0 Karten; Blüten kontrahiert auf 27 / 40 / 40 / 36 / 24, Weg durch Blüte auf 5 / 27 / 35 / 29 / 17. Dünne Graphen sind fast Bäume, dichte schafft Greedy fast perfekt. Mehr Ballung hilft der Baseline (24 → 2 Karten bei 100 %). |
| Der vollständige Graph | ✅ n ungerade, jeder erreicht jeden: Greedy ist sofort optimal, aber der Beweis braucht **(n − 1)/2 ineinander verschachtelte Blüten** und genau **n (n − 1)** angesehene Kanten (n = 5 / 11 / 29 / 35: 20 / 110 / 812 / 1 190) – auf jeder Karte; ohne Kontraktion beweisbar auf 0 von 40. Gerade n: 0 angesehene Kanten. |
| Feste Karten | ✅ Dreieck mit Anhängsel (Greedy 1, Optimum 2), Blüte mit Stiel (4 / 5, Weg 9 Kanten, 4 im Inneren), verschachtelte Blüten (4 / 5, Tiefe 2), Windmühle (4 / 4, Tiefe 4, 24 Kanten, A leer), Stern (D = 3 Fahrer, A = 1). Ohne Kontraktion enden die drei ersten bei (1, 4, 4) statt (2, 5, 5). |

## Was nicht funktioniert hat / widerlegte Vorab-Hypothesen

- **„Die Suche der Vorgänger scheitert in Blüten – also nehmen wir sie als Baseline.“** Nein: wörtlich auf die symmetrische Adjazenz übertragen liefert die Breitensuche auf 98 von 100 Karten (n = 30, Reichweite 20, Greedy-Start) einen **Weg mit doppelter Ecke**, keinen gültigen. Die faire Baseline ist Edmonds' Waldsuche ohne den Kontraktionsschritt: stets gültig, auf 400 zufälligen zweiseitigen Graphen optimal (Test), auf allgemeinen manchmal zu klein.
- **„Ohne Blüten verliert die Suche viele Paare.“** Nein: auf nur 18 von 100 Karten, meist eines, ≈ 1,4 % der Paare, und unter den meisten Nummerierungen gar keines.
- **„Die Falle hängt nicht an der Nummerierung.“** Doch: von 300 zufälligen Nummerierungen fängt sie die Baseline auf dem Dreieck 70-mal, auf der Blüte mit Stiel 133-mal und nur auf den **verschachtelten Blüten jedes Mal** (Greedy-Start).
- **„Blüten sind selten.“** Nein: sie werden auf allen 100 Karten kontrahiert; nur der Weg läuft nicht immer durch eine.
- **„Petersen ist der Worst Case.“** Nicht realisierbar: keine Punktmenge mit Schwellenwert ergibt ihn, und er hat ein perfektes Matching. Worst Case sind die **Windmühle** (eine einzige Blüte aus lauter Blüten) und der **vollständige Graph**.
- **„Greedy-Start spart Aufwand.“** Bei den Verbesserungen ja (÷ 10), bei den angesehenen Kanten nur ein Drittel: die letzte, erfolglose Suche und die breiten frühen Suchen dominieren.
- **„Ohne Kontraktion gibt es keinen Beweis.“** Meist, aber nicht immer: auf 16 der 82 richtigen Karten gelingt er, auf dichten Karten (n = 30, Reichweite 40) auf 98 von 99.
- **Abgrenzung:** Blossom = networkx (`max_weight_matching(maxcardinality=True)`) = Brute Force auf jedem getesteten Graphen (1 500 Läufe auf Karten und Zufallsgraphen G(n, p), Brute Force bis n = 14, alle drei Starts); Tutte–Berge per Brute Force über alle Teilmengen; die Mengen D und A gleich ihrer Brute-Force-Definition (420 Läufe). Negativkontrolle: ohne das Aufklappen (`lift=False`) ist der Weg auf 52 von 100 Karten ungültig.

## Was die Demo zeigt

- **Suche und Ablauf:** Schritt-Slider und ▶️ über die **Ereignisse** (Runde beginnt, Fahrer entdeckt, Blüte gefunden, Weg umgeklappt): die Karte mit dem Wald (gerade grün, ungerade rot), den gewählten Paaren, den Blüten als **durchscheinenden konvexen Hüllen** (verschachtelt = dunkler, Basis mit Ring; die Karte bleibt erhalten, statt die Blüte zu einem Punkt zu schrumpfen) und dem Verbesserungsweg (Stücke im Inneren einer Blüte in zweiter Farbe – der Umweg gerader Länge); daneben der Verlauf und die Blütentabelle; am Ende der **Beweis** mit D, A, C und der Tutte–Berge-Gleichung. Umschalter für den Start (leer / Greedy) und die Suche (Blossom / ohne Kontraktion, ebenfalls Schritt für Schritt).
- **Wie gut?** Paare, Verbesserungen und Weglängen, Blüten und Tiefe, angesehene Kanten; Vergleichstabelle (beide Greedy, Blossom, ohne Kontraktion) mit „Optimalität beweisbar“; Verteilung über 100 feste Karten (Mittel, Median, Verlust), die **Vier-Stufen-Leiter** und die drei Starts.
- **Wovon hängt es ab?** Aufwand gegen Größe (n = 10 bis 320), „Andere Nummerierung“ (12 Nummerierungen, beide Suchvarianten), Reichweiten-Sweep, der vollständige Graph, Brute-Force-Beweis auf 20 kleinen Karten.
- **Feste Karten:** Dreieck mit Anhängsel, Blüte mit Stiel, verschachtelte Blüten, Windmühle, Stern; **Wo die Annahmen enden.**

## Modell und Verfahren

- **Graph:** Fahrer als Punkte auf der 100 × 100-Karte, Kante bei aufgerundeter Fahrzeit ≤ Reichweite (ganzzahlig per `isqrt`). Eine Gruppe, keine zwei Seiten. Die Karte hat einen eigenen Zufallsgenerator (`SplitMix64`, eine Punktmenge).
- **Blossom (`bl_blossom.py`):** Wald aus allen freien Fahrern, eine Verbesserung je Runde. `label` (gerade / ungerade / keins), Vorgänger `p`, Wurzel `root`, Basis `base`, `members[base]` (die Kontraktion kostet O(Größe)). Je gerader Ecke v und Nachbar u: Kante zählen; überspringen bei gleicher Basis oder Partner; u gerade in einem **anderen** Baum → Verbesserungsweg; u gerade im **selben** Baum → **Kontraktion** (gemeinsamer Vorfahr, beide Seiten bis zur Basis, Vorgänger der geraden Ecken auf die gegenüberliegende Brückenecke setzen, Mitglieder umbasieren, ungerade Mitglieder werden gerade); u ungerade → überspringen; u ohne Label → ungerade, sein Partner gerade. **Aufklappen ist implizit** (das Umsetzen der Vorgänger).
- **Baseline:** dieselbe Suche, Kante zwischen zwei geraden Ecken desselben Baums wird übersprungen.
- **Beweis:** D = gerade, A = ungerade, C = ohne Label. Gilt bei S = A `odd(G − S) − |S| = n − 2 · Paare`, ist das Matching (schwache Dualität, Tutte–Berge) bewiesen größtmöglich; Struktur: Komponenten von G[D] ungerade, von G[C] gerade, keine D–C-Kante.
- **Aufwand:** drei Zähler (angesehene Kanten, Kontraktionen, Ecken in kontrahierten Blüten), nie Sekunden; Theorie O(n · |E|) mit Mitgliederlisten, die einfache Basis-Feld-Version O(n³).

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `bl_constants.py` | Regler-Grenzen, Presets und Hilfetexte, feste Seed-Mengen |
| `bl_presets.py` | Permalink, Preset- und Zufalls-Seed-Logik (Standardmuster des Portfolios, kopiert und um Start und Suche ergänzt) |
| `bl_scenario.py` | Fahrer-Karten, eigener Zufallsgenerator (aus den Vorgängerdemos kopiert, jetzt mit einer Punktmenge), Umnummerierung, die festen Lehrbuchkarten |
| `bl_greedy.py` | **Neu:** Startpaarungen (leer, Greedy billigste Kante, Greedy Fahrer für Fahrer) |
| `bl_blossom.py` | **Neu:** Blossom (Wald, Kontraktion, Aufklappen), Baseline ohne Kontraktion, Ereignisprotokoll mit Schnappschüssen, Beweis |
| `bl_oracle.py` | **Neu:** Brute Force (Bitmasken-Dynamik, alle Teilmengen für Tutte–Berge) für Tests und den Beweis-Versuch in der App |
| `bl_evaluation.py` | Einordnung, Vergleichstabelle, Verteilung, Leiter, Nummerierungs-Experiment, Sweeps, Aufwand, vollständiger Graph |
| `bl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt für Touch-Geräte; keine Legende auf den Karten, `constrain="domain"`) |
| `tests/` | Algorithmus (unabhängiger Prüfer je Verbesserung, networkx, Brute Force, Tutte–Berge, Gallai–Edmonds, feste Karten, Negativkontrollen), Auswertung, Presets, belegte Zahlen, AppTest-Rauchtests (auch Abspielen auf mehrbildrigen Karten für jede Kombination aus Start und Suche) |

Die kopierten Bausteine werden durch Tests bewacht (Zufallsgenerator-Vektor, eine festgeschriebene Punktliste). Alle Daten sind synthetisch; die Laufzeit braucht nur numpy, pandas, plotly und streamlit (scipy und networkx sind reine Testorakel).

## Lokal starten

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\streamlit run app.py
```

## Tests ausführen

```bash
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\python -m pytest tests -v
```

Die Logik rechnet ausschließlich mit ganzen Zahlen; die im Text genannten Anteile und Mittelwerte sind deshalb auf jeder Plattform identisch.
Die CI (`.github/workflows/tests.yml`) läuft auf Ubuntu mit Python 3.12, bei jedem Push und wöchentlich mit den jeweils neuesten Bibliotheksversionen.
