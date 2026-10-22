# Countability classification: instructions

You are classifying anatomical terms from developmental anatomy ontologies (EHDAA2 = human
developmental anatomy, Carnegie stages 1-20; Uberon = cross-species anatomy). Use your own
knowledge of human embryology and anatomy only. Do not use the web or any other tool except to
read the batch file and write your output file.

The question for every term: **in one normal human embryo (or organism), how many separate
structures does this term denote, at the time it exists?** This decides whether the term can be
represented as a single individual in an idealised atlas of one embryo.

## Categories (choose exactly one)

- **ONE** — exactly one per embryo. Median or unpaired structures (notochord, heart tube,
  primitive streak, stomodeum), single organs (liver, pancreas primordium), a tissue, layer or
  region of a single structure (liver mesenchyme, heart tube endocardium), unique cavities and
  membranes (amniotic cavity, amnion). Also a single mass even if diffuse, if there is one per
  embryo (e.g. "6th arch mesenchyme from neural crest" if understood as one located mass).
- **FIXED** — a fixed number greater than one of separate structures, the members NOT separately
  named by this term. Usually left/right pairs (optic vesicle, otic pit, gonadal ridge, lung bud
  if bilateral) or small fixed sets (umbilical arteries = 2). Give n.
- **MEMBER** — one specific member of a series or set, identified by index or position (somite 21,
  rhombomere 7, pharyngeal arch 3, T2 vertebral condensation, upper limb bud). If that member is
  itself bilateral, it is still MEMBER: give n = 2.
- **GROUP** — a collective or generic term for a whole series or set whose members are
  enumerable (somite group, rhombomere group, "pharyngeal arch" in general, cervical vertebral
  condensations). Give n (approximate is fine, e.g. ~42) and mark the count variable if it
  varies between normal embryos.
- **MANY** — an indeterminate, large or variable number of units of one kind: cell types and cell
  populations (neural crest cells, primordial germ cells, haemangioblasts), repeated units within
  an organ or region (chorionic villi, nephrons, glomeruli, alveoli, hair follicles, capillaries,
  blood islands), and diffuse material (blood, mesenchyme in general).
- **TYPE** — an abstract or upper-level classifier rather than a part of the body plan, whose
  instances are heterogeneous kinds spread through the body (anatomical structure, tissue,
  organ, multi-tissue structure, artery, nerve, gland, skeletal element, embryonic structure).

Guidance:
- Count at the time the structure exists, at its fullest extent (somites: the full complement).
- Bilateral pairs: count both sides. "optic vesicle" → FIXED, n=2.
- If unsure between two categories, pick the better one and lower your confidence.
- If the label is ambiguous, use the definition, is_a and part_of columns.

## Output

Write a tab-separated file with this exact header and one row per input row, same ids:

    id	category	n	sided	confidence	note

- `n`: integer, or `~N` if approximate, or `var` if it varies between normal embryos, or blank
  for MANY and TYPE.
- `sided`: `Y` if the count is mainly a left/right doubling, else `N`.
- `confidence`: `H`, `M` or `L`.
- `note`: at most 12 words. Required when confidence is M or L, or n is `var`; else blank.

No other text in the file. Every input id must appear exactly once.
