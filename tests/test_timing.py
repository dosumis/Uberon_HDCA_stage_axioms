"""Fixtures for datalog/timing.dl (docs/timing-individuals.md §8).

Each directory under tests/timing/cases/ is one case:

    input/      fact files; any the case omits are supplied empty, except
                stage_rel.csv, which defaults to tests/timing/stages.csv
    expected/   NAME.csv         must equal the program's NAME.csv, as a set of rows
                NAME.subset.csv  must be contained in it
    macros      optional, one Soufflé -M macro per line

This file runs Soufflé and compares rows. It draws no temporal conclusion of
its own -- that is the point of keeping the reasoning in Datalog.
"""

import csv
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "datalog" / "timing.dl"
TIMING = Path(__file__).resolve().parent / "timing"
CASES = sorted(p for p in (TIMING / "cases").iterdir() if p.is_dir())

# Header rows for every input relation the program reads.
INPUTS = {
    "bound.csv": "x,pred,stage,why\n",
    "edge.csv": "x,rel,y,why\n",
    "stage_rel.csv": "a,rel,b,why\n",
    "seed.csv": "x\n",
    "label.csv": "id,label\n",
    "individuate.tsv": "uberon_id\tuberon_label\tindividuate\tcurator\tdate\tnote\n",
    "withheld.tsv": "why\treason\tcurator\tdate\n",
}

pytestmark = pytest.mark.skipif(
    shutil.which("souffle") is None, reason="souffle not on PATH")


def run(facts: Path, out: Path, macros=()):
    """Run the program over a facts directory; return the output directory."""
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["souffle", "-F", str(facts), "-D", str(out)]
    for m in macros:
        cmd += ["-M", m]
    subprocess.run(cmd + [str(PROGRAM)], check=True, capture_output=True, text=True)
    return out


def rows(path: Path):
    with path.open(newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        return {tuple(r) for r in reader if r}


def stage_facts(case: Path, facts: Path):
    facts.mkdir(parents=True)
    for name, header in INPUTS.items():
        given = case / "input" / name
        if given.exists():
            shutil.copy(given, facts / name)
        elif name == "stage_rel.csv":
            shutil.copy(TIMING / "stages.csv", facts / name)
        else:
            (facts / name).write_text(header)


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_case(case, tmp_path):
    facts = tmp_path / "facts"
    stage_facts(case, facts)
    macros_file = case / "macros"
    macros = macros_file.read_text().split() if macros_file.exists() else []
    out = run(facts, tmp_path / "out", macros)

    expectations = sorted((case / "expected").iterdir())
    assert expectations, f"{case.name} has no expected output"
    for exp in expectations:
        if exp.name.endswith(".subset.csv"):
            actual = rows(out / exp.name.replace(".subset.csv", ".csv"))
            missing = rows(exp) - actual
            assert not missing, f"{exp.name}: missing {sorted(missing)}"
        else:
            actual, wanted = rows(out / exp.name), rows(exp)
            assert actual == wanted, (
                f"{exp.name}:\n  unexpected {sorted(actual - wanted)}"
                f"\n  missing    {sorted(wanted - actual)}")
