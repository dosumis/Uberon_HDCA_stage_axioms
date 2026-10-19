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
src/evidence/           quoted passages behind the sourced claims, + findings
src/taxon_stage/        table -> OWL, scoped classes, validation, measurement
schema/                 axioms.schema.json, evidence.schema.json
sparql/expand.ru        GCI left-hand side -> named class
sparql/checks/          monotonicity, unexpanded-GCI
sparql/extract.rq       materialised bounds back out as a table
sparql/timing/           fact export for the timing reasoner
datalog/                timing of existence between structures (Soufflé); docs/timing-individuals.md
src/timing/             curated inputs to it: singleton tags, withheld axioms
contribution/           what would go to Uberon: sourced GCIs + a review table
docs/                   design: end bounds, timing between structures
tickets/                drafted Uberon new-term requests
.claude/skills/         stage-evidence (source corpus + verifier), wiki fetch
.claude/hooks/          the Write/Edit gate that enforces the verifier
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
make timing     conflicts and bounds between structures  (needs merged-full.owl, souffle)
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
of them inherited. 462 (term, predicate, stage) facts.

Those figures are from the last full `make reach`, which predates the evidence
pass — see [Reproducing the numbers](#reproducing-the-numbers).

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

Rows leave `latent` only by acquiring a quoted passage. 60 have; 116 have not,
and each of those records in `evidence_text` what was looked for and not found,
so an examined row is distinguishable from an untouched one.

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

## Sourcing, and why it is machine-checked

The table was seeded from background knowledge, so the question is not whether
it reads plausibly — it does — but whether anything stands behind it. Sourcing
runs against a local corpus of O'Rahilly & Müller, *Developmental Stages in
Human Embryos* (Carnegie Publication 637, 1987), the reference that defines the
staging system, transcribed stage by stage and mirrored by
`.claude/skills/stage-evidence`.

Each sourced claim gets an evidence record: the source's exact words, the stage
and section they come from, and whether the source hedges. 42 records so far,
conforming to `schema/evidence.schema.json`.

A Write/Edit hook blocks anything that cannot be checked. It replays the edit
against the file first, so it sees whole records rather than the fragment being
touched, and refuses:

- a quote that is not verbatim in the document it cites, including paraphrase
  and stitched-together sentences
- a real sentence filed under a stage it did not come from
- an identifier whose label is not its own — `UBERON:0005079` beside "ureteric
  bud" reads perfectly and is the eggshell
- a hedged passage recorded as unhedged

Every refusal names the edit that repairs it, with the real value in it. The
limit is worth stating: the hook proves a quote was *copied*, not that it
*supports the claim*. Machine-picked quotes fail exactly there — the
best-scoring sentence for `allantois` at CS7 is about the chick embryo — which
is why 37 rows that read as consistent with the source still wait for a person
to choose the sentence.

### What the source said back

All 176 claims were read against it. Per-structure verdicts and the quotes are
in [`src/evidence/README.md`](src/evidence/README.md).

| | claims |
|---|---:|
| CONFIRMED | 63 |
| WEAK — rests on a hedged or indirect passage | 37 |
| NO-SOURCE — the book does not name the structure | 19 |
| OUT-OF-SCOPE — fetal; the corpus ends at CS23 | 14 |
| UNREAD — no stage-specific statement to judge against | 7 |
| OPEN — the source is not self-consistent | 6 |
| SHIFT — the source puts it at a different stage | 6 |
| CONTRADICTED | 4 |

20 rows were changed as a result: 17 stage corrections, one evidence text, and
both `pronephros` bounds superseded rather than moved — the source quotes Torrey
(1954) that "the concept of the pronephros does not apply to the human embryo",
so there is no correct stage to move them to. Superseded rows stay in the table
and drop out of the build.

The largest single correction was the neural tube marginal layer, out by three
stages. The most instructive was the ureteric bud: its CS13 start rested on "a
ureteric bud **may possibly** be present in some specimens ... although further
confirmation is needed", where CS14 states plainly that it "acquires a
metanephrogenic cap".

## Status

Draft, and the draft is now partly sourced.

**174 live axioms over 113 structures**, plus 2 superseded. 60 rows carry a
quoted passage; 116 do not and say why. 61 structures carry both a start and an
end bound, which is what makes a claim refutable rather than merely true.

155 claims are `point` and 21 `interval`. The interval rows are not hedging:
somites, pharyngeal arches, arch arteries, neural crest and the generic limb bud
genuinely appear in sequence, and a point claim about them would be false rather
than merely imprecise.

Coverage follows the classic human embryology curriculum, because that is where
background knowledge is reliable enough to be worth a curator's time checking:
gastrulation and the extraembryonic membranes, neurulation and the neural tube
layers, somites, the pharyngeal arches with their pouches and arch arteries,
cardiac looping and septation, the eye/ear/nose placodes, the facial
prominences, foregut derivatives, the three kidneys and the genital ducts, the
limb buds and the apical ectodermal ridge. A later pass added fetal rows, which
the corpus cannot reach at all.

### What is ready to go to Uberon

`make contribute` packages only what is sourced: **33 axioms over 33
structures**, all start bounds, each carrying the passage it rests on. 29 are
argued from a passage describing the structure at that stage, 4 from its absence
at an earlier one. See [`contribution/`](contribution/).

141 claims are withheld — 116 unsourced, and 25 where the source was read for
the term but no passage bears on the particular claim. Those are mostly end
bounds, for a structural reason: the evidence store records *start*, *present*
and *absent* observations and nothing recording an **end**.

### The end-bound problem

End bounds are not symmetrical with start bounds and the difference is not
laziness. A start bound is usually an observation — absent at one stage, present
at the next. Many end bounds are not: nothing disappears, the structure acquires
enough pattern that we stop calling it by the old name and start naming its
parts. When a pharyngeal arch stops being an arch is a decision about
vocabulary, not an observation about tissue.

[`docs/end-bound-convention.md`](docs/end-bound-convention.md) proposes an
`offset_type` column to confine that judgement to one category and give it a
predicate that does not overstate. Nothing in the build implements it yet.

Two things are known to be missing from that draft. The loose predicate is doing
two unrelated jobs — "we do not know the stage", which better sourcing can fix,
and "the instances genuinely differ", which it cannot, since the axioms quantify
over every instance and somites demonstrably start at different stages. And a
point bound does not survive subclass inheritance: asserted on a class whose
subclasses are staggered along an axis, it hands the children a false axiom. A
parent's bounds have to be at least as loose as every child's, which is
checkable the same way `monotonicity.rq` is and is not yet checked.

## Reproducing the numbers

`make check`, `make validate`, `make axioms`, `make materialize` and `make test`
need nothing but ROBOT and network access for identifier lookup. The round trip
currently extracts 174 rows, matching the 174 live axioms.

The reach figures above (310 terms, 462 facts) come from the last full
`make reach`, which needs `UBERON=path/to/uberon-base.owl` and relation-graph on
PATH. That run predates the evidence pass, so the stages it materialised are the
pre-correction ones and two superseded rows are still counted; re-run it before
quoting the numbers anywhere that matters.
