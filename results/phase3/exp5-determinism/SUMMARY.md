# Exp5 - why do generated tokens differ between RAM tiers? (2026-10-16 night shift)

Setup: Maya v1.1.11 (d187195 build), Maya-S-v2-IQ2_XXS, 1x RTX 5090, 32K ctx, greedy (`temperature=0`), non-thinking chat template,
6 fixed chat prompts x 256 tokens, `scripts/maya_probe.py` / `maya_tier_sweep.py`; raw token ids in the `*-runs/` directories.

## Result: every divergence we saw goes through the CPU lane; with `STRATA_GLM_CPU_LANE=0` the outputs are bit-identical

| arm (3 rounds each, 6 prompts) | runs identical to its own round 0 | vs `t26L0` (lane off, tier 26) |
|---|---|---|
| t26L0 - tier 26 GB, lane off | 6/6 prompts, all rounds | (reference) |
| t42L0 - tier 42 GB, lane off | 6/6, all rounds | **6/6 identical** |
| t26 - tier 26 GB, lane on (default) | 6/6, all rounds | 1/6 |
| t42 - tier 42 GB, lane on (default) | 6/6, all rounds | 0/6 |
| t26L0m / t42L0m - lane off + `MTP_DECODE=1` (12/12 drafts accepted) | 6/6 | **6/6 identical** to MTP off |
| t26m - lane on + `MTP_DECODE=1` | **NOT repeatable**: round 0 and round 1 differ | differ |

- MTP is not active by default on this machine (`spec_steps=0`: one GPU, non-APU). Forced on, it changes nothing with the lane off (so its "same answers" claim holds here) and is ~8% slower (10.0 vs 10.9 tok/s).
- Pinned-RAM tier size changes WHICH experts are in RAM and therefore which of them the CPU lane computes (the lane takes `k` of `f` RAM-tier experts of a route, `k` from a table timed at start and re-timed in decode: `STRATA_GLM_CPU_RETIME`). Lane off => every expert on the GPU => tier-independent output.

## Classification: numerics of two valid implementations, not a race or an uninitialised read
- Evidence 1 (determinism): inside one arm, three engine starts give identical token ids (lane on, tiers 32/38/42 and 26 in the later sweep; lane off everywhere). A data race or uninitialised memory would not repeat bit for bit.
- Evidence 2 (size): `STRATA_GLM_CPU_LANE_CHECK=1` on the calibration expert (layer 3, IQ types 16/18), relative L2 error vs a double-precision reference built from ggml's dequantised rows:
  **GPU kernels 1.63%, CPU lane 2.89%, GPU-vs-CPU-lane 2.97%.** (`CPU_LANE_VERIFY=1` gave 1.5% for the lane on its calibration calls; that mode slows the lane so much that the engine turns the lane off - do not use it for timing.) These are quantisation-level differences (activations are quantised differently on the two paths), orders of magnitude above float rounding, and one expert of ~8 per layer through 78 layers is enough to flip a near-tie in the greedy choice.
  Measured on ONE expert of ONE layer: not a statement about every layer.
- Evidence 3 (timing dependence): the lane's expert split is re-timed in decode. In the tier-32/38/42 runs the engine logged `CPU lane timed again in decode: an expert 0.167-0.170 ms (planned with 0.136-0.140)` and moved from `0 0 1 1 2 2 3 3 4` to `0 0 1 1 2 2 3 3 3` in EVERY run (so those runs repeat), but at tier 26 it happened in some starts (a smoke run, one lane+MTP run) and not in others; a different plan = different experts on the CPU = different tokens. Output with the lane on therefore depends on timing-derived decisions; only the lane-off arm is timing-independent.
- NOT explained: the very first engine start after the reboot (tier 26, phase 2 sweep, round 0) differed from rounds 1-2 on 5/6 prompts; in this night's runs round 0 never differed. We do not know why (no `timed again` line in those logs).
- Not done: logits at the first divergent token (the engine's `--dump-logits` is in `maya generate`; not wired for the GLM server path here). So "top-2 margin was tiny at the divergence" is a hypothesis, not a measurement.

## Quality (`scripts/maya_quality.py`: 42 programmatically graded tasks, greedy, 320 tokens)
| arm | pass | math | code | json | ja | en |
|---|---|---|---|---|---|---|
| lane off, tier 26 | 39/42 | 10/10 | 8/8 | 8/8 | 5/8 | 8/8 |
| lane on, tier 26 | 40/42 | 10/10 | 8/8 | 8/8 | 6/8 | 8/8 |
| lane on, tier 42 | 40/42 | 10/10 | 8/8 | 8/8 | 6/8 | 8/8 |

24/42 token streams identical lane-on vs lane-off; the pass/fail flips are all in the Japanese constrained-format tasks, in both directions (`ja01`, `ja05`, `ja07` fail->pass, `ja08` pass->fail). With 42 tasks a difference of one or two tasks is noise: **no quality difference was detected; this suite could not detect a small one.** Graders: `scripts/maya_quality.py` (two grader bugs were found and fixed before these numbers: the stop token `<|user|>` was left in the text, and a JSON array was cut at the last object brace; `tests/test_quality_graders.py`).

## What this means for users / upstream
- If you need run-to-run AND tier-to-tier reproducible greedy output (regression tests, comparisons across settings), set `STRATA_GLM_CPU_LANE=0`; it cost -4.3% decode at tier 26 and -9.5% at tier 42 here (a1-lane-ab medians, n=3: 10.90 vs 11.39 and 17.41 vs 19.23 tok/s).
- The CPU lane's results are less accurate than the GPU path's (2.9% vs 1.6% on the calibration expert). A finer activation quantisation in the lane would reduce both the gap to the GPU and the tier-dependence; that is an engine change and was not attempted.
