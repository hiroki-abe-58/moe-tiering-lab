#!/usr/bin/env python3
"""Interleaved sweep of ``scripts/maya_probe.py`` sessions: one engine start per run, conditions reversed each round.

  python scripts/maya_tier_sweep.py --maya-dir <maya> --config maya-xxx.json --rounds 3 \\
      --cond t26:STRATA_GLM_RAM_GB=26 --cond t38:STRATA_GLM_RAM_GB=38 --out results/phase2/tier.json

Condition = NAME or NAME:KEY=VALUE[,KEY=VALUE...]; the first is the baseline and its first run is the token-stream
reference. Every run's raw JSON (token ids, per-request metrics, memory samples) is kept next to --out in
``<out stem>-runs/``. Tests: ``python -I -m unittest discover -s tests``.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import stats, sweep  # noqa: E402


def python_of(maya_dir: Path) -> str:
    for rel in ("Scripts/python.exe", "bin/python"):
        p = maya_dir / ".venv" / rel
        if p.exists():
            return str(p)
    raise SystemExit(f"{maya_dir}: no .venv (Maya's own Python is needed for psutil and serve.server)")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maya-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--cond", action="append", required=True)
    ap.add_argument("--common", default="", help="KEY=VALUE[,..] for every condition")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--no-long", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    conds = {}
    for c in a.cond:
        name, _, spec = c.partition(":")
        conds[name] = [kv for kv in spec.split(",") if kv]
    common = [kv for kv in a.common.split(",") if kv]
    order = stats.interleave(list(conds), a.rounds)
    print("run order:", " ".join(order))
    if a.dry_run:
        return 0
    py = python_of(a.maya_dir)
    probe = Path(__file__).with_name("maya_probe.py")
    runs_dir = a.out.with_name(a.out.stem + "-runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    records, streams, seen = [], {}, {}
    for i, name in enumerate(order, 1):
        rnd = seen.get(name, 0)
        seen[name] = rnd + 1
        out = runs_dir / f"{name}-r{rnd}.json"
        cmd = [py, str(probe), "--maya-dir", str(a.maya_dir), "--config", str(a.config), "--label", f"{name}-r{rnd}",
               "--out", str(out)] + (["--no-long"] if a.no_long else [])
        for kv in common + conds[name]:
            cmd += ["--env", kv]
        print(f"[{i}/{len(order)}] {name} round {rnd} ...", flush=True)
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            print(p.stdout[-1500:], p.stderr[-1500:])
            raise SystemExit(f"run failed: {name} round {rnd}")
        print("   ", p.stdout.strip().splitlines()[-1], flush=True)
        run = json.loads(out.read_text(encoding="utf-8"))
        records.append(sweep.run_record(run, name, rnd))
        streams.setdefault(name, {})[f"{rnd:03d}"] = sweep.token_streams(run)
        a.out.write_text(json.dumps({"order": order, "common": common, "conditions": conds, "records": records}, indent=1),
                         encoding="utf-8")
    base = next(iter(conds))
    md = sweep.markdown(sweep.summarize(records, base), base, sweep.stream_report(streams, base))
    a.out.with_suffix(".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
