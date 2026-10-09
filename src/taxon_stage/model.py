"""The axiom table: its shape, and the rules that make a row well-formed.

The table is the source of truth. Everything else in this repo is generated
from it, so the checks here are the only thing standing between a typo and a
published axiom.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, fields
from pathlib import Path

OBO = "http://purl.obolibrary.org/obo/"

# Each predicate, and the onset_type it is allowed to express. The pairing is
# the whole point of recording onset_type: the curator judges the shape of the
# claim, and the predicate follows mechanically.
PREDICATES = {
    "RO:0002488": ("existence starts during", "point"),
    "RO:0002492": ("existence ends during", "point"),
    "RO:0002491": ("existence starts and ends during", "single-stage"),
    "RO:0002496": ("existence starts during or after", "interval"),
    "RO:0002497": ("existence ends during or before", "interval"),
}

# Stage ontology per taxon. A claim about a human structure against a mouse
# stage is the kind of error that reads perfectly well and is always wrong.
STAGE_ONTOLOGY_FOR_TAXON = {
    "NCBITaxon:9606": "HsapDv",
    "NCBITaxon:10090": "MmusDv",
}

CURIE = re.compile(r"^([A-Za-z][A-Za-z0-9]*):([0-9]+)$")


@dataclass(frozen=True)
class Axiom:
    uberon_id: str
    uberon_label: str
    taxon_id: str
    taxon_label: str
    onset_type: str
    predicate: str
    stage_id: str
    stage_label: str
    evidence_code: str
    evidence_text: str
    source: str
    curator: str
    date: str
    status: str

    @property
    def is_sourced(self) -> bool:
        """A row nobody has checked against anything. `curator: latent` marks a
        claim seeded from background knowledge; it is a to-do, not provenance."""
        return bool(self.source) and self.curator != "latent"


def load(path: Path) -> list[Axiom]:
    names = [f.name for f in fields(Axiom)]
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        missing = set(names) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        return [Axiom(**{n: (row.get(n) or "").strip() for n in names}) for row in reader]


def check(axioms: list[Axiom]) -> list[str]:
    """Structural problems, worst first. Identifier-resolution and label
    agreement are a separate, online check -- see validate.py."""
    problems: list[str] = []
    seen: set[tuple[str, str, str]] = set()

    for i, a in enumerate(axioms, start=2):  # row 1 is the header
        where = f"row {i} ({a.uberon_label or a.uberon_id})"

        for field_name, value in (("uberon_id", a.uberon_id), ("taxon_id", a.taxon_id),
                                  ("stage_id", a.stage_id)):
            if not CURIE.match(value):
                problems.append(f"{where}: {field_name} {value!r} is not a CURIE")

        if a.predicate not in PREDICATES:
            problems.append(f"{where}: unknown predicate {a.predicate!r}")
        else:
            _, expected = PREDICATES[a.predicate]
            if a.onset_type != expected:
                problems.append(
                    f"{where}: onset_type {a.onset_type!r} does not match predicate "
                    f"{a.predicate} ({PREDICATES[a.predicate][0]}), which expects {expected!r}"
                )

        prefix = STAGE_ONTOLOGY_FOR_TAXON.get(a.taxon_id)
        if prefix and not a.stage_id.startswith(prefix + ":"):
            problems.append(
                f"{where}: taxon {a.taxon_id} takes {prefix} stages, got {a.stage_id}"
            )
        elif not prefix:
            problems.append(f"{where}: no stage ontology registered for taxon {a.taxon_id}")

        if a.status not in ("proposed", "accepted", "superseded"):
            problems.append(f"{where}: unknown status {a.status!r}")

        if a.status == "accepted" and not a.is_sourced:
            problems.append(f"{where}: status is accepted but the claim has no source")

        # One structure may carry a start and an end, but not two starts.
        key = (a.uberon_id, a.taxon_id, a.predicate)
        if a.status != "superseded":
            if key in seen:
                problems.append(f"{where}: duplicate {a.predicate} for this structure and taxon")
            seen.add(key)

    for a in axioms:
        start = (a.uberon_id, a.taxon_id, "RO:0002488")
        loose = (a.uberon_id, a.taxon_id, "RO:0002496")
        if start in seen and loose in seen:
            problems.append(
                f"{a.uberon_label or a.uberon_id}: has both an exact and a loose start bound; "
                "pick one, they say different things"
            )
            break

    return problems
