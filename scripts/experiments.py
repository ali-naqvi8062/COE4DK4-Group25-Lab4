"""Run one experiment at a time and save the seed-level measurements."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
import time

from common import ROOT, SEEDS, build, run

WINDOWS = [1, 2, 3, 4, 6, 8, 10, 11, 12, 16, 24, 32, 48, 64]
ERRORS = [0, .01, .025, .05, .1, .15, .2, .3, .4, .5]
ACK_ERRORS = [0, .01, .025, .05, .1, .2, .3, .4, .5]
TIMEOUTS = [2, 4, 6, 8, 10, 11, 12, 15, 20, 30, 50, 80, 120]


def configurations(part):
    configs = []

    def add(x, series, ws, wr, **kwargs):
        configs.append(dict(x=x, series=series, ws=ws, wr=wr, n=0, pd=0, pa=0,
                            timeout=15, duration=500000, warmup=50000) | kwargs)

    if part in ["2", "3b"]:
        for w in WINDOWS:
            pd = .1 if part == "3b" else 0
            add(w, "S&W", 1, 1, pd=pd)
            add(w, "GBN", w, 1, pd=pd)
            for wr in ([2, 8, 32] if part == "2" else [4, 16, 32]):
                add(w, f"SR Wr={wr}", w, wr, pd=pd)
    elif part in ["3a", "4", "5"]:
        values = ERRORS if part == "3a" else ACK_ERRORS if part == "4" else TIMEOUTS
        for x in values:
            settings = dict(pd=x if part == "3a" else .1,
                            pa=x if part == "4" else .1 if part == "5" else 0,
                            timeout=x if part == "5" else 15)
            add(x, "S&W", 1, 1, **settings)
            add(x, "GBN", 32, 1, **settings)
            for wr in [4, 16, 32]:
                add(x, f"SR Wr={wr}", 32, wr, **settings)
    elif part in ["6", "7"]:
        for n in ([100] if part == "6" else [10, 1000]):
            for pd, pa in [(0, 0), (.05, 0), (.05, .05)]:
                for w in WINDOWS:
                    settings = dict(n=n, pd=pd, pa=pa, warmup=0)
                    add(w, "S&W", 1, 1, **settings)
                    add(w, "GBN", w, 1, **settings)
                    for wr in [4, 16, 32]:
                        add(w, f"SR Wr={wr}", w, wr, **settings)
    return configs


def execute(config):
    options = {k: v for k, v in config.items() if k not in ["x", "series"]}
    result, _ = run(**options)
    return config | result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("part", choices=["2", "3a", "3b", "4", "5", "6", "7"])
    args = parser.parse_args()
    build()
    jobs = []
    for config in configurations(args.part):
        stochastic = config["pd"] > 0 or config["pa"] > 0
        for seed in (SEEDS if stochastic else SEEDS[:1]):
            jobs.append(config | dict(seed=seed, reps=200 if config["n"] and stochastic else 1))
    out = ROOT / "results" / f"experiment{args.part}"
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    rows = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, row in enumerate(pool.map(execute, jobs), 1):
            rows.append(row)
            if i % 25 == 0 or i == len(jobs):
                print(f"Experiment {args.part}: {i}/{len(jobs)} runs", flush=True)
    with (out / "raw.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out / "metadata.json").write_text(json.dumps(dict(
        experiment=args.part, seed_set=SEEDS, jobs=len(jobs),
        source_sha256=hashlib.sha256((ROOT / "src/arq.c").read_bytes()).hexdigest(),
        elapsed_seconds=round(time.perf_counter()-start, 2),
        compiler="gcc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror",
        data_packet_bits=1000, link_rate_bps=1000000, one_way_propagation_ms=5,
        ack_transmission_ms=0, processing_ms=0
    ), indent=2) + "\n")


if __name__ == "__main__":
    main()
