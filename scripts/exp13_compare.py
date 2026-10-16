#!/usr/bin/env python3
"""Bitwise comparison of logit traces / route logs of the exp13 determinism runs (dev engine: STRATA_GLM_LOGIT_TRACE, ROUTE_LOG).
  python scripts/exp13_compare.py <dir> name1 name2 ...   (files <name>.trace.jsonl, route-<name>.0)
Per pair: positions compared, the first position whose logits differ at all, the first routing flip, the first greedy-token
difference, and the largest |difference| of the top-1 logit before that token difference. Standard library only."""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exp9_routes as R  # noqa: E402

d = Path(sys.argv[1])
names = [n for n in sys.argv[2:] if (d / f"{n}.trace.jsonl").exists() and (d / f"route-{n}.0").exists()]
T = {n: R.load_trace(d / f"{n}.trace.jsonl") for n in names}
Rt = {n: R.load_routes(d / f"route-{n}.0") for n in names}
print("| pair | positions | first logit difference | first routing flip | first greedy-token difference | max abs top-1 logit difference before it |")
print("|---|---|---|---|---|---|")
for a, b in itertools.combinations(names, 2):
    n = min(len(T[a]), len(T[b]))
    fd = next((k for k in range(n) if T[a][k]["top"] != T[b][k]["top"] or T[a][k]["tok"] != T[b][k]["tok"]), None)
    fr = next((k for k in range(min(len(Rt[a]), len(Rt[b]), n)) if any(ia != ib for (la, ia), (lb, ib) in zip(Rt[a][k], Rt[b][k]))), None)
    tk = next((k for k in range(n) if T[a][k]["tok"] != T[b][k]["tok"]), None)
    stop = n if tk is None else tk
    dl = [abs(T[a][k]["top"][0][1] - T[b][k]["top"][0][1]) for k in range(stop) if T[a][k]["top"][0][0] == T[b][k]["top"][0][0]]
    print(f"| {a} vs {b} | {n} | {fd if fd is not None else 'none (bit-identical)'} | {fr if fr is not None else 'none'} | {tk if tk is not None else 'none'} | {('%.3g' % max(dl)) if dl else '-'} |")
