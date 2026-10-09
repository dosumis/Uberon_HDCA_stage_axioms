"""Generate the taxon-scoped classes that make the GCIs materialise.

A GCI has no named subject, so nothing attaches an edge to it. `expand.ru`
names the left-hand side of each GCI; this names the same intersection for every
term that could *inherit* one, because `GEN_hs_Y SubClassOf GEN_hs_X` follows
from `Y SubClassOf X` only if both scoped classes exist.

Two filters decide the population, and both matter:

  * `descendants` -- a term not below an axiom subject can never inherit a
    bound, so scoping it is waste. 310 instead of 13195.
  * `taxon subset` -- a term that cannot exist in the taxon gives an empty
    scoped class, whose inherited bounds are vacuously true. `Weberian vertebra
    and in_taxon some Homo sapiens` is the shape of the problem.

Output is OWL functional syntax rather than a ROBOT template. Templates resolve
names in Manchester cells by *label*, which means the ontology must declare a
label for the structure, the property and the taxon; functional syntax takes
CURIEs and generates 13195 classes in under a second.
"""

from __future__ import annotations

from pathlib import Path

SCOPED_BASE = "https://w3id.org/taxon-stage-axioms/scoped/"
IN_TAXON = "RO:0002162"

PREFIXES = {
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "UBERON": "http://purl.obolibrary.org/obo/UBERON_",
    "NCBITaxon": "http://purl.obolibrary.org/obo/NCBITaxon_",
    "RO": "http://purl.obolibrary.org/obo/RO_",
    "TSA": SCOPED_BASE,
}


def scoped_iri(curie: str, taxon: str) -> str:
    """Deterministic in both inputs, and reversible by splitting on the hyphen.

    `expand.ru` builds the same IRI in SPARQL. The two must agree exactly: if
    they drift, the merge produces two classes for one thing, inheritance stops,
    and nothing fails -- the reach number just quietly drops. See
    tests/test_model.py for the pin.
    """
    return SCOPED_BASE + f"{curie.replace(':', '_')}-{taxon.replace(':', '_')}"


def render(local_ids: list[str], taxon: str) -> str:
    taxon_local = taxon.replace(":", "_")
    lines = [f"Prefix({k}:=<{v}>)" for k, v in PREFIXES.items()]
    lines += ["", "Ontology(<https://w3id.org/taxon-stage-axioms/scoped.ofn>",
              f"Declaration(Class({taxon}))",
              f"Declaration(ObjectProperty({IN_TAXON}))"]
    for local in sorted(local_ids):
        gen = f"TSA:{local}-{taxon_local}"
        lines.append(f"Declaration(Class({gen}))")
        lines.append(
            f"EquivalentClasses({gen} ObjectIntersectionOf("
            f"UBERON:{local.split('_')[1]} "
            f"ObjectSomeValuesFrom({IN_TAXON} {taxon})))"
        )
    lines.append(")")
    return "\n".join(lines) + "\n"


def select(descendants: set[str], in_taxon: set[str] | None) -> tuple[list[str], int]:
    """Returns (kept, skipped_as_out_of_taxon)."""
    if in_taxon is None:
        return sorted(descendants), 0
    kept = sorted(descendants & in_taxon)
    return kept, len(descendants) - len(kept)


def write(descendants: set[str], in_taxon: set[str] | None, out: Path,
          taxon: str) -> tuple[int, int]:
    kept, skipped = select(descendants, in_taxon)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(kept, taxon))
    return len(kept), skipped
