# Plan: an individual layer for reasoning about timing of existence

Draft for discussion. Nothing in the build implements this yet.

## The aim

Reason about **when developmental structures exist, relative to each other and to stages**, well
enough to drive error-checking and annotation. Two things stand in the way of doing it in OWL:

- **Composition is disjunctive.** `A starts when B ends` composed with `B starts when C ends`
  gives `A strictly after C` — fine. But most compositions yield a *set* of possible relations,
  and OWL property chains produce one definite conclusion. The full Allen composition table is
  842 chains, of which **132 are rejected by OWL 2's regularity condition** because they are
  cyclic. No amount of care works around that; it is a decidability constraint.
- **Narrowing is impossible.** Two routes giving "during-or-finishes-or-overlapped-by" and
  "overlaps-or-starts-or-during" should narrow to "during". That is object-property
  intersection, which OWL 2 does not have.

Both are closed-world, relational problems. Datalog does them in one rule and a stratified
negation respectively.

So: **a second layer, over individuals, outside OWL.** Generated from the OWL, read-only with
respect to it, feeding error reports back to curators.

Regular OWL reasoning is unaffected. Promotion of results back into OWL is a *bonus*, not a
dependency — see "deferred".

---

## 1. The modelling, in one page

Three families of relation, each internally type-consistent. Nothing spans continuant and
occurrent, so there is no category error.

```
C:C   exists_after, exists_immediately_after          continuant → continuant
O:O   preceded_by, immediately_preceded_by            occurrent  → occurrent    (the stage series)
C:O   existence_starts_during, ..._during_or_after    continuant → occurrent    (RO, already used here)
```

A developmental relation carries the **C:C** timing relation as a superproperty — both sides
continuant:

```
transformation_of  ⊑  develops_directly_from
transformation_of  ⊑  exists_immediately_after
```

Two chains then cross between families. The type arithmetic works out unaided: a chain's domain
comes from its first property and its range from its last.

```
exists_after            ∘ existence_starts_during  ⊑  existence_starts_during_or_after
existence_starts_during ∘ preceded_by              ⊑  existence_starts_during_or_after
```

**Why this and not the obvious alternatives.** Subsuming a developmental relation under BFO's
`preceded_by` makes every structure involved unsatisfiable — BFO declares continuant and
occurrent disjoint. Subsuming it under RO's `existence_*` family fails the same way, because
that family inherits `range = occurrent` from `relation between physical entity and a process or
stage`. Both failures are demonstrated, with reasoner output, in
`dev_reasoning_experiments/examples/01-broken.ofn` and `02-also-broken.ofn`.

Worked example with the chains firing: `examples/08-develops-from-timing.ofn` in that repo.
Asserting only `liver transformation_of liver_bud` — nothing about stages — ELK derives
`liver ⊑ existence_starts_during_or_after some CS11`, reaching it from a stage anchor two
developmental steps away.

---

## 2. What gets individuated

The criterion is **"exactly one per idealised organism"**, *not* "a discrete countable object".
A located mass qualifies: there is one `6th arch mesenchyme from neural crest` in an embryo.

This matters more than it sounds. Measured over EHDAA2's 2,125 `develops_from` edges that have
stage bounds on both ends:

| criterion | edges entering the individual layer |
|---|---|
| "discrete countable object" | 1,184 — 56% |
| **"one per organism"** | **2,091 — 98%** |

Under the wrong criterion the longest chain collapses from 17 to 8 and **271 terms lose their
only precursor** — `somite 21 ← trunk and cervical paraxial mesoderm`. Under the right one the
longest chain is 14 and only a handful are cut off.

What is genuinely excluded is **unenumerated populations**: `haemangioblasts`,
`primordial germ cells`, `blastemal cells`. Those stay class-level, in OWL-EL, and nothing
special happens at the boundary — an edge enters the individual layer iff both its endpoints are
individuated, and everything else is simply not expanded.

So the shape is *nearly all of developmental anatomy in the individual layer, a few cell
populations left behind* — not a small special-cased subset.

### Flagging

An annotation property on the term, so the flag is invisible to the reasoner and survives ROBOT
operations:

```
TSA:individuate  "singleton"        one per organism
TSA:individuate  "indexed:1-39"     a series; mint one individual per index
```

Index-matching between families (`myotome N` ← `dermomyotome N`) is a relation *between*
families and has no single term to hang on. It needs a small separate declaration — one line per
family pair. Without it the generator cross-products: 35 × 39 spurious edges instead of 35.

---

## 3. Pipeline

Follows the existing convention exactly — a SPARQL update over the artefact, for the same reason
`expand.ru` is one: it has to work on axioms we did not write.

```
make axioms      (unchanged)   src/axioms.tsv            → build/axioms.ofn
make scoped      (unchanged)   expand GCIs, scope terms  → build/scoped.ofn
                 ─────────────────────────────────────────────────────────
make individuate (NEW)         sparql/individuate.ru     → build/individuals.ttl
make timing      (NEW)         rules + facts             → build/timing-report.tsv
```

`individuate.ru` mints individuals with a deterministic IRI — a function of (structure, taxon,
index) — exactly as `expand.ru` mints class IRIs, so nothing has to allocate identifiers and the
mapping back to Uberon stays string surgery.

Everything new is **additive**. `build/axioms.ofn` and the contribution package are untouched.
Delete the two targets and the repo is as it was.

### Which engine

Not ELK. **ELK does not materialise ABox property chains** — 3 derived facts against HermiT's 9
on the same input. The limitation is ELK, not the EL profile; Whelk does implement them, but is
45× slower than HermiT at 5,000 individuals.

For the first pass, HermiT over the generated individuals is adequate and needs no new
dependency: 5,000 individuals in 5.5 s. If it stops being adequate, the individual layer is in
**OWL 2 RL**, which is the profile designed for rule engines, so Soufflé or RDFox becomes
available without changing the model.

The class-level layer is EL-only and stays with relation-graph. RL cannot hold it — RL bans
`∃R.C` in superclass position, which is how OBO states everything.

---

## 4. Error checking

Property-level constraints are unavailable: `DisjointObjectProperties`,
`AsymmetricObjectProperty` and `IrreflexiveObjectProperty` all require a *simple* property, and
transitivity makes `exists_after` non-simple. All three are rejected from OWL 2 DL.

Move the constraint to classes, where there is no simplicity requirement:

```
During_CS11    ≡ ∃ existence_starts_during          . CS11
AtOrAfter_CS13 ≡ ∃ existence_starts_during_or_after . CS13
DisjointClasses( During_CS11, AtOrAfter_CS13 )
```

A product asserted to start before its own precursor then becomes **unsatisfiable**, caught by
ELK, in OWL 2 EL. This is `monotonicity.rq` done as classification rather than as a query.

Generated: for 23 Carnegie stages, 46 defined classes and **253 disjointness axioms**, C(N,2)
growth, 0.6 s under ELK.

**Error output must name the source axiom, not the generated individual.** `arch_artery_3_9606
is unsatisfiable` is useless to a curator; `the develops_from assertion on UBERON:0003956 is
temporally impossible given the CS11 bound on X` is actionable. That means carrying provenance —
which asserted axiom produced which generated triple — through the expansion. Nearly free if the
generator does it from the start, painful to retrofit.

The same applies to evidence: generated individuals should inherit the evidence of the
class-level assertion they came from, or the audit trail breaks at the layer boundary.

---

## 5. First test: the pharyngeal arch system

Not the whole table. ~21 of the current 176 rows, chosen because:

- **Both endpoints are already curated** for arches 1–4, 6 and arteries 1–2
- It is **indexed**, so individuation and index-matching both get exercised
- It covers **both** `offset_type` categories in one series — arch arteries 1 and 2 regress,
  while 3 → carotid, 4 → aortic arch/subclavian, 6 → pulmonary/ductus are transformations
- Nested: artery N `part_of` arch N, pouch N `part_of` arch N
- Sourced from O'Rahilly & Müller, which the evidence pipeline already reads
- The derivatives are clinically meaningful — aortic arch anomalies

The relations that fall out of the curated bounds, computed:

```
artery N  starts  arch N            Allen s   — index-matched, exact
artery 1  vs arch 3                 Allen o   — cross-index, different relation
arch N    vs arch M                 Allen Fef — "ends with": all arches end together,
                                                their onsets stagger
```

### What it would prove, in order

1. **The chains fire on real curated data** — a structure gets timing it was never assigned.
2. **The error check catches a real error** — seed one backwards `transformation_of`; better,
   run it over all 176 rows and see whether anything already there trips.
3. **Promotion returns something new** — `pharyngeal arch artery ⊑ starts some pharyngeal arch`
   is not statable today. If promotion returns only what is already asserted, individuation
   bought nothing and we learn that cheaply.

---

## 6. Deferred

**The macro-expansion stack.** ROBOT + SPARQL for now, because the convention exists here and
costs nothing to extend. Known alternatives, if the string-handling becomes the bottleneck:
`py-horned-owl` rejects malformed axioms at construction and parses Uberon 11× faster than
rdflib; `owlready2` does not (it silently serialises a string where a class belongs). Refactoring
to either belongs on its own branch, measured against this one.

**Promotion back to OWL.** Entailable — `EquivalentClasses(Somite ObjectOneOf(...))` plus the
individual timings lets HermiT derive the class-level axiom, and a negative control confirms it
is withheld when a member violates. But it is **DL-only** (multi-individual `ObjectOneOf` is not
in EL) and costs 10 s at 500 individuals, versus microseconds for the same universal in SPARQL.
Treat as a bonus; do not build the architecture on it.

**Everything that is not developmental anatomy.** Cell-type timing, HP onset, disease
progression. Out of scope here.

---

## 7. Open decisions

- **Individual IRI scheme.** `TSA:` namespace or something Uberon-adjacent? Determines whether
  any of this can ever be contributed rather than staying local.
- **Where the C:C timing relations live.** Local to this repo until proven, or proposed to RO?
  RO currently has no continuant-to-continuant timing relation at all — the gap is real.
- **Relation names.** `exists_after` / `exists_immediately_after` are from the original sketch in
  `examples/08a-dos-original.ofn`. Worth settling before they propagate into generated artefacts.
