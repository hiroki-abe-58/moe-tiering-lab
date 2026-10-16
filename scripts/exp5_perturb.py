#!/usr/bin/env python3
"""Does outside load change the generated tokens? One engine start per run, with or without a stress process alongside.

  <maya>\\.venv\\Scripts\\python.exe scripts\\exp5_perturb.py --maya-dir <maya> --config <cfg> --rounds 2 --out-dir results/phase3/exp5-determinism/perturb

Arms: idle / stressed, each with the CPU lane on and off (CPU plan fixed so the lane's own re-timing is not a variable).
The stress is CPU spinners (half of the logical CPUs) plus a reader streaming a large file from the same drive as the
experts (read-only, never written). Raw token ids: ``<arm>-r<N>.json`` (maya_probe format).
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import time
from pathlib import Path

STRESS = r'''
import os, sys, threading, time
dur = float(sys.argv[2]); path = sys.argv[1]; end = time.time() + dur
def spin():
    x = 0
    while time.time() < end:
        for _ in range(20000): x += 1
def reader():
    # unbuffered (FILE_FLAG_NO_BUFFERING): the OS file cache must not fill up with what this reads
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.restype = wintypes.HANDLE
    k.VirtualAlloc.restype = ctypes.c_void_p
    k.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
    k.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    h = k.CreateFileW(path, 0x80000000, 1, None, 3, 0x20000000 | 0x08000000, None)   # NO_BUFFERING | SEQUENTIAL_SCAN
    if h in (None, wintypes.HANDLE(-1).value):
        return
    n = 8 << 20
    buf = k.VirtualAlloc(None, n, 0x3000, 0x04)
    got = wintypes.DWORD(0)
    while time.time() < end:
        if not k.ReadFile(h, buf, n, ctypes.byref(got), None) or got.value == 0:
            k.SetFilePointerEx(h, ctypes.c_longlong(0), None, 0)
    k.CloseHandle(h)
ts = [threading.Thread(target=spin) for _ in range(max(2, (os.cpu_count() or 8) // 2))] + [threading.Thread(target=reader)]
[t.start() for t in ts]; [t.join() for t in ts]
'''


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maya-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--tier-gb", type=int, default=26)
    ap.add_argument("--plan", default="001122333", help="STRATA_GLM_CPU_PLAN, fixed in every arm")
    ap.add_argument("--stress-file", type=Path, required=True, help="a large existing file on the experts' drive (read only)")
    ap.add_argument("--out-dir", type=Path, required=True)
    a = ap.parse_args(argv)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    arms = {"idle": [], "stress": ["S"], "L0idle": ["L0"], "L0stress": ["L0", "S"]}
    order = []
    for r in range(a.rounds):
        names = list(arms)
        order += [(n, r) for n in (names if r % 2 == 0 else names[::-1])]
    probe = Path(__file__).with_name("maya_probe.py")
    for name, r in order:
        flags = arms[name]
        out = a.out_dir / f"{name}-r{r}.json"
        cmd = [sys.executable, str(probe), "--maya-dir", str(a.maya_dir), "--config", str(a.config), "--label", f"{name}-r{r}",
               "--out", str(out), "--no-long", "--env", f"STRATA_GLM_RAM_GB={a.tier_gb}", "--env", f"STRATA_GLM_CPU_PLAN={a.plan}"]
        if "L0" in flags:
            cmd += ["--env", "STRATA_GLM_CPU_LANE=0"]
        stress = None
        if "S" in flags:
            stress = subprocess.Popen([sys.executable, "-I", "-c", STRESS, str(a.stress_file), "1500"])
            time.sleep(3)
        print(f"{name} round {r} ...", flush=True)
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=1500)
        finally:
            if stress is not None:
                stress.kill()
        if p.returncode != 0:
            print(p.stdout[-800:], p.stderr[-800:])
            raise SystemExit(f"run failed: {name} {r}")
        print("   ", p.stdout.strip().splitlines()[-1], flush=True)
    # which runs produced identical tokens
    T = {}
    for name, r in order:
        j = json.loads((a.out_dir / f"{name}-r{r}.json").read_text(encoding="utf-8"))
        T[f"{name}-r{r}"] = tuple(tuple(q["tokens"]) for q in j["requests"] if q["label"].startswith("chat:"))
    classes, rows = {}, []
    for k, v in T.items():
        classes.setdefault(v, chr(65 + len(classes)))
        rows.append(f"{k}={classes[v]}")
    summary = {"runs_in_order": rows, "distinct_output_sets": len(classes)}
    (a.out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
