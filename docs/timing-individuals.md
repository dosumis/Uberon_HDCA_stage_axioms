# Plan: an individual layer for reasoning about timing of existence

Draft for discussion. Nothing in the build implements this yet.

---

## 1. Why

Reason about **when developmental structures exist, relative to each other and to stages**, well
enough to drive error-checking and annotation.

Two things block doing it in OWL:

- **Composition is disjunctive.** `A starts when B ends` ∘ `B starts when C ends` gives
  `A strictly after C`. But most compositions yield a *set* of possible relations, and a property
  chain produces one definite conclusion. The full Allen table is 842 chains, **132 of which OWL 2
  rejects** because they are cyclic and violate the regularity condition. That is a decidability
  constraint, not an implementation gap.
- **Narrowing is impossible.** Two routes giving `{during, finishes, overlapped-by}` and
  `{overlaps, starts, during}` should narrow to `during`. That is object-property intersection,
  absent from OWL 2.

Both are closed-world relational problems — one Datalog rule and one stratified negation.

So: **a second layer over individuals, generated from the OWL, read-only with respect to it.**
Regular OWL reasoning is unaffected. Promotion of results back into OWL is a *bonus*, not a
dependency (§8).

---

## 2. The modelling

Three families of relation, each internally type-consistent. Nothing spans continuant and
occurrent, so there is no category error.

```
C:C   exists_after, exists_immediately_after        continuant → continuant   ← NEW
O:O   preceded_by, immediately_preceded_by          occurrent  → occurrent    (BFO/RO, stages)
C:O   existence_starts_during, ..._during_or_after  continuant → occurrent    (RO, already used)
```

A developmental relation carries the **C:C** relation as a superproperty — both sides continuant:

```
transformation_of  ⊑  develops_directly_from
transformation_of  ⊑  exists_immediately_after
```

Two chains cross between families. The type arithmetic works out unaided — a chain's domain comes
from its first property, its range from its last:

```
exists_after            ∘ existence_starts_during  ⊑  existence_starts_during_or_after
existence_starts_during ∘ preceded_by              ⊑  existence_starts_during_or_after
```

### Why not the obvious alternatives

Both fail, with reasoner output, in `dev_reasoning_experiments/examples/`:

| | |
|---|---|
| `transformation_of ⊑ BFO:preceded_by` | **unsatisfiable** — BFO declares continuant and occurrent disjoint (`01-broken.ofn`) |
| `transformation_of ⊑ RO:0002583` | **unsatisfiable** — the `existence_*` family inherits `range = occurrent` from RO:0002581 (`02-also-broken.ofn`) |

Working version: `08-develops-from-timing.ofn`. Asserting only `liver transformation_of
liver_bud` — nothing about stages — ELK derives `liver ⊑ existence_starts_during_or_after some
CS11`, reaching it from a stage anchor two developmental steps away.

---

## 3. What gets individuated

The criterion is **"exactly one per idealised organism"**, *not* "a discrete countable object".
A located mass qualifies: there is one `6th arch mesenchyme from neural crest` per embryo.

Measured over EHDAA2's 2,125 `develops_from` edges with stage bounds on both ends:

| criterion | edges entering the individual layer | longest chain | terms losing their only precursor |
|---|---|---|---|
| "discrete countable object" | 1,184 — 56% | 8 | 271 |
| **"one per organism"** | **2,091 — 98%** | **14** | ~8 |

Under the wrong criterion `somite 21 ← trunk and cervical paraxial mesoderm` is cut, severing the
somite series from its origin. Under the right one almost nothing is lost.

Excluded: **unenumerated populations** — `haemangioblasts`, `primordial germ cells`,
`blastemal cells`. These stay class-level in OWL-EL. **No boundary convention is needed**: an
edge enters the individual layer iff both endpoints are individuated, and everything else is
simply not expanded. The two layers are parallel, not stitched together.

---

## 4. Naming

### Individual IRIs

Follows `expand.ru`'s minting convention — deterministic, a pure function of the inputs, so
nothing has to allocate identifiers:

```
https://w3id.org/taxon-stage-axioms/individual/{UBERON_LOCAL}-{TAXON_LOCAL}[-{INDEX}]

  .../individual/UBERON_0003956-9606        singleton
  .../individual/UBERON_0002539-9606-03     third member of an indexed series
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
http://purl.obolibrary.org/obo/uberon/core#exists_immediately_after
```

**Aim: promote to RO once the experiments show it worthwhile.** RO currently has *no*
continuant-to-continuant timing relation at all — the gap is real, and this is the evidence
needed to argue for filling it. Until then, no OBO IDs are minted.

---

## 5. Files to add

```
src/timing/relations.ofn          the three families + chains + the two new relations  (~40 lines)
src/timing/individuate.tsv        which terms expand, and how
src/timing/families.tsv           index-matched family pairs
sparql/individuate.ru             mint individuals + OPAs from the flagged terms
sparql/checks/timing.rq           report, keyed on the SOURCE axiom
src/taxon_stage/disjointness.py   generate the stage-disjointness module
tests/test_timing.py              entailment assertions
```

### `src/timing/relations.ofn`

The only genuinely new modelling. Declares the two C:C relations, the subproperty links from the
developmental relations, and the two chains. Everything else is imported RO/BFO.

```
Prefix(uc:=<http://purl.obolibrary.org/obo/uberon/core#>)
Prefix(obo:=<http://purl.obolibrary.org/obo/>)

Declaration(ObjectProperty(uc:exists_after))
Declaration(ObjectProperty(uc:exists_immediately_after))
TransitiveObjectProperty(uc:exists_after)
SubObjectPropertyOf(uc:exists_immediately_after uc:exists_after)

# developmental relations carry the C:C relation
SubObjectPropertyOf(obo:RO_0002495 uc:exists_immediately_after)   # immediate transformation of
SubObjectPropertyOf(obo:RO_0002494 uc:exists_after)               # transformation of
SubObjectPropertyOf(obo:RO_0002202 uc:exists_after)               # develops from

# the two chains
SubObjectPropertyOf(ObjectPropertyChain(uc:exists_after obo:RO_0002488) obo:RO_0002496)
SubObjectPropertyOf(ObjectPropertyChain(obo:RO_0002488 obo:BFO_0000062) obo:RO_0002496)
```

### `src/timing/individuate.tsv`

Flagged via an annotation property so it is invisible to the reasoner and survives ROBOT
operations. Two columns, plus the usual provenance:

```
uberon_id        individuate      note
UBERON:0003956   singleton        one pharyngeal arch artery 3 per embryo
UBERON:0002539   indexed:1-39     somites
UBERON:0009611   excluded         unenumerated population — haemangioblasts
```

Emitted into the artefact as `TSA:individuate "singleton"` etc. before `individuate.ru` runs.

### `src/timing/families.tsv`

Index-matching is a relation *between* families and has no single term to hang an annotation on.
Without it the generator cross-products — 35 × 39 spurious edges instead of 35.

```
product_id       precursor_id     relation
UBERON:0003082   UBERON:0005156   RO:0002495      # myotome N ← dermomyotome N
```

---

## 6. Pipeline

Additive. `build/axioms.ofn` and the contribution package are untouched; delete the two targets
and the repo is as it was.

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

### Which reasoner

**Not ELK** — it does not materialise ABox property chains (3 derived facts against HermiT's 9
on the same input). The limitation is ELK, not the EL profile; Whelk implements them but is 45×
slower than HermiT at 5,000 individuals.

HermiT is adequate here and adds no dependency: 5,000 individuals in 5.5 s. If it stops being
adequate, the individual layer is in **OWL 2 RL** — the profile designed for rule engines — so
Soufflé or RDFox becomes available without changing the model.

The class-level layer stays EL with relation-graph. RL cannot hold it: RL bans `∃R.C` in
superclass position, which is how OBO states everything.

---

## 7. Error checking

Property-level constraints are unavailable — `DisjointObjectProperties`,
`AsymmetricObjectProperty` and `IrreflexiveObjectProperty` all require a **simple** property, and
transitivity makes `exists_after` non-simple. All three are rejected from OWL 2 DL.

Move the constraint to classes, where there is no simplicity requirement:

```
During_CS11    ≡ ∃ existence_starts_during          . CS11
AtOrAfter_CS13 ≡ ∃ existence_starts_during_or_after . CS13
DisjointClasses( During_CS11, AtOrAfter_CS13 )
```

A product asserted to start before its own precursor becomes **unsatisfiable**, caught by ELK, in
OWL 2 EL. This is `monotonicity.rq` as classification rather than query. Generated by
`src/taxon_stage/disjointness.py`: for 23 Carnegie stages, 46 defined classes and **253
disjointness axioms**, C(N,2) growth, 0.6 s under ELK.

### Two things the generator must do from the start

**Report against the source axiom, not the generated individual.** `UBERON_0003956-9606-03 is
unsatisfiable` is useless to a curator. The report needs to name the asserted axiom and the row
of `src/axioms.tsv` it came from. That means `individuate.ru` emits a provenance triple per
generated OPA — `TSA:derived_from` pointing at the source restriction — and
`sparql/checks/timing.rq` joins through it.

**Carry evidence across the boundary.** This repo is rigorous about evidence per axiom. A
generated individual should inherit the evidence annotation of the class-level assertion it came
from, or the audit trail breaks exactly where the new reasoning starts.

Both are nearly free if designed in, painful to retrofit.

---

## 8. First test: the pharyngeal arch system

~21 of the current 176 rows, chosen because:

- **Both endpoints already curated** for arches 1–4, 6 and arteries 1–2
- **Indexed**, so individuation and index-matching are both exercised
- Covers **both** `offset_type` categories in one series — arteries 1 and 2 regress; 3 → carotid,
  4 → aortic arch/subclavian, 6 → pulmonary/ductus are transformations
- Nested: artery N `part_of` arch N, pouch N `part_of` arch N
- Sourced from O'Rahilly & Müller, which the evidence pipeline already reads
- Clinically meaningful derivatives — aortic arch anomalies

Relations computable from the curated bounds today:

```
artery N  starts  arch N      Allen s    index-matched, exact
artery 1  vs arch 3           Allen o    cross-index, a different relation
arch N    vs arch M           Allen Fef  "ends with" — all arches end together,
                                         onsets stagger
```

### What it proves, in order

1. **The chains fire on real curated data** — a structure gets timing it was never assigned.
2. **The error check catches a real error** — seed one backwards `transformation_of`; better,
   run over all 176 rows and see whether anything already present trips it.
3. **Promotion returns something new** — `pharyngeal arch artery ⊑ starts some pharyngeal arch`
   is not statable today. If promotion returns only what is already asserted, individuation
   bought nothing, and we learn that cheaply.

---

## 9. Deferred

**The macro stack.** ROBOT + SPARQL, because the convention exists here and costs nothing to
extend. If string handling becomes the bottleneck: `py-horned-owl` rejects malformed axioms at
construction and parses Uberon 11× faster than rdflib; `owlready2` does neither — it silently
serialises a string where a class belongs. Refactoring belongs on its own branch, measured
against this one.

**Promotion back to OWL.** Entailable: `EquivalentClasses(C ObjectOneOf(...))` plus individual
timings lets HermiT derive the class-level axiom, and a negative control confirms it is withheld
when a member violates. But **DL-only** — multi-individual `ObjectOneOf` is not in EL — and 10 s
at 500 individuals against microseconds for the same universal in SPARQL. A bonus; do not build
on it.

**Everything that is not developmental anatomy.** Cell-type timing, HP onset, disease
progression.

---

## 10. Still open

- **Relation names.** `exists_after` / `exists_immediately_after` are from the original sketch in
  `dev_reasoning_experiments/examples/08a-dos-original.ofn`. Worth settling before they propagate
  into generated artefacts and the RO proposal.
- **Whether `develops_from` itself should carry `exists_after`.** §2 assumes yes. Measured
  against EHDAA2, 18% of `develops_from` assertions have the precursor demonstrably still present
  when the product appears, so the weaker `exists_after` holds while `preceded_by` would not —
  but that is one dataset.
- **Whether the arch series alone is enough to judge.** It exercises the machinery but is small;
  a second series with different shape (the somites, which stagger over 5 stages) would test more.
