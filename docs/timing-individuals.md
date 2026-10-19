# Plan: reasoning about when structures exist, relative to each other

**Status: draft for discussion, with a working proof of concept on the
`timing-souffle-poc` branch (`make timing`). §10 records what it found.**

> **New to this?** §1 is what this repo does today and what it cannot answer. §2 is the one
> modelling move everything rests on: treat every structure's existence as two time points.
> §3 is the semantics table — the single source of truth, which the Datalog transcribes rule
> for rule. §4 says what an atlas node is. §5 states the hypotheses the POC tests, so they can
> fail. §6–§8 are the engine, the files and the tests. §11 is what RO would have to change.

This plan originates in experiments in
[dosumis/dev_reasoning_experiments](https://github.com/dosumis/dev_reasoning_experiments)
(references pinned to commit
[`584150e`](https://github.com/dosumis/dev_reasoning_experiments/tree/584150e)). An earlier draft
of this document reasoned over Allen interval relations directly; §2 explains why it no longer
does.

---

## 1. Background: where this repo is now

This repo curates **when anatomical structures exist, relative to developmental stages**. Each
row of [`src/axioms.tsv`](../src/axioms.tsv) ties an Uberon structure to an HsapDv stage with
evidence — 176 rows, four RO predicates:

| predicate | | rows |
|---|---|---|
| RO:0002488 | existence starts during | 101 |
| RO:0002492 | existence ends during | 54 |
| RO:0002496 | existence starts during or after | 13 |
| RO:0002497 | existence ends during or before | 8 |

### What it cannot do

Every assertion is **structure-to-stage**. Nothing relates two structures to each other in time,
so these have no answer today:

- A structure has a `develops_from` precursor but no bounds of its own. What bounds follow?
- Uberon says the otic pit is `part_of` the otic placode; the table says the pit outlives the
  placode. Which is wrong?
- Arch artery 3 has no curated end. Does anything we assert constrain it?

The information is present — stage bounds, plus Uberon's developmental and partonomic relations
— but in assertions that never meet.

### Why OWL cannot make them meet

Structures are continuants, stages occurrents, and RO's timing relations are
continuant-to-occurrent. Giving `develops_from` a temporal reading by subproperty fails on BFO
typing:

| attempt | result |
|---|---|
| `transformation_of ⊑ BFO:preceded_by` | **unsatisfiable** — continuant and occurrent are disjoint ([`01-broken.ofn`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/examples/01-broken.ofn)) |
| `transformation_of ⊑ RO:0002583` | **unsatisfiable** — `existence_*` inherits `range = occurrent` ([`02-also-broken.ofn`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/examples/02-also-broken.ofn)) |

And even with well-typed relations, OWL cannot do what timing needs: combine two constraints on
one thing, walk a relation backwards, or report a conflict without the whole ontology becoming
inconsistent. That reasoning goes to Datalog (§6). OWL keeps the class layer, unchanged.

---

## 2. The modelling move: existence as two points

Give every structure X two time points, **s(X)** (it starts to exist) and **e(X)** (it ceases),
with s(X) < e(X). Give every stage S two points, **start(S)** < **end(S)**.

Every relation this work uses then becomes a conjunction of `≤`, `<` and `=` between points —
§3 is the complete list. Nothing else is needed, and that is what makes the approach defensible:

- **It is exact.** A network of `≤ / < / =` constraints over points (the *convex point algebra*)
  is decided completely by transitive closure: it is inconsistent iff some point is strictly
  before itself, and the tightest bound on any point is what the closure entails. No
  approximation, no "one round of narrowing", no brute-force calibration, no stratified negation
  in the reasoning itself.
- **Stage granularity is handled by construction.** "Both start during CS11" is two points
  between start(CS11) and end(CS11), unordered unless something orders them. The earlier draft's
  integer-stage model read that as *equal* starts and so asserted Allen `s` and `Fef`
  relations the data does not support.
- **Stages need no ordinals.** HsapDv's own relations — `immediately_preceded_by`,
  `preceded_by`, `part_of` — become constraints between stage points. Sub-stages (CS5a–c),
  nested coarse stages ("fetal stage" ⊃ LMP months ⊃ weeks) and gaps in HsapDv's linking are all
  handled by the same mechanism. HsapDv has no CS23 → week-9 adjacency edge, yet
  end(CS23) ≤ start(9th week) is still derived through `fetal immediately_preceded_by embryonic`
  and part_of.
- **Allen relations become output, not substrate.** The Allen relation between two structures
  is read off the four endpoint comparisons after closure (§6, report).

**What it cannot express:** `≠`, and genuine disjunction ("X before Y *or* after Y"). Nothing in
RO's developmental vocabulary needs either. This is the scope boundary, stated so that a future
relation that needs one is recognised as out of scope rather than squeezed in.

### Notation

`dfOMP` etc. are Allen relation sets: `p m o F D s e S d f O M P` are the thirteen atoms, lower
and upper case converse to each other, a string is a disjunction. They appear only as names for
endpoint patterns in §3 and in the report.

---

## 3. The semantics table

The single source of truth. [`datalog/semantics.dl`](../datalog/semantics.dl) transcribes it
**one rule per row**; a reviewer checks the program against this table and nothing else.

### Stage relations (from HsapDv)

| relation | constraint |
|---|---|
| every stage S | start(S) < end(S) |
| A `immediately_preceded_by` B (RO:0002087) | end(B) = start(A) |
| A `preceded_by` B (BFO:0000062) | end(B) ≤ start(A) |
| A `part_of` B (BFO:0000050) | start(B) ≤ start(A), end(A) ≤ end(B) |

### Structure-to-stage (the curated table, and any such GCI in Uberon)

| relation | constraint |
|---|---|
| every structure X | s(X) < e(X) |
| starts during S (RO:0002488) | start(S) ≤ s(X) < end(S) |
| starts during or after S (RO:0002496) | start(S) ≤ s(X) |
| ends during S (RO:0002492) | start(S) ≤ e(X) < end(S) |
| ends during or before S (RO:0002497) | e(X) < end(S) |
| exists during S (RO:0002491) | start(S) ≤ s(X), e(X) ≤ end(S) |

### Structure-to-structure (Uberon)

| relation | Allen (X to Y) | constraint | when Y is not a singleton (§4) |
|---|---|---|---|
| X `develops_from` Y (RO:0002202) | `dfOMP` | s(Y) < s(X) | unchanged |
| X `directly_develops_from` Y (RO:0002207) | `dfOM` | s(Y) < s(X) ≤ e(Y) | unchanged |
| X `transformation_of` Y (RO:0002494) | `MP` | e(Y) ≤ s(X) | **weakens to** s(Y) < s(X) |
| X `immediate_transformation_of` Y (RO:0002495) | `M` | e(Y) = s(X) | **weakens to** s(Y) < s(X) ≤ e(Y) |
| X `part_of` Y (BFO:0000050) — **H1** | `sdfe` | s(Y) ≤ s(X), e(X) ≤ e(Y) | unchanged |
| X `SubClassOf` Y | — | s(Y) ≤ s(X), e(X) ≤ e(Y) | (windows only) |

`directly_develops_from` has a switch: compiled with `-M RO_2207_AS_DEFINED` it takes RO's
current text, e(Y) ≤ s(X). §11 explains why the default departs from it.

### Class axioms are inherited

Uberon states everything as all-some class axioms, so a relation or bound on G holds of every
subclass M. The Datalog applies that directly: **every structure-to-stage and
structure-to-structure axiom on G is also an axiom on each subclass M** (provenance preserved).
This is the inheritance OWL would perform, done where the reasoning happens — and it is what
makes the README's open problem detectable: a point bound asserted on a generic class whose
subclasses are staggered now *conflicts* with the subclass's own bound instead of silently
handing it a false one.

---

## 4. What an atlas node is: an existence window

An anatomy ontology describes classes. The reasoning needs things with a start and an end. The
bridge is the **existence window**: for a class C in the idealised organism of one taxon, C*
runs from when its first instance starts to when its last instance ends.

- For a structure there is exactly one of — arch 3, the liver — the window *is* the structure's
  lifetime. This is the atlas-of-an-idealised-individual reading.
- For a series or a population — "pharyngeal arch", somites, haemangioblasts — it is the hull of
  all of them.

Working each row of §3 through under Uberon's all-some reading: every constraint **except the two
transformation relations holds exactly on windows**. (Example: if every X develops from some Y,
then the first X starts after *some* Y started, hence after the first Y started.) The two
transformations degrade because "each X starts when *some* Y ends" says nothing about when the
*last* Y ends — unless there is only one Y. So exactness needs only the **precursor** to be a
singleton; X may be anything.

Consequences:

- **Every term can take part**, not only countable ones. Generic and series terms are sound
  participants; the earlier draft's countability gate, and its measurement of how much data it
  cost, are no longer needed.
- **The `singleton` tag only buys precision**, and only on transformation edges whose precursor
  carries it. It lives in [`src/timing/individuate.tsv`](../src/timing/individuate.tsv), empty
  so far. Mis-tagging can only ever over-tighten a transformation constraint; that is the whole
  of the risk.
- **Series need no machinery.** The generic term is a window like any other. Uberon in fact has
  numbered somite terms (`somite 1` … `somite 30`), and they enter the network as ordinary nodes;
  what is missing is per-somite *bounds*, which neither Uberon nor this repo has.

### Which nodes enter

The **population** is `make scoped`'s: the axiom subjects and their reasoned descendants,
intersected with Uberon's human subset. From there the node set is **closed forward**: if X is a
node and X `develops_from` / `part_of` / `SubClassOf` … Y, then Y is a node. That is sound under
all-some — an instance of X in a human implies an instance of Y in that human — so no taxon
filter is needed on the targets. Nothing is pulled in *backwards* (a Z that develops from a node
might not exist in the taxon at all).

One taxon per run. Uberon's relations are taxon-neutral; applying them inside a human run
assumes they hold in human, which is what Uberon's taxon constraints are for.

---

## 5. Hypotheses: what the POC tests

The atlas is the method. These are the claims, each of which can fail:

- **H1 — part_of implies temporal containment.** A part's lifetime lies within its whole's.
  This is the reading of *part_of* "at all times the part exists" (Smith et al. 2005). RO's
  current part_of is not committed to it, and Uberon may use part_of where a morphogenetic
  successor is meant.
- **H2 — develops_from implies the product starts strictly later.** The `exists_after` link.
- **H3 — the network is useful.** It produces conflicts a curator accepts as real errors, and
  non-trivial bounds that are true.

Success and failure:

| | |
|---|---|
| **Machinery works** | every fixture in §8 gives its expected output; the property test agrees with the brute-force oracle |
| **Succeeds** | conflicts point at statements a curator accepts as wrong; leave-one-out (§8, R3) recovers hidden bounds soundly and non-trivially |
| **Fails usefully** | conflicts are dominated by H1/H2 failing — then the relations, not the stage data, are the problem, and that is a report to Uberon |
| **Fails** | only trivial bounds (those following from s(X) < e(X) alone) are derived |

---

## 6. Engine: Soufflé, from the start

All reasoning is Datalog in `datalog/`. Nothing in Python, SPARQL or the Makefile draws a
temporal conclusion; they move facts in and results out. Soufflé because the rules are
inspectable against §3, because it scales well past this repo's size, and because a Python
prototype would have to be replaced at EHDAA2 scale anyway.

| file | role |
|---|---|
| `datalog/semantics.dl` | §3, one rule per row → `le(a, b, why)`, `lt(a, b, why)` |
| `datalog/network.dl` | closure; conflicts; tightest stage bounds |
| `datalog/report.dl` | read-only views: bounds as RO predicates, new-vs-curated, Allen view, conflict explanations |
| `datalog/timing.dl` | includes the three; the program `make timing` runs |

### Closure

`path(a, b)` (a ≤ b entailed) and `spath(a, b)` (a < b entailed) are the transitive closure over
`le ∪ lt`, with `spath` requiring at least one strict edge. That is the whole reasoner. The
network is inconsistent iff `spath(p, p)` for some point.

### Explaining a conflict

"Every edge on a cycle through a bad point" is the obvious explanation and, on real data, a
useless one: cycles through the stage frame share stage points, so unrelated conflicts merge, and
a structure whose own bounds bridge the same stretch of stages lies on a cycle without being to
blame. The POC's first real run flagged 101 structures that way.

The explanation that works splits constraints by what they join — *frame* (stage to stage),
*structural* (structure to structure), *anchor* (a bound) — and looks for **excursions**: an
anchor puts structure point X at or after stage point Q1, a structural path leads from X to Y,
an anchor puts Y before Q2, and the frame puts Q2 at or before Q1. A conflict is reported as
**the two bounds that cannot both hold, plus the structural path between them**. Each
constraint carries its source axiom (TSV row and curator, Uberon axiom, HsapDv axiom), so it
reads "these statements cannot all be true".

This is complete when the frame is totally ordered: replace every excursion that does not
conflict by the frame order it agrees with, and a strict cycle would remain in the frame alone.
Strict cycles among structures with no stage involved are reported separately. HsapDv's frame is
only partially ordered, so a conflict needing two excursions together is possible in principle;
the program reports bad points with no explanation at all rather than hiding them (none so far).

### Passes, and withholding

A conflict that runs through the stage frame collapses part of the frame's order, so bounds
computed alongside it are unreliable for everything downstream. `make timing` therefore runs in
passes: pass 1's conflicts are **the conflict report**; each later pass withholds every axiom in
the previous pass's explanations and reruns, until nothing conflicts. Bounds are read from the
last pass — a consistent remainder, with what was removed and why listed in that pass's
`withheld.tsv`.

Withholding is one mechanism with two users: the passes, and
[`src/timing/withheld.tsv`](../src/timing/withheld.tsv), where a curator withholds an axiom by
its identity with a reason. Its first entry is an HsapDv error (§10).

### Bounds

Bounds are reported against **any** HsapDv stage — a bound on "fetal stage" has no leaf stage to
land on:

- **lower** — S with start(S) ≤ p entailed, and no stage starting strictly later also so
  ("during or after S");
- **upper** — S with p < end(S) entailed, and no stage ending strictly earlier also so
  ("during or before S");
- stages the frame entails start (or end) together tie and are all reported.

A bound is **new** when the structure's own statements — asserted, or inherited at class level,
which OWL already provides — plus s(X) < e(X) do not imply it. Only new bounds count toward H3.

One implementation note, because it cost a factor of a thousand: rules that build a point from
bound variables (`stage(S), stage(S2), path($SS(S), $SS(S2))`) make Soufflé's interpreter scan
`path` per pair. Rules iterate `path` and take points apart instead.

### Allen view

For a pair of structures joined by an edge, the possible Allen atoms are those whose four
endpoint comparisons are each permitted by the closure. Pairwise-exact, jointly an
over-approximation — it can list an atom no single assignment realises. Reported, never reasoned
from.

### Scale

Closure is all-pairs over points: O(n²) space. The POC's network is 778 structures and ~300
stages, 1.1M `path` tuples, closed in under 2 s; a whole pass, reporting included, is ~14 s in
the interpreter. EHDAA2 scale (~2,000 structures) is tens of millions of tuples — within
Soufflé's range, compiled (`souffle -c`) if need be; partitioning by organ system, or magic-set
restriction to the pairs of interest, are the levers beyond that.

---

## 7. Files

```
datalog/semantics.dl  network.dl  report.dl  timing.dl
sparql/timing/
  bound.rq           curated GCIs -> stage-bound facts       (over build/axioms.ofn)
  seed.rq            scoped classes -> population            (over build/scoped.ofn)
  edge.rq            Uberon named-to-named edges, 5 relations + SubClassOf (over merged-full.owl)
  stage_rel.rq       HsapDv stage relations                  (over build/hsapdv.owl)
  label.rq           labels, for the report only
src/timing/individuate.tsv   singleton tags (curated, provenance columns)
src/timing/withheld.tsv      axioms withheld from every run, each with a reason
tests/timing/cases/<case>/   input/*  expected/*.csv  [macros]   one directory per fixture
tests/test_timing.py         runs souffle per fixture and compares row sets
tests/test_timing_oracle.py  random networks against a brute-force oracle
```

Fact export is SPARQL over the artefacts, as with `expand.ru`, so the same step works on GCIs in
Uberon that this repo did not write. `make facts` needs `build/merged-full.owl` (from
`make reach`) and fetches HsapDv into `build/`; `make timing` reasons. Outputs, per pass, in
`build/timing/pass<N>/`: `conflict.csv`, `conflict_summary.csv`, `conflict_path.csv`,
`cycle.csv`, `unexplained.csv`, `in_conflict.csv`, `lower_bound.csv`, `upper_bound.csv`,
`bounds_report.csv` (labelled), `allen.csv`, `withhold_next.tsv`. `build/timing/out` is the last
pass.

---

## 8. Tests

### Fixtures — small, hand-checkable, expected output written first

| # | input | expected |
|---|---|---|
| U1 | A, B both start during CS11 | consistent; s(A), s(B) unordered; Allen view of A vs B not a single atom |
| U2 | X `develops_from` Y, both start during CS11 | **consistent** (the integer model got this wrong) |
| U3 | X starts CS10, Y starts CS12, X `develops_from` Y | conflict between the two bounds; path is the `develops_from` edge alone |
| U4 | X `develops_from` Y, Y starts CS12, X unbounded | s(X) during or after CS12 — new |
| U5 | X `immediate_transformation_of` Y, Y ends CS14 | singletons: s(X) during CS14. X not tagged: s(X) after start(Y)'s stage, before end(CS14) |
| U6 | X `develops_from` Y, Y `develops_from` X, both in CS11 | a structural cycle, with no stage involved — reported as such |
| U7 | X `directly_develops_from` Y, Y persists after X starts | consistent by default; conflict with `-M RO_2207_AS_DEFINED` |
| U8 | G starts during CS12; M `SubClassOf` G, M starts during CS13 | conflict — the inheritance trap |
| U9 | two independent conflicts and a clean pair | both conflicts reported separately; the clean pair's bounds unaffected |
| U10 | X starts during week 9, Y starts during CS23, Y `develops_from` X; Z ends during or before "fetal stage" | conflict — CS23 before week 9 is derived only through embryonic/fetal part_of and adjacency; Z's upper bound lands on "fetal stage" itself |
| U11 | U3, with its `develops_from` edge in `withheld.tsv` | no conflict |

### Property test

180 random networks — 120 of two structures, 60 of three, over a three-stage chain, with random
bounds of all five predicates, random relations of all five kinds and random singleton tags —
checked against a brute-force oracle. The oracle restates §3 as predicates over integer time and
tries every placement of every point on a grid fine enough to lose no solution of the dense
timeline (2n + 1 cells per stage for n structures). It checks consistency both ways, that every
conflict is explained, and the exact lower and upper stage of every point. It lives only in
`tests/` and shares no code with the reasoner, so a bug in one is unlikely to be mirrored in the
other. It replaces the earlier draft's 12-minute calibration.

### Real data

- **R1 — conflicts.** A throwaway prototype of the §3 semantics over the current table and
  Uberon's edges among the curated structures predicted four. Recorded here *before* the
  Datalog ran, so the Datalog is checked against them rather than tuned to them:

  | conflict | rows | most likely culprit |
  |---|---|---|
  | neural tube marginal layer `develops_from` mantle layer; marginal starts CS12, mantle CS13 | both sourced | the Uberon edge |
  | lung saccule `part_of` alveolus of lung; saccule starts wk24, alveolus wk36 | both latent | Uberon edge — saccules precede alveoli |
  | otic pit `part_of` otic placode; pit outlives placode | placode sourced, pit unread | part_of where a successor is meant (H1) |
  | neural groove `part_of` neural plate; groove outlives plate | groove sourced, plate latent | plate's end bound, or the same H1 pattern |

- **R2 — new bounds** predicted by the prototype: arch arteries 3, 4, 6 end during or before CS17
  (via part_of their arch — H1-dependent, upper bound only); pancreas primordium starts during
  CS12 (its own lower bound plus its parts); generic pharyngeal arch starts during CS10.
- **R3 — leave-one-out**, the value test. Hide one curated row, re-derive, score *soundness*
  (the derived range contains the hidden stage) and *informativeness* (how narrow it is). Here
  first; then EHDAA2, which is human and Carnegie-staged, at 2,125 bounded `develops_from` edges.

---

## 9. The OWL side

Unchanged in kind. The C:C relations remain the vocabulary and the RO proposal:

```
uc:exists_after             dfOMP    develops_from, transformation_of ⊑ it
uc:exists_directly_after    dfOM     directly_develops_from ⊑ it
uc:exists_immediately_after M        immediate_transformation_of ⊑ it
```

(`uc:` = `http://purl.obolibrary.org/obo/uberon/core#`, following Uberon's 24 existing
non-OBO-ID properties.) The class-level chains

```
exists_after            ∘ existence_starts_during  ⊑  existence_starts_during_or_after
existence_starts_during ∘ preceded_by              ⊑  existence_starts_during_or_after
```

already work under ELK
([`08-develops-from-timing.ofn`](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/examples/08-develops-from-timing.ofn)).
They are the subset of §3 OWL can carry; the Datalog is the rest. The stage-disjointness module
the earlier draft proposed becomes an optional cross-check: anything it makes unsatisfiable, the
Datalog must also flag.

Promotion of Datalog results back into OWL is deferred. The natural form is to emit new bounds
as GCIs for review, the same shape the table produces.

---

## 10. POC results

From `make timing` on the `timing-souffle-poc` branch, 2026-10-19: the 174 live rows, Uberon
2026-10-01 (`build/merged-full.owl`), HsapDv 2025-01-23. 778 structures enter the network (310
seeds, closed forward).

### Machinery

All 13 fixtures (§8) give their expected output, and all 180 random networks agree with the
brute-force oracle on consistency, explanation and exact bounds.

### HsapDv is inconsistent on its own

Before any structure was added, the stage frame alone had a strict cycle: HsapDv asserts
`Carnegie stage 05a` both `part_of` and `immediately_preceded_by` `Carnegie stage 05`. A part
cannot begin when its whole ends. The edge — presumably meant to point at CS04 — is in
`src/timing/withheld.tsv` with that reason, and is to be reported to HsapDv.

### R1 — conflicts

**All four predicted conflicts appear, each with exactly the predicted path.** Six more appear
that the prototype could not see, because the Datalog follows paths through structures with no
curated bounds and through class inheritance. Ten distinct conflicts in all (33 rows before
merging inherited copies), over 40 structures:

| # | bound | vs bound | path | likely culprit |
|---|---|---|---|---|
| 1 | NT mantle layer starts CS13 *(sourced)* | NT marginal layer starts CS12 *(sourced)* | marginal `develops_from` mantle | **the Uberon edge** — both bounds are O'Rahilly's |
| 2 | rhombic lip starts CS16 *(sourced)* | NT marginal layer starts CS12, *inherited by* cerebellum marginal layer | cerebellum `develops_from` rhombic lip; cerebellum marginal layer `part_of` cerebellum | **the inheritance trap**: a point bound on a generic class, false of a late subclass |
| 3, 4 | neural tube starts CS10 *(sourced)*; posterior neural tube starts CS10 | neural plate starts CS8, *inherited by* hindbrain/midbrain neural plate | neural tube ⊃ posterior/anterior NT ← presumptive hindbrain/midbrain ← hindbrain/midbrain neural plate (`develops_from`) | **Uberon edges run backwards**: neural plate regions made to develop from neural tube regions |
| 5 | lateral plate mesoderm starts CS8 | amnion starts CS5 | amnion `develops_from` amniotic fold `develops_from` somatopleure `part_of` LPM | **a relation false in human**: the amniotic-fold route is chick and mouse; the human amnion cavitates in the epiblast (§4's taxon assumption) |
| 6 | lateral plate mesoderm starts CS8 | chorionic villus starts CS6 *(sourced)* | via chorion membrane `develops_from` amniotic fold — same route | same as 5 |
| 7 | allantois starts CS7 | chorionic villus starts CS6 *(sourced)* | villus `develops_from` chorionic plate `part_of` placental disc `part_of` placenta `develops_from` allantois | the definitive placenta's partonomy applied to primary villi; or what "chorionic villus" covers |
| 8 | alveolus starts wk36 | lung saccule starts wk24 | saccule `part_of` alveolus | **inverted partonomy**: saccules precede alveoli |
| 9 | otic pit ends CS12 | otic placode ends CS11 *(sourced)* | pit `part_of` placode | **part_of for a successive stage** (H1) |
| 10 | neural groove ends CS11 *(sourced)* | neural plate ends CS10 | groove `part_of` plate | the same pattern, or the plate's latent end bound |

Seven of the ten point at Uberon's relations rather than at stage rows, and they are of four
recognisable kinds: an edge that runs backwards (3, 4, 8), a relation true only in other taxa
(5, 6), part_of used for a successive stage (9, perhaps 10), and the inheritance trap (2).

### R2 — new bounds

**Every predicted bound appears**: arch arteries 3, 4, 6 end during or before CS17; pancreas
primordium starts during CS12; the generic pharyngeal arch starts during CS10; the generic arch
artery's end tightens from CS20 to CS17.

Over everything: 746 new bound rows on 344 structures — 24 curated structures tightened, 75
uncurated structures in the population, 245 structures reached forward from it. Most are
one-sided. They come from pass 2, which withheld the 91 axioms in pass 1's conflicts, so
structures in those families get weaker bounds than they would once the conflicts are resolved.

### H1 carries most of it

Rerun with part_of containment withheld (`-M NO_H1`): **2 distinct conflicts instead of 10**
(1 and 4 survive), and 246 new bound rows instead of 746. Containment is behind most of the
error-finding and most of the bounds — and also behind three of the conflicts where part_of
itself is the suspect (8, 9, 10). It is the hypothesis to test hardest.

`-M RO_2207_AS_DEFINED` changes nothing here: Uberon uses `directly_develops_from` once, outside
the population.

### Not yet run

**R3, leave-one-out**, and EHDAA2. Both are next; neither needs new rules.

---

## 11. What RO would have to change for this to be compatible

This is a proof of concept. It asserts things RO currently contradicts, deliberately. Nothing is
contributed upstream as it stands. All items are filed with evidence in
[RO_REPORT.md](https://github.com/dosumis/dev_reasoning_experiments/blob/584150e/RO_REPORT.md).

| # | change | why this work needs it | cost to RO |
|---|---|---|---|
| 1 | **Add continuant-to-continuant timing relations.** RO has none. | The C:C family is minted locally for want of them | 3 relations |
| 2 | **Fix `directly develops from` (RO:0002207)**: `start(x) ≥ end(y)` → `≤`. | RO's text is `MP`, which forbids delamination from a persisting precursor; this work reads it as `dfOM` | 1 definition; used once in Uberon, never in EHDAA2, already "Candidate definition" |
| 3 | **Add `starts after`**, converse of `starts before` (RO:0002089). | The weakest safe developmental claim | 1 relation |
| 4 | **Declare missing inverses** on the `existence_*` relations, `transformation of`, `immediate transformation of`, `ends after`. | Class-level chains walk one way only (the Datalog does not need them) | 6 axioms |

Fix 2 is testable here: fixture U7, and the real run with `-M RO_2207_AS_DEFINED`.

### Living with, not asking to change

- **`develops_from` inherits whatever `directly_develops_from` means**, since RO defines it as
  that relation's transitive closure. It is given the weakest reading (`s(Y) < s(X)`) regardless,
  which is sound either way.
- **RO:0002496/0002497 are non-strict.** "Starts during or after" permits an equal start. §3
  uses exactly that reading; it costs recall (EHDAA2: 14 detectable `develops_from` conflicts
  against 50 under a strict reading), not soundness.

---

## 12. Deferred

- **Budding as a derived category** (`directly_develops_from` and not a transformation) —
  stratified negation, reporting only, once the network is trusted.
- **EHDAA2 as a second input**, after R3 has run here.
- **Promotion** of new bounds to reviewable GCIs.
- **Spatial reasoning**, and anything that is not developmental anatomy.
