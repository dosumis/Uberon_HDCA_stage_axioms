# HDCA tissue annotations against the timing network: first results

Steps 1–3 of [hdca-plan.md](hdca-plan.md), run 2026-10-22 on branch `timing-souffle-poc`.

- **Input:** HDCA_metadata's filled Tier 1 table, 1,386 libraries with a mapped tissue and stage
  (80 dropped as unmapped), 491 of them at embryonic stages.
- **Network:** this repo's 174 curated rows, Uberon 2026-10-01, HsapDv 2025-01-23, and EHDAA2
  from its OBO PURL.

```
make hdca HDCA_RUN_NAME=baseline EHDAA2_MACROS=                      # no EHDAA2
make hdca HDCA_RUN_NAME=written-starts HDCA_MACROS=EHDAA2_STARTS_ONLY # the run used below
```

For every annotated (tissue, stage) pair the network answers one of three things:
- **absent**: the tissue has ended before the stage starts, or starts only after it ends;
- **present throughout**: the tissue exists from before the stage starts until after it ends;
- **possible**: neither is entailed.

For pairs that are not present throughout, it suggests related terms that exist at the stage.
HDCA's choice of term is HDCA's; these are alternatives, not corrections.

---

## 1. Runs

EHDAA2 bounds are imported only for HDCA-relevant terms: the annotated tissues, their
precursors and wholes, and their direct parts. They come only through one-to-one Uberon
cross-references, and every imported bound is tagged EHDAA2.

| run | EHDAA2 bounds | conflicting bound pairs | embryonic libraries: absent / possible / present throughout |
|---|---|---:|---|
| baseline | none | 33 | 4 / 401 / 86 |
| written | starts and ends, as written | 463 | 12 / 399 / 80 |
| intended | starts and ends, as "during" | 1,407 | 11 / 392 / 88 |
| **written-starts** | starts only, as written | 210 | 11 / 409 / 71 |
| intended-starts | starts only, as "during" | 1,083 | 10 / 390 / 91 |
| written-starts, no part_of containment | starts only | 27 | 21 / 468 / 2 |

## 2. What EHDAA2 taught us

**Its bounds are boundaries of its own vocabulary, not lifetimes of what Uberon names.**
- EHDAA2's "neural tube" ends at CS12, "neuroectoderm" at CS9, "endoderm of foregut" at CS9.
  That is where EHDAA2 switches to finer, stage-specific terms.
- Uberon's matching terms persist. Imported as ends, those stages contradict every later
  neural structure, which is most of the 463.
- Starts have the same problem, less often. EHDAA2's "chordate pharynx" starts at CS16, but
  Uberon's pharynx contains the CS10 arch arteries and thyroid primordium.

**Cross-references are not equivalences.** EHDAA2's zona pellucida, of the early embryo, maps
to Uberon's ovarian zona pellucida, which is part of the ovary. A one-to-one filter does not
catch this.

**So EHDAA2 cannot be bulk-imported.** Start bounds read as written (lower bounds only) are
the safest form. Even then they over-constrain wherever Uberon's concept is broader than
EHDAA2's. EHDAA2 is better used as per-term evidence in curation (§5) than as an axiom source.

**The disagreements are themselves curation leads.** Examples where both sources talk about
the same structure:
- optic vesicle: CS11 from O'Rahilly versus CS12 from EHDAA2;
- floor plate of the midbrain: CS12 from EHDAA2, against this table's generic "floor plate
  starts during CS10". That is the inheritance trap: a point bound on a generic class.

## 3. Flags: annotations whose tissue cannot exist at the stage

From the written-starts run. Compared with the expectations recorded in the plan before
anything ran:

| annotation | libraries | flagged? | expected? | derivation and comment |
|---|---:|---|---|---|
| thymus @ CS9 | 3 | **absent** | yes | thymus develops from thymus primordium, which starts later. Probably a stage error, the same pattern HDCA_metadata found in other thymus samples |
| thymus @ CS17 | 4 | **absent** | partly | from EHDAA2's start for "thymus" proper; the primordium exists. A naming question |
| testis @ CS17 | 1 | **absent** | yes (borderline) | EHDAA2's testis starts after CS17; the indifferent gonad exists |
| tetrapod frontal bone @ CS16 | 1 | **absent** | yes | no bone before ossification |
| vault of skull @ CS16 | 1 | **absent** | yes | as above |
| basicranium @ CS16 | 1 | **absent** | yes | part of the chondrocranium, which starts at CS17 (sourced). Relies on part_of containment |
| vertebra, vertebral column @ CS16–17 | 41 | possible | yes | no start bound for "vertebra" in any source |
| occipital bone @ CS16 | 1 | possible | yes | as above |
| cerebral cortex @ CS19 | 8 | possible | depends on curation | no start bound, and no precursor in Uberon |
| striatum @ CS19 | 14 | possible | depends on curation | as above |
| cerebellum @ CS18–19 | 17 | possible | yes | precursor known (rhombic lip), but no start bound for "cerebellum" |

**False positives seen, and their causes:**
- **mesonephric duct @ weeks 11–13** (baseline). The duct is `part_of` mesonephros, so it
  inherits the mesonephros's CS20 end. But the Wolffian duct persists in males. This is the
  containment reading of part_of over-reaching, as the plan warned.
- **medulla oblongata @ CS17, spinal cord @ CS12** (no-containment run). These come from
  EHDAA2's vocabulary boundaries surviving once fewer conflicts are withheld.

Every flag carries its derivation, so each of these can be traced to the axiom responsible.

## 4. Suggestions

Suggestions work **where the precursor has an upper bound on its start**:

| annotation | top suggestion | run |
|---|---|---|
| vertebra @ CS16 | **sclerotome**, then somite | intended-starts |
| striatum @ CS19 | **ventral part of telencephalon**, telencephalon | intended-starts |
| liver @ CS14–16 | septum transversum | written-starts |
| occipital bone @ CS21–23 | sclerotome | written-starts |
| basicranium @ CS21–23 | chondrocranium | written-starts |

They fail where it doesn't. Thymus primordium (for thymus), indifferent gonad (for testis) and
rhombic lip or cerebellar plate (for cerebellum) are all the right answers, and are all in
Uberon. But none has an upper bound on its start, so nothing says it has *certainly* started
by the annotated stage. Suggestions through wholes ("brain", "skeletal system") are true but
mostly noise; precursor suggestions rank first.

## 5. Diagnosis: the bottleneck is curated knowledge for HDCA's own terms

Three kinds of knowledge are missing, in order of impact:

1. **When an adult-named term first applies:** vertebra, cerebral cortex, striatum, cerebellum,
   skull bones, thymus, testis. No source the network has says.
2. **That permanent organs persist.** Nothing says the liver still exists after CS16, so even
   "liver @ CS16" can only be "possible". This needs a bound type the table lacks: "ends during
   or after S". RO has no such predicate, so it would be a local addition to the semantics
   table.
3. **Upper bounds on precursor starts:** thymus primordium, indifferent gonad, rhombic lip,
   vertebra cartilage element.

**Next: targeted agentic curation, strictly limited to HDCA-relevant terms.** That is the 70
HDCA tissues used at embryonic stages plus their 32 direct Uberon precursors, minus those
already curated: **89 terms**. For each term, a start bound (point or interval, with the naming
convention stated) and an end or persistence statement, checked against three sources:
- the O'Rahilly & Müller staging corpus, through the stage-evidence skill, with verbatim and
  verified quotes;
- EHDAA2, as evidence per term rather than as imported axioms, noting where its term is
  narrower than Uberon's;
- Wikipedia, through the fetch skill, observing its species-safety rules.

Then rerun this check and triage what changes.
