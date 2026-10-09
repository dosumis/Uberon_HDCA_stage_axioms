"""Read Uberon's computed taxon-applicability tags.

Uberon's release workflow tags terms with `human_subset` / `mouse_subset`,
computed at build time from the taxon restriction axioms. They are not perfect
-- they are a build-time approximation, not a logical guarantee -- but they are
a reasonable guide to whether a term applies in a taxon, and they are the only
such guide available at this granularity.

Two things to know about where they live:

  * They are NOT in Ubergraph. Its `ontology` graph carries 770865 `inSubset`
    triples over 3045 subsets, and neither taxon subset is among them;
    Ubergraph ingests a Uberon product built before the tagging workflow runs.
  * They are NOT in uberon-base.owl either. They appear in the full release
    products -- uberon.obo and uberon.owl.

So this reads the OBO release directly, which is also the cheapest way to get
them: a line-oriented scan of a 21MB file rather than an OWL parse.
"""

from __future__ import annotations

import collections
from pathlib import Path

SUBSET_FOR_TAXON = {
    "NCBITaxon:9606": "human_subset",
    "NCBITaxon:10090": "mouse_subset",
}


def subset_members(obo_path: Path, subset: str) -> set[str]:
    """UBERON local ids (UBERON_0000001 form) tagged with `subset`."""
    members: set[str] = set()
    current: str | None = None
    with open(obo_path, errors="replace") as fh:
        for line in fh:
            if line.startswith("[") :
                current = None
            elif line.startswith("id: UBERON:"):
                current = line[4:].strip().replace(":", "_")
            elif current and line.startswith("subset: "):
                if line[8:].strip() == subset:
                    members.add(current)
    return members


def counts(obo_path: Path) -> dict[str, int]:
    """Every subset and how many Uberon terms carry it -- for checking that a
    requested subset exists before silently filtering everything away."""
    out: collections.Counter = collections.Counter()
    current = None
    with open(obo_path, errors="replace") as fh:
        for line in fh:
            if line.startswith("["):
                current = None
            elif line.startswith("id: UBERON:"):
                current = line[4:].strip()
            elif current and line.startswith("subset: "):
                out[line[8:].strip()] += 1
    return dict(out)
