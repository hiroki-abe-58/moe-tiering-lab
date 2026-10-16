#!/usr/bin/env python3
"""Summarise a lane-audit JSONL (the dev build's STRATA_GLM_LANE_AUDIT output): one line per audited lane call.

  python scripts/audit_summary.py results/phase4/exp9-fidelity/audit-t42.jsonl [--md out.md]

Per quantity (rel. L2 error vs the double-precision reference, max abs error / max |ref|, cosine similarity): the median
and the 10th-90th percentile over calls, and the number of calls and distinct layers. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def pct(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def load(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def table(rows, keys, title):
    out = [f"### {title}", "", "| quantity | rel. L2 median (p10-p90) | max-abs / max-ref median (p10-p90) | 1 - cosine median |", "|---|---|---|---|"]
    for k in keys:
        if not all(k in r["stats"] for r in rows):
            continue
        l2 = [r["stats"][k]["l2"] for r in rows]
        li = [r["stats"][k]["linf"] for r in rows]
        c = [1.0 - r["stats"][k]["cos"] for r in rows]
        out.append(f"| {k} | {statistics.median(l2) * 100:.3f}% ({pct(l2, 10) * 100:.3f}-{pct(l2, 90) * 100:.3f}) | "
                   f"{statistics.median(li) * 100:.3f}% ({pct(li, 10) * 100:.3f}-{pct(li, 90) * 100:.3f}) | {statistics.median(c):.2e} |")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jsonl", type=Path, nargs="+")
    ap.add_argument("--md", type=Path)
    a = ap.parse_args(argv)
    rows = [r for p in a.jsonl for r in load(p)]
    if not rows:
        print("no rows", file=sys.stderr)
        return 1
    layers = sorted({r["layer"] for r in rows})
    head = (f"{len(rows)} lane calls, {len(layers)} distinct layers ({layers[0]}..{layers[-1]}), experts per call "
            f"{min(r['ne'] for r in rows)}-{max(r['ne'] for r in rows)}, weight types {sorted({tuple(r['types']) for r in rows})}; "
            f"input peakiness amax/rms median {statistics.median(r['x_amax'] / r['x_rms'] for r in rows):.1f}")
    keys = list(rows[0]["stats"].keys())
    actual = [k for k in ("gpu", "cpu", "gpu_vs_cpu", "gpu_vs_gpu_emul", "cpu_vs_cpu_emul") if k in keys]
    x_only = [k for k in keys if k.startswith("x_") and not k.startswith(("xlane_h_", "xK256_h_"))]
    h_only = [k for k in keys if k.startswith("h_")]
    both = [k for k in keys if k.startswith("xh_")]
    mixed = [k for k in keys if k.startswith(("xlane_h_", "xK256_h_"))]
    parts = [head, "", table(rows, actual, "measured paths (vs the double reference; gpu_vs_cpu is between the two)"),
             "", table(rows, x_only, "emulation: only the gate/up input x quantised (h exact)"),
             "", table(rows, h_only, "emulation: only the down input h quantised (x exact)"),
             "", table(rows, both, "emulation: x and h in the same format"),
             "", table(rows, mixed, "emulation: x in the lane's format, h in another")]
    # per-layer split of the two measured paths
    by_layer: dict[int, list] = {}
    for r in rows:
        by_layer.setdefault(r["layer"], []).append(r)
    lines = ["### per layer (median rel. L2 vs reference)", "", "| layer | calls | gpu | cpu |", "|---|---|---|---|"]
    for ly in sorted(by_layer):
        rr = by_layer[ly]
        lines.append(f"| {ly} | {len(rr)} | {statistics.median(x['stats']['gpu']['l2'] for x in rr) * 100:.2f}% | "
                     f"{statistics.median(x['stats']['cpu']['l2'] for x in rr) * 100:.2f}% |")
    parts += ["", "\n".join(lines)]
    text = "\n".join(parts) + "\n"
    print(text)
    if a.md:
        a.md.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
