# Pipeline: table -> GCIs -> named classes -> reasoning -> materialised table.
#
# The table is the only hand-edited file. Everything in build/ is disposable.

ROBOT ?= robot
PY    ?= PYTHONPATH=src uv run --no-project python -m taxon_stage.cli
TAXON ?= NCBITaxon:9606
TAXON_LABEL ?= Homo sapiens

TABLE  := src/axioms.tsv
SEED   := src/seed.tsv
BUILD  := build

.PHONY: all check axioms scoped reasoned test clean
all: check axioms

check:                         ## structural validation of the table
	$(PY) check $(TABLE)

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

# Scope expansion is a second, population-driven job: a bound on a parent only
# reaches a child if the child also has a scoped class.
$(BUILD)/scoped.tsv: $(SEED) src/taxon_stage/scope.py
	$(PY) scope $(SEED) -o $@ --taxon "$(TAXON)" --taxon-label "$(TAXON_LABEL)"

scoped: $(BUILD)/expanded.ttl $(BUILD)/scoped.tsv

# ELK classifies; relation-graph materialises the existentials. ROBOT's reasoner
# step asserts named subsumptions only -- enough to show inheritance works, not
# enough to produce the edge table. See README.
reasoned: scoped
	$(ROBOT) template --template $(BUILD)/scoped.tsv --input $(UBERON) --output $(BUILD)/scoped.ofn
	$(ROBOT) merge --input $(UBERON) --input $(BUILD)/scoped.ofn --input $(BUILD)/axioms.ofn \
	  reason --reasoner ELK --axiom-generators "SubClass" --output $(BUILD)/reasoned.ofn

test:
	PYTHONPATH=src uv run --no-project --with pytest pytest -q tests

clean:
	rm -rf $(BUILD)
