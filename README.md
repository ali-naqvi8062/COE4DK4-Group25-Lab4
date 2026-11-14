# COE4DK4 Lab 4 - Group 25

ARQ protocol simulation for COE4DK4 Lab 4 (2026).

## Status

The Lab 4 simulator is in `src/arq.c`. The original Lab 3 ALOHA files are
preserved in `legacy/` and are not used by the ARQ simulator.

Lab 4 covers Stop-and-Wait, Go-Back-N, and Selective-Repeat, including
packet errors, ACK errors, window sizes, retransmission timeouts, and finite
packet transfers.

## Build and verify

Install a C11 compiler (GCC) and Python 3.10 or later. From this folder:

```text
python -m pip install -r requirements.txt
python scripts/test_arq.py
python scripts/verify.py
```

The scripts compile the simulator into `build/`. For a single finite run:

```text
build/arq.exe --ws 16 --wr 16 --n 100 --pd 0.05 --pa 0.05 --seed 400450701
```

On Linux or macOS use `build/arq`. Omit `--n` for a backlogged run.
Use `--trace` to write event CSV to stderr; the result JSON is written to stdout.
The model and timer assumptions are documented in `docs/design.md`.

## Experiments and report

Run each experiment separately, then plot its saved measurements:

```text
python scripts/experiments.py 2
python scripts/plots.py 2
```

Repeat for `3a`, `3b`, `4`, `5`, `6`, and `7`. Each run saves seed-level data
and the simulator source hash in `results/experiment*/`. Plotting writes
summary CSV files and PNG/PDF figures with connected measured points and
95% confidence intervals. The independent replications use the same seed set
for every protocol.

```text
python scripts/reliability.py
python scripts/report.py
python scripts/audit.py
python scripts/package.py
```

The report is `output/pdf/COE4DK4_Group25_Lab4_Report.pdf`. Its Markdown copy
and generator are included for editing. Report tables are also saved as CSV
files under `tables/`. The separate submission archive is
`output/COE4DK4_Group25_Lab4_Code.zip`.

See `docs/requirements_checklist.md` for the mapping from the lab manual to
the results and report pages. The report uses the Lab 3 title-page style,
Times text, numbered figure captions, and experiment-based organization.

## Group workflow

Create a branch for each change, commit related changes together, and use a
pull request to merge into `main`.

The course manual and previous report are local reference files and are not
tracked in this repository. Copyright and license notices in the original
C files are retained.
