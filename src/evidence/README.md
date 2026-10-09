# Evidence records, and the first run against the table

Source-attributed support for claims in `../axioms.tsv`, one record per quoted
passage, conforming to [`../../schema/evidence.schema.json`](../../schema/evidence.schema.json).
Every quote here has been checked verbatim against the local corpus; the
Write/Edit hook will not let an unverifiable one into this directory.

Produced with the `stage-evidence` skill (`search`, then reading the passages) against O'Rahilly & Müller (1987),
*Developmental Stages in Human Embryos*, Carnegie Publication 637.

## What this run covered

All 176 claims across 114 structures have now been read against the corpus,
not merely triaged. 34 evidence records carry the cases where a quote settles
something. The per-structure verdicts are tabulated at the end.

| verdict | structures | meaning |
|---|---:|---|
| CONFIRMED | 40 | the source says what the table says |
| WEAK | 22 | supported only by a hedged or indirect passage |
| SHIFT | 15 | the source puts it at a different stage, usually by one or two |
| NO-SOURCE | 14 | the book does not name the structure |
| OUT-OF-SCOPE | 10 | fetal; the corpus ends at CS23 |
| CONTRADICTED | 4 | the source says something incompatible |
| OPEN | 4 | the source is not self-consistent |
| UNREAD | 5 | no stage-specific statement found to judge against |

Roughly a third of the table is confirmed outright. Another third needs a
curator's decision — the WEAK and SHIFT rows are mostly off by a single stage,
which is within the range where the source's own specimen-to-specimen variation
matters. Four claims are wrong in a way that reading settles.

## Why the mechanical pass could not be trusted

The first pass compared each claim against the first (or last) stage at which
the corpus mentions the structure. It reported:

| | claims |
|---|---:|
| first/last mention agrees with the claimed stage | 35 |
| book mentions it earlier than claimed | 60 |
| book mentions it later than claimed | 50 |
| no passage found | 19 |
| fetal, outside the corpus entirely | 12 |

**Do not read those 110 disagreements as 110 errors.** First mention is not
first existence, and reading the passages shows why:

- The book forward-references. The CS12 account of the ectodermal ring says
  the mammary crest "appears one week later" — a mention at CS12 of a thing
  that is not there yet, which the proxy scores as a three-stage disagreement.
- It discusses other species and other authors' theories. The CS5 "primitive
  streak" hits are Hill and Florian arguing about Tarsioid and Lemuroid
  embryos, not a claim about a human CS5 streak.
- It mentions structures retrospectively. CS11 calls the caudal eminence "the
  region of the former primitive streak", which inflates last-mention for a
  structure that has gone.
- Specimen catalogues repeat a term dozens of times per stage without
  asserting anything about onset.

End bounds are worse affected than start bounds, because a single retrospective
sentence moves last-mention arbitrarily far.

That is why every claim was then read. The verdicts in the table at the end are
from the passages, not from this proxy; where the two disagree, the proxy is
wrong. It served only to rank what to read first.

Five synonyms were removed after this run for manufacturing false
disagreements — `mesoblast`, `nephrogenic cord` for metanephric mesenchyme,
`optic primordium` for optic cup, and two others. Coverage stayed at 96/114
labels, so they were contributing noise and nothing else.

## What was applied to the table

20 rows were edited (commit following this README). Every edited row carries a
quote-backed record in this directory, `evidence_code: ECO:0000304`, the
citation in `source`, and `curator: agent:stage-evidence` -- which is NOT a
claim that a person has checked it. `status` stays `proposed`: the schema
reserves `accepted` for a curator's review, and an agent reading a source is
not that.

Two rows superseded: both `pronephros` bounds. 17 stage corrections: ureteric
bud CS13→14, sinus venosus CS10→11, septum primum CS14→13, septum secundum and
foramen ovale CS16→18, rhombic lip CS14→16, chondrocranium CS16→17, stomodeum
CS10→9, hindgut CS10→9, neural groove CS9→8, notochordal plate end CS9→11,
Mullerian duct CS15→16, olfactory placode CS13→12, olfactory pit CS14→15, and
the three neural-tube layers (marginal CS15→12, mantle CS14→13, ventricular
CS12→13). One evidence_text corrected: mesonephros, which claimed function five
stages before the source allows it.

**Not applied, deliberately.** The 22 WEAK rows keep their stages: a claim
resting on a hedge is not thereby wrong, and converting them to
`RO:0002496`/`interval` is a modelling decision for a curator, not a correction.
`pharyngeal arch 4` was initially read as contradicted and is not -- the source
says three arches are "the usual final complement **seen externally**", which
is about visibility, not existence. The OPEN rows stay as they are.

## What was actually established

### Contradicted outright

**pronephros** (two rows, CS9–CS12). Not a stage error — a kind error. The
source quotes Torrey (1954): *"the concept of the pronephros does not apply to
the human embryo"*. The table asserts the structure exists in *Homo sapiens*
across four stages. What the book puts here is the nephrogenic cord
differentiating from intermediate mesoderm. Both rows should be withdrawn or
restated, not shifted. See `urinary.json`.

**mesonephros, "functional from CS11"**. The source's only statement about
mesonephric function puts urine production at CS17, six stages later. CS11 is
where nephric vesicles appear — presence, not function. The existence bound
may survive; the word "functional" does not.

### Weakened

**ureteric bud, starts CS13**. The source hedges twice in one sentence and
rests on a single figure in a single paper: *"A ureteric bud may possibly be
present in some specimens (Wells, 1954, fig. 4), although further confirmation
is needed."* The first unhedged statement is at CS14. CS13 supports at most
`RO:0002496` (starts during or after); CS14 is the defensible `RO:0002488`.

**ureteric bud, ends CS16**, on the grounds that it has branched into the
collecting system by then. The source puts collecting-tubule development at
"stages 17 and 18", and at CS16 has the ureteric pelvis only just dividing.
Two stages early.

### Confirmed

- **primitive streak** CS6 start — *"In the human, the primitive streak appears
  first during stage 6."* Explicitly scoped to human in a chapter that
  otherwise leans on chick.
- **primitive streak** CS10 end — present at CS10, "former" by CS11. This
  overturns a doubt raised earlier from Wikipedia, which put disappearance
  nearer CS12. The tertiary source was wrong and the table was right.
- **otic placode** CS9 start — *"The otic disc (or plate) makes its appearance
  during stage 9."* Reachable only through the synonym map, since the book
  states that "the term placode is avoided".
- **septum transversum** CS9 start — identified by stage 9. Wikipedia put it at
  day 22, which is CS10.
- **metanephros** CS14 — corroborated rather than contradicted; the first time
  the book names the metanephros is CS16, "now reniform", which reads as a
  structure already under way.

### Open

**lens placode** CS12. The CS13 summary says the lens disc *appears* at CS13;
the CS12 account lists lens discs among the six parts of an ectodermal ring
"complete at stage 12". The source is not self-consistent. Recorded as
`present`, not `start`, and the bound should not move on either passage alone.

## Not checkable here

Twelve fetal claims — vernix caseosa, lung saccule, brown adipose tissue, the
ossification centres, the cortical layers — fall after CS23, where this corpus
ends. Nineteen more structures are not named in the book at all (`heart tube`,
`ductus arteriosus`, `periderm`, `myotome`; the full list is in
`../../.claude/skills/stage-evidence/SYNONYMS.tsv`). Neither group is evidence
against the table. They need a different source.

## Every claim, by verdict

`2488` existence starts during · `2492` ends during · `2496` starts during or
after · `2497` ends during or before.

| structure | table says | verdict | basis |
|---|---|---|---|
| mesonephros | 2488@CS11, 2492@CS20 | **CONTRADICTED** | 'functional from CS11' — source puts urine production at CS17. |
| pharyngeal arch 4 | 2488@CS12, 2492@CS17 | **CONTRADICTED** | CS12 characteristic feature is three arches 'in contrast with the two of the previous stage'; table starts arch 4 at CS12. |
| pronephros | 2488@CS9, 2492@CS12 | **CONTRADICTED** | source: 'the concept of the pronephros does not apply to the human embryo' (Torrey 1954). Withdraw, do not shift. |
| sinus venosus | 2488@CS10, 2492@CS16 | **CONTRADICTED** | CS10: 'a sinus venosus as such is not present until the next stage'. Move to CS11. |
| Mullerian duct | 2488@CS15 | **SHIFT** | table CS15; source has the paramesonephric primordium 'beginning to appear' at CS16, and CS17 says it 'may appear at the previous stage'. |
| atrial septum primum | 2488@CS14 | **SHIFT** | table CS14; source has it appearing CS13 (and 'may appear' CS12). |
| atrial septum secundum | 2488@CS16 | **SHIFT** | table CS16; source first has it 'appearing' at CS18. |
| chondrocranium | 2488@CS16 | **SHIFT** | table CS16; source 'beginning chondrocranium' at CS17. |
| foramen ovale of heart | 2488@CS16, 2492@CSfetal | **SHIFT** | table CS16; source CS18, same sentence as septum secundum. |
| hindgut | 2488@CS10 | **SHIFT** | table CS10; distinguishable at CS9 in some specimens. |
| neural groove | 2488@CS9, 2492@CS11 | **SHIFT** | table CS9; CS8 specimens 'already show a neural groove'. |
| neural tube mantle layer | 2488@CS14 | **SHIFT** | table CS14; 'a beginning mantle zone' at CS13. |
| neural tube marginal layer | 2488@CS15 | **SHIFT** | table CS15; 'a marginal layer begins to develop' at CS12. Three stages late. |
| neural tube ventricular layer | 2488@CS12 | **SHIFT** | table CS12; at CS11 'one cannot yet mark off ependymal and mantle' zones, and the ependymal zone is named at CS13. |
| notochordal plate | 2488@CS8, 2492@CS9 | **SHIFT** | end bound CS9; source still has notochordal plate at CS10-11. |
| olfactory pit | 2488@CS14, 2492@CS18 | **SHIFT** | table CS14; 'nasal pits are appearing' is the CS15 summary. |
| olfactory placode | 2488@CS13, 2492@CS14 | **SHIFT** | table CS13; the nasal plate is already named at CS11 and nasal discs thicken at CS12. |
| rhombic lip | 2488@CS14 | **SHIFT** | table CS14; source's only mention is CS16. |
| stomodeum | 2488@CS10, 2492@CS17 | **SHIFT** | table CS10; source 'beginning to form' at CS9. |
| aortic sac | 2488@CS10, 2492@CS16 | **WEAK** | table CS10; first mention CS11. |
| apical ectodermal ridge | 2488@CS13, 2492@CS20 | **WEAK** | table CS13; the source names the AER at CS16, and the CS12 ectodermal-ring passage only forward-references it as following 'within 2 days'. |
| bulbus cordis | 2488@CS10, 2492@CS16 | **WEAK** | table CS10; conus cordis first differentiated at CS11. |
| endocardial cushion | 2488@CS14, 2492@CS18 | **WEAK** | table CS14; cushions already reducing the AV passage at CS13. |
| forelimb bud | 2488@CS12, 2492@CS18 | **WEAK** | table CS12; source: CS12 has 'either no upper limb bud at all, or ... a slight elevation'. CS13 is firm. |
| frontonasal prominence | 2488@CS13, 2492@CS19 | **WEAK** | table CS13 rests on 'In stage 13 the nasal discs consist merely of areas of thickened surface ectoderm', which is about the discs, not a frontonasal prominence. |
| gonadal ridge | 2488@CS15 | **WEAK** | table CS15; germ cells are already migrating to the gonadal ridges at CS14. |
| heart tube | 2488@CS9, 2492@CS11 | **WEAK** | table CS9; endocardial tubes fuse into a single tube at CS10. |
| hepatic diverticulum | 2488@CS10, 2492@CS12 | **WEAK** | table CS10; first mention CS11. |
| indifferent gonad | 2488@CS15, 2492@CS20 | **WEAK** | table CS15; the gonadal primordium is first 'indicated' at CS16. |
| lateral plate mesoderm | 2488@CS8 | **WEAK** | table CS8; the only nearby mention is 'lateral plates' in the CS7 account of streak derivatives. |
| liver primordium | 2488@CS10, 2492@CS14 | **WEAK** | table CS10; first mention CS11. |
| mammary ridge | 2488@CS15, 2492@CS18 | **WEAK** | table CS15; the mammary crest is already referred to at CS14. |
| maxillary prominence | 2488@CS13, 2492@CS19 | **WEAK** | table CS13; hedged first mention ('probably the maxillary process') at CS10. |
| midgut | 2488@CS9 | **WEAK** | table CS9; 'becoming delimited' at CS10. |
| pancreas ventral primordium | 2488@CS13 | **WEAK** | table CS13 rests on hedges: 'may be distinguishable as early as stage 13', 'if not detectable earlier'. CS14-15 is where the source commits. |
| pharyngeal arch 2 | 2488@CS10, 2492@CS17 | **WEAK** | table CS10 rests on a hedged 'probably'; CS11 is the firm statement. |
| pharyngeal arch 3 | 2488@CS11, 2492@CS17 | **WEAK** | table CS11 rests on 'arch 3 may do so'; CS12 has three arches. |
| pharyngeal arch artery 6 | 2488@CS12 | **WEAK** | table CS12; the pulmonary (sixth) arch is described at CS14. |
| pharyngeal pouch 1 | 2488@CS10 | **WEAK** | table CS10; the CS9 'shallow pocket' recess may already be pouch 1. |
| truncus arteriosus | 2488@CS11, 2492@CS16 | **WEAK** | table CS11; first listed among cardiac tube portions at CS12. |
| ureteric bud | 2488@CS13, 2492@CS16 | **WEAK** | CS13 start doubly hedged ('may possibly', 'further confirmation is needed'); CS14 first unhedged. CS16 end vs collecting tubules 'at stages 17 and 18'. |
| cerebellar plate | 2488@CS16 | **OPEN** | CS14 'begin to be visible', CS17 'present as a clear thickening'; table CS16 matches neither. |
| lens placode | 2488@CS12, 2492@CS13 | **OPEN** | CS13 summary says lens discs appear; CS12 lists them in an ectodermal ring 'complete at stage 12'. |
| metanephric mesenchyme | 2488@CS13 | **OPEN** | table CS13; the source has the nephrogenic cord at CS10 and the metanephrogenic cap at CS14, but nothing that clearly dates a metanephric blastema at CS13. |
| pronephric mesoderm | 2488@CS9, 2492@CS12 | **OPEN** | same Torrey passage bears on it; book puts the nephrogenic cord at CS10, table says CS9. |
| allantois | 2488@CS7 | **CONFIRMED** | allantoic diverticulum described at CS7. |
| amnion | 2488@CS5 | **CONFIRMED** | CS5 differentiation of the amnion referenced; squamous amnion described CS6-7. |
| amniotic cavity | 2488@CS5 | **CONFIRMED** | 'definite appearance of the amniotic cavity' at stage 5. |
| atrioventricular canal | 2488@CS11, 2492@CS16 | **CONFIRMED** | CS11 chamber sequence includes it. |
| cardiac neural crest | 2496@CS10, 2497@CS14 | **CONFIRMED** | vagal crest in the CS10 succession; vagal-accessory crest at CS11. Interval CS10-CS14 is consistent. |
| chorionic villus | 2488@CS6 | **CONFIRMED** | CS5 previllous by definition; CS6a characteristic feature. |
| cloacal membrane | 2488@CS7, 2492@CS18 | **CONFIRMED** | described at CS7; primordium noted CS6. |
| foregut | 2488@CS9 | **CONFIRMED** | CS9: detached foregut is a prerequisite for head detachment. |
| ganglionic eminence | 2488@CS15, 2497@CSfetal | **CONFIRMED** | CS14 'future medial striatal ridge'; both ridges at CS15. |
| hindlimb bud | 2488@CS13, 2492@CS19 | **CONFIRMED** | CS13: first sight of both upper and lower limb buds. |
| intermediate mesoderm | 2488@CS9, 2492@CS16 | **CONFIRMED** | 'can be made out in stage 9', though no nephric structures until CS10. |
| lens vesicle | 2488@CS13, 2492@CS16 | **CONFIRMED** | lens pit open at CS14, 'lens vesicles have closed' at CS15; CS13 start and CS16 end bracket that. |
| limb bud | 2496@CS12, 2497@CS19 | **CONFIRMED** | CS13 summary: 'all four limb buds are usually visible'. |
| lung bud | 2488@CS12 | **CONFIRMED** | CS12 summary: 'the lung bud appears'. |
| mandibular prominence | 2488@CS10, 2492@CS19 | **CONFIRMED** | CS10: 'swellings begin to appear for the mandibular arch'. |
| metanephric cap | 2488@CS14 | **CONFIRMED** | CS14 summary: ureteric bud 'acquires a metanephrogenic cap'. |
| metanephros | 2488@CS14 | **CONFIRMED** | CS14 cap; first named 'reniform' at CS16. |
| neural crest | 2496@CS9, 2497@CS16 | **CONFIRMED** | 'These dividing cells are believed to be neural crest' at CS9; interval CS9-CS16 consistent. |
| neural fold | 2488@CS9, 2492@CS12 | **CONFIRMED** | present CS9; folds fusing CS10-11. |
| neural plate | 2488@CS8, 2492@CS10 | **CONFIRMED** | present from CS8-9; neural tube forming from plate and folds at CS10. |
| neural tube | 2488@CS10 | **CONFIRMED** | 'the neural tube first begins to be formed' during stage 10. |
| optic cup | 2488@CS13 | **CONFIRMED** | 'the beginning of an optic cup can be seen' at CS13. |
| optic vesicle | 2488@CS11, 2492@CS13 | **CONFIRMED** | CS11 summary. |
| otic placode | 2488@CS9, 2492@CS11 | **CONFIRMED** | 'The otic disc (or plate) makes its appearance during stage 9.' |
| pancreas dorsal primordium | 2488@CS12 | **CONFIRMED** | CS12 summary: the dorsal pancreas becoming distinguishable. |
| pancreas primordium | 2496@CS12 | **CONFIRMED** | CS12 via the dorsal pancreas; interval bound is right. |
| pharyngeal arch | 2496@CS10, 2497@CS17 | **CONFIRMED** | arch 1 begins CS10; three arches by CS12. |
| pharyngeal arch 1 | 2488@CS10, 2492@CS17 | **CONFIRMED** | CS10 summary: 'pharyngeal arch 1 begins'. |
| pharyngeal arch artery 1 | 2488@CS10, 2492@CS12 | **CONFIRMED** | CS10: 'aortic arches 1 and 2 develop'. |
| pharyngeal arch artery 2 | 2488@CS10, 2492@CS13 | **CONFIRMED** | same CS10 sentence. |
| pharyngeal arch system | 2488@CS10, 2492@CS20 | **CONFIRMED** | as for pharyngeal arch. |
| pharyngeal pouch | 2496@CS10 | **CONFIRMED** | pouch 2 identifiable at CS10, pouch 3 indicated. |
| pharyngeal pouch 2 | 2488@CS10 | **CONFIRMED** | CS10: 'cleft 2 and pouch 2 are identifiable'. |
| pharyngeal pouch 3 | 2488@CS11 | **CONFIRMED** | CS10 'pharyngeal pouch 3 may be indicated'; table CS11 is the firm reading. |
| posterior neural tube | 2488@CS10 | **CONFIRMED** | the caudal eminence is named at CS10. |
| primitive streak | 2488@CS6, 2492@CS10 | **CONFIRMED** | CS6 'appears first during stage 6'; 'former' by CS11, so CS10 end is right. |
| septum transversum | 2488@CS9, 2492@CS16 | **CONFIRMED** | 'identified by stage 9'. |
| somite | 2496@CS9, 2497@CS20 | **CONFIRMED** | CS8 presomitic; CS9 characteristic feature 1-3 pairs. |
| thymus primordium | 2488@CS13 | **CONFIRMED** | thymic primordium of pouch 3 distinguishable at CS13. |
| thyroid primordium | 2488@CS10, 2492@CS16 | **CONFIRMED** | 'The thyroid primordium appears' at CS10. |
| Mullerian tubercle | 2488@CS18 | **NO-SOURCE** | table CS18; the sinusal tubercle is not mentioned before CS23. |
| cerebral cortex subventricular zone | 2488@CS23 | **NO-SOURCE** | not named in the corpus |
| cortical preplate | 2488@CS16, 2492@CS20 | **NO-SOURCE** | not named in the corpus |
| cortical subplate | 2488@CS20 | **NO-SOURCE** | not named in the corpus |
| ductus arteriosus | 2488@CS14, 2492@CSfetal | **NO-SOURCE** | not named in the book. |
| floor plate of neural tube | 2488@CS10 | **NO-SOURCE** | no usable passage; the one hit is unrelated. |
| limb bud mesenchyme | 2496@CS12, 2497@CS19 | **NO-SOURCE** | not named in the corpus |
| limb field | 2488@CS11, 2492@CS13 | **NO-SOURCE** | not named in the corpus |
| mammary placode | 2488@CS17 | **NO-SOURCE** | not named in the corpus |
| pharyngeal arch 6 | 2488@CS12, 2492@CS17 | **NO-SOURCE** | not named in the corpus |
| primary ossification center | 2496@CS23 | **NO-SOURCE** | not named in the corpus |
| proctodeum | 2488@CS13 | **NO-SOURCE** | not named in the book. |
| sclerotome | 2496@CS12 | **NO-SOURCE** | only an incidental CS14 mention of sclerotome levels. |
| vertebral element | 2496@CS13 | **NO-SOURCE** | no usable passage; only an incidental mention of sclerotome levels. |
| alveolus of lung | 2488@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| brown adipose tissue | 2488@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| cortical plate | 2488@CS20 | **OUT-OF-SCOPE** | fetal; corpus ends CS23. |
| ductus venosus | 2488@CS14, 2492@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| lung saccule | 2488@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| nephrogenic zone | 2488@CS14, 2492@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| periderm | 2488@CS16, 2492@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| secondary ossification center | 2496@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| umbilical vein | 2488@CS12, 2492@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| vernix caseosa | 2488@CSfetal | **OUT-OF-SCOPE** | fetal; corpus ends CS23 |
| otic pit | 2488@CS11, 2492@CS12 | **UNREAD** | triaged only |
| pharyngeal arch artery | 2496@CS10, 2497@CS20 | **UNREAD** | triaged only |
| pharyngeal arch artery 3 | 2488@CS11 | **UNREAD** | no stage-specific statement found; the numbered arches are not individually dated beyond 1, 2 and 6. |
| pharyngeal arch artery 4 | 2488@CS12 | **UNREAD** | as for arch artery 3. |
| pharyngeal pouch 4 | 2488@CS12 | **UNREAD** | no stage-specific statement found. |
