"""Orakel für Tests und den Beweis-Versuch in der App: Brute Force, das nichts vom Blossom-Algorithmus verwendet.

- `max_matching_size(adj)`: exakt per Bitmasken-Dynamik (Ecke mit kleinstem Index: allein lassen oder mit einem Nachbarn paaren), brauchbar bis etwa n = 20.
- `tutte_berge(adj)`: das Maximum von odd(G - S) - |S| über ALLE Teilmengen S (n <= 16); nach dem Satz von Tutte-Berge gleich n - 2 * (größtes Matching).
"""

from functools import lru_cache


def max_matching_size(adj):
    n = len(adj)
    nb = [sum(1 << j for j in adj[i]) for i in range(n)]

    @lru_cache(None)
    def f(mask):
        if mask == 0:
            return 0
        i = (mask & -mask).bit_length() - 1
        rest = mask & ~(1 << i)
        best = f(rest)
        c = nb[i] & rest
        while c:
            j = (c & -c).bit_length() - 1
            c &= c - 1
            best = max(best, 1 + f(rest & ~(1 << j)))
        return best
    return f((1 << n) - 1)


def odd_components(adj, removed):
    """Zahl der Komponenten mit ungerader Eckenzahl in G ohne die Ecken `removed`."""
    n = len(adj)
    seen = set(removed)
    odd = 0
    for s in range(n):
        if s in seen:
            continue
        seen.add(s)
        stack, size = [s], 0
        while stack:
            x = stack.pop()
            size += 1
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        odd += size % 2
    return odd


def tutte_berge(adj):
    """max_S (odd(G - S) - |S|) über alle Teilmengen S."""
    n = len(adj)
    best = -n
    for mask in range(1 << n):
        s = [i for i in range(n) if mask >> i & 1]
        best = max(best, odd_components(adj, s) - len(s))
    return best
