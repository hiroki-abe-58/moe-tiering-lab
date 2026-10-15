import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from moelab import probe, sweep  # noqa: E402


def req(label, toks, decode_ms=1000.0, produced=10, stat=None, bw=None, prompt_len=30, prompt_ms=100.0):
    done = {"produced": produced, "prompt_len": prompt_len, "prompt_ms": prompt_ms, "decode_ms": decode_ms,
            "finish": "length", "spec_hits": 5, "spec_steps": 10, "reuse": 0, "vram_hits": 1, "lookups": 2}
    r = {"label": label, "tokens": toks, "done": done, "metrics": probe.request_metrics(done), "ssd_read_gbs": bw}
    if stat:
        r["engine_stat"] = stat
    return r


def run(decode_ms, tier, toks=(1, 2, 3)):
    stat = {"disk_ms_tok": 40.0, "disk_waits_tok": 20.0, "disk_ms_per_wait": 2.0, "disk_share": 0.5, "vram_hit_pct": 64.0}
    reqs = [req("warmup", [9]), req("chat:a", list(toks), decode_ms, stat=stat, bw=1.5),
            req("chat:b", list(toks), decode_ms, stat=stat, bw=1.7),
            req("prefill:2048", [7], prompt_len=2048, prompt_ms=8000.0),
            req("prefill:8192", [8], prompt_len=8192, prompt_ms=8000.0)]
    return {"requests": reqs, "ram_tier_gb": tier, "load_s": 60.0,
            "memory": {"min_phys_avail_gb": 9.0, "min_commit_avail_gb": 20.0, "max_commit_used_pct": 80.0, "max_vram_mib": 31000}}


class Records(unittest.TestCase):
    def test_record(self):
        r = sweep.run_record(run(1000.0, 26.0), "t26", 0)
        self.assertAlmostEqual(r["decode_tok_s"], 10.0)
        self.assertAlmostEqual(r["disk_share"], 0.5)
        self.assertAlmostEqual(r["ssd_read_gbs"], 1.6)
        self.assertAlmostEqual(r["prefill_2048"], 1000 * 2048 / 8000.0)
        self.assertAlmostEqual(r["ttft_8192_ms"], 8000.0)
        self.assertEqual(r["max_commit_used_pct"], 80.0)

    def test_streams_exclude_warmup(self):
        s = sweep.token_streams(run(1000.0, 26.0))
        self.assertEqual(sorted(s), ["chat:a", "chat:b", "prefill:2048", "prefill:8192"])


class Summary(unittest.TestCase):
    def test_pct(self):
        recs = [sweep.run_record(run(1000.0, 26.0), "t26", i) for i in range(3)] + \
               [sweep.run_record(run(800.0, 38.0), "t38", i) for i in range(3)]
        s = sweep.summarize(recs, "t26")
        self.assertAlmostEqual(s["t38"]["decode_tok_s"]["pct_vs_baseline"], 25.0)
        self.assertEqual(s["t38"]["decode_tok_s"]["above_noise"], 1.0)

    def test_streams(self):
        streams = {"a": {"0": sweep.token_streams(run(1, 1)), "1": sweep.token_streams(run(1, 1))},
                   "b": {"0": sweep.token_streams(run(1, 1)), "1": sweep.token_streams(run(1, 1, toks=(1, 9, 3)))}}
        rep = sweep.stream_report(streams, "a")
        self.assertEqual(rep["a"]["identical_to_reference"], 2)
        self.assertEqual(rep["b"]["identical_to_reference"], 1)
        self.assertEqual(rep["b"]["earliest_divergence_token"], 1)
        self.assertEqual(rep["b"]["diverging_prompts"], ["chat:a", "chat:b"])

    def test_markdown(self):
        recs = [sweep.run_record(run(1000.0, 26.0), "t26", 0), sweep.run_record(run(800.0, 38.0), "t38", 0)]
        streams = {"t26": {"0": sweep.token_streams(run(1, 1))}, "t38": {"0": sweep.token_streams(run(1, 1))}}
        md = sweep.markdown(sweep.summarize(recs, "t26"), "t26", sweep.stream_report(streams, "t26"))
        self.assertIn("| decode_tok_s |", md)
        self.assertIn("identical", md)


if __name__ == "__main__":
    unittest.main()
