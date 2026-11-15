"""Make a code-only submission archive for Lab 4."""
from zipfile import ZipFile, ZIP_DEFLATED

from common import ROOT

files = [
    "src/arq.c",
    "scripts/common.py",
    "scripts/test_arq.py",
    "scripts/verify.py",
    "scripts/experiments.py",
    "scripts/plots.py",
    "scripts/reliability.py",
    "docs/design.md",
]
readme = """# COE4DK4 Lab 4 - Group 25

## Files

- src/arq.c: complete S&W, GBN, and SR simulator. No additional C files are needed.
- scripts/common.py: compiler and simulator runner.
- scripts/test_arq.py: verification tests.
- scripts/verify.py: Experiment 1 event traces.
- scripts/experiments.py: Experiments 2, 3a, 3b, 4, 5, 6, and 7.
- scripts/plots.py: plots and summary tables from experiment results.
- scripts/reliability.py: longer-run checks.
- docs/design.md: model and timer assumptions.

## Build and run

Install GCC and Python 3.10 or later, then extract this ZIP and open a terminal
in the extracted folder. Keep the src, scripts, and docs folders together.

    python -m pip install -r requirements.txt
    python scripts/test_arq.py
    python scripts/verify.py

The tests compile the simulator into build/. A single Windows run is:

    build/arq.exe --ws 16 --wr 16 --n 100 --pd 0.05 --pa 0.05 --seed 400450701

Use build/arq on Linux or macOS. Omit --n for a continuously backlogged source.
Use --trace for event CSV on stderr. Results are printed as JSON on stdout.

To compile manually, create build/ and run:

    gcc -std=c11 -O2 -Wall -Wextra -Wpedantic src/arq.c -o build/arq -lm

On Windows, name the output build/arq.exe.

## Experiments

    python scripts/experiments.py 2
    python scripts/plots.py 2

Repeat those commands for 3a, 3b, 4, 5, 6, and 7. Run the reliability check
after completing those experiments:

    python scripts/reliability.py

The scripts generate results/ and figures/. The report is submitted separately.
"""

destination = ROOT / "output/COE4DK4_Group25_Lab4_Code_Only.zip"
destination.parent.mkdir(exist_ok=True)
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for name in files:
        archive.write(ROOT / name, name)
    archive.writestr("README.md", readme)
    archive.writestr("requirements.txt", "matplotlib>=3.8\nnumpy>=1.26\nscipy>=1.11\n")

with ZipFile(destination) as archive:
    assert archive.testzip() is None
    assert set(archive.namelist()) == set(files + ["README.md", "requirements.txt"])
print(f"Created {destination.name} with {len(files) + 2} files.")
