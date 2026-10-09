"""Package the axioms as a contribution to Uberon.

The GCIs are already what Uberon would take -- `build` emits them with their
evidence as axiom annotations. What this adds is selection and a review
artefact: a curator cannot review Manchester syntax at volume, so the same rows
go out as a table beside the OWL.

Default is sourced rows only. An unsourced claim is a to-do, and shipping 114
of them beside 60 checked ones makes the checked ones harder to trust rather
than the batch larger.
"""

from __future__ import annotations

import csv
from pathlib import Path

from .build import render
from .model import Axiom, PREDICATES


def selected(axioms: list[Axiom], sourced_only: bool = True) -> list[Axiom]:
    live = [a for a in axioms if a.status != "superseded"]
    return [a for a in live if a.is_sourced] if sourced_only else live


def review_table(axioms: list[Axiom], path: Path) -> None:
    """One row per proposed axiom, in the order a reviewer would read them:
    grouped by structure, with the evidence quote beside the claim it supports."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["uberon_id", "uberon_label", "taxon", "claim",
                    "stage_id", "stage_label", "evidence", "evidence_code", "source"])
        for a in sorted(axioms, key=lambda a: (a.uberon_label, a.predicate)):
            w.writerow([a.uberon_id, a.uberon_label, a.taxon_label,
                        PREDICATES[a.predicate][0], a.stage_id, a.stage_label,
                        a.evidence_text, a.evidence_code, a.source])


def write(axioms: list[Axiom], out_dir: Path, sourced_only: bool = True) -> dict:
    chosen = selected(axioms, sourced_only)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "uberon-human-stage-gcis.ofn").write_text(
        render(chosen, for_contribution=True))
    review_table(chosen, out_dir / "review.tsv")
    return {
        "axioms": len(chosen),
        "structures": len({a.uberon_id for a in chosen}),
        "sourced_only": sourced_only,
        "withheld": len([a for a in axioms if a.status != "superseded"]) - len(chosen),
    }
