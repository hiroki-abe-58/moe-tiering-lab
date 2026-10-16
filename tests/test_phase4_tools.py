import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import audit_summary  # noqa: E402
import exp10_pairs  # noqa: E402
import exp9_routes  # noqa: E402


class FirstDiff(unittest.TestCase):
    def test_equal_and_prefix_and_differing(self):
        self.assertIsNone(exp10_pairs.first_diff([1, 2, 3], [1, 2, 3]))
        self.assertEqual(exp10_pairs.first_diff([1, 2, 3], [1, 2, 4]), 2)
        self.assertEqual(exp10_pairs.first_diff([1, 2], [1, 2, 3]), 2)   # one stops early: they part where the shorter ends


class Routes(unittest.TestCase):
    def _routes(self, lines):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.0"
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return exp9_routes.load_routes(p)

    def test_positions_split_where_the_layer_stops_increasing(self):
        calls = self._routes(["3 1 2 3 4 5 6 7 8 0 0 0 |", "4 1 2 3 4 5 6 7 8 0 0 0 |", "3 1 2 3 4 5 6 7 8 0 0 0 |"])
        self.assertEqual([len(c) for c in calls], [2, 1])

    def test_compare_counts_flips_before_the_first_different_token(self):
        ra = [[(3, frozenset(range(8)))], [(3, frozenset(range(8)))]]
        rb = [[(3, frozenset(range(8)))], [(3, frozenset([0, 1, 2, 3, 4, 5, 6, 9]))]]
        ta = [{"pos": 0, "tok": 5, "top": [[5, 2.0], [6, 1.0]]}, {"pos": 1, "tok": 7, "top": [[7, 3.0], [1, 1.0]]}]
        tb = [{"pos": 0, "tok": 5, "top": [[5, 2.5], [6, 1.0]]}, {"pos": 1, "tok": 8, "top": [[8, 3.0], [7, 2.9]]}]
        c = exp9_routes.compare(ra, ta, rb, tb)
        self.assertEqual(c["first_token_diff"], 1)
        self.assertEqual(c["calls_with_flip_before"], 0)    # the flip is at the position where the tokens part, not before it
        self.assertAlmostEqual(c["dlogit_max"], 0.5)


class AuditSummary(unittest.TestCase):
    def test_percentile(self):
        self.assertEqual(audit_summary.pct([1, 2, 3, 4, 5], 50), 3)
        self.assertEqual(audit_summary.pct([1, 2, 3, 4, 5], 0), 1)
        self.assertEqual(audit_summary.pct([1, 2, 3, 4, 5], 100), 5)

    def test_table_reads_a_line(self):
        row = {"layer": 3, "ne": 2, "types": [16, 18], "x_amax": 1.0, "x_rms": 0.25,
               "stats": {"gpu": {"l2": 0.01, "linf": 0.02, "cos": 0.9999}, "cpu": {"l2": 0.02, "linf": 0.03, "cos": 0.999}}}
        text = audit_summary.table([row], ["gpu", "cpu"], "t")
        self.assertIn("| gpu | 1.000%", text)
        self.assertIn("| cpu | 2.000%", text)


if __name__ == "__main__":
    unittest.main()
