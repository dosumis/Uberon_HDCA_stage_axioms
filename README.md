# taxon-stage-axioms

Taxon-scoped developmental stage bounds for Uberon structures: when, in a named
species, an anatomical structure starts and stops existing.

A curated table is the source of truth. OWL, named classes for reasoning, and a
materialised edge table are all generated from it.

## Why not just assert it on the Uberon class

`heart tube SubClassOf existence_starts_during some 'Carnegie stage 09'` is an
all-some claim. It says every heart tube in every organism starts at CS9, which
is false the moment a second species is considered — Carnegie stages are human.
So the axioms are General Class Inclusions, scoped by taxon:

```
(heart tube and in_taxon some Homo sapiens)
    SubClassOf existence_starts_during some 'Carnegie stage 09'
```

That is correct, and it is also invisible. A GCI has no named subject, so
relation-graph has nothing to attach an edge to and the axiom materialises as
nothing at all. Giving the left-hand side a name is what the expansion macro
does, and it is why that macro is a SPARQL update over the *artefact* rather
than another output of the table generator — the same step has to work on GCIs
in Uberon that we did not write.

## Why bother with OWL at all

Lookup would be better served by a table. OWL earns its place for one thing:
**a bound asserted on a parent reaches every child.** Demonstrated end to end in
`tests/fixtures/mini-uberon.ofn` — assert on `ganglionic eminence`, and ELK
infers

```
medial ganglionic eminence (Homo sapiens)  ⊑  ganglionic eminence (Homo sapiens)
lateral ganglionic eminence (Homo sapiens) ⊑  ganglionic eminence (Homo sapiens)
```

That is the same inference that supplies most of Uberon's existing bound
coverage: 4521 terms assert a start bound, 14613 have one once subclass
inheritance is read.

What OWL does **not** give you here is temporal consistency. EL has no
arithmetic over stages, so no reasoner will notice that a structure starts
before the thing it develops from. That stays a SPARQL query
(`sparql/checks/monotonicity.rq`), and HsapDv makes it answerable: 220
`immediately_preceded_by` and 50 `preceded_by` edges, against the single
ordering edge Uberon's species-neutral stages offer between embryonic
sub-stages.

## Layout

```
src/axioms.tsv          the only hand-edited file; schema in schema/
src/evidence/           quoted passages backing the sourced claims
src/taxon_stage/        table -> OWL, scoped classes, validation, measurement
sparql/expand.ru        GCI left-hand side -> named class
sparql/checks/          monotonicity, unexpanded-GCI
sparql/extract.rq       materialised bounds back out as a table
contribution/           what would go to Uberon: sourced GCIs + a review table
```

## Pipeline

```
make check      structural validation of the table        (offline, instant)
make validate   identifier/label agreement                (online, cached)
make axioms     table -> build/axioms.ofn                 (the contribution)
make scoped     expand GCIs, scope the terms that can inherit
make materialize round trip with no Uberon                (ROBOT only)
make reach      the real run                              (needs UBERON=, UBERON_OBO=)
make contribute package the sourced axioms
make test
```

### Which terms get a scoped class

A GCI has no named subject, so nothing materialises it; `expand.ru` names the
left-hand side. But a bound on a parent only reaches a child if the child has a
scoped class too, so the population matters.

It is the **reasoned subClassOf descendants of the axiom subjects**, intersected
with Uberon's computed taxon subset:

| | classes |
|---|---:|
| axiom subjects | 113 |
| + reasoned descendants | 324 |
| ∩ `human_subset` | **310** |
| every Uberon class, for comparison | 16432 |

Both filters earn their place. A term not below an axiom subject can never
inherit anything — scoping all of Uberon costs 13195 classes to reach the same
310. A term that cannot exist in the taxon gives an empty scoped class whose
inherited bounds are vacuously true; `Weberian vertebra and in_taxon some Homo
sapiens` is the shape of that, and the subset tag removes it along with the fin
ridges, the ural vertebrae and `forelimb wing bud`.

Verified lossless: scoping all 16432 and scoping the 310 both reach exactly 310
terms with 462 facts.

There is no bootstrap. `GEN_hs_Y SubClassOf GEN_hs_X` follows from `Y SubClassOf
X`, which is a fact about Uberon alone — so you ask Uberon for the descendants
and build exactly those. Take the closure from a **reasoner**, though: the
asserted `is_a` hierarchy gives 316 and misses eight terms subsumed through
logical definitions (`pharyngeal arch 7`, `trunk vertebra`, the chorionic villus
subtypes). Ubergraph's redundant graph already holds it, cached in
`build/descendants.json` against the subjects it was computed for.

### What the axioms reach

113 asserted structures, **310** Uberon terms carrying an HsapDv bound, **197**
of them inherited. 462 (term, predicate, stage) facts from 176 asserted rows.

Materialising the existential edges needs **relation-graph** — ROBOT's `reason`
asserts named subsumptions only. `make materialize` uses `robot materialize` for
the per-commit round trip, which needs no Uberon and no extra tools;
`make reach` uses relation-graph, which gives the closure and is what Ubergraph
itself uses, so local numbers and published numbers are comparable.

## Two things that cost an afternoon

**ROBOT template resolves Manchester cells by label, not CURIE.** A cell of
`UBERON:0004023 and (RO:0002162 some NCBITaxon:9606)` is a parse error, so a
template needs labels declared for the structure, the property *and* the taxon.
That is why `scope.py` emits OWL functional syntax instead — CURIEs work, and
there is no dependency on what the target ontology happens to label.

**Reusing the GCI's bnode in the expansion does not survive an OWLAPI round
trip.** The macro inserts `GEN owl:equivalentClass ?lhs` sharing the existing
expression node; after serialisation the two are separate structures. This is
harmless — linking `GEN` to the GCI's consequent was always an entailment, not
an RDF path — but it means `sparql/extract.rq` must run *after* materialisation,
never on the expanded file.

## Curation

Every row starts `status: proposed` with `curator: latent`, meaning the claim
came from a language model's background knowledge and nobody has checked it.
That is a to-do, not provenance: `check` refuses to mark a row `accepted`
without a source, and `latent` never counts as sourced however the other columns
are filled in.

`onset_type` is the curator-facing judgement and `predicate` follows from it:

| onset_type | meaning | predicate |
|---|---|---|
| `point` | a definable onset or offset, so an exact stage can be named — and can be wrong | `RO:0002488` / `RO:0002492` |
| `interval` | appears or resolves progressively across stages (somites, arch arteries, serial condensations) | `RO:0002496` / `RO:0002497` |
| `single-stage` | exists within one stage only | `RO:0002491` |

Symmetry is not the criterion. Paired structures can be progressive — forelimb
bud appears at CS12 and hindlimb at CS13, and somite pairs form in sequence over
a dozen stages. The question is whether there is an onset to name.

The point/interval distinction is the fix for what made Uberon's existing bounds
unusable: `existence starts during or after` is unfalsifiable in practice, and
3348 terms asserting "after gastrula stage" taught us nothing. A point claim can
be wrong, so it can be checked.

## Status

Draft. **151 axioms over 96 structures**, all `proposed` and none sourced.
55 structures carry both a start and an end bound, which is what makes a claim
refutable rather than merely true.

Coverage follows the classic human embryology curriculum, because that is where
background knowledge is reliable enough to be worth a curator's time checking:
gastrulation and the extraembryonic membranes, neurulation and the neural tube
layers, somites, the pharyngeal arches with their pouches and arch arteries,
cardiac looping and septation, the eye/ear/nose placodes, the facial
prominences, foregut derivatives, the three kidneys and the genital ducts, the
limb buds and the apical ectodermal ridge.

132 claims are `point` and 19 `interval`. The interval rows are not hedging:
somites, pharyngeal arches, arch arteries, neural crest and the generic limb bud
genuinely appear in sequence, and a point claim about them would be false rather
than merely imprecise.

What is deliberately absent: anything fetal, anything where the stage turns on a
detail I could not state without a source, and the whole of post-CS23
development. The infrastructure is exercised end to end; the content is a
seeded draft awaiting review.
