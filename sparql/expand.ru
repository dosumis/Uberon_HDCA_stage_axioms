# Mint a named class for the anonymous left-hand side of every taxon-scoped GCI.
#
# A GCI has no named subject, so relation-graph has nothing to attach an edge
# to and the axiom materialises as nothing at all. Giving the LHS a name fixes
# that without changing what the ontology says: the generated class is
# *equivalent* to the expression, so it is a handle, not a new claim.
#
# This runs over any ontology carrying GCIs of this shape -- including Uberon
# itself, once the axioms are contributed upstream. That is why it is a SPARQL
# update over the artefact rather than another output of the table generator.
#
# The IRI is a deterministic function of (structure, taxon), so SPARQL never has
# to mint a fresh identifier and the mapping back to Uberon is string surgery.
#
#   robot query --input axioms.ofn --update sparql/expand.ru --output expanded.ofn

PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX obo:  <http://purl.obolibrary.org/obo/>
PREFIX TSA:  <https://w3id.org/taxon-stage-axioms/>

INSERT {
  ?gen a owl:Class ;
       owl:equivalentClass ?lhs ;
       TSA:scoped_from ?struct ;
       TSA:scoped_to ?taxon .
}
WHERE {
  ?ax a owl:Axiom ;
      owl:annotatedSource ?lhs ;
      owl:annotatedProperty rdfs:subClassOf .

  # The LHS is an intersection of a named structure and an in_taxon restriction.
  # Matching on shape rather than on the expand_for_reasoning annotation is
  # deliberate: an annotation can be forgotten, and a GCI that silently fails to
  # expand is invisible. Opting out is the exception, below.
  ?lhs owl:intersectionOf/rdf:rest*/rdf:first ?struct .
  FILTER(isIRI(?struct))

  ?lhs owl:intersectionOf/rdf:rest*/rdf:first ?tx .
  ?tx owl:onProperty obo:RO_0002162 ;
      owl:someValuesFrom ?taxon .
  FILTER(isIRI(?taxon))

  FILTER NOT EXISTS { ?ax TSA:expand_for_reasoning false }

  BIND(REPLACE(STR(?struct), "^.*[/#]", "") AS ?structLocal)
  BIND(REPLACE(STR(?taxon),  "^.*[/#]", "") AS ?taxonLocal)
  BIND(IRI(CONCAT("https://w3id.org/taxon-stage-axioms/scoped/",
                  ?structLocal, "-", ?taxonLocal)) AS ?gen)
}
