# Add taxon-scoped developmental stage axioms for human embryonic structures

**Ontology:** Uberon
**Type:** new axioms (GCIs), no new terms

## Proposal

33 General Class Inclusion axioms over 33 existing Uberon classes, giving the
Carnegie stage at which each structure begins to exist in human. Every axiom
carries the quoted passage it rests on as an axiom annotation.

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

`existence starts during` (RO:0002488) where the structure has a nameable
onset: 32 of the 33. `existence starts during or after` (RO:0002496) for the
one case -- `somite` -- where it appears progressively and a point claim would
be false rather than merely imprecise.

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
    Annotation(rdfs:comment "[Carnegie stage 13, start] Internal: septum primum
      and foramen primum appear in the heart; right and left lung buds are
      recognizable, and the trachea begins its development; ...")
    Annotation(oboInOwl:hasDbXref "O'Rahilly R, Muller F (1987) ...")
    ObjectIntersectionOf(UBERON:0004154 ObjectSomeValuesFrom(RO:0002162 NCBITaxon:9606))
    ObjectSomeValuesFrom(RO:0002488 HsapDv:0000020)
)
```

The quotes are load-bearing rather than decorative: reading the source moved 17
stage assignments and retired 2 claims outright.

29 of the 33 are **direct** -- a passage describing the structure at the stage
claimed. The other 4 are **contextual**: the source records the structure as
absent at an earlier stage, which bounds the onset without fixing it. The
`support` column says which, per axiom, rather than leaving a reviewer to work
it out from the quote.

## The axioms

`CS` is a Carnegie stage. `≥` marks the one claim using the loose predicate.
`support` is `direct` where a passage describes the structure at that stage,
`contextual` where the argument is that it is absent at an earlier one.

| Uberon class | starts | support |
|---|---|---|
| UBERON:0000301 amniotic cavity | CS05 | direct |
| UBERON:0004154 atrial septum primum | CS13 | direct |
| UBERON:0004155 atrial septum secundum | CS18 | direct |
| UBERON:0002241 chondrocranium | CS17 | direct |
| UBERON:0007106 chorionic villus | CS06 | contextual |
| UBERON:0004754 foramen ovale of heart | CS18 | direct |
| UBERON:0001046 hindgut | CS09 | direct |
| UBERON:0005418 hindlimb bud | CS13 | direct |
| UBERON:0003064 intermediate mesoderm | CS09 | direct |
| UBERON:0000118 lung bud | CS12 | direct |
| UBERON:0005867 mandibular prominence | CS10 | direct |
| UBERON:0003890 Mullerian duct | CS16 | direct |
| UBERON:0005061 neural groove | CS08 | direct |
| UBERON:0001049 neural tube | CS10 | direct |
| UBERON:0004061 neural tube mantle layer | CS13 | direct |
| UBERON:0004062 neural tube marginal layer | CS12 | direct |
| UBERON:0004060 neural tube ventricular layer | CS13 | direct |
| UBERON:0005870 olfactory pit | CS15 | direct |
| UBERON:0003050 olfactory placode | CS12 | direct |
| UBERON:0003072 optic cup | CS13 | direct |
| UBERON:0004128 optic vesicle | CS11 | direct |
| UBERON:0003069 otic placode | CS09 | direct |
| UBERON:0003115 pharyngeal arch 4 | CS12 | contextual |
| UBERON:0007123 pharyngeal pouch 2 | CS10 | direct |
| UBERON:0004341 primitive streak | CS06 | direct |
| UBERON:0006215 rhombic lip | CS16 | direct |
| UBERON:0004161 septum transversum | CS09 | direct |
| UBERON:0002063 sinus venosus | CS11 | contextual |
| UBERON:0002329 somite | ≥ CS09 | contextual |
| UBERON:0000930 stomodeum | CS09 | direct |
| UBERON:0005562 thymus primordium | CS13 | direct |
| UBERON:0003091 thyroid primordium | CS10 | direct |
| UBERON:0000084 ureteric bud | CS14 | direct |

<details><summary>The quoted passage behind each of the 33 axioms</summary>

```
amniotic cavity - starts during CS05  [direct]
    [Carnegie stage 05, start] Additional features of stage 5 include the
    definite appearance of the amniotic cavity and the formation of extra-
    embryonic mesoblast.

atrial septum primum - starts during CS13  [direct]
    [Carnegie stage 13, start] Internal: septum primum and foramen primum
    appear in the heart; right and left lung buds are recognizable, and the
    trachea begins its development; retinal and lens discs appear; the
    endolymphatic appendage becomes distinguishable by the end of the stage.

atrial septum secundum - starts during CS18  [direct]
    [Carnegie stage 18, start] Internal: in the heart, septum secundum and
    the associated foramen ovale are appearing; the membranous part of the
    interventricular septum is beginning to take form; the vomeronasal organ
    is represented by a groove; choanae develop; some subsegmental buds
    develop in the bronchial tree; collecting tubules develop from the

chondrocranium - starts during CS17  [direct]
    [Carnegie stage 17, start] The cerebellar plate (innerer Kleinhirnwulst
    of Hochsetter) is present as a clear thickening.

chorionic villus - starts during CS06  [contextual]
    [Carnegie stage 05, absent] Characteristic features: implanted but
    previllous; solid trophoblast in 5a; trophoblastic lacunae,
    cytotrophoblastic clumps, and primary umbilical vesicle in 5b; lacunar
    vascular circle and some mesoblastic crests in cytotrophoblastic clumps
    in 5c

foramen ovale of heart - starts during CS18  [direct]
    [Carnegie stage 18, start] Internal: in the heart, septum secundum and
    the associated foramen ovale are appearing; the membranous part of the
    interventricular septum is beginning to take form; the vomeronasal organ
    is represented by a groove; choanae develop; some subsegmental buds
    develop in the bronchial tree; collecting tubules develop from the

hindgut - starts during CS09  [direct]
    [Carnegie stage 09, start] The stomodeum is beginning to form.

hindlimb bud - starts during CS13  [direct]
    [Carnegie stage 13, start] Internal: septum primum and foramen primum
    appear in the heart; right and left lung buds are recognizable, and the
    trachea begins its development; retinal and lens discs appear; the
    endolymphatic appendage becomes distinguishable by the end of the stage.

intermediate mesoderm - starts during CS09  [direct]
    [Carnegie stage 09, start] The stomodeum is beginning to form.

lung bud - starts during CS12  [direct]
    [Carnegie stage 12, start] Internal: the interventricular septum has
    begun; the cystic primordium and the dorsal pancreas are becoming
    distinguishable; the lung bud appears.

mandibular prominence - starts during CS10  [direct]
    [Carnegie stage 10, start] Although a sinus venosus as such is not
    present until the next stage, left and right sinusal horns appear during
    stage 10.

Mullerian duct - starts during CS16  [direct]
    [Carnegie stage 16, start] The primordium of the paramesonephric duct is
    beginning to appear as an invagination of thickened coelomic epithelium
    over the mesonephros.

neural groove - starts during CS08  [direct]
    [Carnegie stage 08, start] The most advanced embryos with regard to
    endodermal spread are also more advanced in other respects. (Nos. 5960
    and 7545 already show a neural groove.) It may be that this endoderm is
    derived from the caudal part of the primitive streak (fig. 6-2).

neural tube - starts during CS10  [direct]
    [Carnegie stage 10, start] Although a sinus venosus as such is not
    present until the next stage, left and right sinusal horns appear during
    stage 10.

neural tube mantle layer - starts during CS13  [direct]
    [Carnegie stage 13, start] The remaining wall is made up of the
    undifferentiated ependymal zone, except for a beginning mantle zone in
    the region that is to form the ventral horn of gray matter.

neural tube marginal layer - starts during CS12  [direct]
    [Carnegie stage 12, start] Neurofibrils begin to form for the first time
    in the rhombencephalic wall, and in most embryos a marginal layer begins
    to develop.

neural tube ventricular layer - starts during CS13  [direct]
    [Carnegie stage 13, start] The remaining wall is made up of the
    undifferentiated ependymal zone, except for a beginning mantle zone in
    the region that is to form the ventral horn of gray matter.

olfactory pit - starts during CS15  [direct]
    [Carnegie stage 15, start] External: lens vesicles are closed; nasal
    pits are appearing; hand plates are forming.

olfactory placode - starts during CS12  [direct]
    [Carnegie stage 12, start] The nasal discs become thicker and form a
    portion of the ectodermal ring on both sides of the closed neuropore
    (O'Rahilly and Müller, 1985).

optic cup - starts during CS13  [direct]
    [Carnegie stage 13, start] Internal: septum primum and foramen primum
    appear in the heart; right and left lung buds are recognizable, and the
    trachea begins its development; retinal and lens discs appear; the
    endolymphatic appendage becomes distinguishable by the end of the stage.

optic vesicle - starts during CS11  [direct]
    [Carnegie stage 11, start] Internal: the sinus venosus develops; the
    oropharyngeal membrane ruptures; the mesonephric duct and nephric
    tubules appear; the optic vesicle and otic pit develop.

otic placode - starts during CS09  [direct]
    [Carnegie stage 09, start] The otic disc (or plate) makes its appearance
    during stage 9 (fig. 9-6).

pharyngeal arch 4 - starts during CS12  [contextual]
    [Carnegie stage 12, absent] Internal: the interventricular septum has
    begun; the cystic primordium and the dorsal pancreas are becoming
    distinguishable; the lung bud appears.

pharyngeal pouch 2 - starts during CS10  [direct]
    [Carnegie stage 10, start] Although a sinus venosus as such is not
    present until the next stage, left and right sinusal horns appear during
    stage 10.

primitive streak - starts during CS06  [direct]
    [Carnegie stage 06, start] In the human, the primitive streak appears
    first during stage 6. [Carnegie stage 11, absent] The caudal eminence,
    which lies between the cloacal membrane and the site of the neurenteric
    canal, represents the region of the former primitive streak.

rhombic lip - starts during CS16  [direct]
    [Carnegie stage 16, start] The alar lamina is developing, and its upper
    part, the rhombic lip, is very dense.

septum transversum - starts during CS09  [direct]
    [Carnegie stage 09, start] Other features that have been identified by
    stage 9 include the "cardiac jelly" (Davis, 1927), the mesocardium, and
    the septum transversum (Ingalls, 1920).

sinus venosus - starts during CS11  [contextual]
    [Carnegie stage 10, absent] Although a sinus venosus as such is not
    present until the next stage, left and right sinusal horns appear during
    stage 10.

somite - starts during CS09  [contextual]
    [Carnegie stage 08, absent] The embryo is presomitic, i.e., somites are
    not yet visible.

stomodeum - starts during CS09  [direct]
    [Carnegie stage 09, start] The stomodeum is beginning to form.

thymus primordium - starts during CS13  [direct]
    [Carnegie stage 13, start] Internal: septum primum and foramen primum
    appear in the heart; right and left lung buds are recognizable, and the
    trachea begins its development; retinal and lens discs appear; the
    endolymphatic appendage becomes distinguishable by the end of the stage.

thyroid primordium - starts during CS10  [direct]
    [Carnegie stage 10, start] Although a sinus venosus as such is not
    present until the next stage, left and right sinusal horns appear during
    stage 10.

ureteric bud - starts during CS14  [direct]
    [Carnegie stage 14, start] Internal: the ventral pancreas (if not
    detectable earlier) is distinguishable at stages 14 and 15; right and
    left lung sacs grow dorsad; the ureteric bud acquires a metanephrogenic
    cap; future cerebral hemispheres and cerebellar plates begin to be
    visible. [Carnegie stage 13, present] A ureteric bud may possibly be

```
</details>

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

## Not included, and why

Our source table holds 174 live claims. 141 are withheld:

- **116 are unsourced** -- seeded from background knowledge and not yet checked
  against anything. Tracked as `curator: latent`; they will be offered once
  sourced.
- **25 are sourced but unsupported.** A curator read the source for the term,
  but no passage bears on that particular claim. Most are end bounds: our
  evidence store records *start*, *present* and *absent* observations and
  nothing that records an **end**, so no end bound can currently be evidenced
  at all. Attaching a nearby quote to such a claim would read as support, so
  they are held back rather than dressed up.

The practical consequence is that this batch is start bounds only. End bounds
need the source read again for when each structure was last seen, which is a
curation job rather than something the build can fix, and they will follow as a
second batch.

Three separate tickets request missing terms (fetal zone of adrenal cortex,
germinal matrix, a `lanugo` synonym). They are independent of this proposal.

## Source

Generated by <https://github.com/dosumis/taxon-stage-axioms> — curated table,
schema, evidence records and the build that produces this file.
