"""Parsers for Project Maya's text outputs (``maya-bench.txt`` and the engine's ``glm stat:`` lines).

The formats are the ones Project Maya v1.1.x writes (``maya.py: bench()`` and ``src/program/generate.cpp``).
Parsing is key by key, so a field that a future version adds or drops does not break the others.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

_NUM = r"(-?\d+(?:\.\d+)?)"

# "glm stat: decode 247.44 ms/tok (4.04 tok/s) | vram hit 64.27% | ram fetches 82.00/tok | disk 12.85 reads/tok in
#  15.06 waits/tok, 184.31 ms/tok | promotions 0.1/tok | cpu lane 3.2/tok in 11.0 ms/tok | prompt 1.2 ms/tok |
#  vram 100/200 ram 10/20"
_STAT_FIELDS = {
    "decode_ms_tok": re.compile(r"decode " + _NUM + r" ms/tok"),
    "decode_tok_s": re.compile(r"\(" + _NUM + r" tok/s\)"),
    "vram_hit_pct": re.compile(r"vram hit " + _NUM + r"%"),
    "ram_fetches_tok": re.compile(r"ram fetches " + _NUM + r"/tok"),
    "disk_reads_tok": re.compile(r"disk " + _NUM + r" reads/tok"),
    "disk_waits_tok": re.compile(r" in " + _NUM + r" waits/tok"),
    "disk_ms_tok": re.compile(r"waits/tok, " + _NUM + r" ms/tok"),
    "promotions_tok": re.compile(r"promotions " + _NUM + r"/tok"),
    "cpu_lane_tok": re.compile(r"cpu lane " + _NUM + r"/tok"),
    "cpu_lane_ms_tok": re.compile(r"cpu lane " + _NUM + r"/tok in " + _NUM + r" ms/tok"),
    "prompt_ms_tok": re.compile(r"prompt " + _NUM + r" ms/tok"),
}
_STAT_POOL = re.compile(r"vram (\d+)/(\d+) ram (\d+)/(\d+)")


def parse_stat_line(line: str) -> Optional[Dict[str, float]]:
    """One ``glm stat:`` line -> {field: value}; None if it is not one."""
    if "glm stat:" not in line:
        return None
    out: Dict[str, float] = {}
    for key, rx in _STAT_FIELDS.items():
        m = rx.search(line)
        if m:
            out[key] = float(m.group(m.lastindex))   # the last group: cpu_lane_ms_tok is the "in ... ms/tok" one
    m = _STAT_POOL.search(line)
    if m:
        out["vram_used"], out["vram_slots"], out["ram_used"], out["ram_slots"] = (float(g) for g in m.groups())
    if "disk_reads_tok" in out and out.get("disk_waits_tok", 0) > 0 and "disk_ms_tok" in out:
        out["disk_ms_per_wait"] = out["disk_ms_tok"] / out["disk_waits_tok"]
    if "decode_ms_tok" in out and out.get("disk_ms_tok") is not None and out["decode_ms_tok"] > 0:
        out["disk_share"] = out["disk_ms_tok"] / out["decode_ms_tok"]
    return out or None


_DECODE_LINE = re.compile(r"^\s+" + _NUM + r" tokens/s\s+(.*\S)\s*$")
_PREFILL_LINE = re.compile(r"^prefill \(reading the prompt\): " + _NUM + r" tokens/s, (\d+) tokens")
_HEADER = re.compile(r"^Project Maya v(\S+) benchmark, (.+)$")
_SETUP = re.compile(r"^setup: (\S+), context (\d+)")


def parse_bench(text: str) -> Dict[str, object]:
    """``maya-bench.txt`` -> {version, when, context, decode: [tok/s], prefill: {tokens: tok/s}, stats: [stat dicts]}."""
    res: Dict[str, object] = {"version": None, "when": None, "context": None, "decode": [], "prefill": {}, "stats": []}
    decode: List[float] = []
    prefill: Dict[int, float] = {}
    stats: List[Dict[str, float]] = []
    in_engine = False
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if (m := _HEADER.match(line)):
            res["version"], res["when"] = m.group(1), m.group(2)
        elif (m := _SETUP.match(line)):
            res["context"] = int(m.group(2))
        elif line.startswith("engine lines:"):
            in_engine = True
        elif in_engine:
            s = parse_stat_line(line)
            if s:
                stats.append(s)
        elif (m := _PREFILL_LINE.match(line)):
            prefill[int(m.group(2))] = float(m.group(1))
        elif (m := _DECODE_LINE.match(line)):
            decode.append(float(m.group(1)))
    res["decode"], res["prefill"], res["stats"] = decode, prefill, stats
    return res
