#!/usr/bin/env python3
"""Per-condition SSD numbers from a ``maya_tier_sweep.py`` run directory (``*-runs/<cond>-r<N>.json``).

  python scripts/io_analysis.py results/phase2/exp4-tier-sweep-runs

For each condition (median over the chat requests of every round): bytes per disk read, GB/s *while the service thread waits*
(bytes the drive delivered / the engine's disk-wait time), waits and reads per token, ms per wait, and how much of a token
is not disk wait. Bytes come from the OS counter of the busiest drive during each request, so they include anything else
that read from that drive meanwhile; ``disk_ms_tok`` is the engine's own ``glm stat:`` figure.
"""
from __future__ import annotations

import glob
import json
import re
import statistics as st
import sys
from collections import defaultdict


def main(argv=None) -> int:
    d = (argv or sys.argv[1:] or ["."])[0]
    rows = defaultdict(list)
    for f in sorted(glob.glob(d.rstrip("/\\") + "/*.json")):
        m = re.match(r"(.+)-r(\d+)\.json$", f.replace("\\", "/").split("/")[-1])
        if not m:
            continue
        run = json.load(open(f, encoding="utf-8"))
        disk = run.get("ssd_disk")
        for r in run["requests"]:
            s, n = r.get("engine_stat"), r["done"]["produced"]
            if not r["label"].startswith("chat:") or not s or not n or not disk:
                continue
            b, reads, wait_s = r["disk_read_bytes"].get(disk, 0), s["disk_reads_tok"] * n, s["disk_ms_tok"] * n / 1000.0
            if reads and wait_s:
                rows[m.group(1)].append((b / reads / 1e6, b / 1e9 / wait_s, s["disk_waits_tok"], s["disk_reads_tok"],
                                         s["disk_ms_per_wait"], s["decode_ms_tok"], s["disk_ms_tok"]))
    print("cond | MB/read | GB/s in waits | waits/tok | reads/wait | ms/wait | disk ms/tok | other ms/tok")
    for c, v in rows.items():
        md = lambda i: st.median(x[i] for x in v)
        print(f"{c} | {md(0):.2f} | {md(1):.2f} | {md(2):.1f} | {md(3) / md(2):.2f} | {md(4):.2f} | {md(6):.1f} | {md(5) - md(6):.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
