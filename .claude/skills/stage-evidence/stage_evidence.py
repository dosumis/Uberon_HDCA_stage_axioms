#!/usr/bin/env python3
"""Stage evidence: local corpora of what published sources actually say about
when human structures exist, and the checks that keep quotes from them honest.

The axiom table's job is to say when a structure exists in a named taxon. That
claim is only worth as much as the passage behind it, so this tool does two
things and keeps them apart:

  - it finds candidate passages (`build`, `search`, `stages`), and
  - it refuses to believe a quote it cannot find again (`verify`).

The second part is the point. A language model asked for a supporting quote
will produce one whether or not the source contains it, and a plausible
fabricated quote is indistinguishable from a real one by reading. It is
entirely distinguishable by string match, which is what `verify` does -- and
what the Write/Edit hooks run on every edit so the check cannot be skipped.

Two corpora, deliberately unequal, and the inequality is recorded rather than
remembered:

  ORahilly1987  Carnegie stages 1-23, human by construction, descriptive
                morphology by the people who defined the staging system.
                Primary. Every passage carries a stage, so a quote can be
                checked against the stage it is filed under.

  Wikipedia     Everything else, including the fetal period the 1987 book does
                not reach. Tertiary, and -- the part that matters -- of NO
                declared species. Its articles on human structures carry chick
                and mouse timings in the same voice as human ones, so a quote
                from this corpus is accepted only if it names a human frame of
                reference itself and names no other animal's. That gate is
                enforced in `verify`, not left to a curator's care.

A record citing either corpus goes through the same schema and the same
verifier. What differs is what it must survive.

Primary source: O'Rahilly R, Muller F (1987) *Developmental Stages in Human Embryos*,
Carnegie Institution of Washington Publication 637. The text is transcribed
stage by stage on the UNSW Embryology wiki, which is what we mirror: it is
clean (the Carnegie PDF is OCR, and renders e.g. "Shikinami" as "Shikinarni"),
it is already segmented by stage and organ system, and every passage has a
stable URL to cite. Copyright (c) 1987 Carnegie Institution of Washington --
free to read and cite, not ours to redistribute, so the mirror is a build
artifact and stays out of git.

Everything here is stdlib. No pip install, no network except `build`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import difflib
import ssl
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict, field
from pathlib import Path

WIKI = "https://embryology.med.unsw.edu.au/embryology/index.php"
PAGE = "1987_Developmental_Stages_In_Human_Embryos_-_Stage_{n}"
UA = "taxon-stage-axioms/0.1 (https://github.com/dosumis/taxon-stage-axioms)"

# The corpus describes exactly one species. Recording that on every document --
# rather than assuming it -- is what lets `verify` reject a human claim backed
# by a quote from some other source we might add later. The failure this guards
# against is real: Wikipedia's apical-ectodermal-ridge article times the AER in
# chick ("stage 20HH") and its rhombic-lip article in mouse ("E15"), and both
# read as human timings to anything matching on numbers alone.
CORPUS_TAXON = "NCBITaxon:9606"
CORPUS_TAXON_LABEL = "Homo sapiens"

# What each corpus is, and what a quote from it has to survive. `taxon: None`
# means the corpus does not declare a species -- not that it is species-neutral,
# but that any given passage could be about anything. That is strictly worse
# than a known-wrong species, because it cannot be filtered by provenance and
# has to be filtered sentence by sentence.
CORPORA = {
    "ORahilly1987": {
        "taxon": CORPUS_TAXON,
        "tier": "primary",
        "scope": "Carnegie stages 1-23 (human embryonic period, to ~day 60)",
        "stage_attributed": True,
        "citation": ("O'Rahilly R, Muller F (1987) Developmental Stages in "
                     "Human Embryos. Carnegie Institution of Washington "
                     "Publication 637."),
    },
    "Wikipedia": {
        "taxon": None,
        "tier": "tertiary",
        "scope": "whatever the article covers; species not declared",
        "stage_attributed": False,
        "citation": "English Wikipedia (see each passage's source_url)",
    },
}

# An explicitly human frame of reference. A Wikipedia quote must contain one of
# these to be usable as human evidence.
HUMAN_MARKERS = [
    "human", "carnegie stage", "carnegie", "postovulatory", "post-ovulatory",
    "post-fertilization", "post-fertilisation", "postfertilization",
    "week of gestation", "weeks of gestation", "gestational age", "dpo",
]

# Another animal's staging system. Any of these in a quote disqualifies it as
# human evidence outright, whatever else the sentence says. Measured, not
# imagined: Wikipedia's apical-ectodermal-ridge article gives "stage 20HH"
# (chick) and its rhombic-lip article "embryonic day 9.5" and "E15-P15"
# (mouse), both in articles about structures we curate for human.
FOREIGN_MARKERS = [
    (r"\bstage\s*\d+\s*HH\b", "Hamburger-Hamilton staging (chick)"),
    (r"\bHH\s*\d+\b", "Hamburger-Hamilton staging (chick)"),
    (r"\bE\d+(?:\.\d+)?\b", "embryonic day E-number (mouse)"),
    (r"\bP\d+\b", "postnatal day P-number (mouse)"),
    (r"\bNF\s*stage\b", "Nieuwkoop-Faber staging (Xenopus)"),
    (r"\bhpf\b", "hours post-fertilization (zebrafish)"),
    (r"\b(?:chick|chicken|mouse|murine|rat|zebrafish|xenopus|avian)\b",
     "names a non-human animal"),
]

# Carnegie stage -> HsapDv class, from OLS (ontology=hsapdv, all 23 present and
# agreeing with the pairs already used in src/axioms.tsv). Hardcoded because it
# is a closed, stable list and a curation run should not depend on OLS being up.
STAGE_IDS = {
    1: "HsapDv:0000003", 2: "HsapDv:0000005", 3: "HsapDv:0000007",
    4: "HsapDv:0000008", 5: "HsapDv:0000009", 6: "HsapDv:0000011",
    7: "HsapDv:0000013", 8: "HsapDv:0000014", 9: "HsapDv:0000016",
    10: "HsapDv:0000017", 11: "HsapDv:0000018", 12: "HsapDv:0000019",
    13: "HsapDv:0000020", 14: "HsapDv:0000021", 15: "HsapDv:0000022",
    16: "HsapDv:0000023", 17: "HsapDv:0000024", 18: "HsapDv:0000025",
    19: "HsapDv:0000026", 20: "HsapDv:0000027", 21: "HsapDv:0000028",
    22: "HsapDv:0000029", 23: "HsapDv:0000030",
}

# Phrases with which O'Rahilly marks a claim he is not willing to stand behind.
# These matter more than they look: the book says a ureteric bud "may possibly
# be present" at stage 13 and "further confirmation is needed", while stage 14
# states flatly that it "acquires a metanephrogenic cap". Quote the first
# without its hedge and you have converted the source's uncertainty into our
# certainty -- so `verify` makes dropping the hedge an error, not a style note.
HEDGES = [
    "may possibly", "may perhaps", "possibly", "perhaps", "probably",
    "presumably", "apparently", "appears to be", "seems to be",
    "further confirmation is needed", "needs confirmation", "not certain",
    "uncertain", "doubtful", "has been claimed", "it is claimed",
    "if present", "may be present", "may already", "is said to",
    "difficult to determine", "not been confirmed", "remains to be",
]


# --------------------------------------------------------------------------
# text normalisation
# --------------------------------------------------------------------------

def norm(s: str) -> str:
    """Fold away the differences a quote may legitimately pick up in transit --
    unicode dashes, curly quotes, line wrapping -- and nothing else.

    Deliberately NOT case-folding or stripping punctuation. A quote that
    differs from the source in wording is a different quote, and the whole
    value of the check is that it is strict enough to catch paraphrase that a
    reader would wave through.
    """
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"[‐-―−]", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _drop_balanced(text: str, open_tok: str, close_tok: str) -> str:
    """Remove balanced {{...}} / [[...]] spans, innermost first, so nested
    markup (a File: link whose caption contains a wiki link) comes out whole
    rather than leaving a dangling bracket in the middle of a quotable line."""
    pattern = re.compile(
        re.escape(open_tok) + r"((?:(?!" + re.escape(open_tok) + r"|"
        + re.escape(close_tok) + r").)*)" + re.escape(close_tok), re.S)
    prev = None
    while prev != text:
        prev = text
        text = pattern.sub("", text)
    return text


def strip_wikitext(raw: str) -> str:
    """Wikitext -> the plain prose a curator would quote.

    This has to be deterministic: the stripped string is what quotes are
    matched against, so any wobble here turns a true quote into a failing one.
    """
    t = raw
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"<gallery.*?</gallery>", "", t, flags=re.S | re.I)
    t = re.sub(r"<ref[^>]*?/>", "", t, flags=re.I)
    t = re.sub(r"<ref.*?</ref>", "", t, flags=re.S | re.I)
    t = re.sub(r"\{\|.*?\|\}", "", t, flags=re.S)          # tables
    t = _drop_balanced(t, "{{", "}}")                      # templates, {{#pmid:..}}
    # File/Image links first (their captions may contain further links), then
    # ordinary links collapse to the text a reader sees.
    t = re.sub(r"\[\[(?:File|Image):[^\[\]]*(?:\[\[[^\]]*\]\][^\[\]]*)*\]\]",
               "", t, flags=re.I)
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\[(?:https?:)?//\S+\s+([^\]]*)\]", r"\1", t)
    t = re.sub(r"\[(?:https?:)?//\S+\]", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("'''", "").replace("''", "")
    t = re.sub(r"^[*#:;]+\s*", "", t, flags=re.M)
    t = re.sub(r"&nbsp;", " ", t)
    return t


def hedges_in(text: str) -> list[str]:
    low = norm(text).lower()
    return [h for h in HEDGES if h in low]


# --------------------------------------------------------------------------
# corpus
# --------------------------------------------------------------------------

@dataclass
class Passage:
    """One quotable paragraph, with everything needed to cite it and to check
    that a later quote really came from here."""
    source_id: str          # ORahilly1987:stage13 | Wikipedia:Otic_placode
    corpus: str             # ORahilly1987 | Wikipedia
    section: str            # Urinary System | the article section
    text: str
    source_url: str
    tier: str = "primary"
    # Stage attribution exists only for a corpus organised by stage. A
    # Wikipedia passage has none, which is itself the reason a claim resting on
    # one is weaker: there is no structural fact to check the attribution
    # against, only the sentence.
    carnegie_stage: int | None = None
    stage_id: str | None = None
    stage_label: str | None = None
    taxon_id: str | None = CORPUS_TAXON
    hedges: list[str] = field(default_factory=list)


def cache_dir() -> Path:
    env = os.environ.get("TAXON_STAGE_CORPUS")
    if env:
        return Path(env)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent / ".evidence-cache"
    return here.parent / ".evidence-cache"


def corpus_path() -> Path:
    return cache_dir() / "corpus.json"


def _ssl_context() -> ssl.SSLContext:
    """Same dance as fetch-wiki-info-api: Homebrew Python on macOS does not
    always trust the system roots, so find a CA bundle rather than fail."""
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    for path in (
        os.environ.get("SSL_CERT_FILE"),
        "/etc/ssl/cert.pem",
        "/opt/homebrew/etc/ca-certificates/cert.pem",
        os.path.expanduser("~/.homebrew/etc/ca-certificates/cert.pem"),
        "/usr/local/etc/ca-certificates/cert.pem",
    ):
        if path and os.path.exists(path):
            return ssl.create_default_context(cafile=path)
    return ssl.create_default_context()


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60, context=_ssl_context()) as r:
        return r.read().decode("utf-8", "replace")


def page_url(n: int) -> str:
    return f"{WIKI}?title={PAGE.format(n=n)}"


def build_corpus(stages: list[int]) -> list[Passage]:
    out: list[Passage] = []
    for n in stages:
        raw = fetch(page_url(n) + "&action=raw")
        if len(raw) < 500:
            print(f"  stage {n}: short page ({len(raw)} bytes), skipped",
                  file=sys.stderr)
            continue
        section = "(top)"
        buf: list[str] = []

        def flush() -> None:
            body = strip_wikitext("\n".join(buf))
            for para in body.split("\n"):
                para = norm(para)
                # Short lines are headings, figure leftovers and stray markup,
                # not claims anyone would cite.
                if len(para) < 40:
                    continue
                out.append(Passage(
                    source_id=f"ORahilly1987:stage{n}",
                    corpus="ORahilly1987",
                    tier="primary",
                    carnegie_stage=n,
                    stage_id=STAGE_IDS[n],
                    stage_label=f"Carnegie stage {n:02d}",
                    section=section,
                    text=para,
                    source_url=page_url(n),
                    hedges=hedges_in(para),
                ))
            buf.clear()

        for line in raw.splitlines():
            head = re.fullmatch(r"\s*(={2,4})\s*(.+?)\s*\1\s*", line)
            if head:
                flush()
                section = head.group(2).strip()
                continue
            buf.append(line)
        flush()
        print(f"  stage {n:>2}: {sum(1 for p in out if p.carnegie_stage == n)}"
              f" passages", file=sys.stderr)
    return out


WIKI_SKILL = (Path(__file__).resolve().parent.parent
              / "fetch-wiki-info-api" / "fetch_wiki_info.py")


def build_wikipedia(terms: list[str]) -> list[Passage]:
    """Add Wikipedia articles as a second, lesser corpus.

    Fetching is delegated to the fetch-wiki-info-api skill rather than
    reimplemented here: it already handles Wikidata disambiguation, redirect
    resolution and the relevance gate, and one copy of that logic is enough.
    This function's own job is only to cut the article into quotable passages
    and label them with what they are -- tertiary, species undeclared.
    """
    if not WIKI_SKILL.exists():
        raise SystemExit(f"fetch-wiki-info-api skill not found at {WIKI_SKILL}")
    out: list[Passage] = []
    for term in terms:
        try:
            p = subprocess.run([sys.executable, str(WIKI_SKILL), term, "--json"],
                               capture_output=True, text=True, timeout=90)
            data = json.loads(p.stdout)
        except Exception as e:                           # noqa: BLE001
            print(f"  {term}: fetch failed ({e})", file=sys.stderr)
            continue
        page = data.get("wikipedia") or {}
        title = page.get("title")
        body = page.get("full_text") or page.get("summary") or ""
        if not title or not body:
            print(f"  {term}: no article text", file=sys.stderr)
            continue
        section = "(lead)"
        n = 0
        for para in body.split("\n"):
            para = norm(para)
            if not para:
                continue
            # Wikipedia's plain-text extract marks sections as short bare lines.
            if len(para) < 60 and not para.endswith("."):
                section = para
                continue
            if len(para) < 40:
                continue
            out.append(Passage(
                source_id=f"Wikipedia:{title}",
                corpus="Wikipedia",
                tier="tertiary",
                section=section,
                text=para,
                source_url=page.get("url") or "",
                taxon_id=None,
                hedges=hedges_in(para),
            ))
            n += 1
        print(f"  {term}: {n} passages from {title}", file=sys.stderr)
    return out


def species_problems(quote: str) -> tuple[list[str], list[str]]:
    """(foreign markers found, human markers found) in a quote.

    Used only for corpora that declare no species. The asymmetry is the point:
    a foreign marker disqualifies, and the absence of a human marker also
    disqualifies. "Probably human" is not a category -- an unmarked timing in a
    mixed-species source is unusable, and most of them are unmarked.
    """
    low = norm(quote).lower()
    foreign = [why for rx, why in FOREIGN_MARKERS
               if re.search(rx, quote, re.I)]
    human = [m for m in HUMAN_MARKERS if m in low]
    return foreign, human


def load_corpus() -> list[Passage]:
    p = corpus_path()
    if not p.exists():
        raise SystemExit(
            f"No corpus at {p}.\n"
            f"Build it first:  python3 {Path(__file__).name} build")
    data = json.loads(p.read_text())
    return [Passage(**d) for d in data["passages"]]


def load_synonyms() -> dict[str, list[str]]:
    """Uberon's label for a structure is often not the book's name for it.

    O'Rahilly writes 'lens disc' and 'otic disc' where Uberon says 'lens
    placode' and 'otic placode'. Searching the book for the Uberon label alone
    returns nothing and looks exactly like the book being silent on the
    subject, which is the most dangerous possible failure mode for a tool whose
    output is read as evidence of absence.
    """
    f = Path(__file__).parent / "SYNONYMS.tsv"
    syn: dict[str, list[str]] = {}
    if not f.exists():
        return syn
    for line in f.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            syn[parts[0].strip().lower()] = [
                s.strip() for s in parts[1].split("|") if s.strip()]
    return syn


# --------------------------------------------------------------------------
# search
# --------------------------------------------------------------------------

def search(passages: list[Passage], terms: list[str],
           stage: int | None = None) -> list[tuple[Passage, list[str]]]:
    pats = [(t, re.compile(r"\b" + re.escape(t).replace(r"\ ", r"\s+") + r"\w{0,3}\b",
                           re.I)) for t in terms]
    hits = []
    for p in passages:
        if stage is not None and p.carnegie_stage != stage:
            continue
        matched = [t for t, pat in pats if pat.search(p.text)]
        if matched:
            hits.append((p, matched))
    return hits


def cmd_search(args: argparse.Namespace) -> int:
    passages = load_corpus()
    syn = load_synonyms()
    term = args.term
    terms = [term] + [s for s in syn.get(term.lower(), []) if s.lower() != term.lower()]
    if getattr(args, "corpus", None):
        passages = [p for p in passages if p.corpus == args.corpus]
    hits = search(passages, terms, args.stage)

    if args.json:
        print(json.dumps({
            "query": term, "searched_terms": terms,
            "synonyms_known": term.lower() in syn,
            "hits": [{**asdict(p), "matched_terms": m} for p, m in hits],
        }, indent=2))
        return 0

    print(f"# {term}")
    print(f"\nSearched: {', '.join(terms)}")
    if term.lower() not in syn:
        print("\n**No synonym entry for this term.** O'Rahilly's name for a "
              "structure often differs from Uberon's (lens placode -> 'lens "
              "disc'). A zero-hit result here is NOT evidence the book is "
              "silent -- check SYNONYMS.tsv and the book's index before "
              "concluding anything.")
    if not hits:
        print(f"\nNo passages matched in {len(passages)} passages.")
        return 0

    print(f"\n{len(hits)} passage(s):\n")
    for p, matched in hits:
        head = (f"{p.stage_label} ({p.stage_id})" if p.stage_id
                else f"{p.corpus} -- no stage attribution")
        print(f"## {head} -- {p.section}")
        print(f"source_id: {p.source_id}   [{p.tier}]")
        if p.taxon_id is None:
            foreign, human = species_problems(p.text)
            if foreign:
                print(f"NOT HUMAN: {'; '.join(foreign)}  <- unusable as human "
                      f"evidence; verify will reject a record quoting this")
            elif not human:
                print(f"NO HUMAN MARKER: this source declares no species and "
                      f"this passage names no human frame of reference; "
                      f"verify will reject a human record quoting it")
            else:
                print(f"human marker: {', '.join(human)}")
        if p.hedges:
            print(f"HEDGED: {', '.join(p.hedges)}  <- the source is not "
                  f"committing; any record quoting this must set hedged: true")
        print(f"matched: {', '.join(matched)}")
        print(f"\n> {p.text}\n")
        print(f"{p.source_url}\n")
    return 0


def cmd_stages(args: argparse.Namespace) -> int:
    passages = load_corpus()
    by_stage: dict[int, list[Passage]] = {}
    for p in passages:
        by_stage.setdefault(p.carnegie_stage, []).append(p)
    print("stage\thsapdv\tpassages\tsize_and_age_as_stated_by_the_source")
    for n in sorted(by_stage):
        age = ""
        for p in by_stage[n]:
            m = re.search(r"Approximately[^.]*?postovulatory days?", p.text)
            if m:
                age = m.group(0)
                break
        print(f"CS{n:02d}\t{STAGE_IDS[n]}\t{len(by_stage[n])}\t{age}")
    print("\nBlank age = the wiki transcription of that stage does not carry "
          "the 'Size and Age' bullet. Do not fill it in from memory.",
          file=sys.stderr)
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    # Corpora accumulate. Building Wikipedia for a handful of terms must not
    # silently discard the O'Rahilly mirror, so existing passages from other
    # corpora are carried through.
    existing: list[Passage] = []
    if corpus_path().exists():
        try:
            existing = [p for p in load_corpus() if p.corpus != args.corpus]
        except SystemExit:
            pass

    if args.corpus == "Wikipedia":
        if not args.terms:
            raise SystemExit(
                "Wikipedia has no fixed extent -- name the structures to "
                "fetch:\n  build --corpus Wikipedia 'otic placode' 'vernix "
                "caseosa'")
        print(f"Fetching {len(args.terms)} Wikipedia articles "
              f"(tertiary, species undeclared)...", file=sys.stderr)
        passages = existing + build_wikipedia(args.terms)
    else:
        stages = args.stages or list(range(1, 24))
        print(f"Fetching {len(stages)} stage pages from UNSW Embryology...",
              file=sys.stderr)
        passages = existing + build_corpus(stages)
    d = cache_dir()
    d.mkdir(parents=True, exist_ok=True)
    corpus_path().write_text(json.dumps({
        "corpora": CORPORA,
        "mirror": "UNSW Embryology wiki transcription (ORahilly1987)",
        "copyright": "O'Rahilly & Muller 1987 (c) Carnegie Institution of "
                     "Washington; Wikipedia CC BY-SA. Cached locally for "
                     "curation; not redistributed.",
        "stage_ids": {str(k): v for k, v in STAGE_IDS.items()},
        "passages": [asdict(p) for p in passages],
    }, indent=1))
    counts: dict[str, int] = {}
    for p in passages:
        counts[p.corpus] = counts.get(p.corpus, 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    print(f"\n{len(passages)} passages ({summary}) -> {corpus_path()}",
          file=sys.stderr)
    return 0


# --------------------------------------------------------------------------
# verify -- the part the hooks call
# --------------------------------------------------------------------------

REQUIRED = ["uberon_id", "taxon_id", "stage_id", "claim", "quote",
            "source_id", "section", "hedged"]


def _index(passages: list[Passage]) -> dict[str, list[Passage]]:
    idx: dict[str, list[Passage]] = {}
    for p in passages:
        idx.setdefault(p.source_id, []).append(p)
    return idx


def _nearest(q: str, passages: list[Passage]) -> tuple[Passage, str] | None:
    """The real sentence most like the one that failed.

    When a quote is a near miss -- a word dropped, a clause tidied, two
    sentences welded together -- the useful response is not "wrong" but "here
    is what the source actually says". Offering the real text is also the only
    form of help that cannot be gamed: it moves the record toward the source
    rather than away from it.
    """
    best, score = None, 0.0
    for p in passages:
        # Split before a capital only: the text is full of "(fig. 15-10)" and
        # "(Wells, 1954, fig. 4)", and cutting inside those hands back a
        # truncated sentence that would fail the verbatim check in turn.
        for sent in re.split(r"(?<=[.;])\s+(?=[A-Z])", p.text):
            if len(sent) < 25:
                continue
            r = difflib.SequenceMatcher(None, q.lower(), sent.lower()).ratio()
            if r > score:
                best, score = (p, sent), r
    return best if score >= 0.6 else None


def check_quote(quote: str, passages: list[Passage],
                source_id: str | None) -> tuple[Passage | None, dict | None]:
    """Find the passage a quote came from, or say exactly how to fix it.

    Returns (passage, problem). Scoped to source_id when given, so a quote that
    exists somewhere in the corpus but not in the cited document is an error
    rather than a pass -- misattributing a real sentence is the likeliest way a
    true-looking record goes wrong.
    """
    q = norm(quote)
    if len(q) < 25:
        return None, {
            "problem": f"quote is {len(q)} chars; too short to be checkable",
            "fix": "Quote a complete clause -- at least 25 characters of the "
                   "source's own words."}
    pool = [p for p in passages if p.source_id == source_id] if source_id else passages
    if source_id and not pool:
        known = sorted({p.source_id for p in passages})[:4]
        return None, {
            "problem": f"source_id {source_id!r} is not in the corpus",
            "fix": f"Use a source_id the corpus has, e.g. "
                   f"{', '.join(known)}. Run `search` to see which document a "
                   f"passage belongs to, or `build` the corpus it needs."}
    for p in pool:
        if q in p.text:
            return p, None

    low = q.lower()
    for p in pool:
        if low in p.text.lower():
            i = p.text.lower().index(low)
            return None, {
                "problem": "quote matches only case-insensitively",
                "fix": f"Replace the quote with the source's exact "
                       f"capitalisation:\n    {p.text[i:i + len(q)]}"}

    elsewhere = [p for p in passages if q in p.text]
    if elsewhere:
        got = elsewhere[0]
        where = (f"{got.stage_label}, {got.section}" if got.stage_label
                 else f"{got.corpus}, {got.section}")
        fix = (f'Set "source_id": "{got.source_id}" and "section": '
               f'"{got.section}"')
        if got.stage_id:
            fix += f' and "stage_id": "{got.stage_id}"'
        fix += (". The sentence is real; only the attribution is wrong. Do "
                "NOT edit the quote to fit the document you first named.")
        return None, {
            "problem": f"quote is real but belongs to {got.source_id} "
                       f"({where}), not {source_id}",
            "fix": fix}

    near = _nearest(q, pool or passages)
    if near:
        p, sent = near
        return None, {
            "problem": "quote is close to the source but not identical -- it "
                       "has been paraphrased, trimmed or stitched together",
            "fix": f"Replace it with the source's exact words:\n    {sent}\n"
                   f"(from {p.source_id}, {p.section})"}
    return None, {
        "problem": "quote does not appear in the corpus at all; it was not "
                   "copied from the source",
        "fix": "Do not reword it. Run\n"
               "    python3 .claude/skills/stage-evidence/stage_evidence.py "
               "search '<structure>'\n"
               "and paste a passage from the output, or delete the record and "
               "say the source does not cover this structure."}


def verify_record(rec: dict, passages: list[Passage]) -> list[dict]:
    """Every problem with one record, each carrying the edit that repairs it.

    Problems are returned rather than printed so the hook can render them back
    to whoever is writing, with the fix attached. A check that only says "no"
    teaches nothing; the cheapest way to satisfy it is usually to delete the
    field it complained about.
    """
    errs: list[dict] = []
    where = rec.get("uberon_label") or rec.get("uberon_id") or "record"

    def add(problem: str, fix: str) -> None:
        errs.append({"where": where, "problem": problem, "fix": fix})

    missing = [k for k in REQUIRED if k not in rec or rec[k] in ("", None)]
    if missing:
        add(f"missing required field(s): {', '.join(missing)}",
            f"Add {', '.join(missing)}. See schema/evidence.schema.json for "
            f"what each one means.")
        if "quote" in missing or "source_id" in missing:
            return errs

    passage, problem = check_quote(rec["quote"], passages, rec.get("source_id"))
    if problem:
        add(problem["problem"], problem["fix"])
        return errs
    assert passage is not None

    if passage.taxon_id is None:
        foreign, human = species_problems(rec["quote"])
        if foreign:
            add(f"quote comes from {passage.corpus}, which declares no "
                f"species, and the quote itself uses {'; '.join(foreign)}",
                f"This is not human evidence. Delete the record, or replace "
                f"the quote with one that states a human frame of reference. "
                f"Trimming the animal's name out of the sentence does not "
                f"make the timing human.")
        elif not human and rec.get("taxon_id") == CORPUS_TAXON:
            add(f"quote comes from {passage.corpus}, which declares no "
                f"species, and names no human frame of reference",
                f"Quote a sentence containing one of: human, Carnegie stage, "
                f"postovulatory, post-fertilization, week of gestation. If "
                f"the article has no such sentence about this structure, the "
                f"timing is unusable -- delete the record.")
    elif rec.get("taxon_id") != passage.taxon_id:
        add(f"record is about {rec.get('taxon_id')} but {passage.source_id} "
            f"is a {passage.taxon_id} source",
            f'Set "taxon_id": "{passage.taxon_id}", or cite a source about '
            f'{rec.get("taxon_id")}. A quote cannot support a claim about a '
            f'different species.')

    if rec.get("source_tier") and rec["source_tier"] != passage.tier:
        add(f"source_tier is {rec['source_tier']!r} but {passage.corpus} is "
            f"{passage.tier!r}",
            f'Set "source_tier": "{passage.tier}".')

    if passage.stage_id is None:
        if rec.get("stage_id") and not rec.get("note"):
            add(f"{passage.corpus} passages carry no stage, so stage_id "
                f"{rec['stage_id']} is your inference, not the source's",
                f'Add a "note" saying how you reached {rec["stage_id"]} from '
                f'this quote, and what would corroborate it. The inference '
                f'may be right; it must not read as the source\'s words.')
    elif rec.get("stage_id") != passage.stage_id:
        add(f"stage_id is {rec.get('stage_id')} but this quote comes from "
            f"{passage.stage_id} ({passage.stage_label})",
            f'Set "stage_id": "{passage.stage_id}" and "stage_label": '
            f'"{passage.stage_label}". If you meant to claim '
            f'{rec.get("stage_id")}, find a quote from that stage instead:\n'
            f'    python3 .claude/skills/stage-evidence/stage_evidence.py '
            f'search \'{rec.get("uberon_label") or "<structure>"}\' --stage '
            f'<n>')

    if rec.get("section") and norm(rec["section"]) != norm(passage.section):
        add(f"section is {rec['section']!r} but the quote sits under "
            f"{passage.section!r}",
            f'Set "section": "{passage.section}".')

    quoted_hedges = hedges_in(rec["quote"])
    if quoted_hedges and not rec.get("hedged"):
        add(f"the source hedges this ({', '.join(quoted_hedges)}) but "
            f"hedged is false",
            f'Set "hedged": true. Then reconsider `claim`: a hedged passage '
            f'rarely supports a hard "start"/"end" bound -- it usually '
            f'supports "present", with the firm bound coming from a later '
            f'stage that states it without hedging. Do not trim the hedge '
            f'out of the quote.')

    return errs


def extract_quotes(blob: str) -> list[str]:
    """Pull quote strings out of a Write/Edit payload.

    The payload may be a whole JSON file, one edited fragment, or a TSV line,
    so this does not try to parse structure -- it looks for the `quote` field
    wherever it appears and checks each value it finds. Over-matching costs
    nothing; under-matching would let a fabricated quote through.
    """
    out = []
    for m in re.finditer(r'"quote"\s*:\s*"((?:[^"\\]|\\.)*)"', blob):
        try:
            out.append(json.loads('"' + m.group(1) + '"'))
        except json.JSONDecodeError:
            pass
    return out


def cmd_verify(args: argparse.Namespace) -> int:
    passages = load_corpus()
    errs: list[dict] = []

    if args.payload:
        blob = sys.stdin.read()
        # Prefer whole records: they can be checked for stage, section,
        # species and hedging, not just for the quote existing. A payload that
        # does not parse is a mid-edit fragment, so fall back to quotes alone
        # rather than refusing to check anything.
        records = None
        try:
            data = json.loads(blob)
            records = data if isinstance(data, list) else data.get("evidence", [data])
        except json.JSONDecodeError:
            pass
        if isinstance(records, list) and records and isinstance(records[0], dict) \
                and "quote" in records[0]:
            for rec in records:
                errs.extend(verify_record(rec, passages))
        else:
            for q in extract_quotes(blob):
                _, problem = check_quote(q, passages, None)
                if problem:
                    errs.append({"where": f"quote {q[:50]!r}...", **problem})
    else:
        text = Path(args.file).read_text() if args.file else sys.stdin.read()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"not valid JSON: {e}", file=sys.stderr)
            return 1
        records = data if isinstance(data, list) else data.get("evidence", [data])
        for rec in records:
            errs.extend(verify_record(rec, passages))

    if not errs:
        return 0
    if args.json:
        print(json.dumps({"problems": errs}, indent=1))
    else:
        print("Evidence check failed:\n", file=sys.stderr)
        for e in errs:
            print(f"  {e['where']}: {e['problem']}", file=sys.stderr)
            print(f"      FIX: {e['fix']}\n", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="mirror a corpus locally")
    b.add_argument("terms", nargs="*",
                   help="Wikipedia: structures to fetch. ORahilly1987: unused.")
    b.add_argument("--corpus", default="ORahilly1987", choices=list(CORPORA))
    b.add_argument("--stages", nargs="*", type=int,
                   help="ORahilly1987 only: restrict to these stages")
    b.set_defaults(func=cmd_build)

    s = sub.add_parser("search", help="find passages about a structure")
    s.add_argument("term")
    s.add_argument("--stage", type=int, help="restrict to one Carnegie stage")
    s.add_argument("--corpus", choices=list(CORPORA),
                   help="restrict to one corpus")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_search)

    t = sub.add_parser("stages", help="stage table as the source states it")
    t.set_defaults(func=cmd_stages)

    v = sub.add_parser("verify", help="check quotes against the corpus")
    v.add_argument("file", nargs="?", help="evidence JSON (default: stdin)")
    v.add_argument("--payload", action="store_true",
                   help="input is a Write/Edit payload on stdin")
    v.add_argument("--json", action="store_true",
                   help="structured problems, for the hook to render")
    v.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
