"""Turn ``scripts/maya_probe.py`` run files into per-run records, per-condition summaries and token-stream checks."""
from __future__ import annotations

from typing import Dict, List, Optional

from . import probe, stats

METRICS = ("decode_tok_s", "decode_ms_tok", "ttft_chat_ms", "prefill_2048", "prefill_8192", "ttft_8192_ms",
           "disk_ms_tok", "disk_waits_tok", "disk_ms_per_wait", "disk_share", "vram_hit_pct", "ssd_read_gbs",
           "spec_accept", "ram_tier_gb", "load_s", "min_phys_avail_gb", "min_commit_avail_gb", "max_commit_used_pct",
           "max_vram_mib")


def _med(xs: List[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return stats.median(xs) if xs else None


def run_record(run: Dict[str, object], cond: str, rnd: int) -> Dict[str, object]:
    """One ``maya_probe`` JSON -> flat metrics. Chat requests give decode/TTFT/disk numbers (medians over the prompts)."""
    reqs: List[Dict[str, object]] = run["requests"]  # type: ignore[assignment]
    chat = [r for r in reqs if str(r["label"]).startswith("chat:")]
    ms = [r["metrics"] for r in chat]  # type: ignore[index]
    es = [r.get("engine_stat") or {} for r in chat]
    rec: Dict[str, object] = {
        "cond": cond, "round": rnd,
        "decode_tok_s": _med([m.get("decode_tok_s") for m in ms]),
        "decode_ms_tok": _med([m.get("decode_ms_tok") for m in ms]),
        "ttft_chat_ms": _med([m.get("ttft_ms") for m in ms]),
        "spec_accept": _med([m.get("spec_accept") for m in ms]),
        "disk_ms_tok": _med([e.get("disk_ms_tok") for e in es]),
        "disk_waits_tok": _med([e.get("disk_waits_tok") for e in es]),
        "disk_ms_per_wait": _med([e.get("disk_ms_per_wait") for e in es]),
        "disk_share": _med([e.get("disk_share") for e in es]),
        "vram_hit_pct": _med([e.get("vram_hit_pct") for e in es]),
        "ssd_read_gbs": _med([r.get("ssd_read_gbs") for r in chat]),
        "ram_tier_gb": run.get("ram_tier_gb"), "load_s": run.get("load_s"),
    }
    for n in (2048, 8192):
        pr = [r for r in reqs if r["label"] == f"prefill:{n}"]
        rec[f"prefill_{n}"] = pr[0]["metrics"].get("prompt_tok_s") if pr else None  # type: ignore[index,union-attr]
    p8 = [r for r in reqs if r["label"] == "prefill:8192"]
    rec["ttft_8192_ms"] = p8[0]["metrics"].get("ttft_ms") if p8 else None  # type: ignore[index,union-attr]
    mem: Dict[str, float] = run.get("memory") or {}  # type: ignore[assignment]
    for k in ("min_phys_avail_gb", "min_commit_avail_gb", "max_commit_used_pct", "max_vram_mib"):
        rec[k] = mem.get(k)
    return rec


def token_streams(run: Dict[str, object]) -> Dict[str, List[int]]:
    return {str(r["label"]): list(r["tokens"]) for r in run["requests"]  # type: ignore[union-attr,index]
            if str(r["label"]).startswith(("chat:", "prefill:"))}


def summarize(records: List[Dict[str, object]], baseline: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    by: Dict[str, List[Dict[str, object]]] = {}
    for r in records:
        by.setdefault(str(r["cond"]), []).append(r)
    if baseline not in by:
        raise KeyError(baseline)

    def vals(c: str, m: str) -> List[float]:
        return [float(r[m]) for r in by[c] if r.get(m) is not None]  # type: ignore[arg-type]

    out: Dict[str, Dict[str, Dict[str, float]]] = {c: {} for c in by}
    for c in by:
        for m in METRICS:
            v = vals(c, m)
            if v:
                out[c][m] = stats.summarize(v)
    for c in by:
        for m, s in out[c].items():
            b = out[baseline].get(m)
            if c != baseline and b and b["median"]:
                s["pct_vs_baseline"] = stats.pct_change(b["median"], s["median"])
                s["above_noise"] = float(stats.noise_exceeded(vals(baseline, m), vals(c, m)))
    return out


def stream_report(streams: Dict[str, Dict[str, Dict[str, List[int]]]], ref_cond: str) -> Dict[str, Dict[str, object]]:
    """streams[cond][round_key] = {label: tokens}. Reference = ref_cond's first round.

    Per condition: how many runs matched the reference on every prompt, and the earliest divergence seen.
    """
    ref_runs = streams[ref_cond]
    ref = ref_runs[sorted(ref_runs)[0]]
    rep: Dict[str, Dict[str, object]] = {}
    for cond, runs in streams.items():
        n_ident, earliest, bad_labels = 0, None, set()
        for key in sorted(runs):
            cmp = probe.compare_streams(ref, runs[key])
            if probe.all_identical(cmp):
                n_ident += 1
            for label, v in cmp.items():
                if not v["identical"]:
                    bad_labels.add(label)
                    d = v["first_divergence"]
                    if d is not None and (earliest is None or d < earliest):
                        earliest = d
        rep[cond] = {"runs": len(runs), "identical_to_reference": n_ident, "earliest_divergence_token": earliest,
                     "diverging_prompts": sorted(bad_labels)}
    return rep


def markdown(summary: Dict[str, Dict[str, Dict[str, float]]], baseline: str, report: Dict[str, Dict[str, object]]) -> str:
    conds = list(summary)
    lines = ["| metric | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
    for m in METRICS:
        if not any(m in summary[c] for c in conds):
            continue
        cells = []
        for c in conds:
            s = summary[c].get(m)
            if not s:
                cells.append("n/a")
                continue
            t = f"{s['median']:.2f} ({s['min']:.2f}-{s['max']:.2f})"
            if c != baseline and "pct_vs_baseline" in s:
                t += f" **{s['pct_vs_baseline']:+.1f}%**" + ("" if s.get("above_noise") else " ~noise")
            cells.append(t)
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    lines += ["", "Token streams vs the first run of the baseline (all prompts, greedy):", "",
              "| condition | runs | identical | earliest divergence (token) | diverging prompts |", "|---|---|---|---|---|"]
    for c, r in report.items():
        lines.append(f"| {c} | {r['runs']} | {r['identical_to_reference']} | {r['earliest_divergence_token']} | "
                     f"{', '.join(r['diverging_prompts']) or '-'} |")
    return "\n".join(lines) + "\n"
