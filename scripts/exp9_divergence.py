#!/usr/bin/env python3
"""Where two greedy runs part, and how close the call was: token streams of two quality-suite runs plus the dev engine's
STRATA_GLM_LOGIT_TRACE files (one JSON line per decoded position: position, greedy token, the four highest logits).

  python scripts/exp9_divergence.py --a q-t26.json --a-trace q-t26.trace.jsonl --b q-t42.json --b-trace q-t42.trace.jsonl \\
      [--label "t26 vs t42, lane default"] [--md out.md] [--json out.json]

Both runs of a task have the same prompt, so up to the first token that differs they have fed the model the same context
(the same positions, the same KV cache up to numerical noise); at that token the two engines saw the same prompt but
computed slightly different logits. For each task that parts: the index of the first differing token, each run's margin
(top-1 minus top-2 logit) there, and how far apart the two runs' logits for the two candidate tokens are. A margin much
smaller than the logit noise of the paths (a 1% change of a hidden state moves a logit by tenths) means the call was a
coin flip, not a computation that went wrong. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


def load_run(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    return {r["id"]: r for r in d["results"]}


def load_trace(path: Path) -> list:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def segments(run: dict, trace: list) -> dict:
    """task id -> (generated-region start call, calls): the trace is cut where the position does not continue by one (a new request);
    segment i belongs to the i-th task; the last n_tokens - 1 calls of a segment predict the task's generated tokens 1..n-1 (call k
    predicts token k - (calls - n_tokens) ), the first calls are the prompt's own positions."""
    segs, cur = [], []
    for line in trace:
        if cur and line["pos"] != cur[-1]["pos"] + 1:
            segs.append(cur)
            cur = []
        cur.append(line)
    if cur:
        segs.append(cur)
    out = {}
    for (tid, r), seg in zip(run.items(), segs):
        n = len(r["tokens"])
        g0 = max(0, len(seg) - n)          # first call whose prediction is a generated token (token 0 .. n-1)
        out[tid] = {k - g0: seg[k] for k in range(g0, len(seg))}
    return out


def logit_of(line: dict, tok: int):
    for t, v in line["top"]:
        if t == tok:
            return v
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", type=Path, required=True)
    ap.add_argument("--a-trace", type=Path, required=True)
    ap.add_argument("--b", type=Path, required=True)
    ap.add_argument("--b-trace", type=Path, required=True)
    ap.add_argument("--label", default="A vs B")
    ap.add_argument("--md", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    ra, rb = load_run(a.a), load_run(a.b)
    sa, sb = segments(ra, load_trace(a.a_trace)), segments(rb, load_trace(a.b_trace))
    rows = []
    for tid in ra:
        if tid not in rb:
            continue
        ta, tb = ra[tid]["tokens"], rb[tid]["tokens"]
        n = min(len(ta), len(tb))
        d = next((i for i in range(n) if ta[i] != tb[i]), None)
        if d is None and len(ta) != len(tb):
            d = n
        row = {"id": tid, "fam": ra[tid]["fam"], "n_a": len(ta), "n_b": len(tb), "first_diff": d}
        if d is not None and d < n:
            la, lb = sa.get(tid, {}).get(d), sb.get(tid, {}).get(d)
            if la and lb:
                ma = la["top"][0][1] - la["top"][1][1]
                mb = lb["top"][0][1] - lb["top"][1][1]
                # the two candidates: A's token and B's token, as each run saw them
                ca, cb = ta[d], tb[d]
                a_gap = (logit_of(la, ca) or float("nan")) - (logit_of(la, cb) if logit_of(la, cb) is not None else float("nan"))
                b_gap = (logit_of(lb, ca) if logit_of(lb, ca) is not None else float("nan")) - (logit_of(lb, cb) or float("nan"))
                row.update({"margin_a": ma, "margin_b": mb, "gap_a": a_gap, "gap_b": b_gap, "top_a": la["top"][:2], "top_b": lb["top"][:2]})
        rows.append(row)
    parted = [r for r in rows if r["first_diff"] is not None]
    with_m = [r for r in parted if "margin_a" in r]
    lines = [f"## {a.label}", "",
             f"{len(rows)} tasks; {len(rows) - len(parted)} identical to the last token, {len(parted)} part "
             f"({len(with_m)} with logits at the first differing token)."]
    if parted:
        fd = [r["first_diff"] for r in parted]
        lines.append(f"First differing token index: median {statistics.median(fd):.0f}, min {min(fd)}, max {max(fd)}; "
                     f"{sum(1 for x in fd if x < 32)} of {len(fd)} before token 32.")
    if with_m:
        mm = [min(r["margin_a"], r["margin_b"]) for r in with_m]
        gaps = [abs(r["gap_a"] - r["gap_b"]) for r in with_m if r["gap_a"] == r["gap_a"] and r["gap_b"] == r["gap_b"]]
        lines += ["", "| margin (top-1 minus top-2 logit) at the first differing token | tasks |", "|---|---|"]
        for lim in (0.05, 0.1, 0.25, 0.5, 1.0, 2.0):
            lines.append(f"| smaller than {lim} in at least one run | {sum(1 for m in mm if m < lim)} of {len(mm)} |")
        lines.append(f"\nmedian margin (smaller of the two runs) {statistics.median(mm):.3f}; "
                     f"the two runs' logit gap between the same two tokens differs by median {statistics.median(gaps):.3f} "
                     f"(max {max(gaps):.3f}) - the logit noise between the two arithmetic paths at those positions."
                     if gaps else "")
    lines += ["", "| task | first diff | margin A | margin B | gap A | gap B |", "|---|---|---|---|---|---|"]
    for r in parted:
        lines.append(f"| {r['id']} | {r['first_diff']} | " + " | ".join(f"{r[k]:.3f}" if k in r else "-" for k in ("margin_a", "margin_b", "gap_a", "gap_b")) + " |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.md:
        a.md.write_text(text, encoding="utf-8")
    if a.json:
        a.json.write_text(json.dumps({"label": a.label, "rows": rows}, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
