import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import cputopo  # noqa: E402


def rec(lp, core, eff, llc=0, numa=0, group=0, typ=0, size=32):
    head = struct.pack("<IIIHBBBBBB", size, typ, lp, group, lp, core, llc, numa, eff, 0)
    return head + b"\0" * (size - len(head))


class Topo(unittest.TestCase):
    def hybrid(self):
        # 8 P-cores (class 1) then 16 E-cores (class 0), one thread each (no SMT): Core Ultra 9 285K shape
        return b"".join([rec(i, i, 1) for i in range(8)] + [rec(i, i, 0) for i in range(8, 24)])

    def test_parse_and_classify(self):
        cpus = cputopo.parse_cpu_sets(self.hybrid())
        self.assertEqual(len(cpus), 24)
        c = cputopo.classify(cpus)
        self.assertEqual(c["P"], list(range(8)))
        self.assertEqual(c["E"], list(range(8, 24)))
        self.assertEqual(cputopo.mask(c["P"]), 0xFF)
        self.assertEqual(cputopo.mask(c["E"]), 0xFFFF00)
        self.assertEqual(cputopo.mask(c["all"]), 0xFFFFFF)

    def test_homogeneous_cpu_has_only_p(self):
        cpus = cputopo.parse_cpu_sets(b"".join(rec(i, i // 2, 0) for i in range(16)))
        c = cputopo.classify(cpus)
        self.assertEqual(c["E"], [])
        self.assertEqual(len(c["P"]), 16)

    def test_ignores_non_cpuset_records_and_other_groups(self):
        buf = rec(0, 0, 1, typ=1) + rec(1, 1, 1) + rec(2, 2, 0, group=1)
        cpus = cputopo.parse_cpu_sets(buf)
        self.assertEqual([c.index for c in cpus], [1, 2])
        self.assertEqual(cputopo.classify(cpus)["all"], [1])

    def test_bad_size_rejected(self):
        with self.assertRaises(ValueError):
            cputopo.parse_cpu_sets(rec(0, 0, 0, size=8) if False else struct.pack("<IIIHBBBBBB", 4, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    def test_truncated_tail_ignored(self):
        self.assertEqual(len(cputopo.parse_cpu_sets(rec(0, 0, 1) + b"\0" * 5)), 1)

    def test_resolve_affinity(self):
        cpus = cputopo.parse_cpu_sets(self.hybrid())
        self.assertEqual(cputopo.resolve_affinity("P", cpus), 0xFF)
        self.assertEqual(cputopo.resolve_affinity("E", cpus), 0xFFFF00)
        self.assertEqual(cputopo.resolve_affinity("all", cpus), 0xFFFFFF)
        self.assertEqual(cputopo.resolve_affinity("0x3", cpus), 3)
        with self.assertRaises(ValueError):
            cputopo.resolve_affinity("X", cpus)
        flat = cputopo.parse_cpu_sets(b"".join(rec(i, i, 0) for i in range(4)))
        with self.assertRaises(ValueError):
            cputopo.resolve_affinity("P", flat)

    @unittest.skipUnless(sys.platform == "win32", "Windows API")
    def test_affinity_roundtrip(self):
        before = cputopo.get_process_affinity()
        cputopo.set_process_affinity(before)
        self.assertEqual(cputopo.get_process_affinity(), before)

    @unittest.skipUnless(sys.platform == "win32", "Windows API")
    def test_real_system_has_cpus(self):
        cpus = cputopo.read_system()
        self.assertGreaterEqual(len(cpus), 1)
        self.assertTrue(cputopo.classify(cpus)["all"])


if __name__ == "__main__":
    unittest.main()
