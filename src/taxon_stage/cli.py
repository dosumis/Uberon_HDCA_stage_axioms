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
from . import descendants as desc
from .scope import write as write_scope
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

    c = sub.add_parser("contribute", help="package the axioms for submission to Uberon")
    c.add_argument("table", type=Path)
    c.add_argument("-o", "--out", type=Path, required=True, help="output directory")
    c.add_argument("--all", action="store_true",
                   help="include unsourced claims; off by default, because an "
                        "unsourced claim is a to-do rather than a proposal")

    s = sub.add_parser(
        "scope", help="scoped classes for the terms that can inherit a bound")
    s.add_argument("table", type=Path)
    s.add_argument("-o", "--out", type=Path, required=True)
    s.add_argument("--taxon", default="NCBITaxon:9606")
    s.add_argument("--uberon-obo", type=Path,
                   help="full uberon.obo, read for its computed taxon subset tags. "
                        "Absent from uberon-base.owl and from Ubergraph, so there "
                        "is nowhere else to get them.")
    s.add_argument("--cache", type=Path, default=Path("build/descendants.json"))
    s.add_argument("--refresh", action="store_true",
                   help="refetch descendants even if the cache matches")

    args = parser.parse_args(argv)

    axioms = load(args.table)

    if args.command == "scope":
        subjects = sorted({a.uberon_id for a in axioms if a.status != "superseded"})
        found = desc.load(subjects, args.cache, args.refresh)
        in_taxon = None
        if args.uberon_obo:
            subset = SUBSET_FOR_TAXON.get(args.taxon)
            if not subset:
                print(f"no taxon subset registered for {args.taxon}", file=sys.stderr)
                return 1
            in_taxon = subset_members(args.uberon_obo, subset)
            if not in_taxon:
                print(f"subset {subset!r} tagged no terms; "
                      f"available: {sorted(counts(args.uberon_obo))}", file=sys.stderr)
                return 1
        n, skipped = write_scope(found, in_taxon, args.out, args.taxon)
        note = f"; {skipped} dropped as out of taxon" if skipped else ""
        print(f"wrote {args.out}: {n} scoped classes from "
              f"{len(subjects)} axiom subjects{note}")
        return 0

    if args.command == "contribute":
        info = write_contribution(axioms, args.out, sourced_only=not args.all,
                                  evidence_dir=args.table.parent / "evidence")
        print(f"wrote {args.out}: {info['axioms']} axioms over "
              f"{info['structures']} structures")
        print(f"  withheld: {info['unsourced']} unsourced, "
              f"{info['unsupported']} sourced but with no passage bearing on "
              f"the claim")
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
