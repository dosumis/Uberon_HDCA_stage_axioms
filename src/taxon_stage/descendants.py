"""The set of Uberon terms that can inherit a bound from our axioms.

A scoped class for a term that is not below an axiom subject can never inherit
anything, so generating one is waste. Generating a scoped class for every
Uberon term costs 13195 classes to reach 310 -- 98% of them inert.

The subsumption that matters is `Y SubClassOf X` between **Uberon** classes.
`GEN_hs_Y SubClassOf GEN_hs_X` follows from it directly, so the scoped classes
play no part in deciding which scoped classes to make, and there is no
bootstrap: ask Uberon what the descendants are, then build exactly those.

Take the closure from a reasoner, not from asserted `is_a`. Measured against the
current table: the asserted hierarchy gives 316 descendants and the reasoned one
324, and the eight it misses -- `pharyngeal arch 7`, `trunk vertebra`, the
chorionic villus subtypes -- are subsumed through logical definitions rather
than an `is_a` line. Ubergraph's `redundant` graph already holds that closure,
so this is a query rather than a local reasoning job.

Verified lossless: the 310 terms this selects are exactly the 310 that carried a
bound when every Uberon class was scoped.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ENDPOINT = "https://ubergraph.apps.renci.org/sparql"
OBO = "http://purl.obolibrary.org/obo/"
REDUNDANT = "http://reasoner.renci.org/redundant"

# Ubergraph times out on a single query with a hundred-odd VALUES; this is the
# largest chunk that answered reliably.
CHUNK = 15


def _query(sparql: str, retries: int = 4) -> list[str]:
    import httpx
    import time

    for attempt in range(retries):
        try:
            r = httpx.post(
                ENDPOINT,
                data={"query": sparql},
                headers={"Accept": "application/sparql-results+json"},
                timeout=300,
            )
            r.raise_for_status()
        except (httpx.HTTPError, httpx.TransportError) as exc:
            if attempt == retries - 1:
                raise
            print(f"  retry {attempt + 1} after {exc}", file=sys.stderr)
            time.sleep(2**attempt)
            continue
        return [
            b["d"]["value"].removeprefix(OBO)
            for b in r.json()["results"]["bindings"]
        ]
    raise AssertionError("unreachable")


def fetch(subjects: list[str]) -> set[str]:
    """Reasoned subClassOf descendants of `subjects`, reflexively."""
    found: set[str] = set()
    ordered = sorted(subjects)
    for i in range(0, len(ordered), CHUNK):
        values = " ".join(
            f"<{OBO}{c.replace(':', '_')}>" for c in ordered[i : i + CHUNK]
        )
        found |= set(_query(f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?d WHERE {{
              VALUES ?a {{ {values} }}
              GRAPH <{REDUNDANT}> {{ ?d rdfs:subClassOf ?a . }}
              FILTER(STRSTARTS(STR(?d), "{OBO}UBERON_"))
            }}
        """))
        print(f"  {min(i + CHUNK, len(ordered))}/{len(ordered)} subjects, "
              f"{len(found)} descendants", file=sys.stderr)
    return found | {s.replace(":", "_") for s in subjects}


def load(subjects: list[str], cache: Path | None, refresh: bool = False) -> set[str]:
    """Cached because it is the build's only network dependency, and the answer
    changes only when Uberon's hierarchy or the table's subjects change. The
    cache records the subjects it was computed for, so a new axiom invalidates
    it rather than silently returning a stale, too-small set."""
    key = sorted(subjects)
    if cache and cache.exists() and not refresh:
        stored = json.loads(cache.read_text())
        if stored.get("subjects") == key:
            return set(stored["descendants"])
        print("  cached descendants were computed for different subjects; refetching",
              file=sys.stderr)
    found = fetch(key)
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(
            {"subjects": key, "descendants": sorted(found)}, indent=1))
    return found
