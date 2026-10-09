# Evidence records, and the first run against the table

Source-attributed support for claims in `../axioms.tsv`, one record per quoted
passage, conforming to [`../../schema/evidence.schema.json`](../../schema/evidence.schema.json).
Every quote here has been checked verbatim against the local corpus; the
Write/Edit hook will not let an unverifiable one into this directory.

Produced with the `stage-evidence` skill against O'Rahilly & Müller (1987),
*Developmental Stages in Human Embryos*, Carnegie Publication 637.

## What this run covered

All 176 rows were triaged mechanically. Eleven claims were then curated
properly, by reading. The gap between those two numbers is the point of the
section below.

## The triage is a priority list, not a verdict

The mechanical pass compares each claim against the first (or last) stage at
which the corpus mentions the structure:

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

Of the 114 start-bound claims, 25 are off by two or more stages. Those are the
ones worth a human read first; the full list is in the table at the end.

Five synonyms were removed after this run for manufacturing false
disagreements — `mesoblast`, `nephrogenic cord` for metanephric mesenchyme,
`optic primordium` for optic cup, and two others. Coverage stayed at 96/114
labels, so they were contributing noise and nothing else.

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

## Start-bound claims off by two or more stages

Unread, ranked by size. Each needs the passages looked at before anything moves.

| structure | table says | triage |
|---|---|---|
| proctodeum | CS13 | LATER by 6: book first mentions CS19 |
| Mullerian tubercle | CS18 | LATER by 5: book first mentions CS23 |
| floor plate of neural tube | CS10 | LATER by 4: book first mentions CS14 |
| pharyngeal pouch 2 | CS10 | LATER by 4: book first mentions CS14 |
| umbilical vein | CS12 | EARLIER by 4: book first mentions CS08 |
| amnion | CS05 | EARLIER by 3: book first mentions CS02 |
| hindgut | CS10 | EARLIER by 3: book first mentions CS07 |
| mammary ridge | CS15 | EARLIER by 3: book first mentions CS12 |
| maxillary prominence | CS13 | EARLIER by 3: book first mentions CS10 |
| neural tube mantle layer | CS14 | EARLIER by 3: book first mentions CS11 |
| neural tube marginal layer | CS15 | EARLIER by 3: book first mentions CS12 |
| optic vesicle | CS11 | EARLIER by 3: book first mentions CS08 |
| atrial septum primum | CS14 | EARLIER by 2: book first mentions CS12 |
| atrial septum secundum | CS16 | LATER by 2: book first mentions CS18 |
| cerebellar plate | CS16 | EARLIER by 2: book first mentions CS14 |
| cortical plate | CS20 | LATER by 2: book first mentions CS22 |
| foramen ovale of heart | CS16 | LATER by 2: book first mentions CS18 |
| frontonasal prominence | CS13 | LATER by 2: book first mentions CS15 |
| lung bud | CS12 | EARLIER by 2: book first mentions CS10 |
| olfactory placode | CS13 | EARLIER by 2: book first mentions CS11 |
| pharyngeal arch artery 3 | CS11 | LATER by 2: book first mentions CS13 |
| pharyngeal arch artery 6 | CS12 | LATER by 2: book first mentions CS14 |
| rhombic lip | CS14 | LATER by 2: book first mentions CS16 |
| sclerotome | CS12 | LATER by 2: book first mentions CS14 |
| somite | CS09 | EARLIER by 2: book first mentions CS07 |
