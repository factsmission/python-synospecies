#!/usr/bin/env python3

import requests
import click


@click.command()
@click.argument('genus')
@click.argument('species')
@click.option('--endpoint', '-e')
def main(genus, species, endpoint):
    sparqlEndoint = endpoint or 'https://treatment.ld.plazi.org/sparql'
    # genus = 'Tyrannosaurus'
    # species = 'rex'
    query1 = f'''PREFIX dwc: <http://rs.tdwg.org/dwc/terms/>
PREFIX treat: <http://plazi.org/vocab/treatment#>
SELECT DISTINCT ?tc WHERE {{
  ?tc dwc:genus "{genus}";
      dwc:species "{species}";
      a <http://filteredpush.org/ontologies/oa/dwcFP#TaxonConcept>.
}}'''

    # print(f'Searching {sparqlEndoint} for {genus} {species}')
    r = requests.get(sparqlEndoint,
                     params={'query': query1},
                     headers={'accept': 'application/sparql-results+json'})

    if r.status_code == 200:
        named = [binding['tc']['value']
            for binding in r.json()['results']['bindings']]
        print(f'Found {len(named)} species that are {genus} {species}')
        for url in named:
            synonyms(url, sparqlEndoint)


def synonyms(url, sparqlEndoint):
    query = f'''PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX treat: <http://plazi.org/vocab/treatment#>
SELECT DISTINCT
?tc
?aug ?augd (group_concat(DISTINCT ?augc;separator="; ") as ?augcs)
?def ?defd (group_concat(DISTINCT ?defc;separator="; ") as ?defcs)
?dpr ?dprd (group_concat(DISTINCT ?dprc;separator="; ") as ?dprcs)
WHERE {{
  <{url}> ((^treat:deprecates/(treat:augmentsTaxonConcept|treat:definesTaxonConcept))|
    ((^treat:augmentsTaxonConcept|^treat:definesTaxonConcept)/treat:deprecates))* ?tc .
  OPTIONAL {{
    ?aug treat:augmentsTaxonConcept ?tc;
         dc:creator ?augc.
    OPTIONAL {{
      ?aug treat:publishedIn ?augp.
      ?augp dc:date ?augd.
    }}
  }}
  OPTIONAL {{
    ?def treat:definesTaxonConcept ?tc;
         dc:creator ?defc.
    OPTIONAL {{
      ?def treat:publishedIn ?defp.
      ?defp dc:date ?defd.
    }}
  }}
  OPTIONAL {{
    ?dpr treat:deprecates ?tc;
          dc:creator ?dprc.
    OPTIONAL {{
      ?dpr treat:publishedIn ?dprp.
      ?dprp dc:date ?dprd.
    }}
  }}
}}
GROUP BY ?tc ?aug ?augd ?def ?defd ?dpr ?dprd'''

    # print(f'Searching {sparqlEndoint} for {url}')
    r = requests.get(sparqlEndoint,
                     params={'query': query},
                     headers={'accept': 'application/sparql-results+json'})

    if r.status_code == 200:
        print(f'Synonyms of {url}')
        synonyms = sorted(list(set([binding['tc']['value'] for binding in r.json()[
                          'results']['bindings'] if binding['tc']['value'] != url])))
        if len(synonyms):
            [print(' · ' + s) for s in synonyms]
        else:
            print(' × None found')


if __name__ == "__main__":
    main()
