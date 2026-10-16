#!/usr/bin/env python3
"""Pairwise token-stream comparison of the runs a maya_tier_sweep.py sweep kept (<out stem>-runs/<cond>-r<N>.json).

  python scripts/exp10_pairs.py results/phase4/exp10-a32/sweep1-runs --pair t26:t42 --pair t26a:t42a [--md out.md]

For every pair of conditions A:B and every request (prompt): over all (round i of A, round j of B) pairs, the index of the first
differing token (or 'same'). Also within each condition: do its rounds agree with each other (repeatability across engine
starts)? Standard library only.
"""
from __future__ import annotations

import argparse
import itertools
import json
import statistics
from pathlib import Path


def load(dirp: Path) -> dict:
    runs: dict[str, dict[int, dict]] = {}
    for f in sorted(dirp.glob("*-r*.json")):
        cond, _, r = f.stem.rpartition("-r")
        runs.setdefault(cond, {})[int(r)] = json.loads(f.read_text(encoding="utf-8"))
    return runs


def first_diff(a, b):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return None if len(a) == len(b) else n


def tokens(run: dict) -> dict:
    return {r["label"]: r["tokens"] for r in run["requests"] if r.get("tokens") and not r["label"].startswith("long")}


def compare(runs_a: dict, runs_b: dict, same_cond: bool):
    out = {}
    for (i, ra), (j, rb) in itertools.product(runs_a.items(), runs_b.items()):
        if same_cond and i >= j:
            continue
        ta, tb = tokens(ra), tokens(rb)
        for p in ta:
            if p in tb:
                out.setdefault(p, []).append(first_diff(ta[p], tb[p]))
    return out


def fmt(d):
    lines = ["| prompt | pairs | identical | first differing token index (min / median / max) |", "|---|---|---|---|"]
    tot_same = tot = 0
    allfd = []
    for p, v in d.items():
        same = sum(1 for x in v if x is None)
        fd = [x for x in v if x is not None]
        tot_same += same
        tot += len(v)
        allfd += fd
        lines.append(f"| {p} | {len(v)} | {same} | " + (f"{min(fd)} / {statistics.median(fd):.0f} / {max(fd)}" if fd else "-") + " |")
    head = f"{tot_same} of {tot} stream pairs identical" + (f"; among the others the first differing token is at median {statistics.median(allfd):.0f} (min {min(allfd)}, max {max(allfd)})" if allfd else "")
    return head, "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs_dir", type=Path)
    ap.add_argument("--pair", action="append", default=[], help="A:B condition names")
    ap.add_argument("--md", type=Path)
    a = ap.parse_args(argv)
    runs = load(a.runs_dir)
    parts = [f"conditions: " + ", ".join(f"{c} ({len(r)} runs)" for c, r in runs.items())]
    for c, r in runs.items():
        head, tab = fmt(compare(r, r, True))
        parts += ["", f"### repeatability of {c} across engine starts", head, "", tab]
    for pr in a.pair:
        x, y = pr.split(":")
        head, tab = fmt(compare(runs[x], runs[y], False))
        parts += ["", f"### {x} vs {y} (every round of one against every round of the other)", head, "", tab]
    text = "\n".join(parts) + "\n"
    print(text)
    if a.md:
        a.md.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
