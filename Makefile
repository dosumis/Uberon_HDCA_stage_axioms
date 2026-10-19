# Pipeline: table -> GCIs -> named classes -> reasoning -> materialised table.
#
# The table is the only hand-edited file. Everything in build/ is disposable.

ROBOT ?= robot
PY    ?= PYTHONPATH=src uv run --no-project python -m taxon_stage.cli
TAXON ?= NCBITaxon:9606
TAXON_LABEL ?= Homo sapiens

TABLE  := src/axioms.tsv
BUILD  := build

.PHONY: all check validate axioms scoped materialize reach facts timing contribute test clean
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

# Timing of existence, relative to other structures (docs/timing-individuals.md).
# SPARQL moves facts out of the artefacts; all reasoning is in datalog/.
# Needs build/merged-full.owl from `make reach`, and souffle on PATH.
TIMING := $(BUILD)/timing
FACTS  := $(TIMING)/facts
HSAPDV_URL ?= http://purl.obolibrary.org/obo/hsapdv.owl
SOUFFLE_FLAGS ?=

$(BUILD)/hsapdv.owl:
	curl -sSL -o $@ $(HSAPDV_URL)

$(FACTS)/bound.csv: $(BUILD)/axioms.ofn sparql/timing/bound.rq
	@mkdir -p $(FACTS)
	$(ROBOT) query --input $< --query sparql/timing/bound.rq $@
$(FACTS)/seed.csv: $(BUILD)/scoped.ofn sparql/timing/seed.rq
	@mkdir -p $(FACTS)
	$(ROBOT) query --input $< --query sparql/timing/seed.rq $@
$(FACTS)/edge.csv: $(BUILD)/merged-full.owl sparql/timing/edge.rq
	@mkdir -p $(FACTS)
	$(ROBOT) query --input $< --query sparql/timing/edge.rq $@
$(FACTS)/stage_rel.csv: $(BUILD)/hsapdv.owl sparql/timing/stage_rel.rq
	@mkdir -p $(FACTS)
	$(ROBOT) query --input $< --query sparql/timing/stage_rel.rq $@
$(FACTS)/label.csv: $(BUILD)/merged-full.owl $(BUILD)/hsapdv.owl sparql/timing/label.rq
	@mkdir -p $(FACTS)
	$(ROBOT) query --input $(BUILD)/merged-full.owl --query sparql/timing/label.rq $(FACTS)/label-uberon.csv
	$(ROBOT) query --input $(BUILD)/hsapdv.owl --query sparql/timing/label.rq $(FACTS)/label-hsapdv.csv
	(cat $(FACTS)/label-uberon.csv; tail -n +2 $(FACTS)/label-hsapdv.csv) > $@
$(FACTS)/%.tsv: src/timing/%.tsv
	@mkdir -p $(FACTS)
	cp $< $@

TIMING_FACTS := $(addprefix $(FACTS)/,bound.csv seed.csv edge.csv stage_rel.csv label.csv \
                  individuate.tsv withheld.tsv)
facts: $(TIMING_FACTS)         ## export timing facts from the artefacts

# Runs in passes. Pass 1's conflicts are the conflict report. Each later pass
# withholds every axiom the previous pass's conflicts involve, until none
# remain; $(TIMING)/out is the last pass, whose bounds come from a consistent
# remainder. What was withheld, and why, is in each pass's facts/withheld.tsv.
timing: $(TIMING_FACTS) datalog/*.dl  ## reason over timing; SOUFFLE_FLAGS="-M NO_H1" etc.
	@rm -rf $(TIMING)/pass* $(TIMING)/out
	@set -e; i=1; facts=$(FACTS); \
	while :; do \
	  out=$(TIMING)/pass$$i; mkdir -p $$out; \
	  souffle $(SOUFFLE_FLAGS) -F $$facts -D $$out datalog/timing.dl; \
	  n=$$(( $$(wc -l < $$out/withhold_next.tsv) - 1 )); \
	  echo "pass $$i: $$(( $$(wc -l < $$out/conflict.csv) - 1 )) conflicting bound pairs," \
	    "$$(( $$(wc -l < $$out/cycle.csv) - 1 )) structural cycle edges," \
	    "$$(( $$(wc -l < $$out/in_conflict.csv) - 1 )) structures; withholding $$n axioms"; \
	  if [ $$(wc -l < $$out/unexplained.csv) -gt 1 ]; then \
	    echo "WARNING: pass $$i has conflicts no single excursion explains; see $$out/unexplained.csv"; fi; \
	  [ $$n -eq 0 ] && break; \
	  [ $$i -ge 5 ] && { echo "still conflicted after 5 passes"; exit 1; }; \
	  next=$(TIMING)/pass$$((i+1))-facts; cp -R $$facts $$next; \
	  tail -n +2 $$out/withhold_next.tsv >> $$next/withheld.tsv; \
	  facts=$$next; i=$$((i+1)); \
	done; \
	ln -sfn pass$$i $(TIMING)/out; \
	echo "bounds from pass $$i: new lower $$(grep -c ',new$$' $(TIMING)/out/lower_bound.csv)," \
	  "new upper $$(grep -c ',new$$' $(TIMING)/out/upper_bound.csv)"

contribute:                    ## package sourced axioms for submission to Uberon
	$(PY) contribute $(TABLE) -o contribution

test:
	PYTHONPATH=src uv run --no-project --with pytest pytest -q tests

clean:
	rm -rf $(BUILD)
