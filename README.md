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

## Group workflow

Create a branch for each change, commit related changes together, and use a
pull request to merge into `main`.

The course manual and previous report are local reference files and are not
tracked in this repository. Copyright and license notices in the original
C files are retained.
