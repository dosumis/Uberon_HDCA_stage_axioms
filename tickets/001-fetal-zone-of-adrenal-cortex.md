# New term request: fetal zone of adrenal cortex

**Ontology:** Uberon
**Type:** new term

## Request

A class for the **fetal zone** (provisional cortex) of the human adrenal cortex.

## Why

The fetal adrenal cortex has two histologically and functionally distinct
compartments. The inner **fetal zone** makes up 80–90% of the gland's volume
before birth, is the source of the DHEA-S that the placenta aromatises to
oestrogen, and involutes over the first postnatal months. The outer
**definitive zone** is the precursor of the adult zona glomerulosa and
fasciculata.

Uberon has `adrenal cortex` (UBERON:0001235) and its adult zones, but nothing
for either fetal compartment. There is no way to say which part of a fetal
adrenal a sample came from, and the two have different transcriptional
identities, so single-cell atlases of the fetal adrenal cannot be annotated
against Uberon at the resolution the data distinguishes.

## Searches performed

- Uberon via OLS4, "fetal zone", "definitive zone", "provisional cortex": no hits.
- Uberon labels and exact synonyms, same strings: no hits.
- EHDAA2 (2743 terms), "fetal zone" and "adrenal cortex": no hits. EHDAA2 stops
  at CS20, before the fetal zone is established, so there is no xref to offer.

## Suggested placement

```
fetal zone of adrenal cortex
  part_of  adrenal cortex (UBERON:0001235)
  (human-restricted, or restricted to a clade if the compartment is shared)

definitive zone of adrenal cortex
  part_of  adrenal cortex (UBERON:0001235)
```

A `develops_into` from the definitive zone to the adult cortical zones would
also be useful if that is well enough established.

## Context

Encountered while mapping Human Developmental Cell Atlas tissue annotations to
Uberon. One publication in that corpus annotates samples as "fetal adrenal
tissue"; with no fetal compartment available, the best mapping is plain
`adrenal gland`, which loses the distinction the sample was taken to study.
