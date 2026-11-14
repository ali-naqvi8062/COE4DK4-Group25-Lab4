"""Plot measured points and confidence intervals without fitting data."""
import argparse
import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t

from common import ROOT

STYLES = {
    "S&W": ("#555555", "x"), "GBN": ("#d95f02", "s"),
    "SR Wr=2": ("#1b9e77", "o"), "SR Wr=8": ("#7570b3", "^"),
    "SR Wr=4": ("#1b9e77", "o"), "SR Wr=16": ("#7570b3", "^"),
    "SR Wr=32": ("#1976b6", "D"),
}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .22, "legend.fontsize": 8,
                     "figure.dpi": 120, "savefig.dpi": 220})


def load(part):
    path = ROOT / "results" / f"experiment{part}"
    with (path / "raw.csv").open() as f:
        rows = list(csv.DictReader(f))
    groups = defaultdict(list)
    for row in rows:
        for key in row:
            if key != "series": row[key] = float(row[key])
        groups[(row["n"], row["pd"], row["pa"], row["x"], row["series"])].append(row)
    summary = []
    for (n, pd, pa, x, series), group in groups.items():
        item = dict(n=n, pd=pd, pa=pa, x=x, series=series, ws=group[0]["ws"], wr=group[0]["wr"])
        for metric in ["efficiency", "attempts_per_packet", "time_ms"]:
            values = np.array([r[metric] for r in group])
            mean = values.mean()
            if n and metric == "time_ms":
                count = sum(r["reps"] for r in group)
                mean = sum(r["reps"] * r[metric] for r in group) / count
                ss = sum((r["reps"] - 1)*r["time_sd"]**2 + r["reps"]*(r[metric]-mean)**2 for r in group)
                ci = t.ppf(.975, count-1)*np.sqrt(ss/(count-1)/count) if count > 1 else 0
            else:
                count = len(group)
                ci = t.ppf(.975, count-1)*values.std(ddof=1)/np.sqrt(count) if count > 1 else 0
            item[metric] = mean
            item[metric + "_ci"] = ci
        item["runs"] = sum(r["reps"] for r in group)
        summary.append(item)
    with (path / "summary.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader(); writer.writerows(summary)
    return summary


def draw(ax, rows, metric, xlabel, title):
    for series in STYLES:
        data = sorted((r for r in rows if r["series"] == series), key=lambda r: r["x"])
        if not data: continue
        color, marker = STYLES[series]
        ax.errorbar([r["x"] for r in data], [r[metric] for r in data],
                    yerr=[r[metric + "_ci"] for r in data], color=color, marker=marker,
                    markersize=4, linewidth=1, capsize=2, elinewidth=.7, label=series)
    ax.set_xlabel(xlabel)
    ax.set_ylabel({"efficiency": "Link efficiency", "attempts_per_packet": "Attempts per delivered packet",
                   "time_ms": "Mean completion time (ms)"}[metric])
    ax.set_title(title, fontsize=10)
    ax.set_ylim(bottom=0)


def save(fig, name):
    out = ROOT / "figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out / (name + ".png"), bbox_inches="tight")
    fig.savefig(out / (name + ".pdf"), bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("part", choices=["2", "3a", "3b", "4", "5", "6", "7"])
    part = parser.parse_args().part
    rows = load(part)
    if part in ["6", "7"]:
        for n in sorted({r["n"] for r in rows}):
            fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), layout="constrained")
            for ax, (pd, pa) in zip(axes, [(0,0),(.05,0),(.05,.05)]):
                subset = [r for r in rows if r["n"] == n and r["pd"] == pd and r["pa"] == pa]
                draw(ax, subset, "time_ms", "Send window Ws (packets)", f"N={n:g}, pd={pd:g}, pa={pa:g}")
            axes[0].legend(loc="upper right")
            save(fig, f"experiment{part}_n{n:g}")
            # Full-size individual panels keep the report axes and markers readable.
            for pd, pa in [(0,0),(.05,0),(.05,.05)]:
                fig, ax = plt.subplots(figsize=(7.2, 4), layout="constrained")
                draw(ax, [r for r in rows if r["n"] == n and r["pd"] == pd and r["pa"] == pa],
                     "time_ms", "Send window Ws (packets)", f"N={n:g}, pd={pd:g}, pa={pa:g}; timeout=15 ms")
                ax.legend(ncol=2)
                save(fig, f"experiment{part}_n{n:g}_pd{pd:g}_pa{pa:g}")
        return
    metrics = ["efficiency"] if part in ["2", "3a"] else ["efficiency", "attempts_per_packet"]
    xlabel = "Send window Ws (packets)" if part in ["2", "3b"] else "Data error probability pd" if part == "3a" else "ACK error probability pa" if part == "4" else "Timeout (ms)"
    title = {"2": "No errors; timeout=15 ms", "3a": "Ws=32; pa=0; timeout=15 ms",
             "3b": "pd=0.1; pa=0; timeout=15 ms", "4": "Ws=32; pd=0.1; timeout=15 ms",
             "5": "Ws=32; pd=pa=0.1"}[part]
    for metric in metrics:
        fig, ax = plt.subplots(figsize=(7.2, 4), layout="constrained")
        draw(ax, rows, metric, xlabel, title)
        if part == "2":
            x = np.array(sorted({r["x"] for r in rows}))
            ax.plot(x, np.minimum(1, x/11), "k--", lw=.9, label="Theory: min(1, Ws/11)")
            ax.axvline(11, color="grey", ls=":", lw=.8)
        if part == "3a":
            p = np.linspace(0,.5,201)
            ax.plot(p, 1-p, "k--", lw=.9, label="Ideal SR upper bound")
            ax.plot(p, (1-p)/(1+10*p), "k:", lw=1.1, label="GBN ideal feedback approximation")
            ax.plot(p, (1-p)/(11+4*p), color="#999999", ls="--", lw=1, label="S&W exact renewal")
        if part == "5": ax.axvline(11, color="grey", ls=":", lw=.8)
        ax.legend(ncol=2, loc="best")
        save(fig, f"experiment{part}_{metric}")


if __name__ == "__main__":
    main()
