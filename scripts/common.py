"""Build and run the C simulator from any working directory."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "build" / ("arq.exe" if os.name == "nt" else "arq")
SEEDS = [400450701, 400327698, 400336020, 104729, 130363]


def build():
    EXE.parent.mkdir(exist_ok=True)
    subprocess.run(["gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Wpedantic",
                    "-Werror", str(ROOT / "src/arq.c"), "-o", str(EXE), "-lm"], check=True)


def run(**options):
    args = [str(EXE)]
    for key, value in options.items():
        args.append("--" + key.replace("_", "-"))
        if value is not True:
            args.append(str(value))
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return json.loads(result.stdout), result.stderr
