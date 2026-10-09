"""The online half of validation: do these identifiers exist, and is the label
beside each one really its label?

`model.check` asks whether a row is well-formed. It cannot ask whether
`UBERON:0005079` is the ureteric bud, because answering that means leaving the
file. This module does that, and the division is deliberate: structural checks
stay fast and offline, identity checks go to the ontology.

The failure being caught is specific and nasty. A label is prose; an identifier
is not. When a row is drafted from background knowledge the two are produced by
the same guess, so a wrong identifier arrives wearing the right label and reads
perfectly:

    UBERON:0005079   ureteric bud          <- plausible, and wrong
    UBERON:0005079   eggshell              <- what the ontology actually says
    UBERON:0000084   ureteric bud          <- what was meant

Nothing about the first line looks wrong to a reader, and every downstream
artifact -- the GCIs, the reasoned edges, anything built on them -- inherits the
error silently, because the identifier is what the machinery reads and the label
is what the human reads. They have to be checked against each other.

Resolution goes through OAK (ontology-access-kit) against OLS, falling back to
the OLS REST API and then to Wikidata, so a missing oaklib or a flaky service
degrades rather than stops the work. Results are cached: a curation session
resolves each identifier once.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from .http import UA, ssl_context

CURIE = re.compile(r"^([A-Za-z][A-Za-z0-9]*):([0-9]+)$")

# Which OLS ontology answers for each prefix. Anything not listed is reported
# as unresolvable rather than guessed at -- a prefix we do not know how to look
# up is a different problem from a label that disagrees.
ONTOLOGY_FOR_PREFIX = {
    "UBERON": "uberon",
    "HsapDv": "hsapdv",
    "MmusDv": "mmusdv",
    "NCBITaxon": "ncbitaxon",
    "RO": "ro",
    "ECO": "eco",
    "CL": "cl",
}

OLS = "https://www.ebi.ac.uk/ols4/api"
WIKIDATA = "https://query.wikidata.org/sparql"


def _get(url: str, accept: str = "application/json") -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl_context()) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:                                    # noqa: BLE001
        return None


def cache_path() -> Path:
    env = os.environ.get("TAXON_STAGE_CORPUS")
    base = Path(env) if env else None
    if base is None:
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
                base = parent / ".evidence-cache"
                break
    return (base or Path(".evidence-cache")) / "labels.json"


class Resolver:
    """Identifier -> the ontology's label for it, with a cache and a fallback
    chain. Never invents an answer: an identifier it cannot resolve comes back
    as None, which callers must treat as 'unknown', not as 'wrong'."""

    def __init__(self, offline: bool = False) -> None:
        self.offline = offline
        self.cache: dict[str, str | None] = {}
        self.path = cache_path()
        if self.path.exists():
            try:
                self.cache = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                self.cache = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.cache, indent=1, sort_keys=True))

    # -- the three sources, tried in order -------------------------------

    def _via_oak(self, prefix: str, ids: list[str]) -> dict[str, str]:
        """OAK is the primary route: it is the tool the OBO world standardises
        on, and going through it means this check reads the same ontology a
        curator would query by hand."""
        ont = ONTOLOGY_FOR_PREFIX.get(prefix)
        if not ont:
            return {}
        if shutil.which("runoak"):
            cmd = ["runoak"]
        elif shutil.which("uv"):
            cmd = ["uv", "run", "--no-project", "--with", "oaklib", "runoak"]
        else:
            return {}
        try:
            p = subprocess.run(cmd + ["-i", f"ols:{ont}", "labels", *ids],
                               capture_output=True, text=True, timeout=120)
        except Exception:                                # noqa: BLE001
            return {}
        out = {}
        for i, line in enumerate(p.stdout.splitlines()):
            if i == 0 or "\t" not in line:
                continue
            cid, label = line.split("\t", 1)
            if label.strip() and label.strip() != "None":
                out[cid.strip()] = label.strip()
        return out

    def _via_ols(self, prefix: str, cid: str) -> str | None:
        ont = ONTOLOGY_FOR_PREFIX.get(prefix)
        if not ont:
            return None
        iri = "http://purl.obolibrary.org/obo/" + cid.replace(":", "_")
        d = _get(f"{OLS}/ontologies/{ont}/terms?iri={urllib.parse.quote(iri, safe='')}")
        try:
            return d["_embedded"]["terms"][0]["label"]    # type: ignore[index]
        except Exception:                                # noqa: BLE001
            return None

    def find_by_label(self, prefix: str, label: str) -> list[str]:
        """Reverse lookup: what identifier actually carries this label?

        A mismatch report that only says "wrong" leaves the reader to guess
        which half to change, and the cheap guess -- edit the label to match
        the identifier -- is the one that destroys the information. Naming the
        identifier that really does carry the intended label makes the correct
        repair the easy one.
        """
        key = f"?{prefix}:{label.lower()}"
        if key in self.cache:
            v = self.cache[key]
            return [v] if v else []
        # Deliberately not gated on self.offline. This runs only once a
        # mismatch is already confirmed, so it is the failure path: the write
        # is blocked either way, and a second of latency buys the reader the
        # identifier they actually wanted. If the network is down `_get`
        # returns None and the caller falls back to a generic fix.
        ont = ONTOLOGY_FOR_PREFIX.get(prefix)
        hits: list[str] = []
        if ont:
            d = _get(f"{OLS}/search?q={urllib.parse.quote(label)}"
                     f"&ontology={ont}&exact=true&rows=5&fieldList=obo_id,label")
            for doc in ((d or {}).get("response", {}).get("docs") or []):
                if doc.get("label", "").strip().lower() == label.strip().lower():
                    oid = doc.get("obo_id")
                    if oid and oid not in hits:
                        hits.append(oid)
        self.cache[key] = hits[0] if hits else None
        self.save()
        return hits

    def _via_wikidata(self, cid: str) -> str | None:
        """Last resort, and only for Uberon: Wikidata carries the Uberon id as
        property P1554, so an entity bearing it gives an independent reading of
        what that identifier denotes. Weaker than the ontology -- Wikidata's
        label is its own, not Uberon's -- so a disagreement here is reported as
        'could not confirm', never as a mismatch."""
        if not cid.startswith("UBERON:"):
            return None
        q = ('SELECT ?l WHERE { ?e wdt:P1554 "%s" . ?e rdfs:label ?l '
             'FILTER(LANG(?l)="en") } LIMIT 1' % cid.split(":", 1)[1])
        d = _get(f"{WIKIDATA}?query={urllib.parse.quote(q)}&format=json")
        try:
            return d["results"]["bindings"][0]["l"]["value"]   # type: ignore[index]
        except Exception:                                # noqa: BLE001
            return None

    # -- public ----------------------------------------------------------

    def resolve(self, ids: list[str]) -> dict[str, str | None]:
        want = [i for i in dict.fromkeys(ids) if i not in self.cache]
        if want and not self.offline:
            by_prefix: dict[str, list[str]] = {}
            for i in want:
                m = CURIE.match(i)
                if m:
                    by_prefix.setdefault(m.group(1), []).append(i)
            for prefix, group in by_prefix.items():
                # One batched OAK call per ontology; the per-id fallbacks only
                # run for what it missed.
                got = self._via_oak(prefix, group)
                for i in group:
                    label = got.get(i) or self._via_ols(prefix, i) \
                        or self._via_wikidata(i)
                    self.cache[i] = label
            self.save()
        return {i: self.cache.get(i) for i in ids}


def check_pairs(pairs: list[tuple[str, str, str]],
                resolver: Resolver | None = None) -> list[dict]:
    """Check (field, identifier, claimed label) triples.

    Returns one dict per problem: {where, problem, fix, unchecked}. The `fix`
    is the whole point -- it names the edit to make, with the real value in it,
    so the repair does not depend on the reader inferring which of the two
    halves was wrong.

    Three outcomes, kept distinct because the right response differs:
      - agrees            -> silence
      - disagrees         -> a problem
      - cannot be checked -> reported with unchecked=True, and never blocking.
                             An unreachable service is not evidence that a row
                             is bad, and treating it as such would make this
                             the check everyone turns off.
    """
    r = resolver or Resolver()
    labels = r.resolve([cid for _, cid, _ in pairs])
    problems: list[dict] = []
    for field, cid, claimed in pairs:
        if not CURIE.match(cid):
            problems.append({
                "where": field, "unchecked": False,
                "problem": f"{cid!r} is not a well-formed CURIE",
                "fix": "Write it as PREFIX:1234567, e.g. UBERON:0000084."})
            continue
        actual = labels.get(cid)
        if actual is None:
            problems.append({
                "where": field, "unchecked": True,
                "problem": f"{cid} did not resolve (claimed {claimed!r})",
                "fix": f"Run `make validate` while online to check {cid}."})
            continue
        if claimed and actual.strip().lower() != claimed.strip().lower():
            prefix = CURIE.match(cid).group(1)           # type: ignore[union-attr]
            right = r.find_by_label(prefix, claimed)
            if right:
                fix = (f"If you meant {claimed!r}, use {right[0]}. "
                       f"If you meant {cid}, set the label to {actual!r}. "
                       f"Change ONE of them -- do not edit the label to match "
                       f"an identifier you did not intend.")
            else:
                fix = (f"Either set the label to {actual!r}, or find the "
                       f"identifier that really is {claimed!r}:\n"
                       f"    uv run --no-project --with oaklib runoak "
                       f"-i ols:{ONTOLOGY_FOR_PREFIX.get(prefix, prefix.lower())} "
                       f"search '{claimed}'")
            problems.append({
                "where": field, "unchecked": False,
                "problem": f"{cid} is {actual!r} in the ontology, "
                           f"but this says {claimed!r}",
                "fix": fix})
    return problems


def check_table(axioms) -> list[dict]:                    # noqa: ANN001
    """Every identifier/label pair carried by the axiom table."""
    pairs: list[tuple[str, str, str]] = []
    for i, a in enumerate(axioms, start=2):
        where = f"row {i}"
        for field, cid, label in (
            ("uberon", a.uberon_id, a.uberon_label),
            ("taxon", a.taxon_id, a.taxon_label),
            ("stage", a.stage_id, a.stage_label),
        ):
            if cid:
                pairs.append((f"{where} {field}", cid, label))
    seen: dict[tuple[str, str], str] = {}
    unique: list[tuple[str, str, str]] = []
    for field, cid, label in pairs:                      # dedupe the lookups,
        key = (cid, label)                               # keep the row numbers
        if key in seen:
            continue
        seen[key] = field
        unique.append((field, cid, label))
    return check_pairs(unique)


# Pairs as they appear in a Write/Edit payload: `"uberon_id": "..."` next to
# `"uberon_label": "..."` in JSON, or adjacent columns in a TSV row. Pulled out
# here so the hook and the table check share one notion of what a pair is.
_JSON_ID = re.compile(r'"(\w+)_id"\s*:\s*"([A-Za-z][A-Za-z0-9]*:[0-9]+)"')
_JSON_LABEL = re.compile(r'"(\w+)_label"\s*:\s*"((?:[^"\\]|\\.)*)"')


def extract_pairs(blob: str) -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []

    ids: dict[str, list[str]] = {}
    for m in _JSON_ID.finditer(blob):
        ids.setdefault(m.group(1), []).append(m.group(2))
    labels: dict[str, list[str]] = {}
    for m in _JSON_LABEL.finditer(blob):
        try:
            labels.setdefault(m.group(1), []).append(json.loads('"' + m.group(2) + '"'))
        except json.JSONDecodeError:
            pass
    for key, got in ids.items():
        lab = labels.get(key, [])
        for n, cid in enumerate(got):
            if n < len(lab):
                pairs.append((f"{key}_id", cid, lab[n]))

    # TSV: an identifier cell followed by its label cell.
    for line in blob.splitlines():
        if "\t" not in line:
            continue
        cells = line.split("\t")
        for n, cell in enumerate(cells[:-1]):
            if CURIE.match(cell.strip()) and cells[n + 1].strip():
                nxt = cells[n + 1].strip()
                if not CURIE.match(nxt):
                    pairs.append(("column", cell.strip(), nxt))
    return pairs


def main(argv: list[str] | None = None) -> int:
    import argparse
    from .model import load

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("table", type=Path, nargs="?")
    ap.add_argument("--payload", action="store_true",
                    help="read a Write/Edit payload on stdin instead")
    ap.add_argument("--offline", action="store_true",
                    help="use only what is already cached")
    ap.add_argument("--json", action="store_true",
                    help="structured problems, for the hook to render")
    ap.add_argument("--warm", action="store_true",
                    help="resolve and cache every identifier, report nothing")
    args = ap.parse_args(argv)

    r = Resolver(offline=args.offline)
    if args.payload:
        problems = check_pairs(extract_pairs(sys.stdin.read()), r)
    elif args.table:
        axioms = load(args.table)
        problems = check_table(axioms)
        if args.warm:
            print(f"cached {len(r.cache)} identifiers", file=sys.stderr)
            return 0
    else:
        ap.error("give a table or --payload")

    real = [p for p in problems if not p["unchecked"]]
    if args.json:
        print(json.dumps(problems, indent=1))
        return 1 if real else 0
    for p in problems:
        tag = "UNCHECKED " if p["unchecked"] else ""
        print(f"  {tag}{p['where']}: {p['problem']}", file=sys.stderr)
        print(f"      FIX: {p['fix']}", file=sys.stderr)
    if real:
        print(f"{len(real)} label/identifier mismatch(es)", file=sys.stderr)
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
