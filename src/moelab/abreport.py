"""Aggregate interleaved A/B benchmark runs into a per-condition summary and a Markdown table."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from . import stats

_TIER = re.compile(r"glm fast: CUDA(\d+) RAM tier ([\d.]+) GB pinned, (\d+) slots")


def parse_ram_tier_gb(engine_log: str) -> Optional[float]:
    """Total pinned RAM tier (GB) over all GPUs, from the engine log's start-up lines; None if absent.

    Two conditions are only comparable when the tier was the same size (the disk-read share depends on it).
    """
    sizes = {int(m.group(1)): float(m.group(2)) for m in _TIER.finditer(engine_log)}
    return sum(sizes.values()) if sizes else None


def run_record(cond: str, rnd: int, bench: Dict[str, object], tier_gb: Optional[float]) -> Dict[str, object]:
    """One benchmark run -> a flat record (decode = median of its answers; engine-stat fields = median of its lines)."""
    decode: List[float] = list(bench["decode"])        # type: ignore[arg-type]
    rec: Dict[str, object] = {
        "cond": cond, "round": rnd, "ram_tier_gb": tier_gb,
        "decode_tok_s": stats.median(decode) if decode else None,
        "prefill": dict(bench["prefill"]),             # type: ignore[arg-type]
    }
    keys = ("disk_ms_tok", "disk_waits_tok", "disk_reads_tok", "disk_ms_per_wait", "disk_share", "vram_hit_pct",
            "ram_fetches_tok", "cpu_lane_ms_tok")
    for k in keys:
        vals = [s[k] for s in bench["stats"] if k in s]    # type: ignore[union-attr]
        rec[k] = stats.median(vals) if vals else None
    return rec


def summarize_runs(runs: List[Dict[str, object]], baseline: str) -> Dict[str, Dict[str, object]]:
    """{cond: {metric: summary-dict}} plus pct change of each metric's median against `baseline`."""
    conds: Dict[str, List[Dict[str, object]]] = {}
    for r in runs:
        conds.setdefault(str(r["cond"]), []).append(r)
    if baseline not in conds:
        raise KeyError(f"baseline condition {baseline!r} has no runs")

    def collect(rs: List[Dict[str, object]], key: str) -> List[float]:
        if key.startswith("prefill_"):
            n = int(key.split("_", 1)[1])
            return [float(r["prefill"][n]) for r in rs if n in r["prefill"]]   # type: ignore[index]
        return [float(r[key]) for r in rs if r.get(key) is not None]           # type: ignore[arg-type]

    sizes = sorted({n for r in runs for n in r["prefill"]})                     # type: ignore[union-attr]
    metrics = ["decode_tok_s"] + [f"prefill_{n}" for n in sizes] + ["disk_ms_tok", "disk_waits_tok", "disk_ms_per_wait",
                                                                    "disk_share", "vram_hit_pct", "ram_tier_gb"]
    out: Dict[str, Dict[str, object]] = {}
    for c, rs in conds.items():
        out[c] = {}
        for m in metrics:
            vals = collect(rs, m)
            if vals:
                out[c][m] = stats.summarize(vals)
    for c in out:
        for m, s in out[c].items():
            b = out[baseline].get(m)
            if b and b["median"]:                                               # type: ignore[index]
                s["pct_vs_baseline"] = stats.pct_change(b["median"], s["median"])   # type: ignore[index,arg-type]
                s["above_noise"] = float(stats.noise_exceeded(collect(conds[baseline], m), collect(conds[c], m)))
    return out


def tier_mismatch_warning(runs: List[Dict[str, object]], tolerance_gb: float = 1.0) -> Optional[str]:
    tiers = [float(r["ram_tier_gb"]) for r in runs if r.get("ram_tier_gb") is not None]   # type: ignore[arg-type]
    if len(tiers) >= 2 and max(tiers) - min(tiers) > tolerance_gb:
        return (f"RAM tier varied from {min(tiers):.1f} to {max(tiers):.1f} GB between runs: pin it "
                f"(STRATA_GLM_RAM_GB) or the comparison mixes tier size with the setting under test")
    return None


def markdown(summary: Dict[str, Dict[str, object]], baseline: str, runs: List[Dict[str, object]]) -> str:
    metrics: List[str] = []
    for c in summary:
        for m in summary[c]:
            if m not in metrics:
                metrics.append(m)
    lines = [f"| metric | " + " | ".join(summary) + " |", "|---|" + "---|" * len(summary)]
    for m in metrics:
        cells = []
        for c in summary:
            s = summary[c].get(m)
            if not s:
                cells.append("n/a")
                continue
            txt = f"{s['median']:.2f} (n={int(s['n'])}, {s['min']:.2f}-{s['max']:.2f})"
            if c != baseline and "pct_vs_baseline" in s:
                flag = "" if s.get("above_noise") else " ~noise"
                txt += f" **{s['pct_vs_baseline']:+.1f}%**{flag}"
            cells.append(txt)
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    warn = tier_mismatch_warning(runs)
    if warn:
        lines += ["", f"> WARNING: {warn}"]
    return "\n".join(lines) + "\n"
