import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import abreport  # noqa: E402


def bench(decode, prefill, disk_ms=None):
    st = [{"disk_ms_tok": disk_ms, "disk_waits_tok": 10.0}] if disk_ms is not None else []
    return {"decode": decode, "prefill": prefill, "stats": st}


class Tier(unittest.TestCase):
    def test_sums_gpus(self):
        log = ("glm fast: CUDA0 RAM tier 10.00 GB pinned, 100 slots\n"
               "glm fast: CUDA1 RAM tier 5.50 GB pinned, 50 slots\n")
        self.assertAlmostEqual(abreport.parse_ram_tier_gb(log), 15.5)

    def test_none(self):
        self.assertIsNone(abreport.parse_ram_tier_gb("nothing"))


class Summary(unittest.TestCase):
    def setUp(self):
        self.runs = []
        for rnd, (a, b) in enumerate([(10.0, 11.5), (10.2, 11.6), (9.8, 11.4)]):
            self.runs.append(abreport.run_record("A", rnd, bench([a] * 3, {2048: 100.0}, 200.0), 40.0))
            self.runs.append(abreport.run_record("B", rnd, bench([b] * 3, {2048: 101.0}, 150.0), 40.2))

    def test_pct_and_noise(self):
        s = abreport.summarize_runs(self.runs, "A")
        self.assertAlmostEqual(s["B"]["decode_tok_s"]["pct_vs_baseline"], 15.0, places=3)
        self.assertEqual(s["B"]["decode_tok_s"]["above_noise"], 1.0)
        self.assertAlmostEqual(s["B"]["disk_ms_tok"]["pct_vs_baseline"], -25.0)
        # prefill differs by 1% and the runs are identical inside a condition: MAD 0 -> any difference counts
        self.assertIn("prefill_2048", s["A"])

    def test_missing_baseline(self):
        with self.assertRaises(KeyError):
            abreport.summarize_runs(self.runs, "Z")

    def test_markdown_has_rows_and_no_warning_when_tiers_match(self):
        s = abreport.summarize_runs(self.runs, "A")
        md = abreport.markdown(s, "A", self.runs)
        self.assertIn("| decode_tok_s |", md)
        self.assertIn("+15.0%", md)
        self.assertNotIn("WARNING", md)

    def test_tier_mismatch_warns(self):
        runs = [abreport.run_record("A", 0, bench([1.0], {}), 40.0), abreport.run_record("B", 0, bench([1.0], {}), 44.0)]
        self.assertIn("RAM tier varied", abreport.tier_mismatch_warning(runs))

    def test_record_without_stats(self):
        r = abreport.run_record("A", 0, bench([], {}), None)
        self.assertIsNone(r["decode_tok_s"])
        self.assertIsNone(r["disk_ms_tok"])


if __name__ == "__main__":
    unittest.main()
