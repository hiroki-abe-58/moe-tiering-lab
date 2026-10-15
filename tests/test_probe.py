import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import probe  # noqa: E402

DONE = "DONE 256 31 412.5 22000.0 length 180 200 0 150 400"


class Done(unittest.TestCase):
    def test_parse(self):
        d = probe.parse_done(DONE)
        self.assertEqual(d["produced"], 256)
        self.assertEqual(d["finish"], "length")
        self.assertAlmostEqual(d["decode_ms"], 22000.0)
        self.assertEqual(d["lookups"], 400)

    def test_not_done(self):
        self.assertIsNone(probe.parse_done("ERR boom"))
        self.assertIsNone(probe.parse_done("T 123"))
        self.assertIsNone(probe.parse_done(""))

    def test_metrics(self):
        m = probe.request_metrics(probe.parse_done(DONE))
        self.assertAlmostEqual(m["decode_tok_s"], 1000 * 256 / 22000.0)
        self.assertAlmostEqual(m["decode_ms_tok"], 22000.0 / 256)
        self.assertAlmostEqual(m["ttft_ms"], 412.5)
        self.assertAlmostEqual(m["spec_accept"], 0.9)

    def test_metrics_without_decode(self):
        m = probe.request_metrics(probe.parse_done("DONE 0 31 100.0 0.0 cancel 0 0 0 0 0"))
        self.assertNotIn("decode_tok_s", m)


class Streams(unittest.TestCase):
    def test_divergence(self):
        self.assertIsNone(probe.first_divergence([1, 2, 3], [1, 2, 3]))
        self.assertEqual(probe.first_divergence([1, 2, 3], [1, 9, 3]), 1)
        self.assertEqual(probe.first_divergence([1, 2, 3], [1, 2]), 2)   # a prefix is a divergence at its end
        self.assertEqual(probe.first_divergence([], [5]), 0)

    def test_compare(self):
        ref = {"a": [1, 2, 3], "b": [4, 5]}
        cmp = probe.compare_streams(ref, {"a": [1, 2, 3], "b": [4, 6]})
        self.assertTrue(cmp["a"]["identical"])
        self.assertEqual(cmp["b"]["first_divergence"], 1)
        self.assertFalse(probe.all_identical(cmp))
        self.assertTrue(probe.all_identical(probe.compare_streams(ref, dict(ref))))

    def test_missing_prompt_is_not_identical(self):
        cmp = probe.compare_streams({"a": [1]}, {})
        self.assertFalse(cmp["a"]["identical"])
        self.assertTrue(cmp["a"]["missing"])
        self.assertFalse(probe.all_identical({}))


class Disk(unittest.TestCase):
    def test_bandwidth(self):
        self.assertAlmostEqual(probe.read_bandwidth_gbs(0, 3_000_000_000, 2.0), 1.5)
        self.assertEqual(probe.read_bandwidth_gbs(0, 1, 0.0), 0.0)

    def test_busiest(self):
        self.assertEqual(probe.pick_busiest_disk({"a": 0, "b": 0}, {"a": 10, "b": 5_000}), "b")
        self.assertIsNone(probe.pick_busiest_disk({"a": 1}, {"a": 1}))

    def test_commit_pct(self):
        self.assertAlmostEqual(probe.commit_used_pct(100, 25), 75.0)
        self.assertEqual(probe.commit_used_pct(0, 0), 0.0)


if __name__ == "__main__":
    unittest.main()
