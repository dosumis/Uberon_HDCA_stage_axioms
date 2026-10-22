# How much developmental anatomy is countable?

A first assessment of how much of human developmental anatomy, as EHDAA2 and Uberon represent
it, can be represented as individuals in an idealised atlas of one embryo. The question for
each term: **in one normal embryo, how many separate structures does it denote?**

This is a latent-knowledge assessment: every term was classified by a language model from its
label, definition and position in the ontology, with no external source. A Wikipedia check is
planned as a second round. The per-term table is
[`countability/classification.tsv`](countability/classification.tsv), marked `curator: latent`
as the table's own convention requires.

Run 2026-10-22: EHDAA2 from its OBO PURL; Uberon 2026-10-01.

---

## Answer

| | EHDAA2 (all 2,456 classes) | Uberon, our network (778) | Uberon, our seeds (310) |
|---|---:|---:|---:|
| **Countable** | **96%** (2,359) | 73% (568) | 91% (281) |
| of which, a single individual as it stands | 43% (1,066) | | |
| of which, a left/right pair or a named side | 50% (1,221) | | |
| Not countable: populations, repeated units | 4% (89) | 6% (47) | 9% (28) |
| Not countable: abstract types | 0.3% (8) | 21% (163) | 0.3% (1) |
| **develops_from edges with both ends countable** | **92%** (1,951 of 2,125) | 89% (141 of 159) | |

**Nearly all of EHDAA2 is countable**, and so are 92% of the develops_from edges that timing
inference runs on. About half of the countable terms are bilateral: "optic vesicle" means two
structures, one each side. Uberon looks less countable, but the difference is almost entirely
abstract classes, such as "organ", "multi-tissue structure" or "primordium". These enter our
network only as superclass windows. Leave them out, and the Uberon network is 92% countable too.

Of the 113 structures in our curated table, 103 are countable. The other 10 are populations or
repeated units: chorionic villus, lung saccule, alveolus, neural crest, cardiac neural crest,
metanephric cap, primary and secondary ossification centres, brown adipose tissue and vernix
caseosa.

---

## Categories

| category | meaning | EHDAA2 | examples |
|---|---|---:|---|
| **ONE** | exactly one per embryo | 880 | inner cell mass, ventral pancreas, axial skeleton, hindgut mesothelium |
| **FIXED** | a fixed number > 1, members not separately named; usually a left/right pair | 723 | lens placode, testis, pleural cavity, lateral ventricle choroid plexus |
| **MEMBER** | one named member of a series | 642 | early rhombomere 07, dermomyotome 17, vertebral cartilage condensation T02, finger 3 |
| **GROUP** | a whole series or set as one term | 114 | cervical vertebral cartilage condensation group, head dermomyotome group, spinal nerves |
| **MANY** | an indeterminate number: cell populations, repeated units | 89 | gonadal ridge primordial germ cells, mesoderm blood islands, liver capillary plexus |
| **TYPE** | an abstract classifier, not a part of the body plan | 8 | valve, CNS ganglion, body arteries |

ONE, FIXED, MEMBER and GROUP are countable. MANY and TYPE are not.

---

## How it was done

- **Populations.** All 2,456 live EHDAA2 classes, and all 778 Uberon structures in the timing
  network of [timing-individuals.md](timing-individuals.md). 1,360 EHDAA2 classes have an
  Uberon cross-reference; 222 of the network's structures have an EHDAA2 one.
- **Classification.** Eight parallel model instances, each given about 400 terms with label,
  definition, is_a and part_of parents, and stage bounds, and the instructions in
  [`countability/instructions.md`](countability/instructions.md). Each returned a category, a
  count, whether the count is a left/right doubling, a confidence, and a note where unsure.
- **Consistency check.** 50 EHDAA2 terms, drawn at random, were hidden in all eight batches.
  - Pairwise agreement on the category was **93%**, and 43 of the 50 terms were unanimous.
  - Agreement on countable versus not countable was **100%**.
  - All seven disagreements are ONE vs MEMBER for sided terms ("vitelline vein right",
    "4th arch artery right") or FIXED vs GROUP ("lower jaw incisor"). None crosses the
    countable boundary.
- **Confidence.** 77% high, 21% medium, 1% low (EHDAA2).

---

## What to make of it

- **EHDAA2 is atlas-shaped by design.** It was built as the partonomy of a canonical embryo. It
  names series members individually and splits even cell populations by location, such as the
  primordial germ cells of the allantois, mesonephros and gonadal ridge. That is why it scores
  so high. Uberon is cross-species and type-oriented, so an atlas generated from Uberon needs
  EHDAA2-style terms, or the mappings to them, to reach the same coverage.
- **Countable is not the same as ready.** 43% of EHDAA2 terms are a single individual as they
  stand. Half are bilateral pairs. For timing, a pair is usually fine as one window, because
  the two sides develop together. Where they don't, as in the remodelling of the vitelline and
  cardinal veins, EHDAA2 already names the sides.
- **Uncountable terms still contribute.** As windows, they keep reasoning sound and lose only
  per-member detail. Three of the ten timing conflicts found so far involve uncountable terms:
  chorionic villus, lung saccule, alveolus.
- **Variable counts are rare in this population.** Only 11 countable EHDAA2 terms were given a
  count that varies between normal embryos.

---

## Limits of this assessment

- **One model family.** The agreement figure measures consistency between instances of one
  model, not correctness. Systematic shared errors would not show up. A Wikipedia check of a
  sample, and of every medium- or low-confidence term, is the next step.
- **Judgement at the edges.** Whether "1st arch mandibular mesenchyme" is one mass or two, or
  whether a cranial nerve component is paired, is a modelling choice as much as a fact. The
  instructions fix the convention: count at fullest extent, count both sides.
- **Population scope.** EHDAA2 covers Carnegie stages 1–20 only, so fetal anatomy is not in
  it. The Uberon figures cover the 778 structures in our timing network, not all of Uberon.
