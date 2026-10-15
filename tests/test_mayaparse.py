import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import mayaparse  # noqa: E402

# A line quoted from the public Maya issue #67 (RTX 5090 Laptop, v1.0.15), tail fields filled for the full format.
STAT = ("glm stat: decode 292.48 ms/tok (3.42 tok/s) | vram hit 60.45% | ram fetches 24.68/tok | "
        "disk 12.11 reads/tok in 12.39 waits/tok, 236.77 ms/tok | promotions 0.50/tok | cpu lane 3.20/tok "
        "in 11.00 ms/tok | prompt 1.2 ms/tok | vram 2310/2310 ram 5867/6458")

BENCH = """Project Maya v1.1.11 benchmark, 2026-10-15 20:00
GPUs: NVIDIA GeForce RTX 5090 32 GB; RAM 63 GB; CPU Intel(R) Core(TM) Ultra 9 285K
setup: maya-maya-s.json, context 32768, GPUs 0
decode (writing the answer): mean 14.0 tokens/s over 3 answers of 256 tokens (greedy, thinking off)
    13.5 tokens/s  Explain what a mixture of experts is.
    14.5 tokens/s  Write a haiku about SSDs.
    14.0 tokens/s  Why is the sky blue?
prefill (reading the prompt): 900 tokens/s, 2048 tokens
prefill (reading the prompt): 1100 tokens/s, 8192 tokens

engine lines:
""" + STAT + "\n"


class StatLine(unittest.TestCase):
    def test_fields(self):
        s = mayaparse.parse_stat_line(STAT)
        self.assertAlmostEqual(s["decode_ms_tok"], 292.48)
        self.assertAlmostEqual(s["decode_tok_s"], 3.42)
        self.assertAlmostEqual(s["vram_hit_pct"], 60.45)
        self.assertAlmostEqual(s["ram_fetches_tok"], 24.68)
        self.assertAlmostEqual(s["disk_reads_tok"], 12.11)
        self.assertAlmostEqual(s["disk_waits_tok"], 12.39)
        self.assertAlmostEqual(s["disk_ms_tok"], 236.77)
        self.assertAlmostEqual(s["cpu_lane_tok"], 3.2)
        self.assertAlmostEqual(s["cpu_lane_ms_tok"], 11.0)
        self.assertEqual(s["ram_slots"], 6458)

    def test_derived_matches_issue_67_arithmetic(self):
        s = mayaparse.parse_stat_line(STAT)
        self.assertAlmostEqual(s["disk_ms_per_wait"], 236.77 / 12.39)   # ~19 ms a wait, as the reporter computed
        self.assertAlmostEqual(s["disk_share"], 236.77 / 292.48)        # ~81% of the token is waiting on disk

    def test_not_a_stat_line(self):
        self.assertIsNone(mayaparse.parse_stat_line("glm fast: CUDA0 RAM tier 38.98 GB pinned"))

    def test_older_format_without_pool_counters(self):
        s = mayaparse.parse_stat_line("glm stat: decode 50.0 ms/tok | prompt 400 tok/s")
        self.assertEqual(s, {"decode_ms_tok": 50.0})


class Bench(unittest.TestCase):
    def test_parse(self):
        b = mayaparse.parse_bench(BENCH)
        self.assertEqual(b["version"], "1.1.11")
        self.assertEqual(b["context"], 32768)
        self.assertEqual(b["decode"], [13.5, 14.5, 14.0])
        self.assertEqual(b["prefill"], {2048: 900.0, 8192: 1100.0})
        self.assertEqual(len(b["stats"]), 1)

    def test_crlf(self):
        b = mayaparse.parse_bench(BENCH.replace("\n", "\r\n"))
        self.assertEqual(b["decode"], [13.5, 14.5, 14.0])

    def test_empty(self):
        b = mayaparse.parse_bench("")
        self.assertEqual((b["decode"], b["prefill"], b["stats"]), ([], {}, []))


if __name__ == "__main__":
    unittest.main()
