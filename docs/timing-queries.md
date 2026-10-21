# Timing queries over the endpoint network

Four example queries over the timing network of
[timing-individuals.md](timing-individuals.md), what they returned on current data, and the
assumptions every answer rests on. The queries are in
[`datalog/queries/examples.dl`](../datalog/queries/examples.dl).

Run 2026-10-19 on branch `timing-souffle-poc`: the 174 live rows of `src/axioms.tsv`, Uberon
2026-10-01, HsapDv 2025-01-23.

```
make facts && make timing
souffle -F build/timing/pass2-facts -D build/timing/queries datalog/queries/examples.dl
```

Each query asks about specific structures or stages through `ask_*` facts at the top of its
block. Edit those facts to ask something else. A run takes about a minute, because the query
file includes the whole report program.

---

## How a query works

Every structure X has a start point s(X) and an end point e(X). Every stage S has start(S) and
end(S). After closure the network holds two relations:

- `path(a, b)`: a ≤ b is entailed;
- `spath(a, b)`: a < b is entailed.

A query is a few Datalog rules over these two relations. Something holds **certainly** when the
asserted statements entail it. It holds **possibly** when they do not entail its negation.
Anything else is **unknown**. Negation here is closed-world over *entailment*: "not entailed"
means "the curated statements leave it open", never "false".

---

## Results

### 1. Could two structures ever exist at the same time?

- never: one is entailed to end at or before the other starts;
- certainly: each is entailed to start before the other ends;
- unknown: neither.

| A | B | answer | why |
|---|---|---|---|
| intermediate mesoderm | mesonephros | certainly | IM starts CS9, ends CS16; mesonephros starts CS11 |
| heart tube | atrial septum primum | never | heart tube ends during CS11; septum primum starts during CS13 |
| optic vesicle | optic cup | unknown | the vesicle ends during CS13 and the cup starts during CS13; their order inside CS13 is undetermined |
| neural fold | neural tube | unknown | would be *certainly*, but the neural tube's CS10 start is withheld in pass 2 (it is in conflict #2) |

The optic case is the stage-granularity behaviour working as intended. An integer-stage model
would have answered it, wrongly.

### 2. What develops from a structure, and when can each derivative start?

This walks `develops_from`, `directly_develops_from`, `transformation_of` and
`immediate_transformation_of` backwards and transitively, which class-level OWL cannot do. For
intermediate mesoderm:

| derivative | starts during or after | starts during or before |
|---|---|---|
| nephrogenic cord | CS9 | CS11 |
| urogenital fold | CS9 | CS11 |
| pronephric duct | CS9 | CS13 |
| mesonephric duct | CS11 | CS13 |
| metanephric mesenchyme | CS13 | CS13 |
| metanephros | CS14 | CS14 |
| ureteric bud (and its subclasses) | CS14 | CS14 |
| gonadal ridge | CS15 | CS15 |
| Müllerian duct | CS16 | CS16 |
| primitive urogenital sinus | CS9 | CS18 |

Several derivatives also list "organogenesis stage" as a lower bound beside CS9. That is a tie,
not a duplicate. HsapDv entails that organogenesis stage and CS9 start at the same instant, so
both are equally tight, and the report lists all tied stages.

### 3. What is present during a stage?

- certainly: the structure's lifetime is entailed to overlap the stage;
- possibly: overlap is not ruled out.

For Carnegie stage 12: **132 certainly**, **291 possibly**. The certain ones include all five
pharyngeal arches and arch arteries 2, 4, 6, pharyngeal pouch 4, optic vesicle, lens placode,
olfactory placode, lung bud, forelimb bud, limb field, mesonephros, liver primordium, pancreas
dorsal primordium, thyroid primordium, sinus venosus, truncus arteriosus, bulbus cordis, and
the atrioventricular canal.

Most of the "possibly" rows are structures with no bounds of their own, which nothing rules out
of any stage.

Arch artery 1 is a "possibly" that should be "certainly". It is curated as ending during CS12,
yet the network allows it to end at the instant CS12 begins, with no overlap. That is a flaw in
how "ends during" is encoded, not in the query; see [Open issue](#open-issue-interval-endpoints)
below. Arch artery 3 is correctly "possibly": it has no curated end, so nothing guarantees it
lasts into CS12.

### 4. What must already have started when a structure starts?

For metanephros: 269 structures are entailed to have started first. Among them are the ureteric
bud, metanephric mesenchyme, mesonephros, mesonephric duct, pronephros, nephrogenic cord and
intermediate mesoderm, and also optic cup, pharyngeal arches 1–6, heart tube and neural tube,
through stage bounds alone.

The list is long and noisy, and the noise is instructive. Many rows are generic superclass
windows such as "organ", "anatomical system" and "multicellular organism". These are true under
the window reading: such a window starts when its earliest member starts. But they say nothing
useful. A practical version of this query should keep only curated or seeded structures.

---

## Assumptions behind every answer

### About time

- **Dense, linear time on one idealised timeline.** One canonical human embryo. Variation
  between real embryos is absorbed into the width of the stage bounds, not modelled.
- **Stages are intervals with sharp boundaries.** Each stage has a start and an end point,
  start(S) < end(S). Carnegie stages are defined by morphological criteria and real specimens
  straddle them; the model takes the boundaries as given and reasons only about order relative
  to them.
- **Structures are intervals.** s(X) < e(X): everything exists for some nonzero time.
- **HsapDv supplies the stage order.** `immediately_preceded_by` makes boundaries coincide,
  `preceded_by` orders them, and `part_of` nests stages. One HsapDv edge is withheld because it
  makes HsapDv inconsistent: Carnegie stage 05a, asserted both part of and immediately preceded
  by stage 05. The Carnegie-to-week ordering is derived only through embryonic and fetal
  part_of, because HsapDv has no CS23 → week 9 edge.

### About what Uberon's relations mean

- **Class axioms are all-some, and inherited.** An axiom on G holds for every instance of G
  and of every subclass of G.
- **`develops_from` (H2)**: the product starts strictly after the precursor starts. Nothing is
  assumed about when the precursor ends.
- **`directly_develops_from`**: additionally, the product starts no later than the precursor
  ends. This departs from RO:0002207's current text, deliberately; see timing-individuals.md
  §11.
- **`transformation_of` / `immediate_transformation_of`**: the precursor ends no later than,
  or exactly when, the product starts. This is exact only if the precursor is tagged a
  singleton; none is tagged yet, so the weaker form applies throughout.
- **`part_of` (H1)**: the part's lifetime lies within the whole's. This is the "at all times
  the part exists, it is part of some whole" reading. It is the most consequential assumption:
  withdrawing it cuts distinct conflicts from 10 to 2 and new bounds from 746 to 246.
- **`SubClassOf`**: a subclass's window lies within its superclass's.
- **Taxon.** Uberon's relations are taxon-neutral and are applied to human as they stand.
  Conflict #3 in [uberon-timing-conflicts.md](uberon-timing-conflicts.md) shows where that
  fails.

### About what a structure's "lifetime" is

- **A structure is an existence window.** For a class with one instance per organism, such as
  the liver or pharyngeal arch 3, the window is that instance's lifetime. For a series or
  population, such as "pharyngeal arch" or "somite", it runs from the first member's start to
  the last member's end. Answers about generic classes are answers about that hull.
- **Names mark phases.** A structure "ends" when the curation says the name stops applying.
  Many end bounds are naming conventions rather than observations, as
  [end-bound-convention.md](end-bound-convention.md) discusses.

### About which data the answers use

- **Population.** The 310 scoped classes (axiom subjects and their human-subset descendants),
  closed forward along develops_from, part_of and SubClassOf, which gives 778 structures.
  Nothing is pulled in backwards.
- **Pass 2, not pass 1.** Queries run on the consistent remainder, after the 91 axioms in pass
  1's conflicts have been withheld. Structures in conflict families get weaker answers than
  they will once those conflicts are resolved.
- **Most bounds are unsourced.** 60 of 174 rows carry a quoted passage. "Certainly" means
  *entailed by the curated table plus Uberon under the readings above*. It is not a fact about
  embryos.

---

## Open issue: interval endpoints

The semantics table does not fix whether intervals are open or closed at their ends, and the
encoding is not consistent about it:

| predicate | current encoding | half-open reading, existence = [s, e), stage = [start, end) |
|---|---|---|
| starts during S | start(S) ≤ s(X) < end(S) | unchanged |
| ends during S | start(S) ≤ e(X) < end(S) | **start(S) < e(X) ≤ end(S)** |
| ends during or before S | e(X) < end(S) | **e(X) ≤ end(S)** |
| exists during S | start(S) ≤ s(X), e(X) ≤ end(S) | unchanged |

Under the current encoding, "ends during CS12" permits zero overlap with CS12 and forbids ending
exactly as CS12 ends. Neither is intended. The half-open reading treats e(X) as the first
instant X no longer exists, so its last moment of existence falls inside S. With it, arch
artery 1 is certainly present during CS12.

None of the ten conflicts depends on the choice. Each of them has a strict step somewhere else
in its cycle. Changing the table means changing `datalog/semantics.dl`, the fixtures that
involve end bounds, and the oracle's restatement of the table, together.

## Limits of these queries

- They are point-in-time snapshots of a network that still contains known errors upstream.
- Query 4 needs a filter to curated or seeded structures before it is useful to a person.
- Queries 1 and 3 report pairwise answers. Each comparison is exact on its own. But a
  combination of "possibly" answers is not guaranteed to be jointly possible.
