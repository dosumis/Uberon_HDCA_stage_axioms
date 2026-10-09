# New term request: germinal matrix

**Ontology:** Uberon
**Type:** new term

## Request

A class for the **germinal matrix** — the highly vascular, transient
periventricular proliferative region of the fetal telencephalon, over the
caudate nucleus and adjacent to the ganglionic eminences.

## Why

The germinal matrix is clinically significant in its own right: germinal matrix
haemorrhage is the commonest serious intracranial complication of preterm birth,
and the structure's involution between roughly 24 and 36 weeks is why the risk
window closes. It is a standard term in neuropathology and in fetal brain
imaging.

Uberon has `ganglionic eminence` (UBERON:0004023), `cerebral cortex
subventricular zone` (UBERON:0014940) and `ventricular zone` (UBERON:0003053),
but nothing that names the germinal matrix as such. The ganglionic eminence is
the nearest term and is not a synonym: the germinal matrix is the broader
periventricular region, and the two are distinguished in the clinical and
developmental literature.

## Searches performed

- Uberon via OLS4, "germinal matrix": returns `nail matrix`,
  `hair follicle matrix region`, `long bone epiphyseal plate proliferative zone`
  — no brain structure.
- Uberon labels and exact synonyms: no hits.
- EHDAA2 (2743 terms): no hits. EHDAA2 stops at CS20, before the germinal matrix
  is prominent, so there is no xref to offer.

## Suggested placement

```
germinal matrix
  part_of  telencephalic ventricle wall / lateral ventricle region
  overlaps / has_part  ganglionic eminence (UBERON:0004023)
```

The exact parentage is a judgement for Uberon editors — the relationship to the
ganglionic eminence is the part worth getting right, and I would not want to
assert it without an editor's view.

## Context

Encountered while surveying what Uberon offers for annotating fetal-stage
single-cell atlases. Reported alongside a request for fetal adrenal cortex
compartments; both are cases where the embryonic vocabulary is rich and the
fetal vocabulary is not.
