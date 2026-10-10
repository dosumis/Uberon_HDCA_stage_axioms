import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from taxon_stage.build import gci, render
from taxon_stage.model import Axiom, check, load
from taxon_stage.scope import render as render_scope, scoped_iri, select

ROOT = Path(__file__).resolve().parents[1]


def axiom(**kw):
    base = dict(
        uberon_id="UBERON:0004023", uberon_label="ganglionic eminence",
        taxon_id="NCBITaxon:9606", taxon_label="Homo sapiens",
        onset_type="point", predicate="RO:0002488",
        stage_id="HsapDv:0000022", stage_label="Carnegie stage 15",
        evidence_code="", evidence_text="", source="", curator="x",
        date="2026-10-09", status="proposed",
    )
    return Axiom(**(base | kw))


def test_shipped_table_is_clean():
    assert check(load(ROOT / "src" / "axioms.tsv")) == []


def test_predicate_must_match_onset_type():
    # RO:0002488 is a point claim; calling it an interval is the error the
    # onset_type column exists to catch.
    problems = check([axiom(onset_type="interval")])
    assert any("does not match predicate" in p for p in problems)


def test_stage_ontology_must_match_taxon():
    problems = check([axiom(taxon_id="NCBITaxon:10090", taxon_label="Mus musculus")])
    assert any("takes MmusDv stages" in p for p in problems)


def test_accepted_requires_a_source():
    assert any("no source" in p for p in check([axiom(status="accepted")]))
    assert check([axiom(status="accepted", source="PMID:1", curator="real")]) == []


def test_latent_curation_does_not_count_as_sourced():
    # A claim seeded from background knowledge is a to-do, not provenance.
    assert not axiom(source="PMID:1", curator="latent").is_sourced


def test_duplicate_predicate_for_one_structure_is_rejected():
    assert any("duplicate" in p for p in check([axiom(), axiom()]))


def test_exact_and_loose_start_bounds_are_mutually_exclusive():
    problems = check([axiom(), axiom(predicate="RO:0002496", onset_type="interval")])
    assert any("exact and a loose start bound" in p for p in problems)


def test_gci_has_no_named_subject():
    # The whole design rests on this: the subject is an intersection, so the
    # claim is scoped to the taxon rather than asserted of the structure.
    out = gci(axiom())
    assert "ObjectIntersectionOf(UBERON:0004023 ObjectSomeValuesFrom(RO:0002162 NCBITaxon:9606))" in out
    assert "ObjectSomeValuesFrom(RO:0002488 HsapDv:0000022)" in out


def test_evidence_rides_on_the_axiom():
    out = gci(axiom(source="PMID:123", evidence_text="because"))
    assert 'Annotation(oboInOwl:hasDbXref "PMID:123")' in out
    assert 'Annotation(rdfs:comment "because")' in out


def test_superseded_rows_are_excluded_from_the_owl():
    assert "UBERON:0004023" not in render([axiom(status="superseded")])


def test_scoped_iri_is_deterministic_and_reversible():
    iri = scoped_iri("UBERON:0004023", "NCBITaxon:9606")
    assert iri.endswith("UBERON_0004023-NCBITaxon_9606")
    assert scoped_iri("UBERON:0004023", "NCBITaxon:9606") == iri


def test_scoped_iri_matches_the_sparql_macro():
    """expand.ru builds this IRI in SPARQL and scope.py in Python. If they
    drift, the merge makes two classes for one thing and inheritance stops --
    silently, because nothing errors and the reach number just drops."""
    macro = Path(__file__).resolve().parents[1] / "sparql" / "expand.ru"
    assert "https://w3id.org/taxon-stage-axioms/scoped/" in macro.read_text()
    assert scoped_iri("UBERON:0004023", "NCBITaxon:9606") == (
        "https://w3id.org/taxon-stage-axioms/scoped/UBERON_0004023-NCBITaxon_9606")


def test_select_drops_terms_outside_the_taxon():
    kept, skipped = select({"UBERON_0000955", "UBERON_2001190"}, {"UBERON_0000955"})
    assert kept == ["UBERON_0000955"]
    assert skipped == 1


def test_select_without_a_taxon_subset_keeps_everything():
    kept, skipped = select({"UBERON_0000955", "UBERON_2001190"}, None)
    assert len(kept) == 2 and skipped == 0


def test_render_emits_curies_not_labels():
    # ROBOT templates need labels; functional syntax does not, which is why
    # this generates thousands of classes in under a second.
    out = render_scope(["UBERON_0004023"], "NCBITaxon:9606")
    assert "ObjectIntersectionOf(UBERON:0004023 " in out
    assert "ObjectSomeValuesFrom(RO:0002162 NCBITaxon:9606)" in out


# --- does the evidence bear on the claim? -----------------------------------

def _records(tmp_path, *entries):
    import json
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "e.json").write_text(json.dumps(list(entries)))
    return tmp_path


def test_start_bound_with_a_passage_at_that_stage_is_direct(tmp_path):
    from taxon_stage.support import DIRECT, classify, load_records

    d = _records(tmp_path, {"uberon_id": "UBERON:0004023", "stage_id": "HsapDv:0000022",
                            "claim": "start", "quote": "q"})
    assert classify(axiom(), load_records(d)) == DIRECT


def test_start_bound_argued_from_absence_is_contextual(tmp_path):
    from taxon_stage.support import CONTEXTUAL, classify, load_records

    # absent at an earlier stage bounds the onset without fixing it
    d = _records(tmp_path, {"uberon_id": "UBERON:0004023", "stage_id": "HsapDv:0000021",
                            "claim": "absent", "quote": "q"})
    assert classify(axiom(), load_records(d)) == CONTEXTUAL


def test_end_bound_is_unsupported_by_a_start_passage(tmp_path):
    """The failure this module exists for. A quote about when something appears
    says nothing about when it goes, and attaching it to an end bound reads as
    support that is not there."""
    from taxon_stage.support import NONE, classify, load_records

    d = _records(tmp_path, {"uberon_id": "UBERON:0004023", "stage_id": "HsapDv:0000022",
                            "claim": "start", "quote": "q"})
    end = Axiom(**{**axiom().__dict__, "predicate": "RO:0002492", "onset_type": "point"})
    assert classify(end, load_records(d)) == NONE


def test_contribution_withholds_unsupported_claims(tmp_path):
    from taxon_stage.contribute import write

    d = _records(tmp_path / "ev", {"uberon_id": "UBERON:0004023",
                                   "stage_id": "HsapDv:0000022",
                                   "claim": "start", "quote": "q"})
    supported = axiom(source="PMID:1", curator="real")
    unsupported = Axiom(**{**supported.__dict__, "predicate": "RO:0002492"})
    info = write([supported, unsupported], tmp_path / "out", evidence_dir=d)
    assert info["axioms"] == 1 and info["unsupported"] == 1
