# Carry Uberon's develops_from edges into the taxon-scoped namespace.
#
# `X SubClassOf develops_from some Z` is inherited by the scoped class as
# `X-9606 SubClassOf develops_from some Z` -- the species-neutral Z, because the
# reasoner has no grounds to conclude the filler is the human one. RO declares
# 17 `P o in_taxon -> in_taxon` chains but none for develops_from, and even with
# one the entailment would be "X is in a human", not "X develops from a human Z".
#
# So assert it. Sound, because developmental relations do not cross organisms.
# It buys no new entailment; it makes the scoped ontology self-contained, so a
# reader does not have to know to join back to species-neutral Uberon.
#
# Only fires where both ends already have a scoped class, so it cannot invent
# scope that the expansion did not establish.

PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX obo:  <http://purl.obolibrary.org/obo/>
PREFIX TSA:  <https://w3id.org/taxon-stage-axioms/>

INSERT {
  ?gm rdfs:subClassOf [ a owl:Restriction ;
                        owl:onProperty obo:RO_0002202 ;
                        owl:someValuesFrom ?gd ] .
}
WHERE {
  ?gm TSA:scoped_from ?m ; TSA:scoped_to ?taxon .
  ?gd TSA:scoped_from ?d ; TSA:scoped_to ?taxon .
  ?m rdfs:subClassOf [ a owl:Restriction ;
                       owl:onProperty obo:RO_0002202 ;
                       owl:someValuesFrom ?d ] .
}
