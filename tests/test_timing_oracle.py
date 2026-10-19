"""Property test: datalog/timing.dl against brute-force enumeration.

The oracle shares no code with the reasoner. It restates the semantics table
of docs/timing-individuals.md §3 as predicates over integer time and tries
every placement of every start and end point on a grid:

    region 0      before T1        [0,  K)
    regions 1-3   stages T1..T3    [iK, (i+1)K)
    region 4      after T3         [4K, 5K)

With n structures there are 2n points; K = 2n + 1 leaves room for all of them
to sit strictly inside one region in any order, so the grid loses no solution
the dense timeline has. The network is consistent iff some placement satisfies
everything, and a point's tightest bounds are the first and last region it
can occupy.
"""


import random

import pytest

from test_timing import INPUTS, run, rows, shutil

STAGES = ["T1", "T2", "T3"]
BOUND_PREDS = ["RO:0002488", "RO:0002496", "RO:0002492", "RO:0002497", "RO:0002491"]
RELS = ["RO:0002202", "RO:0002207", "RO:0002494", "RO:0002495", "BFO:0000050"]


def satisfied(n, K, bounds, edges, singletons, place):
    """The semantics table, as a check on one placement. place[x] = (s, e)."""
    def start(t): return (STAGES.index(t) + 1) * K
    def end(t): return (STAGES.index(t) + 2) * K
    for x, p, t in bounds:
        s, e = place[x]
        ok = {
            "RO:0002488": start(t) <= s < end(t),
            "RO:0002496": start(t) <= s,
            "RO:0002492": start(t) <= e < end(t),
            "RO:0002497": e < end(t),
            "RO:0002491": start(t) <= s and e <= end(t),
        }[p]
        if not ok:
            return False
    for x, r, y in edges:
        (sx, ex), (sy, ey) = place[x], place[y]
        single = y in singletons
        ok = {
            "RO:0002202": sy < sx,
            "RO:0002207": sy < sx <= ey,
            "RO:0002494": ey <= sx if single else sy < sx,
            "RO:0002495": ey == sx if single else sy < sx <= ey,
            "BFO:0000050": sy <= sx and ex <= ey,
        }[r]
        if not ok:
            return False
    return True


def oracle(n, bounds, edges, singletons):
    """Return None if inconsistent, else {(x, which): (first, last) region}."""
    K = 2 * n + 1
    names = [f"X{i}" for i in range(n)]
    pairs = [(s, e) for s in range(5 * K) for e in range(s + 1, 5 * K)]
    # Bounds involve one structure: prune its placements before the product.
    own = {x: [pe for pe in pairs
               if satisfied(n, K, [b for b in bounds if b[0] == x], [], singletons,
                            {x: pe})]
           for x in names}
    seen = {(x, w): set() for x in names for w in ("start", "end")}
    found = False

    # Exhaustive search, checking each edge as soon as both its ends are placed.
    def extend(i, place):
        nonlocal found
        if i == n:
            found = True
            for x, (s, e) in place.items():
                seen[(x, "start")].add(s // K)
                seen[(x, "end")].add(e // K)
            return
        x = names[i]
        here = [ed for ed in edges if x in ed[::2] and set(ed[::2]) <= set(names[:i + 1])]
        for pe in own[x]:
            place[x] = pe
            if satisfied(n, K, [], here, singletons, place):
                extend(i + 1, place)
        place.pop(x, None)

    extend(0, {})
    if not found:
        return None
    return {k: (min(v), max(v)) for k, v in seen.items()}


def network(rng, n):
    names = [f"X{i}" for i in range(n)]
    density = 0.4 if n == 2 else 0.25
    while True:
        bounds = [(x, rng.choice(BOUND_PREDS), rng.choice(STAGES))
                  for x in names for _ in range(rng.choice([0, 1, 1, 2]))]
        # Keep the brute force affordable: at most one unbounded structure.
        if sum(1 for x in names if not any(b[0] == x for b in bounds)) <= 1:
            break
    edges = [(x, rng.choice(RELS), y)
             for x in names for y in names if x != y and rng.random() < density]
    singletons = {x for x in names if rng.random() < 0.5}
    return names, bounds, edges, singletons


def write_facts(facts, names, bounds, edges, singletons):
    facts.mkdir(parents=True)
    for name, header in INPUTS.items():
        (facts / name).write_text(header)
    with (facts / "stage_rel.csv").open("a") as f:
        f.write("T2,RO:0002087,T1,s2\nT3,RO:0002087,T2,s3\n")
    with (facts / "seed.csv").open("a") as f:
        f.writelines(f"{x}\n" for x in names)
    with (facts / "bound.csv").open("a") as f:
        f.writelines(f"{x},{p},{t},b{i}\n" for i, (x, p, t) in enumerate(bounds))
    with (facts / "edge.csv").open("a") as f:
        f.writelines(f"{x},{r},{y},r{i}\n" for i, (x, r, y) in enumerate(edges))
    with (facts / "individuate.tsv").open("a") as f:
        f.writelines(f"{x}\t{x}\tsingleton\ttest\t2026-10-19\t\n" for x in singletons)


CASES = [(n, seed) for n in (2,) for seed in range(120)] + \
        [(3, seed) for seed in range(60)]


@pytest.mark.skipif(shutil.which("souffle") is None, reason="souffle not on PATH")
@pytest.mark.parametrize("n,seed", CASES, ids=[f"n{n}-{s}" for n, s in CASES])
def test_matches_oracle(n, seed, tmp_path):
    rng = random.Random(seed)
    names, bounds, edges, singletons = network(rng, n)
    expected = oracle(n, bounds, edges, singletons)

    write_facts(tmp_path / "facts", names, bounds, edges, singletons)
    out = run(tmp_path / "facts", tmp_path / "out")
    conflicted = rows(out / "in_conflict.csv")
    explanations = rows(out / "conflict.csv") | rows(out / "cycle.csv")
    # The frame here is totally ordered, so every conflict must be explained.
    assert not rows(out / "unexplained.csv"), "conflict left unexplained"

    if expected is None:
        assert conflicted and explanations, \
            f"oracle: inconsistent; datalog found no conflict\n{bounds}\n{edges}"
        return
    assert not conflicted and not explanations, \
        f"oracle: consistent; datalog reported {sorted(explanations)}"

    lower = {(x, w): t for x, w, t, _ in rows(out / "lower_bound.csv")}
    upper = {(x, w): t for x, w, t, _ in rows(out / "upper_bound.csv")}
    for key, (first, last) in expected.items():
        # lower: the latest stage whose start the point is always at or after;
        # a point always beyond T3 is still reported against T3. upper: the
        # earliest stage whose end it is always before; likewise T1.
        want_lo = STAGES[min(first, 3) - 1] if first >= 1 else None
        want_up = STAGES[max(last, 1) - 1] if last <= 3 else None
        assert lower.get(key) == want_lo, f"{key} lower: oracle {want_lo}, datalog {lower.get(key)}"
        assert upper.get(key) == want_up, f"{key} upper: oracle {want_up}, datalog {upper.get(key)}"
