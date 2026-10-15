"""Pure helpers for talking to Project Maya's engine ``--serve`` protocol and for comparing token streams.

Protocol (Maya v1.1.x, src/program/generate.cpp), one request per line on stdin:
    GEN <n_new> temperature=0 <comma separated token ids>
and on stdout, per generated token ``T <id>``, then
    DONE <produced> <prompt_len> <prompt_ms> <decode_ms> <finish> <spec_hits> <spec_steps> <reuse> <vram_hits> <lookups>

Definitions used in this repository (see docs/methodology.md):
  * decode ms/token  = decode_ms / produced        (per *produced* token: with MTP drafting one engine step can
                                                    produce several tokens; both numerator and denominator count
                                                    produced tokens)
  * TTFT             = prompt_ms of a request whose reply is read from the first token (the engine's prompt phase,
                       including the first token's logits); queueing in the server is not included
  * SSD wait share   = disk_ms_tok / decode_ms_tok from the same ``glm stat:`` line: the service thread's wall time spent
                       resolving disk misses (from detecting the miss to publishing the response, which the GPU
                       waits for) over the decode phase's wall time. Per-token normalisation cancels, so MTP does not
                       change the ratio.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

DONE_FIELDS = ("produced", "prompt_len", "prompt_ms", "decode_ms", "finish", "spec_hits", "spec_steps", "reuse",
               "vram_hits", "lookups")


def parse_done(line: str) -> Optional[Dict[str, object]]:
    """``DONE ...`` line -> dict (None for ``ERR`` or anything else)."""
    parts = line.split()
    if not parts or parts[0] != "DONE" or len(parts) < 6:
        return None
    vals = parts[1:]
    out: Dict[str, object] = {}
    for key, raw in zip(DONE_FIELDS, vals):
        out[key] = raw if key == "finish" else float(raw)
    for key in ("produced", "prompt_len", "spec_hits", "spec_steps", "reuse", "vram_hits", "lookups"):
        if key in out:
            out[key] = int(out[key])   # type: ignore[arg-type]
    return out


def request_metrics(done: Dict[str, object]) -> Dict[str, float]:
    produced = int(done["produced"])  # type: ignore[arg-type]
    decode_ms = float(done["decode_ms"])  # type: ignore[arg-type]
    prompt_ms = float(done["prompt_ms"])  # type: ignore[arg-type]
    m: Dict[str, float] = {"ttft_ms": prompt_ms, "prompt_tok_s": 1000.0 * int(done["prompt_len"]) / prompt_ms if prompt_ms > 0 else 0.0}  # type: ignore[arg-type]
    if produced > 0 and decode_ms > 0:
        m["decode_tok_s"] = 1000.0 * produced / decode_ms
        m["decode_ms_tok"] = decode_ms / produced
    steps = int(done.get("spec_steps", 0))  # type: ignore[arg-type]
    if steps > 0:
        m["spec_accept"] = int(done.get("spec_hits", 0)) / steps  # type: ignore[arg-type]
    return m


def first_divergence(a: Sequence[int], b: Sequence[int]) -> Optional[int]:
    """Index of the first position where the streams differ; None when identical (same length too)."""
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def compare_streams(ref: Dict[str, List[int]], other: Dict[str, List[int]]) -> Dict[str, Dict[str, object]]:
    """Per prompt label: identical?, first divergence index, lengths."""
    res: Dict[str, Dict[str, object]] = {}
    for label, r in ref.items():
        o = other.get(label)
        if o is None:
            res[label] = {"identical": False, "first_divergence": None, "missing": True, "len_ref": len(r), "len_other": 0}
            continue
        d = first_divergence(r, o)
        res[label] = {"identical": d is None, "first_divergence": d, "len_ref": len(r), "len_other": len(o)}
    return res


def all_identical(cmp: Dict[str, Dict[str, object]]) -> bool:
    return bool(cmp) and all(v["identical"] for v in cmp.values())


def read_bandwidth_gbs(read_bytes_start: int, read_bytes_end: int, seconds: float) -> float:
    """GB/s (10^9 bytes) of a disk's read counter over an interval."""
    return (read_bytes_end - read_bytes_start) / 1e9 / seconds if seconds > 0 else 0.0


def pick_busiest_disk(before: Dict[str, int], after: Dict[str, int]) -> Optional[str]:
    """Name of the disk whose read-byte counter grew most between two snapshots (the one holding the model)."""
    best, best_d = None, 0
    for name, b in after.items():
        d = b - before.get(name, b)
        if d > best_d:
            best, best_d = name, d
    return best


def commit_used_pct(limit_bytes: int, avail_bytes: int) -> float:
    return 100.0 * (limit_bytes - avail_bytes) / limit_bytes if limit_bytes > 0 else 0.0
