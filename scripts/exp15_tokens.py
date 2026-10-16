#!/usr/bin/env python3
"""Per-token decomposition of an Nsight Systems capture of the engine's decode: tokens are delimited by argmax_kernel; for every
token the device time by kernel group (kernel durations summed per stream, so concurrent streams add up) and the span.
  python scripts/exp15_tokens.py E:\oss\maya-logs\nsys-t42.sqlite [--skip N]
Groups: moe_wait (the device spins until the host has read missing experts from the SSD), moe_fetch (PCIe pull of RAM-tier experts),
moe_cpu_wait (spin until the CPU lane answers), experts (gate/up, down), dense (mv_kernel*, hc3, headwise, mla/kda/dsa), other."""
import argparse
import sqlite3
import statistics

ap = argparse.ArgumentParser()
ap.add_argument("sqlite")
ap.add_argument("--skip", type=int, default=0, help="tokens to skip at the start of the window")
a = ap.parse_args()
db = sqlite3.connect(a.sqlite)
names = dict(db.execute("select id, value from StringIds"))
rows = db.execute("select start, end, demangledName, streamId from CUPTI_ACTIVITY_KIND_KERNEL order by start").fetchall()


def group(n):
    if "moe_wait_kernel" in n: return "moe_wait"
    if "moe_fetch_kernel" in n: return "moe_fetch"
    if "moe_cpu_wait_kernel" in n: return "moe_cpu_wait"
    if "moe_gate_up_kernel" in n or "moe_down_kernel" in n: return "experts"
    if "moe_route_kernel" in n or "tab_update" in n or "moe_prefetch" in n: return "route"
    if any(k in n for k in ("mv_kernel", "hc3_kernel", "hc_post", "headwise", "mla_", "kda_", "dsa_", "embed_streams", "head_prep", "swiglu_q8", "rms")): return "dense"
    return "other"


arg = [r for r in rows if "argmax_kernel" in names[r[2]]]
print(f"{len(rows)} kernels, {len(arg)} tokens (argmax)")
res = []
for i in range(a.skip, len(arg) - 1):
    t0, t1 = arg[i][1], arg[i + 1][1]
    g = {}
    for s, e, n, st in rows:
        if s >= t0 and e <= t1:
            k = group(names[n])
            g[k] = g.get(k, 0) + (e - s)
    res.append((t1 - t0, g))
span = [r[0] / 1e6 for r in res]
print(f"token span ms: median {statistics.median(span):.1f}  min {min(span):.1f}  max {max(span):.1f}  (n={len(span)})")
keys = ["moe_wait", "moe_fetch", "moe_cpu_wait", "experts", "route", "dense", "other"]
print("median device ms per token by group (and as % of the median span):")
for k in keys:
    v = [r[1].get(k, 0) / 1e6 for r in res]
    print(f"  {k:13s} {statistics.median(v):7.2f} ms  {100 * statistics.median(v) / statistics.median(span):5.1f}%")
busy = [sum(r[1].values()) / 1e6 for r in res]
print(f"  sum of kernel time {statistics.median(busy):.1f} ms of a {statistics.median(span):.1f} ms span")
# the last third of the window, where the decode has settled
tail = res[len(res) * 2 // 3:]
print(f"last third: span median {statistics.median([r[0] / 1e6 for r in tail]):.1f} ms, " + ", ".join(f"{k} {statistics.median([r[1].get(k, 0) / 1e6 for r in tail]):.1f}" for k in keys))
