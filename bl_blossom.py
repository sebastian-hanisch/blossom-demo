"""Edmonds' Blossom-Algorithmus: größtmögliches Matching in einem allgemeinen Graphen (ungewichtet).

Die Suche der Verbesserungswege-Demo (Breitensuche von allen freien Ecken) ist nur auf zwei Seiten korrekt. In einem allgemeinen Graphen kann eine Kante zwei **gerade** Ecken desselben Baums verbinden:
dann schließt sie einen **ungeraden Kreis**, eine *Blüte* (Fahrer A, B, C, die einander erreichen: A=B, B-C, C-A). Ohne besondere Behandlung sieht die Suche in der Blüte je nach Nummerierung nur eine Richtung
und meldet "kein Verbesserungsweg", obwohl es einen gibt. Edmonds' Lösung: die Blüte zu **einer** Ecke zusammenziehen (kontrahieren), in dieser kleineren Struktur weitersuchen und den Weg am Ende wieder
durch die Blüte hindurch aufklappen (in der richtigen der beiden Richtungen).

Umsetzung (Wald aus allen freien Ecken, eine Verbesserung je Runde, wie die Vorgänger):
- `label` gerade / ungerade / keins, Vorgänger `p`, Wurzel `root`, Basis `base` (die Ecke, die eine Blüte im Wald vertritt), `members[base]` (Mitglieder je Basis: die Kontraktion kostet O(Größe)).
- Je gerader Ecke v und Nachbar u: Kante zählen; überspringen, wenn `base[v] == base[u]` oder u der Partner von v ist; u gerade in einem anderen Baum: **Verbesserungsweg**; u gerade im selben Baum: **Kontraktion**;
  u ungerade: überspringen; u ohne Label: u wird ungerade, sein Partner gerade.
- **Aufklappen ist implizit**: bei der Kontraktion bekommen die geraden Ecken der Blüte als Vorgänger die *gegenüberliegende* Ecke der Brücke; der Weg beim Zurücklaufen (`ptr`) geht dadurch um die Blüte herum, und
  zwar in der Richtung, die eine gerade Zahl von Kanten im Inneren hat. `lift=False` lässt das aus (Negativkontrolle: ungültige Wege).
- `search="nocontract"`: dieselbe Suche, aber ohne den Kontraktionsschritt (eine Kante zwischen zwei geraden Ecken desselben Baums wird übersprungen). Das ist die faire Baseline: sie liefert stets gültige
  Matchings, ist auf zweiseitigen Graphen optimal und in allgemeinen manchmal zu klein.

Aufwand wird gezählt (angesehene Kanten, Kontraktionen, Ecken in kontrahierten Blüten), nie in Sekunden. Alles ist ganzzahlig und deterministisch (Indexreihenfolge, FIFO-Warteschlange).
Das Ergebnis ist ein Ereignisprotokoll mit einem Schnappschuss je Ereignis (`state_at`) und am Ende ein Zertifikat (Gallai-Edmonds / Tutte-Berge, `certificate`).
"""

from collections import deque
from dataclasses import dataclass

from bl_greedy import START_EDGE, pairs_of, start_matching

NONE, EVEN, ODD = 0, 1, 2
SEARCH_EDMONDS, SEARCH_NOCONTRACT = "edmonds", "nocontract"
SEARCHES = (SEARCH_EDMONDS, SEARCH_NOCONTRACT)

EV_ROUND, EV_GROW, EV_BLOSSOM, EV_AUGMENT, EV_FAIL = "round", "grow", "blossom", "augment", "fail"


class PathError(Exception):
    """Der zurückgelaufene Weg ist kein gültiger Weg (nur bei `lift=False` zu erwarten)."""


@dataclass(frozen=True)
class Blossom:
    id: int
    round: int          # in welcher Runde (Suche) sie entstand; nach jeder Verbesserung wird der Wald neu aufgebaut
    base: int
    cycle: tuple        # Basis und die Ecken (bzw. Teilblüten, durch ihre Basis vertreten) des Kreises in Umlaufreihenfolge, ungerade Anzahl
    members: tuple      # alle Fahrer der Blüte (sortiert), auch die der enthaltenen Teilblüten
    depth: int          # 1 = keine Teilblüte
    children: tuple     # Ids der enthaltenen Teilblüten


@dataclass(frozen=True)
class Event:
    kind: str           # "round" | "grow" | "blossom" | "augment" | "fail"
    round: int
    v: int = -1         # grow: gerade Ecke, die u entdeckt; blossom: die beiden Enden der Kante zwischen zwei geraden Ecken; augment: die Enden der Kante zwischen zwei Bäumen
    u: int = -1
    w: int = -1         # grow: der Partner von u, der dadurch gerade wird
    blossom: int = -1   # blossom: Id der neuen Blüte
    path: tuple = ()    # augment: der Verbesserungsweg (Ecken)
    through: tuple = ()  # augment: ((Blüte, Eintritt, Austritt, Kanten im Inneren), ...) für jede Blüte, durch die der Weg läuft
    scanned: int = 0    # bis hierhin angesehene Kanten (kumulativ)


@dataclass(frozen=True)
class Snapshot:
    match: tuple
    label: tuple
    parent: tuple       # Vorgänger im Wald (-1: keiner)
    root: tuple         # Wurzel des Baums (-1: keine)
    blossoms: tuple     # Ids der gerade kontrahierten Blüten


@dataclass(frozen=True)
class Round:
    index: int
    scanned: int
    contractions: int
    path: tuple         # () bei der letzten, erfolglosen Suche
    pairs_after: int
    first: int          # Indizes der Ereignisse dieser Runde (first .. last, 1-basiert, einschließlich)
    last: int


@dataclass(frozen=True)
class Result:
    start: tuple        # Paare zu Beginn
    pairs: tuple        # Paare am Ende
    rounds: tuple       # alle Runden, die letzte (erfolglose) eingeschlossen
    events: tuple
    snapshots: tuple    # snapshots[k] = Zustand nach Ereignis k (k = 0: vor dem ersten Ereignis)
    blossoms: tuple
    label: tuple        # Beschriftung der letzten (erfolglosen) Suche
    scanned_total: int
    contractions: int
    contracted_vertices: int   # Summe der Größen der entstandenen Blüten (Aufwand der Kontraktionen)
    augmentations: int
    max_depth: int
    through_paths: int         # wie viele Verbesserungswege durch mindestens eine Blüte liefen
    error: str = ""            # "invalid_path", falls ein Weg ungültig war (nur bei lift=False)
    search: str = SEARCH_EDMONDS
    start_name: str = START_EDGE

    @property
    def count(self):
        return len(self.pairs)

    @property
    def n_events(self):
        return len(self.events)

    def match_list(self, n):
        m = [-1] * n
        for i, j in self.pairs:
            m[i], m[j] = j, i
        return m


class _Stats:
    def __init__(self):
        self.scanned = 0
        self.contractions = 0
        self.contracted_vertices = 0


def _valid_path(sc, match, path):
    """Ist `path` ein Verbesserungsweg? Einfach, alternierend (nicht gewählt / gewählt / ...), nur echte Kanten, beide Enden frei."""
    if len(path) < 2 or len(path) % 2 or len(set(path)) != len(path):
        return False
    if match[path[0]] >= 0 or match[path[-1]] >= 0:
        return False
    for k in range(len(path) - 1):
        a, b = path[k], path[k + 1]
        if b not in sc.adj[a]:
            return False
        if k % 2 == 1 and match[a] != b:
            return False
        if k % 2 == 0 and match[a] == b:
            return False
    return True


def flip(match, path):
    for k in range(0, len(path) - 1, 2):
        a, b = path[k], path[k + 1]
        match[a], match[b] = b, a


def _through(path, active):
    """Für jede Blüte, deren Mitglieder der Weg in mindestens einer Kante beide berührt: (Id, Eintritt, Austritt, Kanten im Inneren)."""
    out = []
    edges = list(zip(path, path[1:]))
    for b in active:
        mem = set(b.members)
        inner = sum(1 for a, c in edges if a in mem and c in mem)
        if inner:
            inside = [x for x in path if x in mem]
            out.append((b.id, inside[0], inside[-1], inner))
    return tuple(out)


def _search(sc, match, contract, lift, st, round_no, blossoms, rec, roots=None):
    """Eine Suche im Wald aus allen freien Ecken (oder `roots`). Rückgabe: (Weg oder None, Beschriftung). `rec` = None oder eine Liste, in die (Ereignis, Schnappschuss) kommen."""
    n, adj = sc.n, sc.adj
    label, p, base, root = [NONE] * n, [-1] * n, list(range(n)), [-1] * n
    members = {v: [v] for v in range(n)}
    bid = [-1] * n                                    # bid[b]: Id der Blüte mit Basis b (-1: keine)
    active = []
    queue = deque()
    for v in (range(n) if roots is None else roots):
        if match[v] < 0:
            label[v], root[v] = EVEN, v
            queue.append(v)

    def snap():
        return Snapshot(tuple(match), tuple(label), tuple(p), tuple(root), tuple(b.id for b in active))

    def emit(kind, **kw):
        if rec is not None:
            rec.append((Event(kind, round_no, scanned=st.scanned, **kw), snap()))

    def ptr(x):
        seq, guard = [x], 0
        while match[x] >= 0:
            y = match[x]
            seq.append(y)
            x = p[y]
            if x < 0:
                raise PathError("kein Vorgänger")
            seq.append(x)
            guard += 1
            if guard > n:
                raise PathError("Schleife")
        return seq

    def lca(a, b):
        used, guard = set(), 0
        while True:
            a = base[a]
            used.add(a)
            if match[a] < 0:
                break
            a = p[match[a]]
            guard += 1
            if a < 0 or guard > n:
                raise PathError("kein gemeinsamer Vorfahr")
        guard = 0
        while True:
            b = base[b]
            if b in used:
                return b
            b = p[match[b]]
            guard += 1
            if b < 0 or guard > n:
                raise PathError("kein gemeinsamer Vorfahr")

    emit(EV_ROUND)
    while queue:
        v = queue.popleft()
        for u in adj[v]:
            st.scanned += 1
            if base[v] == base[u] or match[v] == u:
                continue
            if label[u] == EVEN:
                if root[u] != root[v]:
                    path = tuple(ptr(v)[::-1] + ptr(u))
                    return path, label, (v, u, _through(path, active))
                if not contract:
                    continue
                b = lca(v, u)
                merged, cyc1, cyc2 = set(), [], []

                def mark(x, ch, cyc):
                    guard = 0
                    while base[x] != b:
                        guard += 1
                        if guard > n:
                            raise PathError("Schleife in der Blüte")
                        merged.add(base[x])
                        merged.add(base[match[x]])
                        cyc.append(base[x])
                        cyc.append(base[match[x]])
                        if lift:
                            p[x] = ch
                        ch = match[x]
                        x = p[match[x]]
                mark(v, u, cyc1)
                mark(u, v, cyc2)
                merged.discard(b)
                cycle = []
                for c in [b] + cyc1[::-1] + cyc2:                # der Weg läuft über Ecken; mehrere Schritte in derselben Teilblüte zählen als eine Ecke des Kreises
                    if not cycle or cycle[-1] != c:
                        cycle.append(c)
                mem = list(members[b])
                for c in sorted(merged):
                    mem += members[c]
                children = tuple(bid[c] for c in cycle if bid[c] >= 0)
                depth = 1 + max((blossoms[i].depth for i in children), default=0)
                blo = Blossom(len(blossoms), round_no, b, tuple(cycle), tuple(sorted(mem)), depth, children)
                blossoms.append(blo)
                active.append(blo)
                bid[b] = blo.id
                st.contractions += 1
                st.contracted_vertices += len(mem)
                for c in sorted(merged):
                    for i in members[c]:
                        base[i] = b
                        if label[i] != EVEN:
                            label[i], root[i] = EVEN, root[b]
                            queue.append(i)
                    members[b] += members[c]
                    del members[c]
                    bid[c] = -1
                emit(EV_BLOSSOM, v=v, u=u, blossom=blo.id)
            elif label[u] == ODD:
                continue
            else:
                if match[u] < 0:                               # freier Fahrer ohne Label (nur bei einer Wurzel-Suche)
                    path = tuple(ptr(v)[::-1] + [u])
                    return path, label, (v, u, _through(path, active))
                label[u], p[u], root[u] = ODD, v, root[v]
                w = match[u]
                label[w], root[w] = EVEN, root[v]
                queue.append(w)
                emit(EV_GROW, v=v, u=u, w=w)
    return None, label, None


def run(sc, start=START_EDGE, search=SEARCH_EDMONDS, record=True, lift=True):
    """Größtmögliches Matching durch Verbesserungswege ab `start` (leer, Greedy edge / order). Rückgabe `Result`."""
    contract = search == SEARCH_EDMONDS
    match = start_matching(sc, start)
    start_pairs = pairs_of(match)
    st = _Stats()
    blossoms, rec, rounds, snaps = [], ([] if record else None), [], []
    if record:
        snaps.append(Snapshot(tuple(match), (NONE,) * sc.n, (-1,) * sc.n, (-1,) * sc.n, ()))
    events = []
    augs = thr = max_depth = 0
    label, error = (NONE,) * sc.n, ""
    r = 0
    while True:
        r += 1
        first, scan0, con0 = len(events) + 1, st.scanned, st.contractions
        rec_r = [] if record else None
        try:
            path, label, info = _search(sc, match, contract, lift, st, r, blossoms, rec_r)
        except PathError:
            path, label, info, error = None, (NONE,) * sc.n, None, "invalid_path"
        if record:
            for e, s in rec_r:
                events.append(e)
                snaps.append(s)
        if error:
            break
        if path is None:
            if record:
                events.append(Event(EV_FAIL, r, scanned=st.scanned))
                snaps.append(Snapshot(tuple(match), tuple(label), snaps[-1].parent if snaps else (-1,) * sc.n, snaps[-1].root if snaps else (-1,) * sc.n, snaps[-1].blossoms if snaps else ()))
            rounds.append(Round(r, st.scanned - scan0, st.contractions - con0, (), sum(1 for x in match if x >= 0) // 2, first, len(events)))
            break
        if not _valid_path(sc, match, path):
            error = "invalid_path"
            break
        v, u, through = info
        if record:
            events.append(Event(EV_AUGMENT, r, v=v, u=u, path=path, through=through, scanned=st.scanned))
            last_snap = snaps[-1]
            flipped = list(match)
            flip(flipped, path)
            snaps.append(Snapshot(tuple(flipped), last_snap.label, last_snap.parent, last_snap.root, last_snap.blossoms))
        flip(match, path)
        augs += 1
        thr += bool(through)
        rounds.append(Round(r, st.scanned - scan0, st.contractions - con0, path, sum(1 for x in match if x >= 0) // 2, first, len(events)))
    max_depth = max((b.depth for b in blossoms), default=0)
    return Result(start_pairs, pairs_of(match), tuple(rounds), tuple(events), tuple(snaps), tuple(blossoms), tuple(label), st.scanned, st.contractions, st.contracted_vertices,
                  augs, max_depth, thr, error, search, start)


def run_single_root(sc, start=START_EDGE, contract=False):
    """Variante à la Kuhn: eine Suche je freier Wurzel (jede Wurzel einmal). Rückgabe (Paare, angesehene Kanten). Nur für den Vergleich der Suchvarianten."""
    match = start_matching(sc, start)
    st = _Stats()
    for r in range(sc.n):
        if match[r] >= 0:
            continue
        try:
            path, _label, _info = _search(sc, match, contract, True, st, 0, [], None, roots=[r])
        except PathError:
            continue
        if path is not None and _valid_path(sc, match, path):
            flip(match, path)
    return pairs_of(match), st.scanned


def state_at(res, k):
    """Zustand nach Ereignis k (k = 0: Startpaarung, noch keine Suche): Schnappschuss und die zugehörigen Blüten."""
    snap = res.snapshots[k]
    return snap, tuple(res.blossoms[i] for i in snap.blossoms)


# --- Beweis: Gallai-Edmonds / Tutte-Berge ------------------------------------------------------------------------------------------

def _components(adj, verts):
    """Zusammenhangskomponenten des von `verts` induzierten Teilgraphen (Listen von Ecken)."""
    vs = set(verts)
    seen, comps = set(), []
    for s in sorted(vs):
        if s in seen:
            continue
        seen.add(s)
        stack, comp = [s], []
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if y in vs and y not in seen:
                    seen.add(y)
                    stack.append(y)
        comps.append(sorted(comp))
    return comps


def certificate(sc, pairs, label):
    """Beweis aus der Beschriftung der letzten erfolglosen Suche: D = gerade, A = ungerade, C = ohne Label.
    Tutte-Berge: für jede Ecken-Menge S gilt  n - 2|M| >= odd(G - S) - |S|.  Gilt bei S = A Gleichheit, ist das Matching bewiesen größtmöglich (schwache Dualität).
    Gallai-Edmonds-Struktur zusätzlich: alle Komponenten von G[D] ungerade, alle von G[C] gerade, keine Kante zwischen D und C."""
    n = sc.n
    D = tuple(v for v in range(n) if label[v] == EVEN)
    A = tuple(v for v in range(n) if label[v] == ODD)
    C = tuple(v for v in range(n) if label[v] == NONE)
    comps_d = _components(sc.adj, D)
    comps_c = _components(sc.adj, C)
    rest = _components(sc.adj, [v for v in range(n) if v not in set(A)])
    odd_after = sum(1 for c in rest if len(c) % 2)
    deficiency = n - 2 * len(pairs)
    dset, cset = set(D), set(C)
    no_dc = not any(u in cset for v in D for u in sc.adj[v])
    return {"D": D, "A": A, "C": C, "comps_D": tuple(len(c) for c in comps_d), "comps_C": tuple(len(c) for c in comps_c), "odd_after_A": odd_after, "deficiency": deficiency,
            "holds": odd_after - len(A) == deficiency, "d_odd": all(len(c) % 2 for c in comps_d), "c_even": all(len(c) % 2 == 0 for c in comps_c), "no_dc_edge": no_dc,
            "ge_ok": all(len(c) % 2 for c in comps_d) and all(len(c) % 2 == 0 for c in comps_c) and no_dc}
