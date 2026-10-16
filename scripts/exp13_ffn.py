#!/usr/bin/env python3
"""Layer by layer, how much two engine runs' FFN outputs differ (dev engine: STRATA_GLM_DUMP_FFN records {int32 layer, float x[E],
float ffn[E]} for the first layer calls; optionally the matching STRATA_GLM_ROUTE_LOG files for the CPU-lane masks).

  python scripts/exp13_ffn.py a.ffn b.ffn --embd 6144 [--route-a route-a.0 --route-b route-b.0] [--calls 3]

Per layer call: relative L2 difference of the FFN input x (what the layer was given) and of its output; with route logs also how many
experts each run sent to the CPU lane in that layer. The first layer whose INPUT differs is where an earlier layer's output
already differed; the size of the OUTPUT difference in a layer whose input is identical is that layer's own arithmetic difference.
Standard library + struct only.
"""
from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path


def load(path: Path, E: int):
    data = path.read_bytes()
    rec = 4 + 8 * E
    out = []
    for o in range(0, len(data) - rec + 1, rec):
        il = struct.unpack_from("<i", data, o)[0]
        x = struct.unpack_from(f"<{E}f", data, o + 4)
        f = struct.unpack_from(f"<{E}f", data, o + 4 + 4 * E)
        out.append((il, x, f))
    return out


def rel(a, b):
    num = math.fsum((p - q) ** 2 for p, q in zip(a, b))
    den = math.fsum(q * q for q in b)
    return math.sqrt(num / den) if den else float("nan")


def masks(path: Path):
    res = []
    for line in path.read_text(encoding="utf-8").splitlines():
        head = line.split("|")[0].split()
        if len(head) < 12:   # (a line cut short at the end of a file being written)
            continue
        res.append((int(head[0]), int(head[11])))   # layer, cpu mask (bits over the 8 routed experts)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--embd", type=int, default=6144)
    ap.add_argument("--route-a", type=Path)
    ap.add_argument("--route-b", type=Path)
    ap.add_argument("--calls", type=int, default=3)
    a = ap.parse_args(argv)
    A, B = load(a.a, a.embd), load(a.b, a.embd)
    ma = masks(a.route_a) if a.route_a else None
    mb = masks(a.route_b) if a.route_b else None
    print("| call | layer | rel. L2 of x | rel. L2 of FFN output | CPU experts A / B |")
    print("|---|---|---|---|---|")
    n = min(len(A), len(B))
    layers_per_call = 42
    for k in range(min(n, a.calls * layers_per_call)):
        (la, xa, fa), (lb, xb, fb) = A[k], B[k]
        c = ""
        if ma and mb:
            c = f"{bin(ma[k][1]).count('1')} / {bin(mb[k][1]).count('1')}"
        print(f"| {k // layers_per_call} | {la} | {rel(xa, xb):.2e} | {rel(fa, fb):.2e} | {c} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
