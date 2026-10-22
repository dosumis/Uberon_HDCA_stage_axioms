# Plan: timing reasoning for HDCA tissue annotation

**Status: plan, for discussion. Nothing here is implemented yet.**

Extend the timing proof of concept ([timing-individuals.md](timing-individuals.md)) from the
structures this repo has curated to the tissues the Human Developmental Cell Atlas actually
annotates, and use it for three jobs:

1. **Is this tissue term right for this stage?** Flag annotations whose tissue cannot exist at
   the annotated stage.
2. **What should we use instead?** Suggest terms that do exist at that stage and are
   developmentally related to the one chosen.
3. **Do the annotations contradict each other?** Within a donor, across sources of stage
   bounds, and between stage and other metadata.

---

## 1. What we have

### HDCA annotations

`HDCA_metadata/reports/tier1_filled/hdca_reprocessing - Tier 1 metadata (sex+stage+tissue+pcw).csv`:
one row per library, with a Uberon tissue and an HsapDv stage mapped by the HDCA metadata work.

| | |
|---|---:|
| libraries | 1,466 |
| publications | 26 |
| donors | 398 |
| tissue terms | 137 (plus 52 libraries "unknown") |
| stage terms | 35 |
| libraries at an embryonic stage (CS9–23, "organogenesis", "embryonic") | 542 over 71 tissue terms |

The embryonic libraries already contain annotations worth questioning, for example:

| tissue | stage(s) | why it looks wrong |
|---|---|---|
| thymus | CS9 (3 libraries) | the thymic primordium appears several stages later |
| vertebra, vertebral column | CS16, CS17 (41) | no vertebrae yet; sclerotome and pre-cartilage condensations |
| occipital bone, frontal bone, vault of skull, basicranium | CS16, "embryonic stage" | no bone until ossification, around CS23 and later |
| cerebral cortex | CS19 (8) | the cortical plate appears around CS20–21; before that, pallium and preplate |
| striatum | CS19 (14) | ganglionic eminences; the striatum is later |
| cerebellum | CS18, CS19 (17) | cerebellar plate and rhombic lip |
| testis | CS17, CS19 (3) | the gonad is indifferent until about CS17–18 |

These are latent-knowledge suspicions, written down here *before* any reasoning is run (see
§4), so the reasoner is checked against them rather than tuned to them.

### Stage bounds

- **This repo's table**: 174 rows, embryonic structures, partly sourced. Covers only 3 of the
  137 HDCA tissue terms.
- **EHDAA2**: stage bounds on 2,444 of its 2,456 classes, written with the same RO relations as
  ours (RO:0002496 starts, RO:0002497 ends). 67 of the 137 HDCA tissue terms have an EHDAA2
  cross-reference in Uberon. EHDAA2 covers Carnegie stages 1–20 only.
- **Uberon's relations**: develops_from and part_of carry bounds from precursors and wholes to
  terms with none (the PoC already does this).

The remaining ~70 HDCA tissues are mostly adult-named structures (knee, occipital bone,
striatum) and fetal stages, which neither source covers.

---

## 2. Extensions

### X1 — HDCA as an input

A loader (I/O only) turns the Tier 1 table into facts:

```
sample(library, donor, publication, tissue, stage)
```

HDCA tissue terms join the population as seeds. Their being annotated on human samples is
itself evidence that they apply to human.

Each sample becomes a **time point**, the moment of sampling, inside its annotated stage:
start(stage) ≤ t(sample) < end(stage). Each tissue it is annotated with must exist then:
s(tissue) ≤ t(sample) < e(tissue). This is the same endpoint machinery as everything else,
with one new kind of point.

### X2 — EHDAA2 bounds as a second source

Import EHDAA2's bounds onto Uberon terms through Uberon's EHDAA2 cross-references, tagged
`EHDAA2` so they never mix with this repo's curated rows. Two readings to compare:

- **as written**: RO:0002496 "starts during or after S", a lower bound only;
- **as intended**: EHDAA2 records the first stage a structure is present, which is "starts
  during S", a point bound.

Cross-references are not always exact equivalents. Import only one-to-one mappings at first,
and report the rest.

### X3 — curated bounds for the uncovered HDCA tissues

For HDCA tissues with neither source, add rows to `src/axioms.tsv`: latent first
(`curator: latent`), then sourced with the stage-evidence skill where O'Rahilly & Müller reach,
and Wikipedia beyond. Start bounds come first, because the most likely error is "too early".

The **naming convention** must be explicit: when does "vertebra" start? At chondrification? At
ossification? Uberon's definition decides. That decision belongs in the row, not in the
reasoner.

---

## 3. Experiments

Each has a question, a method, a pre-registered expectation and a success criterion.

### E1 — Coverage: what can be answered today, and after X2 and X3

For every HDCA library, ask whether its tissue is **certainly present**, **possibly present**,
or **certainly absent** at its stage. Report the three proportions:

- with the current network;
- with EHDAA2 bounds added (both readings);
- with the X3 rows added.

*Expectation:* nearly all "possibly" today. EHDAA2 moves the embryonic libraries to
certainly/absent for about half of the tissues. Fetal libraries stay mostly "possibly" until X3.

*Success:* most embryonic libraries get a definite answer.

### E2 — Flag stage-inappropriate tissue terms

Run the presence check on all 542 embryonic libraries (and the fetal ones where bounds exist).
Report every "certainly absent", with its derivation.

*Pre-registered expectations (latent):* thymus@CS9, vertebra and vertebral column@CS16, the
skull bones at CS16 and "embryonic stage" come out certainly absent. cerebral cortex@CS19,
striatum@CS19 and testis@CS17 depend on how the start bound is curated. Liver, heart, yolk sac,
midbrain, hindbrain and spinal cord come out present.

*Success:* the flags match the expectations above, or each mismatch has an explanation a
curator accepts. Thymus@CS9 is probably a stage error rather than a tissue error. The HDCA
metadata work already found the same pattern in thymus samples, where months were read as
weeks.

### E3 — Suggest stage-appropriate terms

For each flagged, or merely possible, annotation, propose terms that **certainly exist at the
stage** and are developmentally connected to the annotated term:

- its precursors, by walking develops_from backwards (vertebra → vertebral cartilage
  condensation → sclerotome);
- the parts and wholes of those (cerebral cortex → telencephalon, pallium);
- EHDAA2 terms at that stage that map to any of the above.

Rank by developmental distance. Check them against the authors' own free text, already
gathered in `HDCA_metadata/reports/embryonic_tissue_fields_by_sample.csv`.

*Expectation:*
- vertebra@CS16 → vertebral pre-cartilage condensation or sclerotome;
- striatum@CS19 → ganglionic eminence;
- cerebral cortex@CS19 → telencephalon or pallium;
- cerebellum@CS18 → cerebellar plate;
- testis@CS17 → indifferent gonad.

*Success:* for at least 15 of 20 flagged annotations, a curator would accept the top
suggestion.

**Policy, not only correctness:** HDCA may deliberately annotate early samples with the adult
term, to integrate across stages. The tool should make the choice visible, by reporting the
adult term and the stage-appropriate term side by side. It should not overrule a policy.

### E4 — Contradictions within the metadata

Three checks, all with the same machinery:

- **Within a donor.** Every tissue sampled from one donor at one time must coexist. Flag donors
  with two tissues that "never" coexist.
- **Refine coarse stages.** A sample annotated only "organogenesis stage" or "embryonic stage"
  (25 libraries), with tissues that exist only in a window, gets a narrower stage, derived. For
  example, a sample with a yolk sac and a metanephros lies between CS14 and the yolk sac's end.
- **Between sources.** Where both this repo and EHDAA2 bound the same structure, report every
  disagreement. These are curation leads in both directions.

*Expectation:* few donor contradictions, a handful of useful stage refinements, and a few dozen
table-vs-EHDAA2 disagreements, concentrated in end bounds.

### E5 — Fetal libraries

865 libraries are at week stages (weeks 9–31 post-fertilization). Transient structures sampled late
are the interesting cases: yolk sac, mesonephros, Müllerian duct in male donors, ductus
venosus. This needs end bounds (X3) and the half-open endpoint fix noted in
[timing-queries.md](timing-queries.md).

---

## 4. Order of work

1. **X1 + E1 baseline.** Load HDCA, run presence on the current network. Cheap; sets the
   baseline.
2. **X2 + E1 + E4 (between sources).** Import EHDAA2 bounds; measure coverage gain; list
   disagreements with this repo's table.
3. **E2 + E3 on embryonic libraries.** The main demonstration: flags with derivations and
   suggested terms, against the expectations above.
4. **X3 for the remaining tissues**, then E5 and E4 (within a donor, refinement).

Steps 1–3 need no new curation and give concrete results on real HDCA data. Step 4 is where the
agentic curation loop (latent bounds, sourced, verified) earns its place.

## 5. What could make this fail

- **Naming convention dominates.** If whether "vertebra" applies at CS16 is a policy choice,
  the flags measure policy, not error. E3's side-by-side output is the mitigation.
- **EHDAA2's bounds are coarser than they look.** Atlas-derived first and last stages, with
  "starts_at" semantics that need checking against a few sourced rows before they are trusted.
- **Stage mapping errors upstream.** Some flags will be errors in the stage, not the tissue, as
  with the thymus. The report must say which side is more likely, and E4's refinement helps.
- **The part_of reading.** Containment adds many bounds. Overlap is safer. Run E2 under both,
  and report what changes.
