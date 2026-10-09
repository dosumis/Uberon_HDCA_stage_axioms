---
name: stage-evidence
description: Find and verify quotes about when human developing structures exist, from O'Rahilly & Muller (1987) Carnegie stages 1-23 and from Wikipedia. Use when sourcing, checking, or disputing a developmental timing claim. Quotes are machine-verified against a local corpus; fabricated quotes, misattributed stages, mislabelled identifiers and cross-species timings are rejected by Write/Edit hooks.
argument-hint: "[structure label] [--stage N] [--corpus ORahilly1987|Wikipedia]"
allowed-tools: Bash, Read, Write, Edit
---

# Stage evidence

Quote-backed evidence for `src/axioms.tsv`, from corpora that are kept locally
so every quote can be checked against the words that are actually there.

## Two corpora, deliberately unequal

| | `ORahilly1987` | `Wikipedia` |
|---|---|---|
| What | *Developmental Stages in Human Embryos*, Carnegie Publication 637 | English Wikipedia articles |
| Extent | Carnegie stages 1–23 (to ~day 60) | anything, including the fetal period |
| Species | **human by construction** | **not declared** |
| Stage structure | every passage carries its stage | none |
| Tier | primary | tertiary |

The inequality is recorded in the corpus, not left to anyone's memory, and it
changes what a quote has to survive. The O'Rahilly corpus is checked by
*provenance* — the source is human, so its passages are. Wikipedia is checked
*sentence by sentence*, because its articles on human structures carry chick
and mouse timings in the same voice as human ones.

## Setup

```bash
# primary corpus: 23 stage pages, ~1200 passages, a few seconds
python3 .claude/skills/stage-evidence/stage_evidence.py build

# add Wikipedia articles for named structures (there is no fixed extent)
python3 .claude/skills/stage-evidence/stage_evidence.py build --corpus Wikipedia \
    "vernix caseosa" "lung saccule"
```

Corpora accumulate — building one does not discard the other. Everything lands
in `.evidence-cache/` (gitignored: Carnegie Institution copyright, free to read
and cite, not ours to redistribute). Wikipedia fetching is delegated to the
`fetch-wiki-info-api` skill rather than reimplemented.

The O'Rahilly text comes from the UNSW Embryology transcription rather than the
Carnegie PDF: the PDF is OCR and renders "Shikinami" as "Shikinarni", while the
wiki is clean, already segmented by stage and organ system, and citable per
passage.

## Finding evidence

```bash
python3 .claude/skills/stage-evidence/stage_evidence.py search "ureteric bud"
python3 .claude/skills/stage-evidence/stage_evidence.py search "lens placode" --stage 13
python3 .claude/skills/stage-evidence/stage_evidence.py search "vernix caseosa" --corpus Wikipedia
```

Each hit shows corpus, tier, stage (where the corpus has one), section, URL,
and two warnings worth reading.

### The hedge flag

The book distinguishes what it knows from what it suspects, and that is the
most valuable thing in it:

> *stage 13:* "A ureteric bud **may possibly** be present in some specimens
> (Wells, 1954, fig. 4), although **further confirmation is needed**."

> *stage 14:* "the ureteric bud acquires a metanephrogenic cap"

A row asserting `existence starts during Carnegie stage 13` reads the first
sentence as if it were the second. `verify` rejects a record that quotes a
hedged passage without setting `hedged: true`.

### The species flag

On a Wikipedia hit you will see one of:

- `human marker: human, carnegie stage` — usable
- `NO HUMAN MARKER` — the passage names no human frame of reference
- `NOT HUMAN: Hamburger-Hamilton staging (chick)` — disqualified outright

Measured, not hypothetical: the *Apical ectodermal ridge* article gives
"18HH" (chick), *Rhombic lip* gives "E15–P15" (mouse). Both sit in articles
about structures in this axiom table.

The gate reads the **quote**, not the passage around it. A quote trimmed so
that it no longer says "in the human embryo" stops being human evidence, which
is the correct behaviour.

### Zero hits is not evidence of absence

O'Rahilly states outright that **"the term placode is avoided"**. He writes
*lens disc*, *otic disc*, *nasal disc*; *mesoblast* for mesoderm; *process* for
prominence; *upper/lower limb* for fore/hindlimb; *conus cordis* for bulbus
cordis; *aortic arch* for pharyngeal arch artery.

`SYNONYMS.tsv` maps Uberon labels onto the book's vocabulary — it lifts
coverage from 52/114 of the table's labels to 96/114. If `search` warns that a
term has no synonym entry and returns nothing, **that result is not usable**.
The file also records terms confirmed absent and terms out of scope (everything
fetal), so nobody repeats a dead search.

## Writing evidence records

Conforms to [`schema/evidence.schema.json`](../../../schema/evidence.schema.json).

```json
{
  "uberon_id": "UBERON:0000084",
  "uberon_label": "ureteric bud",
  "taxon_id": "NCBITaxon:9606",
  "stage_id": "HsapDv:0000020",
  "stage_label": "Carnegie stage 13",
  "claim": "start",
  "quote": "A ureteric bud may possibly be present in some specimens (Wells, 1954, fig. 4), although further confirmation is needed.",
  "source_id": "ORahilly1987:stage13",
  "section": "Urinary System",
  "source_tier": "primary",
  "hedged": true,
  "note": "The source will not commit to CS13. CS14 states the bud 'acquires a metanephrogenic cap' without hedging, so CS14 is the defensible start bound and CS13 is at best 'starts during or after'.",
  "curator": "do12",
  "date": "2026-10-09"
}
```

Interpretation goes in `note`; `quote` is the source's words and nothing else.
For a Wikipedia record `note` is **required**, because that corpus has no stage
structure and the stage attribution is therefore your inference, not the
source's.

## What is enforced

```bash
python3 .claude/skills/stage-evidence/stage_evidence.py verify src/evidence/kidney.json
make validate     # identifier/label pairs across the whole table
```

One hook in `.claude/settings.json` runs on every Write/Edit/MultiEdit to
`src/evidence/*.json` and `src/axioms.tsv`; everything else passes untouched.
It **blocks the write** — nothing unverifiable reaches disk — and the refusal
names the edit that repairs it.

An Edit is replayed against the file on disk before checking, so the hook sees
whole records rather than the fragment you happened to touch. Changing only a
`stage_id` is still caught, even though that edit contains no quote.

What blocks:

1. **Identifier/label disagreement.** `UBERON:0005079` beside "ureteric bud"
   reads perfectly and is wrong — it is the eggshell. Resolved through OAK
   against OLS (OLS REST and Wikidata `P1554` as fallbacks) and cached, so the
   hook is instant; `make validate` does the online pass. An identifier that
   cannot be resolved is reported, not blocked — an unreachable service is not
   evidence that a row is wrong.
2. **Quote not verbatim in the cited document** — including paraphrase,
   trimming and stitched-together sentences.
3. **Stage misattributed** — a real sentence filed under a stage it did not
   come from.
4. **Section, species rule, dropped hedge, missing fields.**

Every refusal carries a `FIX:` with the real value in it:

```
  * ureteric bud: stage_id is HsapDv:0000020 but this quote comes from
    HsapDv:0000022 (Carnegie stage 15)
    FIX: Set "stage_id": "HsapDv:0000022" and "stage_label": "Carnegie stage 15".
         If you meant to claim HsapDv:0000020, find a quote from that stage instead.

  * ureteric bud: quote is close to the source but not identical
    FIX: Replace it with the source's exact words:
         The ureteric bud is longer, and its tip is expanded as the pelvis of
         the ureter (fig. 15-10).
```

A near-miss quote gets the real sentence handed back; a mislabelled identifier
gets the identifier that actually carries the label you wrote.

**Apply the fix as given.** Do not reword a quote, trim a hedge, or delete a
field to make the check pass — each of those edits is indistinguishable from a
correct one once the file is on disk, which is the reason the check exists.

A quote that cannot be verified is not weak evidence; it is not evidence.

## Stage reference

```bash
python3 .claude/skills/stage-evidence/stage_evidence.py stages
```

Carnegie stage → HsapDv id → the "Size and Age" line *as the source states it*.
The HsapDv mapping is from OLS and agrees with the pairs already in the table.
A blank age means that stage's transcription lacks the bullet — leave it blank.
Converting a stage to a day count from background knowledge and reasoning about
it is exactly the move this skill exists to replace.

## Citing

> O'Rahilly R, Müller F (1987) *Developmental Stages in Human Embryos:
> Including a Revision of Streeter's "Horizons" and a Survey of the Carnegie
> Collection.* Carnegie Institution of Washington Publication 637.

[PDF](https://publicationsonline.carnegiescience.edu/publications_online/developmental_stages.pdf)
· [UNSW transcription](https://embryology.med.unsw.edu.au/embryology/index.php/Book_-_Developmental_Stages_In_Human_Embryos).
Free to read, no open licence — cite it, do not redistribute it.
