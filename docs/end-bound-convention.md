# A convention for end bounds

Draft for discussion. Nothing in the build implements this yet.

## The problem

Start bounds are mostly observations. A source says the structure is absent at
one stage and present at the next, and the onset is bracketed.

End bounds often are not. For many developmental structures nothing disappears:
the thing acquires enough pattern that we stop calling it by the old name and
start naming its parts. When does a pharyngeal arch stop being an arch? When is
the indifferent gonad differentiated enough to be a testis? Those are decisions
about vocabulary, not observations about tissue, and treating them as the latter
is how a table acquires false precision.

## What does not work

The obvious escape is to derive the end from the successor's onset: X ends when
the thing it develops into begins. Measured against the current table, this
fails outright.

Of 61 end bounds, 54 terms have a `develops_from` successor and 16 have a
successor whose start we have curated. In those 16 the arithmetic does not hold:

```
neural plate           end CS10   successor neural crest    starts CS09
intermediate mesoderm  end CS16   successor Mullerian duct  starts CS16
pharyngeal arch artery end CS20   successor aortic sac      starts CS10
periderm               end wk24   successor vernix caseosa  starts wk20
```

`develops_from` does not mean *replaced by*. A precursor routinely persists
while its derivative appears — the neural plate carries on existing after the
neural crest delaminates from it. So the end cannot be computed, and the
convention has to be curated.

## Proposal: an `offset_type` column

Parallel to `onset_type`, recording the curator's judgement about *what kind of
ending this is*, from which the predicate and the evidence standard both follow.

| `offset_type` | what ends | predicate | evidence required |
|---|---|---|---|
| `regression` | the tissue physically goes | `existence ends during` (RO:0002492) | a passage recording it as absent, regressed or no longer present |
| `event` | a named discrete event ends it | `existence ends during` | the timing of that event |
| `transformation` | consumed by becoming its successor; nothing persists under the old name | `existence ends during` | the successor's onset, **and** that the precursor is transformed rather than merely parent |
| `differentiation` | persists while derivatives appear; the end is a decision about when annotation moves to the parts | **`existence ends during or before`** (RO:0002497) | the stage at which a named derivative is itself bounded |

### Why `differentiation` takes the loose predicate

This is the whole point of the scheme. The arbitrariness is real and it is
confined to one category, so put it where it shows. `ends during or before` is
true wherever the transition actually sits, and it does not pretend to a
precision nobody has. A point claim there would be false precision, not a
tighter claim.

It also makes the table symmetrical: `onset_type: interval` already takes the
loose start predicate for structures that appear progressively. Progressive
disappearance gets the same treatment.

### The rule for picking the stage under `differentiation`

*Stop annotating the whole once the parts are nameable.* Take the earliest stage
at which a named derivative has its own start bound. Mechanical, reproducible,
and — because the predicate is a bound rather than a point — defensible even
where the real transition is earlier or later.

## How the current 61 fall out

Rough triage, to be checked term by term:

- **regression** — primitive streak, pharyngeal arch arteries 1 and 2,
  mesonephros, pronephric mesoderm, mammary ridge, apical ectodermal ridge,
  periderm, ganglionic eminence, nephrogenic zone, cardiac neural crest
- **event** — cloacal membrane (ruptures), and the four fetal shunts
  (ductus arteriosus, ductus venosus, foramen ovale, umbilical vein), all of
  which close at birth
- **transformation** — optic vesicle, lens placode, otic placode, otic pit,
  olfactory placode, neural plate/groove/fold, heart tube, notochordal plate,
  hepatic diverticulum, limb field, cortical preplate
- **differentiation** — the pharyngeal arches and the arch system, somite,
  intermediate mesoderm, the three facial prominences, indifferent gonad,
  limb bud and limb bud mesenchyme, liver primordium, neural crest

The clean categories are the minority but they are genuinely clean, and they
include every end bound anyone is likely to query: the shunts closing at birth
and the transient structures regressing.

## An alternative for `transformation`

RO has `existence ends at start of` (RO:0002593): *"the time point at which x
ends is equivalent to the time point at which y starts"*. No range restriction
to occurrents, so

```
optic vesicle  existence_ends_at_start_of  optic cup
```

says the thing directly, with no stage named and so no arbitrariness at all. It
asserts the transition is instantaneous, which for a true transformation is
exactly what is meant.

Worth checking how Uberon uses the relation, if at all, before relying on it.
It only applies where the transition really is a replacement, which is why
`transformation` has to be separated from `differentiation` either way.

## What this does not fix

Nothing here makes "sufficient pattern" objective. The convention confines the
judgement to one category, gives it a predicate that does not overstate, and
writes the rule down so it is applied the same way twice. That is the whole of
the claim.

## Consequence for the current contribution

All 20 end bounds are presently withheld, because the evidence store records
`start`, `present` and `absent` observations and nothing recording an **end**.
Adopting this convention is a precondition for collecting that evidence: the
sourcing pass needs to know which kind of ending it is looking for before it
can tell whether a passage answers the question.
