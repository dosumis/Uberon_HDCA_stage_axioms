"""Generate taxon-scoped classes for a whole population, not just the annotated ones.

The expansion macro gives a named class to every structure that *carries* an
axiom. That is not enough for the inference we actually want: a bound asserted
on `ganglionic eminence` only reaches `lateral ganglionic eminence` if the
latter also has a scoped class, because `X-9606 SubClassOf Y-9606` follows from
`X SubClassOf Y` only when both scoped classes exist.

So this is a second, scope-driven job rather than an axiom-driven one. It emits
a ROBOT template, which handles Manchester class expressions natively -- far
less awkward than constructing RDF lists in a SPARQL update.

Scale, for reference: 3777 developing structures, 16142 Uberon classes. Both are
small for ELK, but the seed should be the population you query, not all of
Uberon by reflex.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

SCOPED_BASE = "https://w3id.org/taxon-stage-axioms/scoped/"
# ROBOT template resolves names in Manchester cells by LABEL, not CURIE -- a
# cell of `UBERON:0004023 and (RO:0002162 some NCBITaxon:9606)` is a parse
# error. So the seed must carry labels, and the ontology the template is applied
# to must declare them for the structure, the property and the taxon.
IN_TAXON_LABEL = "in taxon"
IN_TAXON = "RO:0002162"

# ROBOT template directives. Row 2 of the file, read as column instructions.
TEMPLATE_HEADER = ["ID", "LABEL", "TYPE", "EQ"]
TEMPLATE_DIRECTIVES = ["ID", "LABEL", "TYPE", "EC %"]


def scoped_iri(curie: str, taxon: str) -> str:
    return SCOPED_BASE + f"{curie.replace(':', '_')}-{taxon.replace(':', '_')}"


def rows(seed: list[tuple[str, str]], taxon: str, taxon_label: str):
    """seed is (uberon_curie, uberon_label) pairs; the label is required."""
    for curie, label in seed:
        if not label:
            raise ValueError(
                f"{curie}: a label is required -- ROBOT template resolves Manchester "
                "cells by label, so a seed row without one cannot be expressed"
            )
        yield [
            scoped_iri(curie, taxon),
            f"{label} ({taxon_label})" if label else curie,
            "owl:Class",
            f"'{label}' and ('{IN_TAXON_LABEL}' some '{taxon_label}')",
        ]


def write_template(seed, taxon: str, taxon_label: str, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    seed = list(seed)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(TEMPLATE_HEADER)
        w.writerow(TEMPLATE_DIRECTIVES)
        for row in rows(seed, taxon, taxon_label):
            w.writerow(row)
    return len(seed)


def read_seed(path: Path) -> list[tuple[str, str]]:
    """Seed file: TSV of uberon_id and optional uberon_label, header required."""
    out = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            curie = (row.get("uberon_id") or "").strip()
            if curie:
                out.append((curie, (row.get("uberon_label") or "").strip()))
    return out


# --- scope-all: every class in an ontology, in functional syntax -------------
#
# The ROBOT template route above resolves Manchester cells by label, which means
# the seed must carry labels and the target ontology must declare them. That is
# fine for a hand-picked seed and useless at Uberon scale. Emitting functional
# syntax directly sidesteps label resolution entirely -- CURIEs work, and 16432
# classes generate in under a second.

FUNCTIONAL_PREFIXES = {
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "UBERON": "http://purl.obolibrary.org/obo/UBERON_",
    "NCBITaxon": "http://purl.obolibrary.org/obo/NCBITaxon_",
    "RO": "http://purl.obolibrary.org/obo/RO_",
    "TSA": SCOPED_BASE,
}

CLASS_IRI = re.compile(r'rdf:about="http://purl\.obolibrary\.org/obo/(UBERON_\d+)"')


def uberon_classes(ontology_path: Path) -> list[str]:
    """Every UBERON class IRI mentioned as a subject in the file.

    Deliberately a regex over the serialisation rather than an OWL parse: this
    runs on a 55MB file and only needs the identifiers.
    """
    text = ontology_path.read_text(errors="replace")
    return sorted(set(CLASS_IRI.findall(text)))


def render_scope_all(local_ids: list[str], taxon: str) -> str:
    taxon_local = taxon.replace(":", "_")
    lines = [f"Prefix({k}:=<{v}>)" for k, v in FUNCTIONAL_PREFIXES.items()]
    lines += ["", "Ontology(<https://w3id.org/taxon-stage-axioms/scope-all.ofn>",
              f"Declaration(Class({taxon}))",
              f"Declaration(ObjectProperty({IN_TAXON}))"]
    for local in local_ids:
        gen = f"TSA:{local}-{taxon_local}"
        lines.append(f"Declaration(Class({gen}))")
        lines.append(
            f"EquivalentClasses({gen} ObjectIntersectionOf("
            f"UBERON:{local.split('_')[1]} "
            f"ObjectSomeValuesFrom({IN_TAXON} {taxon})))"
        )
    lines.append(")")
    return "\n".join(lines) + "\n"


def write_scope_all(ontology_path: Path, out: Path, taxon: str) -> int:
    ids = uberon_classes(ontology_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_scope_all(ids, taxon))
    return len(ids)
