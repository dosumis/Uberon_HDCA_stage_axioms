import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from taxon_stage.build import gci, render
from taxon_stage.model import Axiom, check, load
from taxon_stage.scope import rows, scoped_iri

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


def test_scope_template_uses_labels_not_curies():
    # ROBOT template resolves Manchester cells by label; CURIEs are a parse error.
    (row,) = rows([("UBERON:0004023", "ganglionic eminence")], "NCBITaxon:9606", "Homo sapiens")
    assert row[3] == "'ganglionic eminence' and ('in taxon' some 'Homo sapiens')"


def test_scope_rejects_a_seed_row_with_no_label():
    with pytest.raises(ValueError, match="label is required"):
        list(rows([("UBERON:0004023", "")], "NCBITaxon:9606", "Homo sapiens"))
