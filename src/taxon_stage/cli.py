"""Command line surface. Machine-readable where an agent might read it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .build import write
from .model import check, load
from .contribute import write as write_contribution
from .scope import read_seed, write_scope_all, write_template
from .taxon_subset import SUBSET_FOR_TAXON, counts, subset_members
from .validate import check_table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tsa", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("check", help="structural validation of the axiom table")
    v.add_argument("table", type=Path)
    v.add_argument("--json", action="store_true")

    o = sub.add_parser("validate", help="online check: do identifiers resolve, "
                                        "and does each label match its identifier?")
    o.add_argument("table", type=Path)
    o.add_argument("--json", action="store_true")

    b = sub.add_parser("build", help="generate OWL functional syntax from the table")
    b.add_argument("table", type=Path)
    b.add_argument("-o", "--out", type=Path, required=True)

    s = sub.add_parser("scope", help="ROBOT template of taxon-scoped classes for a seed set")
    s.add_argument("seed", type=Path, help="TSV with uberon_id (and optionally uberon_label)")
    s.add_argument("-o", "--out", type=Path, required=True)
    s.add_argument("--taxon", default="NCBITaxon:9606")
    s.add_argument("--taxon-label", default="Homo sapiens")

    c = sub.add_parser("contribute", help="package the axioms for submission to Uberon")
    c.add_argument("table", type=Path)
    c.add_argument("-o", "--out", type=Path, required=True, help="output directory")
    c.add_argument("--all", action="store_true",
                   help="include unsourced claims; off by default, because an "
                        "unsourced claim is a to-do rather than a proposal")

    sa = sub.add_parser("scope-all",
                        help="scoped classes for every Uberon class in an ontology file")
    sa.add_argument("ontology", type=Path)
    sa.add_argument("-o", "--out", type=Path, required=True)
    sa.add_argument("--taxon", default="NCBITaxon:9606")
    sa.add_argument("--uberon-obo", type=Path,
                    help="full uberon.obo, to read the computed taxon subset from. "
                         "Without it, scoped classes are generated for terms that "
                         "cannot exist in the taxon, whose bounds are vacuous.")

    args = parser.parse_args(argv)

    if args.command == "scope-all":
        restrict = None
        if args.uberon_obo:
            subset = SUBSET_FOR_TAXON.get(args.taxon)
            if not subset:
                print(f"no taxon subset registered for {args.taxon}", file=sys.stderr)
                return 1
            restrict = subset_members(args.uberon_obo, subset)
            if not restrict:
                available = sorted(counts(args.uberon_obo))
                print(f"subset {subset!r} tagged no terms; available: {available}",
                      file=sys.stderr)
                return 1
        n, skipped = write_scope_all(args.ontology, args.out, args.taxon, restrict)
        note = f"; {skipped} skipped as out of taxon" if skipped else ""
        print(f"wrote {args.out}: {n} scoped classes{note}")
        return 0

    if args.command == "scope":
        n = write_template(read_seed(args.seed), args.taxon, args.taxon_label, args.out)
        print(f"wrote {args.out}: {n} scoped classes")
        return 0

    axioms = load(args.table)

    if args.command == "contribute":
        info = write_contribution(axioms, args.out, sourced_only=not args.all)
        print(f"wrote {args.out}: {info['axioms']} axioms over {info['structures']} "
              f"structures; {info['withheld']} withheld as unsourced")
        return 0

    if args.command == "check":
        problems = check(axioms)
        if args.json:
            print(json.dumps({"rows": len(axioms), "problems": problems}, indent=2))
        else:
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            print(f"{len(axioms)} rows, {len(problems)} problems")
        return 1 if problems else 0

    if args.command == "validate":
        problems = check_table(axioms)
        real = [p for p in problems if not p["unchecked"]]
        if args.json:
            print(json.dumps({"rows": len(axioms), "problems": problems,
                              "mismatches": len(real)}, indent=2))
        else:
            for p in problems:
                tag = "UNCHECKED " if p["unchecked"] else ""
                print(f"  {tag}{p['where']}: {p['problem']}", file=sys.stderr)
                print(f"      FIX: {p['fix']}", file=sys.stderr)
            print(f"{len(axioms)} rows, {len(real)} label/identifier mismatches")
        return 1 if real else 0

    write(axioms, args.out)
    live = sum(1 for a in axioms if a.status != "superseded")
    print(f"wrote {args.out}: {live} axioms from {len(axioms)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
