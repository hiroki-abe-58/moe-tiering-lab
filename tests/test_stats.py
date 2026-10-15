import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import stats  # noqa: E402


class Stats(unittest.TestCase):
    def test_median(self):
        self.assertEqual(stats.median([3, 1, 2]), 2)
        self.assertEqual(stats.median([4, 1, 2, 3]), 2.5)
        with self.assertRaises(ValueError):
            stats.median([])

    def test_mad_and_quantile(self):
        self.assertEqual(stats.mad([1, 1, 2, 2, 4, 6, 9]), 1)
        self.assertEqual(stats.quantile([1, 2, 3, 4], 0.5), 2.5)
        self.assertEqual(stats.quantile([1, 2, 3, 4], 0.0), 1)
        self.assertEqual(stats.quantile([1, 2, 3, 4], 1.0), 4)

    def test_pct_change(self):
        self.assertAlmostEqual(stats.pct_change(10, 11), 10.0)
        with self.assertRaises(ZeroDivisionError):
            stats.pct_change(0, 1)

    def test_interleave_is_balanced_and_alternates(self):
        order = stats.interleave(["A", "B"], 3)
        self.assertEqual(order, ["A", "B", "B", "A", "A", "B"])
        self.assertEqual(order.count("A"), order.count("B"))
        three = stats.interleave(["A", "B", "C"], 2)
        self.assertEqual(three, ["A", "B", "C", "C", "B", "A"])

    def test_noise(self):
        self.assertTrue(stats.noise_exceeded([10, 10.1, 9.9], [12, 12.1, 11.9]))
        self.assertFalse(stats.noise_exceeded([10, 12, 8], [10.5, 12.5, 8.5]))

    def test_summarize(self):
        s = stats.summarize([1, 2, 3])
        self.assertEqual((s["n"], s["median"], s["min"], s["max"]), (3.0, 2, 1, 3))


if __name__ == "__main__":
    unittest.main()
