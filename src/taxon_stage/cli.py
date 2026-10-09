"""Command line surface. Machine-readable where an agent might read it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .build import write
from .model import check, load
from .scope import read_seed, write_template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tsa", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("check", help="structural validation of the axiom table")
    v.add_argument("table", type=Path)
    v.add_argument("--json", action="store_true")

    b = sub.add_parser("build", help="generate OWL functional syntax from the table")
    b.add_argument("table", type=Path)
    b.add_argument("-o", "--out", type=Path, required=True)

    s = sub.add_parser("scope", help="ROBOT template of taxon-scoped classes for a seed set")
    s.add_argument("seed", type=Path, help="TSV with uberon_id (and optionally uberon_label)")
    s.add_argument("-o", "--out", type=Path, required=True)
    s.add_argument("--taxon", default="NCBITaxon:9606")
    s.add_argument("--taxon-label", default="Homo sapiens")

    args = parser.parse_args(argv)

    if args.command == "scope":
        n = write_template(read_seed(args.seed), args.taxon, args.taxon_label, args.out)
        print(f"wrote {args.out}: {n} scoped classes")
        return 0

    axioms = load(args.table)

    if args.command == "check":
        problems = check(axioms)
        if args.json:
            print(json.dumps({"rows": len(axioms), "problems": problems}, indent=2))
        else:
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            print(f"{len(axioms)} rows, {len(problems)} problems")
        return 1 if problems else 0

    write(axioms, args.out)
    live = sum(1 for a in axioms if a.status != "superseded")
    print(f"wrote {args.out}: {live} axioms from {len(axioms)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
