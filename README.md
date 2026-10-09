# taxon-stage-axioms

Taxon-scoped developmental stage bounds for Uberon structures: when, in a named
species, an anatomical structure starts and stops existing.

A curated table is the source of truth. OWL, named classes for reasoning, and a
materialised edge table are all generated from it.

## Why not just assert it on the Uberon class

`heart tube SubClassOf existence_starts_during some 'Carnegie stage 09'` is an
all-some claim. It says every heart tube in every organism starts at CS9, which
is false the moment a second species is considered — Carnegie stages are human.
So the axioms are General Class Inclusions, scoped by taxon:

```
(heart tube and in_taxon some Homo sapiens)
    SubClassOf existence_starts_during some 'Carnegie stage 09'
```

That is correct, and it is also invisible. A GCI has no named subject, so
relation-graph has nothing to attach an edge to and the axiom materialises as
nothing at all. Giving the left-hand side a name is what the expansion macro
does, and it is why that macro is a SPARQL update over the *artefact* rather
than another output of the table generator — the same step has to work on GCIs
in Uberon that we did not write.

## Why bother with OWL at all

Lookup would be better served by a table. OWL earns its place for one thing:
**a bound asserted on a parent reaches every child.** Demonstrated end to end in
`tests/fixtures/mini-uberon.ofn` — assert on `ganglionic eminence`, and ELK
infers

```
medial ganglionic eminence (Homo sapiens)  ⊑  ganglionic eminence (Homo sapiens)
lateral ganglionic eminence (Homo sapiens) ⊑  ganglionic eminence (Homo sapiens)
```

That is the same inference that supplies most of Uberon's existing bound
coverage: 4521 terms assert a start bound, 14613 have one once subclass
inheritance is read.

What OWL does **not** give you here is temporal consistency. EL has no
arithmetic over stages, so no reasoner will notice that a structure starts
before the thing it develops from. That stays a SPARQL query
(`sparql/checks/monotonicity.rq`), and HsapDv makes it answerable: 220
`immediately_preceded_by` and 50 `preceded_by` edges, against the single
ordering edge Uberon's species-neutral stages offer between embryonic
sub-stages.

## Layout

```
src/axioms.tsv          the only hand-edited file; schema in schema/
src/seed.tsv            which structures get a taxon-scoped class
src/taxon_stage/        table -> OWL, table -> ROBOT template, validation
sparql/expand.ru        GCI left-hand side -> named class
sparql/link-develops-from.ru   carry develops_from into the scoped namespace
sparql/checks/          monotonicity, unexpanded-GCI
sparql/extract.rq       materialised bounds back out as a table
```

## Pipeline

```
make check      validate the table
make axioms     table -> build/axioms.ofn   (this is the contribution)
make scoped     expand GCIs, generate scoped classes for the seed population
make reasoned   classify with ELK   (UBERON=path/to/uberon.owl)
make test
```

Materialising the existential edges needs **relation-graph**, which ROBOT's
`reason` step does not do — it asserts named subsumptions only. `make reasoned`
proves the classification; producing the edge table is a relation-graph run on
its output, and `sparql/extract.rq` reads that.

## Two things that cost an afternoon

**ROBOT template resolves Manchester cells by label, not CURIE.** A cell of
`UBERON:0004023 and (RO:0002162 some NCBITaxon:9606)` is a parse error. The seed
must carry labels and the target ontology must declare them for the structure,
the property and the taxon. `scope.py` refuses a seed row with no label rather
than emitting something that fails later.

**Reusing the GCI's bnode in the expansion does not survive an OWLAPI round
trip.** The macro inserts `GEN owl:equivalentClass ?lhs` sharing the existing
expression node; after serialisation the two are separate structures. This is
harmless — linking `GEN` to the GCI's consequent was always an entailment, not
an RDF path — but it means `sparql/extract.rq` must run *after* materialisation,
never on the expanded file.

## Curation

Every row starts `status: proposed` with `curator: latent`, meaning the claim
came from a language model's background knowledge and nobody has checked it.
That is a to-do, not provenance: `check` refuses to mark a row `accepted`
without a source, and `latent` never counts as sourced however the other columns
are filled in.

`onset_type` is the curator-facing judgement and `predicate` follows from it:

| onset_type | meaning | predicate |
|---|---|---|
| `point` | a definable onset or offset, so an exact stage can be named — and can be wrong | `RO:0002488` / `RO:0002492` |
| `interval` | appears or resolves progressively across stages (somites, arch arteries, serial condensations) | `RO:0002496` / `RO:0002497` |
| `single-stage` | exists within one stage only | `RO:0002491` |

Symmetry is not the criterion. Paired structures can be progressive — forelimb
bud appears at CS12 and hindlimb at CS13, and somite pairs form in sequence over
a dozen stages. The question is whether there is an onset to name.

The point/interval distinction is the fix for what made Uberon's existing bounds
unusable: `existence starts during or after` is unfalsifiable in practice, and
3348 terms asserting "after gastrula stage" taught us nothing. A point claim can
be wrong, so it can be checked.

## Status

Draft. 24 axioms over 20 structures, all `proposed`, none sourced. The
infrastructure is exercised end to end; the content is a worked example.
