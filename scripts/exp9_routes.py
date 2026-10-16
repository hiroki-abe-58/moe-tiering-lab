#!/usr/bin/env python3
"""How a tiny numerical difference becomes a different token: routing flips.

Two engine runs of the same prompts, each with STRATA_GLM_ROUTE_LOG (one line per MoE layer of every decoded position:
``layer e0..e7 fetch miss cpu | near misses``) and STRATA_GLM_LOGIT_TRACE (one JSON line per decoded position with the
four highest logits). The k-th decoded position of both runs is the same token position of the same prompt up to the first
token where they part, so up to there any difference is purely numerical. This reports, per pair:
  - the first position where some layer picked a different set of experts (a routing flip),
  - how many positions before the first different token had at least one flip, and how many layer-routes flipped in all,
  - the largest and the median |difference| of the top-1 logit over the positions before the first different token,
  - the first position where the greedy tokens differ.

  python scripts/exp9_routes.py --run a=route-t26.0,q-t26.trace.jsonl --run b=route-t42.0,q-t42.trace.jsonl [--pairs a:b,...]
Standard library only.
"""
from __future__ import annotations

import argparse
import itertools
import json
import statistics
import sys
from pathlib import Path


def load_routes(path: Path, layers_per_call: int = 0) -> list:
    """Route lines grouped by decoded position: a new position starts when the layer number does not increase."""
    calls, cur, prev = [], [], -1
    for line in path.read_text(encoding="utf-8").splitlines():
        head = line.split("|")[0].split()
        layer, ids = int(head[0]), frozenset(int(x) for x in head[1:9])
        if layer <= prev and cur:
            calls.append(cur)
            cur = []
        cur.append((layer, ids))
        prev = layer
    if cur:
        calls.append(cur)
    return calls


def load_trace(path: Path) -> list:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def compare(ra, ta, rb, tb):
    n = min(len(ra), len(ta), len(rb), len(tb))
    k_tok = next((k for k in range(n) if ta[k]["tok"] != tb[k]["tok"] or ta[k]["pos"] != tb[k]["pos"]), None)
    stop = n if k_tok is None else k_tok
    flips_per_call = [sum(1 for (la, ia), (lb, ib) in zip(ra[k], rb[k]) if la != lb or ia != ib) for k in range(stop)]
    k_flip = next((k for k, f in enumerate(flips_per_call) if f), None)
    dl = []
    for k in range(stop):
        a, b = ta[k]["top"], tb[k]["top"]
        if a[0][0] == b[0][0]:
            dl.append(abs(a[0][1] - b[0][1]))
    return {"calls": n, "first_token_diff": k_tok, "first_route_flip": k_flip,
            "calls_with_flip_before": sum(1 for f in flips_per_call if f), "flips_before": sum(flips_per_call),
            "before": stop, "dlogit_max": max(dl) if dl else None, "dlogit_median": statistics.median(dl) if dl else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", required=True, help="name=routefile,tracefile")
    ap.add_argument("--pairs", help="a:b,c:d (default: all pairs)")
    ap.add_argument("--md", type=Path)
    a = ap.parse_args(argv)
    runs = {}
    for spec in a.run:
        name, files = spec.split("=")
        rf, tf = files.split(",")
        runs[name] = (load_routes(Path(rf)), load_trace(Path(tf)))
        print(f"{name}: {len(runs[name][0])} routed positions, {len(runs[name][1])} traced positions", file=sys.stderr)
    pairs = [tuple(p.split(":")) for p in a.pairs.split(",")] if a.pairs else list(itertools.combinations(runs, 2))
    lines = ["| pair | decoded positions | first different token at | before it: positions with a routing flip | layer-routes flipped | first flip at | max / median \\|dlogit top-1\\| |",
             "|---|---|---|---|---|---|---|"]
    for x, y in pairs:
        c = compare(*runs[x], *runs[y])
        lines.append(f"| {x} vs {y} | {c['calls']} | {c['first_token_diff']} | {c['calls_with_flip_before']} of {c['before']} | "
                     f"{c['flips_before']} | {c['first_route_flip']} | "
                     + (f"{c['dlogit_max']:.3f} / {c['dlogit_median']:.4f}" if c["dlogit_max"] is not None else "-") + " |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.md:
        a.md.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
