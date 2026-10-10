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

import collections
import csv
import dataclasses
import glob
import json
from pathlib import Path

from .build import render
from .model import Axiom, PREDICATES
from .support import CONTEXTUAL, DIRECT, classify, load_records


def _evidence_records(evidence_dir: Path) -> dict[str, list[dict]]:
    """Quoted passages, indexed by the term they are about."""
    out: dict[str, list[dict]] = collections.defaultdict(list)
    for path in sorted(glob.glob(str(evidence_dir / "*.json"))):
        try:
            records = json.loads(Path(path).read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(records, list):
            continue
        for record in records:
            if record.get("uberon_id") and record.get("quote"):
                out[record["uberon_id"]].append(record)
    return out


def _quote_text(records: list[dict], stage_id: str) -> str:
    """The quotes backing one claim, closest first.

    A start bound is often argued from a pair -- absent at one stage, present
    at the next -- so both are carried rather than only the hit. Records for
    the exact stage come first; the rest give the reviewer the surrounding
    argument instead of a pointer to a file in someone else's repository.
    """
    def sort_key(r: dict) -> tuple[int, str]:
        return (0 if r.get("stage_id") == stage_id else 1, r.get("stage_id") or "")

    parts = []
    for r in sorted(records, key=sort_key):
        label = r.get("stage_label") or r.get("stage_id") or "?"
        claim = r.get("claim") or "note"
        quote = " ".join(str(r["quote"]).split())
        parts.append(f"[{label}, {claim}] {quote}")
    return "  ".join(parts)


def selected(axioms: list[Axiom], sourced_only: bool = True) -> list[Axiom]:
    live = [a for a in axioms if a.status != "superseded"]
    return [a for a in live if a.is_sourced] if sourced_only else live


def review_table(axioms: list[Axiom], path: Path,
                 support: dict[str, str] | None = None) -> None:
    """One row per proposed axiom, in the order a reviewer would read them:
    grouped by structure, with the evidence quote beside the claim it supports."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["uberon_id", "uberon_label", "taxon", "claim",
                    "stage_id", "stage_label", "support", "evidence",
                    "evidence_code", "source"])
        for a in sorted(axioms, key=lambda a: (a.uberon_label, a.predicate)):
            w.writerow([a.uberon_id, a.uberon_label, a.taxon_label,
                        PREDICATES[a.predicate][0], a.stage_id, a.stage_label,
                        (support or {}).get(f"{a.uberon_id}|{a.predicate}", ""),
                        a.evidence_text, a.evidence_code, a.source])


def with_quotes(axioms: list[Axiom], evidence_dir: Path) -> list[Axiom]:
    """Replace the working evidence note with the passages themselves.

    In the source table `evidence_text` is a curator's working note, often
    ending in a pointer to src/evidence/. A pointer is useless to a reviewer
    outside this repository, so the contribution carries the quotes inline.
    """
    records = _evidence_records(evidence_dir)
    out = []
    for a in axioms:
        found = records.get(a.uberon_id)
        if found:
            a = dataclasses.replace(a, evidence_text=_quote_text(found, a.stage_id))
        out.append(a)
    return out


def write(axioms: list[Axiom], out_dir: Path, sourced_only: bool = True,
          evidence_dir: Path | None = None, require_support: bool = True) -> dict:
    chosen = selected(axioms, sourced_only)
    unsupported = 0
    support: dict[str, str] = {}
    if evidence_dir and evidence_dir.exists():
        records = load_records(evidence_dir)
        support = {f"{a.uberon_id}|{a.predicate}": classify(a, records) for a in chosen}
        if require_support:
            keep = [a for a in chosen
                    if support[f"{a.uberon_id}|{a.predicate}"] in (DIRECT, CONTEXTUAL)]
            unsupported = len(chosen) - len(keep)
            chosen = keep
        chosen = with_quotes(chosen, evidence_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "uberon-human-stage-gcis.ofn").write_text(
        render(chosen, for_contribution=True))
    review_table(chosen, out_dir / "review.tsv", support)
    return {
        "axioms": len(chosen),
        "structures": len({a.uberon_id for a in chosen}),
        "sourced_only": sourced_only,
        "unsupported": unsupported,
        "unsourced": len([a for a in axioms if a.status != "superseded"
                          and not a.is_sourced]),
    }
