#!/usr/bin/env python3
"""One engine session of Project Maya, measured end to end: token ids, TTFT, speed, SSD wait share, SSD read bandwidth,
RAM / commit / VRAM headroom. Meant to be run by ``scripts/maya_tier_sweep.py`` with Maya's own venv Python
(``<maya>/.venv/Scripts/python.exe``): it imports Maya's ``serve.server`` to build the engine command and environment the
way ``--bench`` and the dashboard do, and needs ``psutil`` (part of Maya's venv).

  <maya>\\.venv\\Scripts\\python.exe scripts\\maya_probe.py --maya-dir <maya> --config maya-xxx.json \\
      --env STRATA_GLM_RAM_GB=38 --label t38 --out run.json

Maya must be stopped (it needs the GPU). Everything is greedy (temperature=0); the prompts are fixed in this file.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import abreport, mayaparse, probe  # noqa: E402

CHAT_PROMPTS = {
    "csv": "Write a Python function that parses a CSV file into a list of dictionaries, with type hints and a docstring.",
    "photosynthesis": "Explain how photosynthesis works, step by step, for a high-school student.",
    "ball": "Write a complete HTML page with a canvas that draws a bouncing ball animation in JavaScript.",
    "sql": "Explain the difference between an inner join and a left join in SQL, with a short example of each.",
    "history": "Summarise the main causes of the French Revolution in about 200 words.",
    "rust": "Write a Rust function that returns the n-th Fibonacci number without recursion, and explain its complexity.",
}
N_NEW = 256
LONG_NEW = 16
LONG_LENS = (2048, 8192)


class MemStatus(ctypes.Structure):
    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]


def mem_snapshot() -> dict:
    if sys.platform != "win32":
        import psutil
        vm = psutil.virtual_memory()
        return {"phys_avail": vm.available, "commit_limit": 0, "commit_avail": 0}
    ms = MemStatus()
    ms.dwLength = ctypes.sizeof(ms)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
    return {"phys_avail": ms.ullAvailPhys, "commit_limit": ms.ullTotalPageFile, "commit_avail": ms.ullAvailPageFile}


def vram_used_mib() -> int:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        return max(int(x) for x in out.split())
    except Exception:
        return -1


class Sampler(threading.Thread):
    """Samples free RAM, commit headroom and VRAM in use while the engine runs."""

    def __init__(self, period: float = 1.0):
        super().__init__(daemon=True)
        self.period, self.stop_flag, self.samples = period, threading.Event(), []

    def run(self):
        while not self.stop_flag.is_set():
            s = mem_snapshot()
            s["vram_mib"] = vram_used_mib()
            s["t"] = time.time()
            self.samples.append(s)
            self.stop_flag.wait(self.period)

    def summary(self) -> dict:
        if not self.samples:
            return {}
        s = self.samples
        out = {"n": len(s), "min_phys_avail_gb": min(x["phys_avail"] for x in s) / 2**30,
               "max_vram_mib": max(x["vram_mib"] for x in s)}
        if s[0]["commit_limit"]:
            out["commit_limit_gb"] = s[0]["commit_limit"] / 2**30
            out["min_commit_avail_gb"] = min(x["commit_avail"] for x in s) / 2**30
            out["max_commit_used_pct"] = max(probe.commit_used_pct(x["commit_limit"], x["commit_avail"]) for x in s)
        return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--maya-dir", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--log", type=Path, help="where to keep the engine's stderr (default: next to --out)")
    ap.add_argument("--no-long", action="store_true", help="skip the 2K/8K prompts")
    a = ap.parse_args(argv)

    import psutil
    root = a.maya_dir.resolve()
    sys.path.insert(0, str(root))
    import serve.server as SV                      # the server's own engine command and environment
    import strata_tokenizer as ST

    cfg = json.loads((a.config if a.config.is_absolute() else root / a.config).read_text(encoding="utf-8"))
    cfg.setdefault("env", {})
    for kv in a.env:
        k, v = kv.split("=", 1)
        cfg["env"][k] = v
    args = cfg.get("args") or []
    pack = Path(args[args.index("--glm-pack") + 1])
    tok = ST.Tokenizer.from_dir(Path(cfg.get("tokenizer") or pack / "tokenizer"))
    chat = lambda q: tok.encode("[gMASK]<sop><|user|>\n" + q + "<|assistant|>\n</think>", parse_special=True)
    text = "\n\n".join(p.read_text(encoding="utf-8", errors="replace")
                       for p in [root / "README.md"] + sorted((root / "docs").glob("*.md")) +
                       sorted((root / "bench" / "results").glob("*.md")) if p.exists())
    doc = tok.encode(text)

    log_path = a.log or a.out.with_suffix(".engine.log")
    sampler = Sampler()
    t_start = time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        sampler.start()
        p = subprocess.Popen([cfg["exe"], "--serve"] + SV.engine_args(cfg), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=log, text=True, env=SV.child_env(cfg), cwd=cfg.get("cwd") or str(root), bufsize=1)
        while True:
            line = p.stdout.readline()
            if not line:
                raise SystemExit(f"the engine stopped while loading (exit code {p.wait(timeout=30)}); see {log_path}")
            if line.startswith("READY"):
                break
        load_s = time.time() - t_start

        def disk_reads() -> dict:
            return {k: v.read_bytes for k, v in psutil.disk_io_counters(perdisk=True).items()}

        requests = []

        def gen(label: str, ids, n_new: int):
            d0, t0 = disk_reads(), time.time()
            p.stdin.write(f"GEN {n_new} temperature=0 " + ",".join(map(str, ids)) + "\n")
            p.stdin.flush()
            toks = []
            while True:
                line = p.stdout.readline()
                if not line:
                    raise SystemExit(f"the engine stopped during {label}; see {log_path}")
                if line.startswith("T "):
                    toks.append(int(line.split()[1]))
                elif line.startswith("DONE") or line.startswith("ERR"):
                    break
            t1, d1 = time.time(), disk_reads()
            done = probe.parse_done(line)
            if done is None:
                raise SystemExit(f"{label}: {line.strip()}")
            requests.append({"label": label, "tokens": toks, "done": done, "metrics": probe.request_metrics(done),
                             "wall_s": t1 - t0, "disk_read_bytes": {k: d1[k] - d0.get(k, d1[k]) for k in d1}})

        gen("warmup", chat("Say hello in five languages."), 64)
        warm = len(requests)
        for name, q in CHAT_PROMPTS.items():
            gen("chat:" + name, chat(q), N_NEW)
        if not a.no_long:
            gen("warmup-long", doc[-LONG_LENS[0]:], 1)
            for i, n in enumerate(LONG_LENS):
                gen(f"prefill:{n}", doc[i * 997:i * 997 + n], LONG_NEW)
        p.stdin.write("QUIT\n")
        p.stdin.flush()
        try:
            p.wait(timeout=180)
        except subprocess.TimeoutExpired:
            p.kill()
    sampler.stop_flag.set()
    sampler.join(timeout=5)

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    stats = [mayaparse.parse_stat_line(l) for l in log_text.splitlines()
             if "glm stat: decode" in l and "(prompt only)" not in l]
    stats = [s for s in stats if s]
    # one `glm stat:` line per request that produced tokens, in request order
    aligned = len(stats) == len(requests)
    if aligned:
        for r, s in zip(requests, stats):
            r["engine_stat"] = s
    disks = [r["disk_read_bytes"] for r in requests[warm:]]
    busiest = max((k for k in (disks[0] if disks else {})), key=lambda k: sum(d.get(k, 0) for d in disks), default=None)
    for r in requests:
        r["ssd_read_gbs"] = probe.read_bandwidth_gbs(0, r["disk_read_bytes"].get(busiest, 0), r["wall_s"]) if busiest else None
    out = {"label": a.label, "env": {k: v for k, v in cfg["env"].items()}, "load_s": load_s,
           "ram_tier_gb": abreport.parse_ram_tier_gb(log_text), "stat_lines_aligned": aligned,
           "ssd_disk": busiest, "memory": sampler.summary(), "requests": requests,
           "log_tier_lines": [l for l in log_text.splitlines() if l.startswith("glm fast:") and ("RAM tier" in l or "commit" in l.lower() or "pinning" in l)]}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1), encoding="utf-8")
    ok = [r for r in requests[warm:] if r["label"].startswith("chat:")]
    print(f"{a.label}: tier {out['ram_tier_gb']} GB, load {load_s:.0f}s, decode "
          + ", ".join(f"{r['metrics'].get('decode_tok_s', 0):.1f}" for r in ok) + " tok/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
