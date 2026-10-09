# Pipeline: table -> GCIs -> named classes -> reasoning -> materialised table.
#
# The table is the only hand-edited file. Everything in build/ is disposable.

ROBOT ?= robot
PY    ?= PYTHONPATH=src uv run --no-project python -m taxon_stage.cli
TAXON ?= NCBITaxon:9606
TAXON_LABEL ?= Homo sapiens

TABLE  := src/axioms.tsv
BUILD  := build

.PHONY: all check validate axioms scoped materialize reach contribute test clean
all: check validate axioms

check:                         ## structural validation of the table
	$(PY) check $(TABLE)

# Online, and so kept separate from `check`: identifiers are resolved against
# OLS through OAK and the answers cached, so this is slow once and instant
# after. A label that disagrees with its identifier is the one error that
# reads perfectly and corrupts everything built downstream.
validate:                      ## check every identifier/label pair against the ontology
	$(PY) validate $(TABLE)

$(BUILD)/axioms.ofn: $(TABLE) src/taxon_stage/build.py
	$(PY) build $(TABLE) -o $@

axioms: $(BUILD)/axioms.ofn    ## the contribution: GCIs with evidence annotations

# Mint a named class for each GCI's anonymous left-hand side. Runs on any
# ontology carrying GCIs of this shape, which is the point -- once these axioms
# are in Uberon, this same step is what makes them queryable.
$(BUILD)/expanded.ttl: $(BUILD)/axioms.ofn sparql/expand.ru
	$(ROBOT) query --input $< --update sparql/expand.ru --output $@
	$(ROBOT) query --input $@ --query sparql/checks/unexpanded-gci.rq $(BUILD)/unexpanded.csv
	@test $$(wc -l < $(BUILD)/unexpanded.csv) -le 1 || \
	  (echo "FAIL: taxon-scoped GCIs did not expand; see $(BUILD)/unexpanded.csv" && exit 1)

# Scope expansion is the second, population-driven job: a bound on a parent
# only reaches a child if the child also has a scoped class. The population is
# the reasoned subClassOf descendants of the axiom subjects, intersected with
# Uberon's computed taxon subset -- 310 classes, not 13195. Terms outside that
# set can never inherit anything, so scoping them is waste.
$(BUILD)/scoped.ofn: $(TABLE) src/taxon_stage/scope.py src/taxon_stage/descendants.py
	$(PY) scope $(TABLE) -o $@ --taxon "$(TAXON)" \
	  $(if $(UBERON_OBO),--uberon-obo $(UBERON_OBO),)

scoped: $(BUILD)/expanded.ttl $(BUILD)/scoped.ofn

# The standalone round trip: no Uberon, no extra tools, runs per commit.
# Proves the table survives OWL generation, expansion and materialisation.
$(BUILD)/extracted.csv: $(BUILD)/expanded.ttl sparql/extract.rq
	$(ROBOT) materialize --input $(BUILD)/expanded.ttl --reasoner ELK --output $(BUILD)/materialized.ofn
	$(ROBOT) query --input $(BUILD)/materialized.ofn --query sparql/extract.rq $@

materialize: $(BUILD)/extracted.csv  ## round trip without Uberon (ROBOT only)
	@echo "extracted $$(( $$(wc -l < $(BUILD)/extracted.csv) - 1 )) rows"

# The real run. Needs UBERON=path/to/uberon-base.owl and relation-graph on PATH.
# ROBOT's materialize gives the non-redundant form only; relation-graph gives
# the closure, and is what Ubergraph itself uses -- so local numbers and
# Ubergraph numbers are comparable rather than merely similar.
# UBERON_OBO is the full uberon.obo release, read only for its computed taxon
# subset tags. They are absent from uberon-base.owl and from Ubergraph, so there
# is no way to get them from the files the rest of the build uses.
#
# Descendants come from Ubergraph and are cached in build/descendants.json; the
# cache records which subjects it was computed for, so adding an axiom
# invalidates it rather than silently returning a too-small set.
$(BUILD)/rg-out.tsv: $(BUILD)/axioms.ofn $(BUILD)/scoped.ofn
	@test -n "$(UBERON)" || (echo "set UBERON=path/to/uberon-base.owl" && exit 1)
	@test -n "$(UBERON_OBO)" || echo "warning: UBERON_OBO unset; scoping terms \
	  that cannot exist in $(TAXON_LABEL), whose bounds are vacuous"
	$(ROBOT) merge --input $(UBERON) --input $(BUILD)/scoped.ofn \
	  --input $(BUILD)/axioms.ofn --output $(BUILD)/merged-full.owl
	relation-graph --ontology-file $(BUILD)/merged-full.owl --output-file $@ \
	  --mode TSV --properties-file sparql/existence-properties.txt --obo-prefixes true

reach: $(BUILD)/rg-out.tsv     ## how many Uberon terms the axioms actually reach
	PYTHONPATH=src uv run --no-project python -m taxon_stage.reach $(BUILD)/rg-out.tsv $(TABLE)

contribute:                    ## package sourced axioms for submission to Uberon
	$(PY) contribute $(TABLE) -o contribution

test:
	PYTHONPATH=src uv run --no-project --with pytest pytest -q tests

clean:
	rm -rf $(BUILD)
