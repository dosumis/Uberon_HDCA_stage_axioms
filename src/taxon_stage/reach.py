"""Measure what the axioms actually reach once Uberon's hierarchy is applied.

The point of scoped classes is that a bound on a parent is inherited by every
child. This counts that: how many Uberon terms end up carrying an HsapDv bound,
against how many we wrote one for.

Reads relation-graph TSV output. Only HsapDv-valued triples count -- Uberon
carries its own species-neutral existence axioms, and the merged ontology
materialises those too, so a scoped class having *a* bound says nothing.
"""

from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

UBERON_IN_IRI = re.compile(r"UBERON[:_](\d+)")


def asserted_structures(table: Path) -> set[str]:
    with open(table, newline="") as fh:
        return {r["uberon_id"].replace(":", "_")
                for r in csv.DictReader(fh, delimiter="\t")
                if r["status"] != "superseded"}


def measure(rg_tsv: Path, table: Path) -> dict:
    asserted = asserted_structures(table)
    bounds: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    for line in open(rg_tsv):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3 or not parts[2].startswith("HsapDv:"):
            continue
        m = UBERON_IN_IRI.search(parts[0])
        if m:
            bounds[f"UBERON_{m.group(1)}"].add((parts[1], parts[2]))
    reached = set(bounds)
    facts = sum(len(v) for v in bounds.values())
    return {
        "asserted_structures": len(asserted),
        "reached_structures": len(reached),
        "inherited_structures": len(reached - asserted),
        "facts": facts,
    }


def main() -> int:
    rg_tsv, table = Path(sys.argv[1]), Path(sys.argv[2])
    m = measure(rg_tsv, table)
    print(f"structures with an asserted axiom : {m['asserted_structures']}")
    print(f"structures carrying an HsapDv bound: {m['reached_structures']}")
    print(f"  of which inherited               : {m['inherited_structures']}")
    print(f"total (term, predicate, stage) facts: {m['facts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
