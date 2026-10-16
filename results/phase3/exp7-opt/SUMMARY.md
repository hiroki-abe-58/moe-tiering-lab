# Exp7 - optimisation screens (2026-10-16, night run)

Same PC/model as Exp5 (RTX 5090, 285K, 64 GB DDR5-5600, SN850X 8 TB, Maya-S-v2-IQ2_XXS, 32K ctx, greedy, `--no-long` probes).
Engine: Maya `main` @ 07c3dc9 plus three uncommitted, unpublished dev patches (an I/O trace line `STRATA_GLM_IO_TRACE`, a reader-thread
knob `STRATA_GLM_IO_THREADS`, an opt-in `STRATA_GLM_LANE_OVERLAP` helper thread). Interleaved rounds (`scripts/maya_tier_sweep.py`),
**only 2 rounds per arm** in C2/C3 (3 in C1): these are screens, not confirmations. "~noise" = ranges overlap.

| id | what | tier | result | verdict |
|---|---|---|---|---|
| C1 | run the CPU lane on a helper thread while the service thread reads the SSD | 26 / 42 | +0.7% / +0.6% decode (upper bound from the trace: 3.6% / 3.8%); tokens unchanged when the lane plan is pinned | not worth a PR |
| C2 | `STRATA_GLM_IO_THREADS` 12 / 16 / 24 (default 8) | 26 | 11.46 / 11.43 / 11.43 vs 11.45 tok/s | no effect |
| C2 | `STRATA_GLM_READ_CHUNKS` 4 / 16 (default 8) | 26 | 4: 11.69 (+2.1%); 16: 11.06 (-3.4%) | 4 is below Maya's own 3% keep rule; no PR |
| C3 | `STRATA_GLM_PROMOTE_MIN` 4 / 8, `STRATA_GLM_PROMOTE` 4 / 16 | 42 | +0.0 / +0.5 / -0.4 / -0.4% (PROMOTE_MIN=8 lowers the VRAM hit rate by 11%) | no gain |
| C3 | `STRATA_GLM_CPU_PLAN` `001122334` / `011223445` / `000111222` vs `001122333` | 42 | -0.3% / **+7.3%** (20.03 vs 18.67 tok/s; ranges 19.71-20.35 vs 18.55-18.78) / -4.0% | see below |
| C4 | Maya's own `tools/calibrate_glm.py` on the tier-42 config (676 s, **one sample per setting**) | 42 | PCIe share 0.10: 22.4 tok/s vs 20.6 for the engine's own 0.60 (+8.8%); CPU threads 16 (default) best; READ_CHUNKS 4 / 2 not confirmed (confirm runs 20.7-23.8, overlapping the default's 22.2-23.6); it printed `STRATA_GLM_PCIE_SHARE=0.10` as its only recommendation | log: `c4-calibrate42.log` |

## How to read C3/C4 (honest caveats)
- My baselines in C1-C3 were **uncalibrated**: the plan is whatever the engine timed at start, and Maya ships a calibration step that
  was never run on this config before. The +7.3% (a different CPU/PCIe split) and the calibrator's +8.8% (PCIe share 0.10; n = 1 per
  setting, no noise estimate) are the same kind of finding - a per-machine split that the user can tune - and are not a code defect.
  They were not repeated for >= 3 rounds, and the tokens change with the split (the plan decides which experts run on the CPU lane, see Exp5), so
  I do not claim a speed-up for general users and made **no pull request**.
- Trace of the question the PR would have had to answer: the most any read/lane overlap can hide is 3.6-3.8% of a token, so the
  remaining ~36 ms/token floor (Exp6) is not in the reader/lane arrangement; it was not decomposed (no nsys capture was run).

## Not done
Replacement-policy and routing-prefetch variants (A, E in the brief; Maya's authors report LRU = LFU and Belady +1%, and read-ahead was
measured as no gain in Phase 2), sync/copy-reduction work (F), and a >= 3-round confirmation of the CPU split. No code from this
experiment is published; the dev patches stay local.
