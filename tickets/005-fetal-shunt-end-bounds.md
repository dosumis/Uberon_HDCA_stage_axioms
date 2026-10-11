# Incorrect end bounds on the fetal circulatory shunts

**Ontology:** Uberon
**Type:** incorrect axiom

## Summary

Three of the four structures that define fetal circulation assert that they
cease to exist by the end of the embryonic period. All three are patent
throughout fetal life and close at or shortly after birth.

| class | asserted | should be |
|---|---|---|
| UBERON:0005440 ductus arteriosus | `existence ends during or before` embryo stage | persists to birth |
| UBERON:0002083 ductus venosus | `existence ends during or before` embryo stage | persists to birth |
| UBERON:0004754 foramen ovale of heart | `existence ends during or before` embryo stage | persists to birth |

`UBERON:0002066 umbilical vein` is bounded at `post-embryonic stage` and so is
not affected.

The assertions are direct, not inferred — they appear in Ubergraph's
`nonredundant` graph against both `embryo stage` and `embryo development`.

## Why this is wrong

These are the three shunts of the fetal circulation and their whole function is
to operate during the fetal period:

- the **ductus arteriosus** diverts right ventricular output from the
  unventilated lungs into the descending aorta, and closes functionally within
  hours to days of the first breath, leaving the ligamentum arteriosum;
- the **ductus venosus** shunts oxygenated umbilical blood past the hepatic
  sinusoids, and closes after birth to become the ligamentum venosum;
- the **foramen ovale** passes blood from right to left atrium, and closes
  functionally at birth when left atrial pressure rises, leaving the fossa
  ovalis.

A bound of `embryo stage` says each is gone by about eight weeks post
fertilization. Patent ductus arteriosus is diagnosed in neonates, which it
could not be if the structure ceased to exist in the embryo.

## How it was found

Running 865 human fetal single-cell libraries (weeks 9–22 post fertilization,
21 publications) against Uberon's own existence bounds. Of 1397 tissue
annotations resolving to an Uberon term, exactly two were flagged as naming a
structure Uberon says has already closed — and both were `ductus arteriosus` in
samples at 13 and 15 weeks.

The annotations are right and the ontology is wrong, which is the useful
direction for this kind of check to fail in.

## Suggested fix

Either relax the bound to the end of the prenatal period, or replace it with
an explicit statement about birth if a suitable class exists. If taxon-scoped
stage axioms are acceptable, the human-specific form would be:

```
(ductus arteriosus and in_taxon some NCBITaxon:9606)
    SubClassOf existence_ends_during some HsapDv:0000075   # 38th week and over
```

which is what we hold in <https://github.com/dosumis/taxon-stage-axioms>, and
is the subject of a separate proposal.

## Worth checking at the same time

Whether the bound was inherited from a parent class covering embryonic
vasculature. If so, the same error may affect siblings not surfaced by this
corpus.
