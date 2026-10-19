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
| **Succeeds if** | a structure that was never assigned a bound acquires one, derived from real curated rows; and the conflict check either flags something genuine or demonstrably clears all 176 |
| **Fails if** | everything derived was already asserted — then the atlas bought nothing, and we have learned that for the cost of one branch |

### The atlas layer does not run in OWL

The class layer stays in OWL — it is proven, it integrates with ROBOT and relation-graph, and it
is what feeds Uberon. The **atlas layer does not**, and the reason is that OWL is bad at exactly
the operations this layer exists to perform:

- *Composition is disjunctive.* Most compositions of two Allen relations yield a **set** of
  possible relations; a property chain concludes exactly one. The full table is 841 compositions
  (29 relations × 29), **132 of which OWL 2 rejects** outright as cyclic under the regularity
  condition. In Datalog the same table is **one rule** over 169 facts, and the regularity wall
  does not exist.
- *Narrowing is object-property intersection*, which OWL 2 does not have at all. Two routes
  giving `dfO` and `osd` should narrow to `d`; in OWL they cannot be combined.
- *Inconsistency is a global failure in OWL* and a **derived fact** in Datalog. That difference
  decides §10.

Each of the three benefits above is also better served outside OWL: a Datalog constant *is* a
node where routes meet; inverses are one rule (`rel(Y,X,Ri) :- rel(X,Y,R), conv(R,Ri)`) rather
than six RO inverse declarations that do not yet exist (§15, item 4).

So the split is **by layer, not by phase**: OWL/ELK for classes, Soufflé for the atlas.
[`datalog/allen.dl`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/datalog/allen.dl)
already implements composition, converse, one-round narrowing, inconsistency and promotion in 56
lines, against the verified composition table.

### The reasoning aims, deliberately limited

Three, scoped so the POC stays tractable and each can be checked by hand:

| | aim | mechanism |
|---|---|---|
| 1 | **Compute** the Allen relation between every pair of structures whose bounds are both curated | integer comparison — no propagation needed |
| 2 | **Bound** the structures whose bounds are *not* curated, from their relations to those that are | composition + one round of narrowing |
| 3 | **Flag** any pair whose label narrows to the empty set | a derived `inconsistent(X,Y)` fact |

Aim 1 is where most of the data sits and needs no interval calculus at all: Carnegie stages are a
totally ordered discrete series, so a structure with both bounds curated is a pair of integers.
**Allen earns its place only on aim 2**, which on the first test is three structures (§11).

### Explicitly *not* in this POC

- **Full path consistency.** One round of narrowing, not iterated to fixpoint — the strata do not
  simply stack, as `REASONING_STACK.md` records. §11 measures what one round costs, exactly,
  by brute force.
- **Promotion back into OWL** (§13). Deferred, and nothing here depends on it.
- **Spatial reasoning over the atlas**, and anything that is not developmental anatomy.

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

**These chains are class-level, and they already work.** Asserting only `liver
transformation_of liver_bud` — nothing about stages — ELK derives `liver ⊑
existence_starts_during_or_after some CS11`, reaching a stage anchor two developmental steps
away
([`08-develops-from-timing.ofn`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/examples/08-develops-from-timing.ofn)).

That result is the reason the class layer stays in OWL and is not re-implemented in Datalog. The
atlas layer does something different — it reasons over *intervals*, not subsumption — and §3 is
why it does so elsewhere. The two share the vocabulary in the table above: the Allen column is
the C:C relations' meaning in OWL **and** their label in the fact table.

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
> intends. §15 lists everything RO would have to change for this work to be contributable.

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

Deferred until there is a source for per-index bounds. §14 notes what that would take.

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
CLASS LAYER (OWL, unchanged in kind)
  src/timing/relations.ofn        the three C:C relations + subproperty links + chains (~40 lines)
  src/taxon_stage/disjointness.py generate the stage-disjointness module

ATLAS LAYER (Datalog)
  src/timing/individuate.tsv      which terms expand, and how
  src/timing/families.tsv         index-matched family pairs
  sparql/export-facts.rq          atlas -> Soufflé .facts, with provenance
  datalog/timing.dl               the reasoning; built on allen.dl
  datalog/stages.facts            Carnegie stage -> ordinal
  src/taxon_stage/calibrate.py    brute-force ground truth for the k<=3 case (12)
  tests/test_timing.py            assertions on derived facts
```

`datalog/timing.dl` is mostly not new work:
[`allen.dl`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/datalog/allen.dl)
already carries composition, converse, narrowing and inconsistency. What this repo adds is the
`part_of` containment rule, the stage-ordinal join, and the report.

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

Emitted into the artefact as `TSA:individuate "singleton"` before `export-facts.rq` runs.

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

| pass | input | engine | detects |
|---|---|---|---|
| A — class-level conflict check | scoped classes + disjointness module | **ELK** | unsatisfiable class → names one term |
| B — fact export | `scoped.ofn` + `relations.ofn` | **ROBOT / SPARQL** | — (translation only) |
| C — interval reasoning | the exported `.facts` | **Soufflé** | computes, composes, narrows, flags |

Pass A is class-level and stays with ELK — that is where the existing build already lives, and a
conflict there names one term. Pass B is pure translation: it walks the tagged classes and writes
Datalog facts. Pass C is the atlas layer, and runs no OWL reasoner at all.

**No HermiT pass.** An earlier draft had one, on the grounds that ELK does not materialise ABox
property chains. That is true of ELK, but it was answering the wrong question — the chains it
would have materialised are a weak shadow of what pass C computes directly (§3).

The split is forced in both directions. The atlas layer's content is in **OWL 2 RL** — the
profile designed for rule engines — which is why it ports to Soufflé (or RDFox) without changing
the model. The class layer cannot follow it: RL bans `∃R.C` in superclass position, which is how
OBO states everything.

```makefile
$(BUILD)/facts/rel.facts: $(BUILD)/scoped.ofn src/timing/relations.ofn sparql/export-facts.rq
	$(ROBOT) merge --input $(BUILD)/scoped.ofn --input src/timing/relations.ofn \
	  --output $(BUILD)/timing-input.ofn
	@mkdir -p $(BUILD)/facts
	$(ROBOT) query --input $(BUILD)/timing-input.ofn \
	  --query sparql/export-facts.rq $(BUILD)/facts/rel.facts

facts: $(BUILD)/facts/rel.facts         ## export the atlas as Datalog facts

$(BUILD)/timing-report.tsv: $(BUILD)/facts/rel.facts datalog/timing.dl
	souffle -F $(BUILD)/facts -D $(BUILD)/out datalog/timing.dl
	cp $(BUILD)/out/report.csv $@

timing: $(BUILD)/timing-report.tsv      ## derive timings, narrow, report conflicts
```

### `sparql/export-facts.rq`, in outline

Same shape as `expand.ru` — a SPARQL query over the artefact, because it has to work on axioms we
did not write. It mints the same IRIs §7 describes; they are simply Datalog constants now rather
than OWL individuals.

```
BIND(REPLACE(STR(?struct), "^.*[/#]", "") AS ?structLocal)
BIND(REPLACE(STR(?taxon),  "^.*[/#]", "") AS ?taxonLocal)
BIND(CONCAT(?structLocal, "-", ?taxonLocal) AS ?ind)
```

It fires where a scoped class carries `TSA:individuate`, and emits one fact per curated bound and
one per developmental relation, each tagged with the source axiom. It only fires where **both**
endpoints are individuated, which is what keeps the layer boundary from needing a convention.

Two fact tables come out, and the split matters because it is the §3 aim-1/aim-2 split made
concrete:

```
interval(Ind, StartOrd, EndOrd)      # both bounds curated   -> aim 1, comparison
startsAt(Ind, StartOrd)              # start only            -> aim 2, propagation
rel(X, Y, Label, SourceAxiom)        # asserted developmental relations
```

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

### The two layers detect conflicts differently, and that is the point

Moving the atlas out of OWL dissolves a problem an earlier draft had to work around:

| | class level (pass A, ELK) | atlas level (pass C, Soufflé) |
|---|---|---|
| a conflict shows up as | an **unsatisfiable class** | a derived `inconsistent(X,Y)` fact |
| what it points at | one named term | the specific pair, with its source axioms |
| effect on the rest of the run | none — build continues | **none** — it is just another row |

In OWL the atlas-level conflict would have been an **inconsistent ABox**: global, pointing at
nothing, and fatal — `robot reason` fails outright and emits no report, so one bad row would hide
every other result. The earlier draft therefore had to keep the disjointness module away from the
individuals to protect the report.

In Datalog an empty label is simply a fact you query for. Narrowing to `{}` yields
`inconsistent(X,Y)` alongside everything else that was derived, so **a conflict costs you that
pair and nothing more**. The disjointness module stays in pass A because that is where it is
cheap and where it names a term; it is not kept out of the atlas to avoid damage, because there
is no damage to avoid.

Both checks run. Neither can silence the other.

### Two things the generator must do from the start

**Report against the source axiom, not the generated individual.**
`inconsistent(UBERON_0003120-9606, UBERON_0003114-9606)` is useless to a curator. The report
needs to name the asserted axiom and the row of `src/axioms.tsv` it came from. That means
`export-facts.rq` carries a source-axiom column on every emitted fact, Soufflé propagates it
through the derivation, and the report joins back to the TSV row.

Carrying provenance through a Datalog derivation is not free — a derived fact has *many*
ancestors, so the rule heads must thread a justification term. Soufflé's provenance machinery
(`--provenance`) does this natively, which is a second reason to prefer it over hand-rolling.

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

Mapped to the three aims of §3:

1. **Aim 1 — computation.** All pairwise relations among the seven fully-curated structures fall
   out by comparison. `artery 1 o arch 3`, `arch N Fef arch M`. No interval calculus needed; if
   this does not work nothing else will.
2. **Aim 2 — propagation.** Arteries 3, 4 and 6 acquire end bounds they were never assigned.
   This is the one that justifies the layer, and the one to watch.
3. **Aim 3 — conflict.** Run over all 176 rows and see whether anything already curated trips
   `inconsistent`. If nothing does, seed one backwards `transformation_of` and confirm it is
   caught, and that the rest of the report survives it.

A fourth thing the test should demonstrate, which is not reasoning but is half the point of the
atlas: **inverses are walkable.** "What develops from arch 3?" returns artery 3 — not a question
the class-level artefact can answer.

### Calibration: exact ground truth, once

Aim 2 uses **one round of narrowing, not full path consistency** (§3). On this test we can
measure exactly what that costs, because the under-determined set is small enough to solve by
brute force.

A Carnegie-staged interval is one of C(23,2) = **253** candidates, so enumerating every
assignment to *k* under-determined structures costs 253^k:

| k | search space | time |
|---|---|---|
| 2 | 64,009 | 3 s |
| **3 — this test** | **16.2M** | **12.6 min** |
| 4 | 4.1 bn | 53 h |
| 5 | 1.0 tn | 1.5 yr |

So `calibrate.py` enumerates all 16.2M assignments for arteries 3, 4 and 6, keeps those
consistent with every curated bound, and intersects them. That is the exact answer. Comparing it
against what one round of narrowing produced tells us precisely what the cheap inference missed.

**Note what governs this**: *k*, the number of under-determined structures — **not** the number
of structures. The cliff is at k=4. This is a one-off calibration on a deliberately small open
set, not a tool that scales, and it is not meant to be one — run it once to quantify the
approximation, then never again.

---

## 12. How this scales

Measured on synthetic networks with the real composition table, 85% of pairs hidden. Python; a
Soufflé implementation of the same fixpoint runs roughly 50–100× faster.

| n | asserted | pairs after closure | exactly determined | mean label size | sec |
|---|---|---|---|---|---|
| 40 | 113 | 1,480 | 742 | 2.96 | 0.26 |
| 80 | 456 | 6,286 | 4,694 | 1.68 | 1.63 |
| 160 | 1,882 | 25,440 | 23,896 | 1.14 | 10.8 |
| 320 | 7,651 | 102,080 | 101,398 | 1.01 | 84.7 |

**Time is ~n³.** Doubling n costs about 7×. At EHDAA2 scale (~2,000 structures) that is roughly
20 billion operations — single-digit minutes in Soufflé, as a batch job. Time is not the binding
constraint.

**The closure densifies to all pairs.** At n=320, 7,651 asserted edges close to 102,080 — exactly
n(n−1). The input was 15% sparse; the output is complete. So the result is Θ(n²) in size
**regardless of input sparsity**, and memory binds before time: 4.5M pairs at n=2,000, 100M at
n=10,000. If specific answers are wanted rather than the whole closure, Soufflé's magic-set
transformation restricts evaluation to the relevant pairs.

**Precision improves as the network grows.** Mean label size falls 3.00 → 1.01 and the
exactly-determined fraction rises from 58% to 99.3%. More intervals means more triangles means
more narrowing. This inverts the usual intuition and is the strongest argument for the approach:
the thing you would expect to degrade is the thing that gets better.

**The lever is partitioning, and it is semantically forced anyway.** All-pairs closure across
developmental anatomy is not something to want — the Allen relation between a human pharyngeal
arch and a mouse metanephros is meaningless. Partition by taxon × organ system and n stays in the
tens to low hundreds, where every row above is sub-second. The arch system is 10 structures; a
whole embryo's major structures is perhaps 500.

Good enough for the POC. Alternatives — ASP for proper fixpoint narrowing, demand-driven
evaluation, incremental maintenance — are research for later, not blockers now.

---

## 13. Deferred

**Full path consistency.** The atlas runs one round of narrowing, not iteration to fixpoint —
each round depends on the previous round's negation, so the strata do not simply stack. ASP
(clingo) handles the non-monotonicity more naturally. §11 measures what one round costs on the
first test, which is the evidence needed to decide whether this matters.

**Minted-index series.** Somites, and anything else where one Uberon term covers a numbered
series. Blocked on a source for per-index bounds (§6).

**The macro stack.** ROBOT + SPARQL for fact export, because the convention exists here and costs
nothing to extend. If string handling becomes the bottleneck: `py-horned-owl` rejects malformed
axioms at construction and parses Uberon 11× faster than rdflib; `owlready2` does neither — it
silently serialises a string where a class belongs. Refactoring belongs on its own branch,
measured against this one.

**Promotion back to OWL.** Turning atlas results into class axioms. In Datalog the rule is
direct — a universal over a closed set, which is `promote(C,S)` in `allen.dl`, already written —
but emitting the result as OWL and getting it back into the class layer is a step this POC does
not take. Treat promotion as a **manual diagnostic, not a build target**: run it once on the arch
series to see whether anything class-level falls out, because that is informative either way.
Nothing in §11's success criteria depends on it.

**Spatial reasoning over the atlas**, and **everything that is not developmental anatomy** —
cell-type timing, HP onset, disease progression.

---

## 14. Still open

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

## 15. What RO would have to change for this to be compatible

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
