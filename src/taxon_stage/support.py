"""Does the evidence actually bear on the claim it is attached to?

`source` being non-empty means a curator read the source for that term. It does
not mean this particular claim is quoted, and the two came apart badly: of 58
axioms with a source, only 29 had a passage supporting the specific claim.

The gap is structural rather than careless. The evidence store records `start`,
`present` and `absent` observations, and nothing records an *end*. So a start
bound can be evidenced directly and an end bound cannot be evidenced at all
until the collection records when a structure was last seen -- which is a
curation task, not something the join can fix.

Attaching a nearby quote to an unevidenced claim is worse than attaching
nothing, because it reads as support. Hence this classification, and hence
`contribute` withholding anything it cannot place.
"""

from __future__ import annotations

import collections
import glob
import json
from pathlib import Path

from .model import Axiom

START_PREDICATES = {"RO:0002488", "RO:0002496"}

DIRECT = "direct"          # a passage about this structure at this stage
CONTEXTUAL = "contextual"  # absent at an earlier stage, so it starts at or after
NONE = "none"


def load_records(evidence_dir: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = collections.defaultdict(list)
    for path in sorted(glob.glob(str(evidence_dir / "*.json"))):
        try:
            records = json.loads(Path(path).read_text())
        except json.JSONDecodeError:
            continue
        if isinstance(records, list):
            for record in records:
                if record.get("uberon_id") and record.get("quote"):
                    out[record["uberon_id"]].append(record)
    return out


def classify(a: Axiom, records: dict[str, list[dict]]) -> str:
    found = records.get(a.uberon_id, [])
    at_stage = [r for r in found if r.get("stage_id") == a.stage_id]

    if a.predicate in START_PREDICATES:
        if any(r.get("claim") in ("start", "present") for r in at_stage):
            return DIRECT
        # "absent at an earlier stage" is a real argument for a start bound,
        # but it bounds rather than fixes it, so it is not direct support.
        if any(r.get("claim") == "absent" for r in found):
            return CONTEXTUAL
        return NONE

    # An end bound needs a passage saying the structure is gone, or last seen.
    if any(r.get("claim") in ("end", "absent") for r in at_stage):
        return DIRECT
    return NONE


def summarise(axioms: list[Axiom], evidence_dir: Path) -> dict[str, int]:
    records = load_records(evidence_dir)
    counts: collections.Counter = collections.Counter()
    for a in axioms:
        counts[classify(a, records)] += 1
    return dict(counts)
