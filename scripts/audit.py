"""Check that every planned configuration and required deliverable is present."""
import csv
import hashlib
import json
import math
import re

import pymupdf

from common import ROOT, SEEDS
from experiments import configurations

source_hash = hashlib.sha256((ROOT / "src/arq.c").read_bytes()).hexdigest()
counts = {}
for part in ["2", "3a", "3b", "4", "5", "6", "7"]:
    folder = ROOT / f"results/experiment{part}"
    metadata = json.loads((folder / "metadata.json").read_text())
    assert metadata["source_sha256"] == source_hash, part
    rows = list(csv.DictReader((folder / "raw.csv").open()))
    expected = []
    for c in configurations(part):
        for seed in (SEEDS if c["pd"] or c["pa"] else SEEDS[:1]):
            expected.append((c,seed))
    assert len(rows) == len(expected) == metadata["jobs"], part
    for row, (c, seed) in zip(rows, expected):
        for k,v in c.items():
            assert row[k] == v if isinstance(v,str) else float(row[k]) == v, (part,k,row)
        assert int(row["seed"]) == seed
        for metric in ["time_ms", "efficiency", "attempts_per_packet"]:
            assert math.isfinite(float(row[metric])) and float(row[metric]) > 0
        assert float(row["efficiency"]) <= 1
        if c["n"]:
            assert int(row["delivered"]) == c["n"] * int(row["reps"])
            assert int(row["attempts"]) >= int(row["delivered"])
            assert int(row["reps"]) == (200 if c["pd"] or c["pa"] else 1)
        else:
            assert abs(float(row["efficiency"]) - int(row["delivered"])/c["duration"]) < 1e-8
    counts[part] = len(rows)

tests = json.loads((ROOT / "results/verification/tests.json").read_text())
assert tests["passed"] and tests["tests"] == 10
for protocol in ["sw","gbn","sr"]:
    for errors in ["errors","no_errors"]:
        rows = list(csv.DictReader((ROOT / f"results/verification/{protocol}_{errors}.csv").open()))
        delivered = [int(r["sequence"]) for r in rows if r["event"] == "DELIVER"]
        assert delivered == [0,1,2,3]
        if errors == "errors":
            assert any(r["event"] == "DATA_LOSS" for r in rows)
            assert any(r["event"] == "ACK_LOSS" for r in rows)

doc = pymupdf.open(ROOT / "output/pdf/COE4DK4_Group25_Lab4_Report.pdf")
assert len(doc) == 12
text = "\n".join(p.get_text() for p in doc)
assert set(map(int,re.findall(r"Figure (\d+)\.",text))) == set(range(1,14))
assert set(map(int,re.findall(r"Table (\d+)\.",text))) == set(range(1,3))
assert not any(x in text for x in ["\u2014", "\u2013", "\ufffd", "TODO", "PLACEHOLDER"])
for page in doc:
    for block in page.get_text("dict")["blocks"]:
        x0,y0,x1,y1 = block["bbox"]
        assert x0 >= 30 and y0 >= 20 and x1 <= 582 and y1 <= 772, (page.number,block["bbox"])
for line in (ROOT / "output/pdf/COE4DK4_Group25_Lab4_Report.md").read_text(encoding="utf-8").splitlines():
    if line.startswith("!["):
        path = line.split("](",1)[1][:-1]
        assert (ROOT / "output/pdf" / path).is_file()

result = dict(passed=True, experiment_seed_jobs=counts, total_seed_jobs=sum(counts.values()),
              report_pages=len(doc), report_figures=13, report_tables=2,
              source_sha256=source_hash, automated_tests=tests["tests"])
(ROOT / "results/audit.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
