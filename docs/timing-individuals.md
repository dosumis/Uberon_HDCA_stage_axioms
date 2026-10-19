# Plan: an individual layer for reasoning about timing of existence

**Status: draft for discussion. Nothing in the build implements this yet.**

> **New to this?** Read §1–§3. §1 is what this repo does today and the questions it cannot
> answer; §2 is the central idea — reading an anatomy ontology as an atlas of one idealised
> individual; §3 is what this proof of concept tests and, just as important, what it
> deliberately does not. §4 is a key to the notation. §5 on is implementation detail.

This plan originates in experiments in a separate repo,
[dosumis/dev_reasoning_experiments](https://github.com/dosumis/dev_reasoning_experiments). Every
reference below is pinned to commit
[`584150e`](https://github.com/dosumis/dev_reasoning_experiments/tree/584150e). That repo holds
the reasoner runs and measurements cited here; this one is the intended test bed.

---

## 1. Background: where this repo is now

This repo curates **when anatomical structures exist, relative to developmental stages**. Each
row of [`src/axioms.tsv`](../src/axioms.tsv) ties an Uberon structure to an HsapDv/MmusDv stage
with evidence. 176 rows today, using four RO predicates:

| predicate | | rows |
|---|---|---|
| RO:0002488 | existence starts during | 101 |
| RO:0002492 | existence ends during | 54 |
| RO:0002496 | existence starts during or after | 13 |
| RO:0002497 | existence ends during or before | 8 |

`sparql/expand.ru` turns these into taxon-scoped classes; `sparql/checks/monotonicity.rq` checks
that nothing ends before it starts.

### What it cannot do

Every assertion is **structure-to-stage**. Nothing relates two structures to each other in time.
So these questions have no answer in the artefact today:

- Does the pharyngeal arch artery exist for exactly as long as its arch?
- Arch 3 starts at CS11 and arch 1 at CS10 — is that consistent with anything we assert about how
  they are developmentally related?
- A structure has a curated `develops_from` precursor but no stage bounds of its own. Can we give
  it bounds from its precursor's?

The information needed is present — stage bounds on both ends, plus Uberon's developmental
relations — but it is spread across assertions that never meet.

### Why they never meet: the category problem

The obvious move is to give `develops_from` a temporal reading. It fails on BFO typing, and the
failure is not cosmetic:

| attempt | result |
|---|---|
| `transformation_of ⊑ BFO:preceded_by` | **unsatisfiable** — BFO declares continuant and occurrent disjoint ([`01-broken.ofn`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/examples/01-broken.ofn)) |
| `transformation_of ⊑ RO:0002583` | **unsatisfiable** — the `existence_*` family inherits `range = occurrent` from RO:0002581 ([`02-also-broken.ofn`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/examples/02-also-broken.ofn)) |

Structures are continuants. Stages are occurrents. The timing relations RO offers are
continuant-to-occurrent. There is no relation in RO that puts two *structures* in temporal order,
so there is nothing for `develops_from` to be a subproperty of.

§5 is the fix for that. §2 and §3 are why we are bothering.

---

## 2. The idea: anatomy as an atlas of an idealised individual

An anatomy ontology like Uberon describes **classes**. `UBERON:0003114 pharyngeal arch 3` stands
for every pharyngeal arch 3 in every embryo that has one. That is the right representation for
nearly everything, and it stays the source of truth here — nothing below replaces it.

But the same content can be read a second way. An **anatomical atlas** does not describe classes;
it describes **one specimen** — this embryo, with these parts, laid out. The parts of a specimen
are not classes but **individuals**: not "pharyngeal arch 3" in general, but *the* pharyngeal
arch 3 *of this organism*.

Make the specimen idealised rather than real — a canonical human embryo rather than one on a
slide — and you get an **atlas of an idealised individual**: one node per structure that a normal
organism has a determinate number of. This is what developmental atlases and anatomical
nomenclature have always implicitly described, and it is what we make explicit here.

### Which structures can be individuals: countability

Not every anatomical class can take a node in such an atlas. The criterion is **countability in
the idealised organism** — does a normal organism have a determinate number of these?

| | example | atlas node |
|---|---|---|
| exactly one | liver, notochord, pharyngeal arch 3 | one individual |
| an enumerable set | somites 1–39, pharyngeal arches 1–6 | one per index |
| no determinate count | haemangioblasts, primordial germ cells, blastemal cells | **none** — stays a class |

Countability here means *determinate number*, not *discrete object you could lift out with
forceps*. There is exactly one `6th arch mesenchyme from neural crest` per embryo, so it is
countable in the sense that matters, even though it is a mass rather than an object. That
distinction is not pedantic: §6 measures it, and reading countability as "discrete object" throws
away nearly half the usable data.

Structures that fail the test are not a problem to be solved. They simply stay class-level, in
the ordinary OWL, and the atlas says nothing about them.

### What the atlas is for here: timing

An atlas node is a single thing that facts can accumulate on. This work uses that for one
purpose only: **reasoning about when structures exist, relative to each other and to stages** —
the gap §1 just described. Everything a structure's timing can be derived from — its own curated
bounds, its parts', its developmental precursors' — lands on one node instead of being spread
across unconnected class axioms. §3 states exactly what that buys and how we will know if it
bought nothing.

Spatial reasoning over an atlas is the obvious neighbouring use and is **not** attempted here.

### Where the individuals come from: macro expansion, not curation

Nothing in the atlas is hand-written. It is **generated from the existing class-level OWL** by
macro expansion:

```
class-level OWL              annotation tag            generated atlas
(Uberon + this repo's    ──  TSA:individuate   ──▶     one individual per tagged
 curated stage bounds)       marks countable           term per taxon, carrying
                             terms                     that term's axioms as
                                                       property assertions
```

A curator marks a term countable with an **annotation property**; the macro does the rest. This
matters for three reasons:

- **The OWL stays canonical.** The atlas is a build artefact, regenerated from source every time.
  There is no second representation to keep in step with the first.
- **Annotations are invisible to the reasoner.** Tagging a term changes no entailment and
  survives ROBOT operations, so the flag can live alongside the curation it describes.
- **The boundary needs no convention.** A relation is expanded into the atlas iff **both** its
  endpoints are tagged. Everything else is simply not expanded — the class layer and the atlas
  run in parallel rather than being stitched together at a seam somebody has to define.

§6 covers what gets tagged, §7 the files, §9 the pipeline.

---

## 3. Aims: what this POC tests

§2's atlas is the method. This is the claim it is being used to test, stated so that it can
fail:

> **Generating an atlas of idealised individuals from the class-level OWL lets timing information
> that is today spread across unconnected class axioms meet at a single node, and produces
> structure-to-structure timing that nobody curated.**

Individuation buys exactly three things. All three are unavailable at class level:

1. **Two derivation routes meet.** `arch_artery_3-9606` carries both its own curated bounds *and*
   whatever arrives along `part_of` from `arch_3-9606`. At class level these are separate
   `∃R.C` restrictions on separate classes with no node in common. On one individual they are
   constraints on one thing, and can be combined.
2. **Chains are walkable in both directions.** `A ⊑ ∃R.B` does not entail `B ⊑ ∃R⁻.A`, so
   class-level chains run one way only. Property assertions between individuals do not have that
   problem — given the inverse, you can ask "what derives from this?" as readily as "what does
   this derive from?".
3. **Per-individual timing.** Arches 1–6 are six classes with six different onsets. A class-level
   statement about "pharyngeal arch" has to hold for all of them, so it collapses to the
   weakest. Individuals keep them apart.

### Success and failure criteria

| | |
|---|---|
| **Succeeds if** | the chains derive timing for a structure that was never assigned any, on real curated rows, and the error check flags at least one genuine conflict (or demonstrably clears all 176) |
| **Fails if** | everything derived was already asserted — then individuation bought nothing, and we have learned that for the cost of one branch |

### Explicitly *not* in this POC

This matters, because an earlier draft justified the layer by capabilities it does not deliver.

**Allen path-consistency and narrowing are deferred.** The long-run motivation for an individual
layer is full interval reasoning: composing relations and narrowing disjunctive labels. Neither
is possible in OWL —

- *Composition is disjunctive.* Most compositions yield a **set** of possible relations; a
  property chain concludes exactly one. The full table is 841 compositions (29 relations × 29),
  **132 of which OWL 2 rejects** outright as cyclic under the regularity condition.
- *Narrowing is object-property intersection*, which OWL 2 does not have. Two routes giving
  `dfO` and `osd` should narrow to `d`. In OWL they cannot be combined at all.

Both are closed-world problems, natural in Datalog — one rule for composition, stratified
negation for narrowing — and
[REASONING_STACK.md](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/REASONING_STACK.md)
measures that case. **This POC does none of it.** §9 runs HermiT over OWL individuals, which is
still open-world: it materialises chains and detects contradictions, and that is all. The three
benefits listed above do not require narrowing, which is why the POC is worth running before
committing to a Datalog stack. If it succeeds, Soufflé is the next branch, not this one.

---

## 4. Notation

**Allen interval relations.** Thirteen atomic relations between two intervals, written as single
letters. Lower case and its upper-case partner are converses of each other:

| | relation of X to Y | converse |
|---|---|---|
| `p` | precedes (gap) | `P` preceded by |
| `m` | meets (X ends exactly as Y starts) | `M` met by |
| `o` | overlaps | `O` overlapped by |
| `F` | finished by | `f` finishes |
| `D` | contains | `d` during |
| `s` | starts | `S` started by |
| `e` | equals | `e` (self-converse) |

A string of letters is a **disjunction** — the relation is one of these but we do not know which.
`dfOMP` means "`d` or `f` or `O` or `M` or `P`". `M*` is the transitive closure of `M`, which
computes to `MP`.

Intervals here are **existence intervals**: for a structure, the span from when it first exists
to when it ceases; for a stage, the stage itself.

**Prefixes.** `uc:` = `http://purl.obolibrary.org/obo/uberon/core#`, `obo:` =
`http://purl.obolibrary.org/obo/`, `TSA:` = this repo's annotation namespace.

---

## 5. The modelling

Three families of relation, each internally type-consistent. No *single* relation has a
continuant on one side and an occurrent on the other — the C:O family spans the categories by
design, but it is RO's existing family and is already typed for it.

```
C:C   exists_after, exists_directly_after,          continuant → continuant   ← NEW
      exists_immediately_after
O:O   preceded_by, immediately_preceded_by          occurrent  → occurrent    (BFO/RO, stages)
C:O   existence_starts_during, ..._during_or_after  continuant → occurrent    (RO, already used)
```

The new C:C family has **three levels**, each a strict subset of its parent:

| relation | Allen | means |
|---|---|---|
| `exists_after` | `dfOMP` | product starts later; a gap is allowed |
| `exists_directly_after` | `dfOM` | **no gap** — product starts at or before the precursor ends |
| `exists_immediately_after` | `M` | precursor ends exactly when the product starts |

A developmental relation carries the appropriate level as a superproperty. Both sides are
continuants, so no category error:

```
develops_from                ⊑  exists_after               weakest; a gap is allowed
transformation_of            ⊑  exists_after               closure is M* = MP ⊆ dfOMP
directly_develops_from       ⊑  exists_directly_after      no gap
immediate_transformation_of  ⊑  exists_immediately_after    Allen M, exact
```

Two chains cross between families, carrying structure-to-structure timing into the
structure-to-stage vocabulary the repo already curates. The type arithmetic works out unaided — a
chain takes its domain from its first property and its range from its last:

```
exists_after            ∘ existence_starts_during  ⊑  existence_starts_during_or_after
existence_starts_during ∘ preceded_by              ⊑  existence_starts_during_or_after
```

**This is the step that makes the layer pay.** Asserting only `liver transformation_of
liver_bud` — nothing about stages — ELK derives `liver ⊑ existence_starts_during_or_after some
CS11`, reaching a stage anchor two developmental steps away
([`08-develops-from-timing.ofn`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/examples/08-develops-from-timing.ofn)).

### Why no relation for budding

`dfOM = M ⊎ dfO`, a **disjoint** union, verified against the composition table. So directness
decomposes exactly into transformation (`M`, precursor ends) and budding/delamination (`dfO`,
precursor persists) — and budding needs no name of its own, because it is *directness minus
transformation*.

Neural crest delaminating from a persisting neural tube is therefore just
`directly_develops_from`: it entails `dfOM`, transformation is not asserted, and the surviving
disjunction permits `dfO`.

Under a later closed-world layer this becomes computable rather than merely permitted —

```
budding(X,Y) :- directly_develops_from(X,Y), not immediate_transformation_of(X,Y).
```

— but that is stratified negation, and per §3 it is **not** part of this POC. Here you get the
honest `dfOM` disjunction and nothing more.

> **This contradicts RO's current definition of RO:0002207, and the POC proceeds anyway.**
> That definition says `start(x) ≥ end(y)` — Allen `MP` — which mandates the precursor has ended
> and so forbids the neural-crest case outright. We take the relation to mean what it evidently
> intends. §14 lists everything RO would have to change for this work to be contributable.

**Caveat on `dfOM`**: it is *not* in the composition-closed 29-relation subalgebra — it is a
union, and unions are not generated from the atoms by composition, converse and intersection. So
it is assertable and composable *through*, but never the tightest derived result. The same is
true of RO's `preceded_by`.

---

## 6. What gets individuated

§2 gave the criterion as countability in the idealised organism. The sharp form is
**"exactly one per idealised organism"**, *not* "a discrete countable object" — and the
difference between those two readings is large enough to measure.

A located mass qualifies under the first and fails the second: there is one
`6th arch mesenchyme from neural crest` per embryo, so it is countable in the sense that
matters, though you could not lift it out as an object.

Measured over EHDAA2's 2,125 `develops_from` edges with stage bounds on both ends:

| criterion | edges entering the individual layer | longest chain | terms losing their only precursor |
|---|---|---|---|
| "discrete countable object" | 1,184 — 56% | 8 | 271 |
| **"one per organism"** | **2,091 — 98%** | **14** | ~8 |

Under the wrong criterion `somite 21 ← trunk and cervical paraxial mesoderm` is cut, severing the
somite series from its origin. Under the right one almost nothing is lost.

Excluded: **unenumerated populations** — `UBERON:0010531 metanephros induced blastemal cells`,
haemangioblasts, primordial germ cells. These stay class-level in OWL-EL. **No boundary convention is needed**: an edge
enters the individual layer iff both endpoints are individuated, and everything else is simply
not expanded. The two layers are parallel, not stitched together.

### Two kinds of series, and only one is in scope

This distinction caused confusion in an earlier draft, so it is worth stating plainly.

**Separately-termed series — in scope.** Pharyngeal arches 1, 2, 3, 4, 6 each have their own
Uberon term, each with its own curated bounds. Each expands to **one** individual. Per-index
timing comes from the curation that already exists:

```
UBERON:0004362  pharyngeal arch 1   starts CS10
UBERON:0003114  pharyngeal arch 3   starts CS11
UBERON:0003115  pharyngeal arch 4   starts CS12
```

These are singletons as far as the generator is concerned. The staggering is real and already
curated.

**Minted-index series — deferred.** Somites 1–39 share a single Uberon term,
`UBERON:0002329 somite`. Minting 39 individuals from it would give all 39 the same bounds,
because that is all the source has. The staggered onset that makes the somite series
interesting **is not in Uberon and is not in this repo**, so the individuals would carry no
information their shared parent did not. Minting them would be machinery without a payload.

Deferred until there is a source for per-index bounds. §13 notes what that would take.

---

## 7. Naming

### Individual IRIs

Follows `expand.ru`'s minting convention — deterministic, a pure function of the inputs, so
nothing has to allocate identifiers:

```
https://w3id.org/taxon-stage-axioms/individual/{UBERON_LOCAL}-{TAXON_LOCAL}[-{INDEX}]

  .../individual/UBERON_0003120-9606        pharyngeal arch artery 3, human
  .../individual/UBERON_0002329-9606-21     21st somite — the deferred minted-index case
```

The `/individual/` path segment is the marker. These are **build artefacts of a macro expansion
and are not for publication** — but if one leaks it is readable and traceable back to its source
term and taxon by string surgery, which is the same property `expand.ru`'s `scoped/` IRIs have.

### New relation IRIs

Uberon already carries 24 object properties without OBO IDs under `uberon/core#` —
`anastomoses_with`, `channel_for`, `distally_connected_to`, `extends_fibers_into`. The new C:C
relations follow that established pattern:

```
http://purl.obolibrary.org/obo/uberon/core#exists_after
http://purl.obolibrary.org/obo/uberon/core#exists_directly_after
http://purl.obolibrary.org/obo/uberon/core#exists_immediately_after
```

`exists_directly_after` deliberately parallels `directly_develops_from` — "directly" carries the
no-gap sense in both.

**Aim: promote to RO once the experiments show it worthwhile.** RO currently has *no*
continuant-to-continuant timing relation at all — the gap is real, and this is the evidence
needed to argue for filling it. Until then, no OBO IDs are minted.

---

## 8. Files to add

```
src/timing/relations.ofn          the three C:C relations + subproperty links + chains  (~40 lines)
src/timing/individuate.tsv        which terms expand, and how
src/timing/families.tsv           index-matched family pairs
sparql/individuate.ru             mint individuals + OPAs from the flagged terms
sparql/checks/timing.rq           report conflicts, keyed on the SOURCE axiom
src/taxon_stage/disjointness.py   generate the stage-disjointness module
tests/test_timing.py              entailment assertions
```

### `src/timing/relations.ofn`

The only genuinely new modelling. Declares the three C:C relations, the subproperty links from
the developmental relations, and the two chains. Everything else is imported RO/BFO.

```
Prefix(uc:=<http://purl.obolibrary.org/obo/uberon/core#>)
Prefix(obo:=<http://purl.obolibrary.org/obo/>)

Declaration(ObjectProperty(uc:exists_after))
Declaration(ObjectProperty(uc:exists_directly_after))
Declaration(ObjectProperty(uc:exists_immediately_after))
TransitiveObjectProperty(uc:exists_after)
SubObjectPropertyOf(uc:exists_directly_after    uc:exists_after)
SubObjectPropertyOf(uc:exists_immediately_after uc:exists_directly_after)

# developmental relations carry the appropriate level
SubObjectPropertyOf(obo:RO_0002202 uc:exists_after)               # develops from
SubObjectPropertyOf(obo:RO_0002494 uc:exists_after)               # transformation of (M* = MP)
SubObjectPropertyOf(obo:RO_0002207 uc:exists_directly_after)      # directly develops from *
SubObjectPropertyOf(obo:RO_0002495 uc:exists_immediately_after)   # immediate transformation of
# * contradicts RO:0002207's current definition, deliberately -- see 14

# the two chains
SubObjectPropertyOf(ObjectPropertyChain(uc:exists_after obo:RO_0002488) obo:RO_0002496)
SubObjectPropertyOf(ObjectPropertyChain(obo:RO_0002488 obo:BFO_0000062) obo:RO_0002496)
```

`transformation_of` gets the **weakest** level, not `exists_directly_after`: its transitive
closure is `M* = MP`, and `P` (a gap) is outside `dfOM`. Verified against the composition table.

### `src/timing/individuate.tsv`

Flagged via an annotation property so it is invisible to the reasoner and survives ROBOT
operations. Same provenance columns as `src/axioms.tsv`, abbreviated here:

```
uberon_id       uberon_label                         individuate  curator  date        note
UBERON:0003120  pharyngeal arch artery 3             singleton    dos      2026-10-18  one per embryo
UBERON:0002329  somite                               excluded     dos      2026-10-18  minted-index, deferred (6)
UBERON:0010531  metanephros induced blastemal cells  excluded     dos      2026-10-18  unenumerated population
```

Emitted into the artefact as `TSA:individuate "singleton"` before `individuate.ru` runs.

### `src/timing/families.tsv`

Index-matching is a relation *between* families and has no single term to hang an annotation on.
Without it the generator cross-products — every artery against every arch instead of each
against its own index.

```
product_id      precursor_id    relation     note
UBERON:0003120  UBERON:0003114  RO:0002202   # arch artery 3 develops from arch 3
```

---

## 9. Pipeline

Additive. `build/axioms.ofn` and the contribution package are untouched; delete the targets and
the repo is as it was.

### Which engine runs what

Three passes, in different profiles, for different reasons. An earlier draft blurred these.

| pass | input | engine | profile | detects |
|---|---|---|---|---|
| A — class-level conflict check | scoped classes + disjointness module | **ELK** | EL | unsatisfiable class → names one term |
| B — individual materialisation | individuals + relations.ofn | **HermiT** | DL input, RL content | derives OPAs via chains |
| C — conflict report | B's output | **SPARQL** | — | conflicting timings as report rows |

Pass A is class-level and stays with ELK — that is where the existing build already lives. Pass B
needs HermiT because **ELK does not materialise ABox property chains** (3 derived facts against
HermiT's 9 on the same input); the limitation is ELK's, not the EL profile's. Whelk implements
them but is 45× slower than HermiT at 5,000 individuals. HermiT handles 5,000 in 5.5 s and adds
no dependency.

The individual layer's *content* is in **OWL 2 RL** — the profile designed for rule engines — so
if HermiT stops being adequate, Soufflé or RDFox becomes available without changing the model.
The class-level layer cannot move: RL bans `∃R.C` in superclass position, which is how OBO states
everything.

```makefile
$(BUILD)/individuals.ttl: $(BUILD)/scoped.ofn src/timing/relations.ofn sparql/individuate.ru
	$(ROBOT) merge --input $(BUILD)/scoped.ofn --input src/timing/relations.ofn \
	  --output $(BUILD)/timing-input.ofn
	$(ROBOT) query --input $(BUILD)/timing-input.ofn --update sparql/individuate.ru --output $@

individuate: $(BUILD)/individuals.ttl   ## mint individuals for flagged terms

$(BUILD)/timing-report.tsv: $(BUILD)/individuals.ttl
	$(ROBOT) reason --reasoner HermiT --input $< --axiom-generators PropertyAssertion \
	  --output $(BUILD)/timing-reasoned.ofn
	$(ROBOT) query --input $(BUILD)/timing-reasoned.ofn --query sparql/checks/timing.rq $@

timing: $(BUILD)/timing-report.tsv      ## derive timings and report conflicts
```

### `sparql/individuate.ru`, in outline

Same shape as `expand.ru` — a SPARQL update over the artefact, because it has to work on axioms
we did not write.

```
BIND(REPLACE(STR(?struct), "^.*[/#]", "") AS ?structLocal)
BIND(REPLACE(STR(?taxon),  "^.*[/#]", "") AS ?taxonLocal)
BIND(IRI(CONCAT("https://w3id.org/taxon-stage-axioms/individual/",
                ?structLocal, "-", ?taxonLocal)) AS ?ind)
```

It fires where a scoped class carries `TSA:individuate`, mints the individual, types it to the
scoped class, and carries each `existence_*` and developmental restriction down to an OPA between
the corresponding individuals. It only fires where **both** endpoints are individuated, which is
what keeps the layer boundary from needing a convention.

---

## 10. Error checking

### The constraint has to live on classes

Property-level constraints are unavailable. `DisjointObjectProperties`, `AsymmetricObjectProperty`
and `IrreflexiveObjectProperty` all require a **simple** property, and transitivity makes
`exists_after` non-simple. All three are rejected from OWL 2 DL.

Move the constraint to classes, where there is no simplicity requirement:

```
During_CS11    ≡ ∃ existence_starts_during          . CS11
AtOrAfter_CS13 ≡ ∃ existence_starts_during_or_after . CS13
DisjointClasses( During_CS11, AtOrAfter_CS13 )
```

A product asserted to start before its own precursor becomes **unsatisfiable**. This is
`monotonicity.rq` as classification rather than query. Generated by
`src/taxon_stage/disjointness.py`: for 23 Carnegie stages, 46 defined classes and **253
disjointness axioms**, C(N,2) growth, 0.6 s under ELK.

### Decision: the disjointness module runs in pass A only, never against the individuals

This is a design decision, not a detail, because the two layers fail differently:

| | class level (pass A, ELK) | individual level (pass B, HermiT) |
|---|---|---|
| a conflict shows up as | an **unsatisfiable class** | an **inconsistent ABox** |
| what it points at | one named term | nothing — inconsistency is global |
| what `robot reason` does | reports the class, build continues | **fails outright, produces no output** |

An inconsistent ABox would take the whole report down with it, so a single bad row would hide
every other result — the opposite of what the next subsection requires.

So: **the disjointness module is merged into pass A and excluded from pass B.** Pass B stays
satisfiable by construction and its conflicts are found by pass C, as SPARQL rows over the
materialised output — a conflict becomes a line in a report, not a build failure. Both checks run;
neither can silence the other.

### Two things the generator must do from the start

**Report against the source axiom, not the generated individual.**
`UBERON_0003120-9606 is unsatisfiable` is useless to a curator. The report needs to name the
asserted axiom and the row of `src/axioms.tsv` it came from. That means `individuate.ru` emits a
provenance triple per generated OPA — `TSA:derived_from` pointing at the source restriction — and
`sparql/checks/timing.rq` joins through it.

**Carry evidence across the boundary.** This repo is rigorous about evidence per axiom. A
generated individual should inherit the evidence annotation of the class-level assertion it came
from, or the audit trail breaks exactly where the new reasoning starts.

Both are nearly free if designed in, painful to retrofit.

---

## 11. First test: the pharyngeal arch system

23 of the current 176 rows, chosen because:

- **Both endpoints already curated** for arches 1–4, 6 and arteries 1–2
- **Separately termed and genuinely staggered**, so per-index timing is exercised without needing
  the deferred minted-index machinery (§6)
- Covers **both** `offset_type` categories in one series — arteries 1 and 2 regress; 3 → carotid,
  4 → aortic arch/subclavian, 6 → pulmonary/ductus are transformations
- Nested: artery N `part_of` arch N, pouch N `part_of` arch N
- Sourced from O'Rahilly & Müller, which the evidence pipeline already reads
- Clinically meaningful derivatives — aortic arch anomalies

The curated rows, which are the actual input:

```
UBERON:0004362  pharyngeal arch 1          starts CS10   ends CS17
UBERON:0003066  pharyngeal arch 2          starts CS10   ends CS17
UBERON:0003114  pharyngeal arch 3          starts CS11   ends CS17
UBERON:0003115  pharyngeal arch 4          starts CS12   ends CS17
UBERON:0003117  pharyngeal arch 6          starts CS12   ends CS17
UBERON:0003118  pharyngeal arch artery 1   starts CS10   ends CS12
UBERON:0003119  pharyngeal arch artery 2   starts CS10   ends CS13
UBERON:0003120  pharyngeal arch artery 3   starts CS11   —  (no end curated)
UBERON:0003121  pharyngeal arch artery 4   starts CS12   —
UBERON:0003123  pharyngeal arch artery 6   starts CS12   —
```

Relations computable from these bounds:

```
artery N  starts  arch N      Allen s     index-matched, exact
artery 1  vs arch 3           Allen o     cross-index, a different relation
arch N    vs arch M           Allen Fef   "ends with" — all arches end CS17,
                                          onsets stagger CS10 → CS12
```

Note arteries 3, 4 and 6 have **no curated end**. That is the clearest test available: if the
chains give them one from their arch, the layer has produced something nobody curated.

### What it proves, in order

1. **The chains fire on real curated data** — arteries 3/4/6 acquire end bounds they were never
   assigned.
2. **The error check catches a real error** — run pass A over all 176 rows and see whether
   anything already present trips it; if nothing does, seed one backwards `transformation_of`
   and confirm it is caught.
3. **Inverses are walkable** — "what develops from arch 3?" returns artery 3, which is not a
   query the class-level artefact can answer.

---

## 12. Deferred

**Allen composition and narrowing.** The long-run reason for an individual layer; see §3 for why
it is out of scope here and what it would need (Soufflé, stratified negation). This POC is partly
a test of whether that investment is justified.

**Minted-index series.** Somites, and anything else where one Uberon term covers a numbered
series. Blocked on a source for per-index bounds (§6).

**The macro stack.** ROBOT + SPARQL, because the convention exists here and costs nothing to
extend. If string handling becomes the bottleneck: `py-horned-owl` rejects malformed axioms at
construction and parses Uberon 11× faster than rdflib; `owlready2` does neither — it silently
serialises a string where a class belongs. Refactoring belongs on its own branch, measured
against this one.

**Promotion back to OWL.** Turning individual-level results into class axioms is **entailable**:
`EquivalentClasses(C ObjectOneOf(...))` plus individual timings lets HermiT derive the class-level
axiom, and a negative control confirms it is withheld when a member violates. But it is
**DL-only** — multi-individual `ObjectOneOf` is not in EL — and costs 10 s at 500 individuals
against microseconds for the same universal in SPARQL.

Treat promotion as a **manual diagnostic, not a build target**: run it once on the arch series to
see whether anything class-level falls out, because that is informative either way. Nothing in
§11's success criteria depends on it.

**Everything that is not developmental anatomy.** Cell-type timing, HP onset, disease
progression.

---

## 13. Still open

- **Whether `develops_from` itself should carry `exists_after`.** §5 assumes yes. Measured
  against EHDAA2, 18.3% of `develops_from` assertions have the precursor demonstrably still
  present when the product appears, so the weaker `exists_after` holds while `preceded_by` would
  not — but that is one dataset. Note RO *defines* `develops_from` as the transitive closure of
  `directly_develops_from`, so it inherits whatever that is fixed to mean.
- **Whether the arch series alone is enough to judge.** It exercises the machinery on real data
  but is 23 rows. A second series of different shape would test more — but the obvious candidate,
  the somites, is blocked on per-index bounds (§6). Identifying a second separately-termed
  staggered series is the cheaper path.
- **Where per-index bounds could come from** for the minted-index case. Carnegie staging
  literature gives somite counts per stage, which inverts to a per-somite onset; whether that is
  curatable at acceptable cost is unknown.

---

## 14. What RO would have to change for this to be compatible

This is a proof of concept. It asserts things RO currently contradicts, deliberately, to find
out whether the approach is worth the effort. Nothing here is contributed upstream as it stands.

If it proves out, these are the changes that would make it compatible. All are filed with
evidence in
[RO_REPORT.md](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/RO_REPORT.md).

| # | Change | Why this work needs it | Cost to RO |
|---|---|---|---|
| 1 | **Add continuant-to-continuant timing relations.** RO has none at all. | The whole C:C family is minted locally in `uberon/core#` for want of them | 3 new relations |
| 2 | **Fix the inequality in `directly develops from` (RO:0002207)**: `start(x) ≥ end(y)` → `≤`. | We link it to `exists_directly_after` (`dfOM`); RO's definition says `MP`, the near-opposite, which forbids delamination | 1 definition; relation used **once** in Uberon, never in EHDAA2, already flagged "Candidate definition" |
| 3 | **Add `starts after`** — the missing converse of `starts before` (RO:0002089). | Needed to state the weakest safe developmental claim at all | 1 relation |
| 4 | **Declare missing inverses** on `existence starts during`, `existence ends during`, `transformation of`, `immediate transformation of`, `ends after`. | Without them, chains are walkable in one direction only — which is benefit 2 of §3 | 6 axioms |

### Two we are living with rather than asking RO to change

**`develops_from` inherits whatever `directly_develops_from` is fixed to mean**, since RO defines
it as that relation's transitive closure. If change 2 lands, `develops_from` tightens with it. We
assign it the weakest level (`exists_after`) regardless, which stays sound either way —
under-committing never produces a false entailment.

**RO:0002496 / RO:0002497 are one-sided and non-strict.** `existence starts during or after` is
`α(x) ≥ α(y)`, permitting equal starts, so it is weaker than the strict `dfOMP` we reason with.
That costs recall, not soundness: fewer conflicts are detectable than would be under a strict
reading. Measured on EHDAA2, the difference is 50 detectable `develops_from` conflicts under a
strict reading against 14 under RO's actual semantics.

### What this means for the POC

Run it against a local merge of RO plus `src/timing/relations.ofn`. Do **not** expect the result
to be consistent with stock RO — change 2 in particular is a direct contradiction, and that is
the point: if the approach works, the contradiction is the argument for the fix.
