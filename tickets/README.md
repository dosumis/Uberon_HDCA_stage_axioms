# Uberon term requests

Drafted, **not posted** — the `gh` token in this environment is invalid
(`gh auth status` reports "The token in keyring is invalid"). To file them:

```
gh auth login
for f in tickets/0*.md; do
  gh issue create --repo obophenotype/uberon \
    --title "$(head -1 "$f" | sed 's/^# //')" \
    --body-file <(tail -n +2 "$f")
done
```

Read them first. Each is a claim about what Uberon lacks, and the searches
behind them are recorded in the ticket so a reviewer can repeat them.

## What got dropped before drafting

An earlier survey listed more gaps than these. Checking properly against OLS4
rather than a local label dump removed most of them, because the local index
carried only exact synonyms:

| claimed missing | actually | 
|---|---|
| subventricular zone | `cerebral cortex subventricular zone` UBERON:0014940 exists |
| subplate | `cortical subplate` UBERON:0004035 exists |
| preplate | `cortical preplate` UBERON:0034711 exists |
| lung developmental stage terms | the *structures* exist (`lung saccule` UBERON:0000116, `alveolus of lung` UBERON:0002299); the stages are arguably GO's business, not Uberon's |

Three survived. That ratio is the reason to search before filing.

## On EHDAA2 xrefs

None to offer. EHDAA2 is queryable through OLS4 (2743 terms; `pronephros`
resolves to EHDAA2:0001570), and returns nothing for the fetal zone, the
germinal matrix or lanugo. It stops at CS20, which is before any of these
structures matter, so its absence is expected rather than informative.
