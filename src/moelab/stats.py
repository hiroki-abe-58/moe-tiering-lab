"""Small, dependency-free statistics for A/B benchmark rounds (medians and spread, not means)."""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence


def median(xs: Sequence[float]) -> float:
    s = sorted(xs)
    if not s:
        raise ValueError("median of an empty sequence")
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def mad(xs: Sequence[float]) -> float:
    """Median absolute deviation (unscaled)."""
    m = median(xs)
    return median([abs(x - m) for x in xs])


def quantile(xs: Sequence[float], q: float) -> float:
    """Linear-interpolated quantile, q in [0, 1]."""
    s = sorted(xs)
    if not s:
        raise ValueError("quantile of an empty sequence")
    pos = q * (len(s) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def summarize(xs: Sequence[float]) -> Dict[str, float]:
    return {"n": float(len(xs)), "median": median(xs), "min": min(xs), "max": max(xs), "mad": mad(xs),
            "iqr": quantile(xs, 0.75) - quantile(xs, 0.25)}


def pct_change(base: float, new: float) -> float:
    if base == 0:
        raise ZeroDivisionError("baseline is zero")
    return 100.0 * (new - base) / base


def interleave(conditions: Sequence[str], rounds: int) -> List[str]:
    """Run order that cancels drift: A B | B A | A B ... (each round reverses the previous one).

    Every condition runs once per round, so counts are equal; first/last positions alternate.
    """
    if rounds < 1 or not conditions:
        raise ValueError("need at least one condition and one round")
    order: List[str] = []
    cur = list(conditions)
    for _ in range(rounds):
        order.extend(cur)
        cur = cur[::-1]
    return order


def noise_exceeded(base: Iterable[float], new: Iterable[float]) -> bool:
    """True when the medians differ by more than the larger of the two MADs (a conservative 'is it above noise')."""
    b, n = list(base), list(new)
    return abs(median(n) - median(b)) > max(mad(b), mad(n))
