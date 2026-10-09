# Species safety when extracting developmental timings from Wikipedia

**Read this before using `fetch_wiki_info.py` output to time a developmental
structure.** Not auto-loaded into agent context; `SKILL.md` links here.

Wikipedia articles on developing anatomical structures mix species without
marking the change. An article titled for a human structure will state a chick
or mouse timing in the next sentence, in the same voice, with no hedge. The
resulting error is invisible on review — a plausible number, attached to the
right structure, under the right taxon — which makes it the single most
dangerous failure mode of this skill.

## The contamination is real, not hypothetical

Measured on a 30-term probe against the structures in `src/axioms.tsv`:

| Article | What it returns | Species |
|---|---|---|
| Apical ectodermal ridge | "At stage 20HH (corresponding to 3.5 days)" | **chick** (Hamburger–Hamilton) |
| Rhombic lip | "as early as embryonic day 9.5", "between E15 and P15" | **mouse** |
| Primitive streak | "In the human embryo, this appears by Carnegie stage 6, about 17 days" | human |

A regex looking for `day \d+` or `stage \d+` takes all three. Only the third is
usable.

## These rules are enforced, not just advised

Everything below is implemented in the `stage-evidence` skill. Wikipedia is
registered there as a corpus **declaring no species**, so a record quoting it
is rejected unless the quote itself carries a human marker and carries no
foreign one. If you are producing evidence records, you do not need to apply
these rules by hand — but you do need to understand why a record was refused.

They still apply by hand anywhere you use this skill's output *outside* that
pipeline.

## Rule: positive human evidence, or no claim

Accept a timing **only** when the sentence carrying it, or the sentence
immediately before it, contains an explicit human marker:

- `human`, `humans`
- `Carnegie stage` / `CS\d+`
- `week of gestation`, `gestational age`, `postovulatory`, `post-fertilization`
- `dpo` (days post-ovulation)

Reject on sight, regardless of context:

- `HH` / `stage \d+HH` — Hamburger–Hamilton, **chick**
- `E\d+(\.\d+)?`, `P\d+` — embryonic/postnatal day, **mouse** (and the
  article will not say so)
- `NF stage` — Nieuwkoop–Faber, **Xenopus**
- `hpf` (hours post-fertilization) — **zebrafish**
- `somite stage` unqualified — used across all model organisms

A bare `day 22` or `4 weeks` with no human marker anywhere nearby is
**unusable**, not "probably human". Most of this skill's developmental output
falls into that category, and discarding it is correct.

## Rule: never convert on the source's behalf

Wikipedia says "sixth week of gestation". That is either:

- 6 weeks post-fertilization ≈ day 36–42 ≈ CS15–17, or
- 6 weeks menstrual ≈ day 22–28 ≈ CS10–13

— a **four-to-six stage** difference, from one ambiguous phrase. Clinical
sources count from the last menstrual period; embryological sources count from
fertilization; Wikipedia uses "gestation" for both.

Record the phrase verbatim and flag the ambiguity. Do not pick a reading and
carry the converted number forward as though the source had given it.

Likewise, do not convert days to Carnegie stages using background knowledge
and then present the result as sourced. The conversion table is itself latent
knowledge; a claim resting on it is not sourced, whatever the citation says.

## Rule: treat Wikipedia as triage, not as evidence

On the 30-term probe, only **10 terms** yielded any human timing at all. Of
those, 5 agreed with the table, 4 disagreed (`mesonephros`, `primitive streak`
end bound, `septum transversum`, `pronephros` end bound), and the rest were too
vague to adjudicate. The *Pronephros* and *Metanephros* articles contradict
each other on when the pronephros appears (day 20 vs day 22).

That is a useful signal for **where to look harder**. It is not a source to
cite. For human embryonic structures the sourceable alternative already exists
in this repo:

```bash
python3 .claude/skills/stage-evidence/stage_evidence.py search "<structure>"
```

O'Rahilly & Müller is human-only by construction, so none of the above applies
to it — which is the main reason to prefer it. Where it has no coverage (the
fetal period, anything after Carnegie stage 23), Wikipedia can be loaded into
the same corpus and the species gate applied per sentence:

```bash
python3 .claude/skills/stage-evidence/stage_evidence.py build --corpus Wikipedia "vernix caseosa"
```

## Wikidata

Carries no developmental timing. `Q247512` (primitive streak) has no temporal
property at all. What it does carry is **P1554 = UBERON ID**, which is worth
using for a different job: confirming the identifier you have is the structure
you think it is.

That is now wired in. `src/taxon_stage/validate.py` resolves identifier/label
pairs through OAK against OLS, falling back to the OLS REST API and then to a
Wikidata P1554 lookup, so a label check still works when OLS is unreachable.
Run it with `make validate`. Wikidata's label is its own rather than Uberon's,
so it is used only to confirm or to report "could not check" -- never to
declare a mismatch on its own.

## If you extract a timing anyway

Record, in this order: the verbatim sentence; whether a human marker was
present and which one; the ambiguity if the unit was "weeks of gestation"; and
`curator: latent` until a person checks it. A Wikipedia-derived timing is a
lead, and should be stored as one.
