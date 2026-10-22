"""HDCA Tier 1 annotations -> sample.csv facts for datalog/hdca.dl.

I/O only: one row per library with a Uberon tissue and an HsapDv stage, as
HDCA_metadata mapped them. Rows whose tissue or stage is unmapped are dropped
and counted. No reasoning happens here.

    python -m taxon_stage.hdca <tier1 csv> <out sample.csv>
"""

import csv
import sys


def main(src: str, out: str) -> None:
    kept = dropped = 0
    with open(src, encoding="utf-8-sig", newline="") as f, open(out, "w", newline="") as g:
        w = csv.writer(g)
        w.writerow(["library", "donor", "publication", "tissue", "stage"])
        for r in csv.DictReader(f):
            tissue = r["tissue_ontology_term_id"].strip()
            stage = r["development_stage_ontology_term_id"].strip()
            if not tissue.startswith("UBERON:") or not stage.startswith("HsapDv:"):
                dropped += 1
                continue
            w.writerow([r["library_id"], r["donor_id"], r["publication_id"], tissue, stage])
            kept += 1
    print(f"{kept} libraries written, {dropped} dropped (tissue or stage unmapped)", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:3])
