#!/usr/bin/env python3
"""Interleaved A/B benchmark driver around Project Maya's own ``--bench``.

It never edits your Maya config: each run uses a temporary copy whose ``"env"`` block carries the condition's
settings. Conditions run in a reversing order (A B | B A | A B ...) so thermal and OS-cache drift hits every
condition alike. Results: a JSON file (every run) and a Markdown table (median, range, % vs the baseline).

  python scripts/maya_ab.py --maya-dir C:\\path\\to\\project-maya --config maya-maya-s.json --rounds 3 \\
      --cond base --cond chunks4:STRATA_GLM_READ_CHUNKS=4 --out results/chunks.json

A condition is NAME or NAME:KEY=VALUE[,KEY=VALUE...]. The first one is the baseline. The pseudo-setting
AFFINITY=P|E|all|0xMASK (Windows) restricts the run to the performance cores, the efficiency cores or a mask. Maya must be stopped (the
benchmark needs the GPU). Pin the RAM tier for every condition (e.g. ``--common STRATA_GLM_RAM_GB=40``) so the
tier size is not what you are measuring; the report warns when it varied.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import abreport, cputopo, mayaparse, stats  # noqa: E402


def parse_env(spec: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for part in filter(None, spec.split(",")):
        if "=" not in part:
            raise ValueError(f"expected KEY=VALUE, got {part!r}")
        k, v = part.split("=", 1)
        if k != "AFFINITY" and not k.startswith("STRATA_") and not k.startswith("MAYA_"):
            raise ValueError(f"{k}: only STRATA_* / MAYA_* settings (or AFFINITY) are expected here")
        env[k] = v
    return env


def parse_cond(arg: str) -> Tuple[str, Dict[str, str]]:
    name, _, spec = arg.partition(":")
    if not name:
        raise ValueError("a condition needs a name")
    return name, parse_env(spec)


def python_of(maya_dir: Path) -> str:
    for rel in ("Scripts/python.exe", "bin/python"):
        p = maya_dir / ".venv" / rel
        if p.exists():
            return str(p)
    return sys.executable


def run_once(maya_dir: Path, config: Path, common: Dict[str, str], cond_env: Dict[str, str], tag: str) -> Dict[str, object]:
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg.setdefault("env", {})
    merged = {**common, **cond_env}
    affinity = merged.pop("AFFINITY", None)     # not an engine setting: the CPUs the benchmark may run on (Windows)
    cfg["env"].update(merged)
    tmp = maya_dir / f".ab-{tag}.json"
    tmp.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    saved = None
    try:
        if affinity:      # the children inherit this process's mask: set it for the run, restore it after
            saved = cputopo.get_process_affinity()
            cputopo.set_process_affinity(cputopo.resolve_affinity(affinity, cputopo.read_system()))
        t0 = time.time()
        p = subprocess.run([python_of(maya_dir), "maya.py", "--bench", "--config", str(tmp)], cwd=maya_dir,
                           capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"--bench failed ({p.returncode}):\n{p.stdout[-1500:]}\n{p.stderr[-1500:]}")
        bench_txt = (maya_dir / "maya-bench.txt").read_text(encoding="utf-8", errors="replace")
        log = (maya_dir / "maya-bench.log").read_text(encoding="utf-8", errors="replace")
        b = mayaparse.parse_bench(bench_txt)
        # the bench file keeps only the last 40 engine lines: take every stat line of the run from the log
        b["stats"] = [s for s in map(mayaparse.parse_stat_line, log.splitlines()) if s]
        rec = abreport.run_record(tag.split("-r")[0], int(tag.rsplit("-r", 1)[1]), b, abreport.parse_ram_tier_gb(log))
        rec["seconds"] = round(time.time() - t0, 1)
        return rec
    finally:
        if saved is not None:
            cputopo.set_process_affinity(saved)
        tmp.unlink(missing_ok=True)


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maya-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True, help="the installed maya-*.json (relative to --maya-dir ok)")
    ap.add_argument("--cond", action="append", required=True, help="NAME or NAME:KEY=VALUE[,KEY=VALUE]; first = baseline")
    ap.add_argument("--common", default="", help="KEY=VALUE[,..] applied to every condition (e.g. a pinned RAM tier)")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True, help="JSON results; a .md table is written next to it")
    ap.add_argument("--dry-run", action="store_true", help="print the run order and exit")
    a = ap.parse_args(argv)

    conds = dict(parse_cond(c) for c in a.cond)
    if len(conds) != len(a.cond):
        ap.error("duplicate condition names")
    common = parse_env(a.common)
    order = stats.interleave(list(conds), a.rounds)
    print("run order:", " ".join(order))
    if a.dry_run:
        return 0

    config = a.config if a.config.is_absolute() else a.maya_dir / a.config
    runs: List[Dict[str, object]] = []
    seen: Dict[str, int] = {}
    for i, name in enumerate(order, 1):
        rnd = seen.get(name, 0)
        seen[name] = rnd + 1
        print(f"[{i}/{len(order)}] {name} round {rnd} ...", flush=True)
        rec = run_once(a.maya_dir, config, common, conds[name], f"{name}-r{rnd}")
        runs.append(rec)
        print(f"    decode {rec['decode_tok_s']} tok/s, prefill {rec['prefill']}, tier {rec['ram_tier_gb']} GB", flush=True)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps({"order": order, "common": common, "conditions": conds, "runs": runs}, indent=2),
                         encoding="utf-8")   # written after every run: an interrupted sweep keeps what it measured
    summary = abreport.summarize_runs(runs, next(iter(conds)))
    md = abreport.markdown(summary, next(iter(conds)), runs)
    a.out.with_suffix(".md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
