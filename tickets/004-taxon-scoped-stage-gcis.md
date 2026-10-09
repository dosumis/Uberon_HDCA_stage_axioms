# Add taxon-scoped developmental stage axioms for human embryonic structures

**Ontology:** Uberon
**Type:** new axioms (GCIs), no new terms

## Proposal

58 General Class Inclusion axioms over 38 existing Uberon classes, giving the
Carnegie stage at which each structure begins or ceases to exist in human.
Every axiom carries a quoted passage from the source as an axiom annotation.

No new terms are requested. Nothing existing is modified.

```
(X and in_taxon some NCBITaxon:9606)
    SubClassOf existence_starts_during some HsapDv:nnnnnnn
```

## Why a GCI rather than an axiom on the class

`heart tube SubClassOf existence_starts_during some 'Carnegie stage 09'` is an
all-some claim: it says every heart tube in every organism starts at CS9. The
Carnegie series is human, so that is false as soon as a second species is
considered. The taxon conjunct is what makes the claim sayable at all, and it
is why these cannot simply be asserted on the species-neutral classes.

## Choice of predicate

`existence starts during` (RO:0002488) and `existence ends during` (RO:0002492)
where the structure has a nameable onset or offset. `existence starts during or
after` (RO:0002496) only where it appears progressively and a point claim would
be false rather than merely imprecise.

37 starts-during, 19 ends-during, 1 starts-during-or-after, 1
ends-during-or-before. **20 of the 38 structures carry both a start and an
end**, which is the part worth having: a bracketed claim can be refuted.

The exact form is deliberate. Uberon's existing bounds are dominated by the
loose predicate against species-neutral stages, where it carries very little —
3348 classes assert `starts during or after gastrula stage`, which is true of
almost everything, and nothing requires an asserted bound to be the tightest
known. A point claim against a Carnegie stage can be wrong, and so can be
checked.

A curator-facing `onset_type` annotation (`point` / `interval`) records the
judgement the predicate follows from, so a reviewer can disagree with the
reasoning rather than only with the result.

## Evidence

Every axiom cites O'Rahilly R, Müller F (1987), *Developmental Stages in Human
Embryos*, Carnegie Institution of Washington Publication 637 — the work the
Carnegie staging system is defined by — with the relevant passage quoted in an
`rdfs:comment` on the axiom and `ECO:0000304` as the evidence code.

Example, as it appears in the file:

```
# atrial septum primum existence starts during Carnegie stage 13 [Homo sapiens]
SubClassOf(
    Annotation(TSA:onset_type "point")
    Annotation(RO:0002558 ECO:0000304)
    Annotation(rdfs:comment "source: CS13 summary 'septum primum and foramen
      primum appear in the heart'; CS12 says they 'may appear'")
    Annotation(oboInOwl:hasDbXref "O'Rahilly R, Muller F (1987) ...")
    ObjectIntersectionOf(UBERON:0004154 ObjectSomeValuesFrom(RO:0002162 NCBITaxon:9606))
    ObjectSomeValuesFrom(RO:0002488 HsapDv:0000020)
)
```

Note the second clause of that comment. Reading the source moved 17 stage
assignments and retired 2 claims outright, so the quotes are load-bearing
rather than decorative.

## Review

`review.tsv` in the same directory has one row per axiom — structure, claim,
stage, evidence quote — because a table is reviewable at this volume and
Manchester syntax is not. It is generated from the same source as the OWL, so
the two cannot disagree.

## Checks run

- Every CURIE resolves, and every label beside an identifier is the ontology's
  own label or a known synonym.
- Predicate agrees with the recorded onset judgement.
- Stage ontology agrees with the taxon.
- No structure carries both an exact and a loose bound in the same direction.
- Round trip: table → OWL → expand → materialise → extract returns exactly the
  rows it started from.

## One consequence worth flagging

A GCI has no named subject, so relation-graph has nothing to attach an edge to
and these axioms will materialise as **nothing** in Ubergraph. They are
correct, present, and invisible to anything reading the materialised graph.

We work around it downstream by generating a named class equivalent to each
GCI's left-hand side before reasoning, which is a build step on our side rather
than a change to Uberon. Measured on uberon-base: 310 scoped classes, 17
seconds in relation-graph, and the axioms reach 310 Uberon terms — 197 of them
inheriting a bound through `subClassOf` from a class we never touched.

Raising it because it affects what Uberon's own consumers will see, and because
if Uberon would rather these were expressed some other way, better to know
before the next batch.

## Not included

116 further claims exist in our source table and are deliberately withheld:
they are seeded from background knowledge and not yet checked against a source.
They are tracked as `status: proposed`, `curator: latent`, and will be offered
only once sourced.

Three separate tickets request missing terms (fetal zone of adrenal cortex,
germinal matrix, a `lanugo` synonym). They are independent of this proposal.

## Source

Generated by <https://github.com/dosumis/taxon-stage-axioms> — curated table,
schema, evidence records and the build that produces this file.
