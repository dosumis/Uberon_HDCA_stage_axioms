#!/usr/bin/env python3
"""Write/Edit gate: nothing unverifiable reaches disk, and every refusal says
exactly which edit repairs it.

Everything is checked BEFORE the write. An earlier design validated whole
records afterwards, on the theory that a complete record only exists once the
file is on disk -- but that let bad content land and relied on it being
corrected later, which is a weaker guarantee than not writing it. So the hook
reconstructs what the file WOULD contain (current contents plus this edit
applied) and validates that. A Write carries its own full content; an Edit is
replayed against the file on disk. Either way the check sees whole records.

What is checked, cheapest first:

  1. Identifier/label agreement, via taxon_stage.validate. `UBERON:0005079`
     beside "ureteric bud" reads perfectly and is wrong -- it is the eggshell.
     The identifier is what the build reads and the label is what the reviewer
     reads, so nothing but a lookup compares them.

  2. Whole evidence records, via the stage-evidence skill: quote verbatim in
     the cited document, stage matching the section it sits in, section,
     the species rule for that corpus, hedges preserved, required fields.

Every refusal carries a FIX naming the edit, with the real value in it -- the
correct identifier, the source's exact sentence, the stage the quote actually
came from. A check that only says "no" teaches nothing, and the cheapest way to
satisfy it is usually to reword the quote or delete the field it complained
about, both of which defeat the point. Naming the right repair is what makes
the honest fix the easy one.

Scope is narrow -- evidence JSON and the axiom table. Everything else in the
repo passes through untouched.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent.parent
TOOL = REPO / ".claude" / "skills" / "stage-evidence" / "stage_evidence.py"
SRC = REPO / "src"

CURIE_IN = re.compile(r"\b[A-Za-z][A-Za-z0-9]*:[0-9]{6,}\b")

GUARDED = [
    re.compile(r"/src/evidence/.*\.json$"),
    re.compile(r"/evidence/.*\.json$"),
    re.compile(r"/src/axioms\.tsv$"),
]


def guarded(path: str) -> bool:
    p = "/" + path.replace(os.sep, "/").lstrip("/")
    return any(rx.search(p) for rx in GUARDED)


def resulting_content(tool_input: dict) -> str | None:
    """What the file will contain if this call succeeds.

    Replaying the edit here is what lets a pre-write hook see whole records
    instead of a fragment. If the replay cannot be done faithfully -- an
    old_string that does not match, an unreadable file -- this returns None and
    the caller falls back to checking the new text alone, which is weaker but
    still catches a fabricated quote.
    """
    if tool_input.get("content") is not None:
        return tool_input["content"]

    path = tool_input.get("file_path") or ""
    try:
        current = Path(path).read_text() if Path(path).exists() else ""
    except OSError:
        return None

    edits = tool_input.get("edits")
    if not edits:
        if "old_string" not in tool_input:
            return None
        edits = [tool_input]

    for e in edits:
        old, new = e.get("old_string"), e.get("new_string")
        if old is None or new is None:
            return None
        if old == "":
            current = new + current
            continue
        if old not in current:
            return None                  # cannot replay faithfully
        current = (current.replace(old, new) if e.get("replace_all")
                   else current.replace(old, new, 1))
    return current


def payload_fragment(tool_input: dict) -> str:
    parts = [tool_input.get("content") or "", tool_input.get("new_string") or ""]
    for edit in tool_input.get("edits") or []:
        parts.append(edit.get("new_string") or "")
    return "\n".join(parts)


def deny(reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def render(problems: list[dict], header: str, tail: str = "") -> str:
    lines = [header, ""]
    for p in problems:
        lines.append(f"  * {p['where']}: {p['problem']}")
        for n, line in enumerate(p["fix"].splitlines()):
            lines.append(f"    {'FIX: ' if n == 0 else '     '}{line}")
        lines.append("")
    if tail:
        lines.append(tail)
    return "\n".join(lines)


def run_labels(text: str) -> list[dict]:
    """Identifier/label agreement. Forward resolution is offline (cache only),
    so an ordinary edit never waits on OLS; an uncached identifier reports
    `unchecked` and does not block, because an unreachable service is not
    evidence that a row is wrong. `make validate` does the online pass."""
    env = dict(os.environ, PYTHONPATH=str(SRC))
    try:
        p = subprocess.run(
            [sys.executable, "-m", "taxon_stage.validate", "--payload",
             "--offline", "--json"],
            input=text, capture_output=True, text=True, timeout=25,
            cwd=str(REPO), env=env)
        return json.loads(p.stdout or "[]")
    except Exception:                                    # noqa: BLE001
        return []


def run_evidence(text: str) -> tuple[list[dict], bool]:
    """Whole-record evidence checks. Returns (problems, ran)."""
    try:
        p = subprocess.run(
            [sys.executable, str(TOOL), "verify", "--payload", "--json"],
            input=text, capture_output=True, text=True, timeout=40)
    except Exception:                                    # noqa: BLE001
        return [], False
    if p.returncode == 0:
        return [], True
    try:
        return json.loads(p.stdout).get("problems", []), True
    except json.JSONDecodeError:
        return [], False


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--pre"
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    if not guarded(path):
        return 0
    if mode != "--pre":
        return 0        # everything blocks pre-write; nothing is left for after

    full = resulting_content(tool_input)
    text = full if full is not None else payload_fragment(tool_input)
    if not text.strip():
        return 0
    if '"quote"' not in text and not CURIE_IN.search(text):
        return 0

    # 1. identifiers and the labels beside them
    label_problems = [p for p in run_labels(text) if not p.get("unchecked")]
    if label_problems:
        deny(render(
            label_problems,
            "BLOCKED: an identifier in this edit does not carry its own label.",
            "Change whichever half is wrong. Do not edit a label to match an "
            "identifier you did not intend --\nthat leaves the file consistent "
            "and the meaning wrong."))

    # 2. the evidence records themselves
    if not TOOL.exists():
        return 0
    problems, ran = run_evidence(text)
    if problems:
        tail = ("Every FIX above names a real value taken from the source; "
                "apply them as given.\nDo not reword a quote, trim a hedge, or "
                "drop a field to make this pass -- those edits are "
                "indistinguishable\nfrom correct ones once the file is on "
                "disk, which is the reason this check exists.")
        if full is None:
            tail += ("\n\n(This edit could not be replayed against the file, "
                     "so only the new text was checked.)")
        deny(render(problems,
                    "BLOCKED: evidence in this edit does not match the source.",
                    tail))
    if not ran:
        deny("BLOCKED: evidence cannot be verified -- the corpus is missing or "
             "unreadable.\n\nAn unchecked quote is indistinguishable from a "
             "checked one once written, so this is refused\nrather than waved "
             "through.\n\n  python3 .claude/skills/stage-evidence/"
             "stage_evidence.py build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
