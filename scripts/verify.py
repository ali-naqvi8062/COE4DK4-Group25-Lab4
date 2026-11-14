"""Save the six short traces requested in Experiment 1."""
import json
from common import ROOT, SEEDS, build, run

build()
out = ROOT / "results/verification"
out.mkdir(parents=True, exist_ok=True)
summary = []
for protocol, ws, wr in [("sw", 1, 1), ("gbn", 4, 1), ("sr", 4, 4)]:
    for p in [0, .5]:
        result, trace = run(ws=ws, wr=wr, n=4, pd=p, pa=p, seed=SEEDS[0], trace=True)
        name = f"{protocol}_{'errors' if p else 'no_errors'}"
        (out / f"{name}.csv").write_text(trace)
        summary.append(dict(name=name, ws=ws, wr=wr, pd=p, pa=p, seed=SEEDS[0], **result))
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
