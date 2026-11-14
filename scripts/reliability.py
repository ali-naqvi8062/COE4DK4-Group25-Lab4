"""Repeat selected operating points with four times the measurement duration."""
from concurrent.futures import ThreadPoolExecutor
import csv
import json
import math
import statistics

from common import ROOT, SEEDS, build, run

POINTS = [
    ("3a", .01, "SR Wr=4"), ("3a", .5, "GBN"),
    ("3a", .5, "SR Wr=32"), ("3b", 64, "SR Wr=4"),
    ("4", .5, "GBN"), ("4", .5, "SR Wr=32"),
    ("5", 2, "GBN"), ("5", 2, "SR Wr=32"),
    ("5", 120, "S&W"), ("5", 120, "SR Wr=4"),
]


def check(point):
    part, x, series = point
    with (ROOT / f"results/experiment{part}/raw.csv").open() as f:
        old = [r for r in csv.DictReader(f) if float(r["x"]) == x and r["series"] == series]
    longer = []
    for row in old:
        options = {k: row[k] for k in ["ws", "wr", "pd", "pa", "timeout", "seed"]}
        result, _ = run(**options, duration=2000000, warmup=200000)
        longer.append(dict(experiment=part, x=x, series=series, seed=row["seed"], **result))
    a = [float(r["efficiency"]) for r in old]
    b = [r["efficiency"] for r in longer]
    # These runs share seeds, so compare paired differences, not independent means.
    differences = [y-z for y,z in zip(b,a)]
    delta = statistics.mean(differences)
    delta_ci = 2.776445 * statistics.stdev(differences) / math.sqrt(len(differences))
    return dict(experiment=part, x=x, series=series,
                original_efficiency=statistics.mean(a), longer_efficiency=statistics.mean(b),
                longer_ci=2.776445*statistics.stdev(b)/math.sqrt(len(b)),
                relative_change_percent=100*delta/statistics.mean(a),
                paired_change=delta, paired_change_ci=delta_ci), longer


if __name__ == "__main__":
    build()
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(check, POINTS))
    out = ROOT / "results/reliability"
    out.mkdir(exist_ok=True)
    for name, rows in [("summary", [x[0] for x in outputs]),
                       ("raw", [r for x in outputs for r in x[1]])]:
        with (out / f"{name}.csv").open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    print(json.dumps([x[0] for x in outputs], indent=2))
