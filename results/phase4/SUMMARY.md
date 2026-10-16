# Phase 4 - CPU-lane numerical fidelity, why tokens differ between starts, and what does not help (2026-10-16)

PC and model as before: RTX 5090, Core Ultra 9 285K, 64 GB DDR5, WD_BLACK SN850X 8 TB, `Maya-S-v2-IQ2_XXS` (gate/up IQ2_XXS,
down IQ3_XXS or IQ2_S), 32K context, greedy. Engine: Project Maya `main` @ 07c3dc9 plus local, unpublished debugging
patches (a per-call numerical audit, a logit/route trace, the CPU-lane variants below). Long runs went through the durable
task harness (`scripts/durable/`, verified first: a job survives its launcher being killed; timeout, STOP file, Strata stop/restore
all tested). One lesson from it: **a Windows scheduled task runs at below-normal priority by default, which made the engine's SSD
reads ~3x slower** (disk 61 vs 18 ms/token); `job_submit.ps1` now sets priority 4, and the first runs under the default (audit1-3,
a first sweep attempt) are not used for any speed number.

## 1. How far apart are the CPU lane and the GPU, and from the truth? (`exp9-fidelity/`)
`STRATA_GLM_LANE_AUDIT` (dev build) copies a real lane call - experts, input, weights - to a worker that runs the same experts through
the GPU's decode kernels and through a double-precision reference built from ggml's dequantised rows. 150 calls over 42 layers
(tier 42 GB, real activations of the 6 prompts; `audit-t42*.jsonl`, summaries `audit-t42*-summary.md`, `scripts/audit_summary.py`).

| path | rel. L2 vs the double reference, median (p10-p90) | between GPU and CPU lane |
|---|---|---|
| GPU kernels | 1.09% (1.02-1.15) | |
| CPU lane, stock (ggml Q8_K activations, blocks of 256) | **1.73%** (1.51-2.11) | **1.94%** |
| CPU lane, `q8_1`: the device's activation quantiser (blocks of 32, FP16 scale) | 1.09% | 0.063% |
| CPU lane, `q8_1d`: plus the device's integer steps (truncating divisions) | 1.09% | **9.8e-8** median (p90 1.06e-7); 6 of 150 calls above 3e-7, worst 1.1e-3 |

* The stock lane's error is **entirely activation quantisation** (an emulation - dequantised rows against the quantise-dequantise
  round trip of x and h in double - reproduces the lane's output to 1e-7). The down projection's input h dominates (h alone in Q8_K: 1.44%,
  x alone: 0.93%); blocks of 32 give 0.81% / 0.73%, blocks of 16 0.64% / 0.64%, a second residual pass of Q8_K 0.006% / 0.004%.
* The device's own error vs the reference is the same 1.09% (its activations are the same q8_1).
* The rare mismatches of `q8_1d` are +-1 q8 codes at rounding ties: the SwiGLU value h is computed with `expf` on the GPU and `std::exp` on the CPU
  and differs in the last bit, which flips a code in ~1.5% of experts (~4% of lane calls) and moves that expert's output by 1e-4..1e-3.
  The CPU cannot reproduce CUDA's `expf` (it ends in the SFU's `ex2.approx`) nor the GPU kernels' float summation order exactly.

## 2. Does a better lane make the tokens agree? No. (`exp10-a32/`, `exp12-a32d/`, `exp9-fidelity/routes.md`)
Interleaved sweeps, 5 rounds, 6 prompts x 256 tokens, `--no-long`:

| setting | decode tok/s, tier 26 | decode tok/s, tier 42 |
|---|---|---|
| stock lane | 11.35 (11.29-11.43) | 18.26 (17.80-18.48) |
| `q8_1` | 11.29 (-0.5%, noise) | 18.14 (-0.7%) |
| `q8_1d` (other sweep, same day) | 11.15 (-1.8%) | 17.61 (-3.6%) |

Single-thread time per 6144-value row (ns): IQ2_XXS ggml 246 / `q8_1` 286 / `q8_1d` 417; IQ3_XXS 327 / 324 / 525; IQ2_S 243 / 359 / 681.

Token streams (first differing token, pairs of starts): stock t26 vs t42 31 of 175 identical; `q8_1` 23 of 175; `q8_1d` 15 of 175; each also
differs from the lane-off run within ~11-17 tokens (median) just like the stock lane (35 / 30 / 40 of 175 identical). Quality (42 programmatic tasks, 256 tokens):
stock 39-42/42 over five runs, `q8_1` 38-40, `q8_1d` 38-39, lane off 39 - no difference beyond run-to-run noise.

Logits at the first token where two runs part (42-task quality suite, 256 tokens; `scripts/exp9_divergence.py` on the dev engine's logit trace; `exp9-fidelity/div-*.md`):

| pair of runs | tasks identical to the end | tasks that part | median first differing token | median margin (top-1 minus top-2 logit, the smaller of the two runs) | margin < 0.25 / < 0.5 | the two runs' logit gap between the same two tokens differs by (median, max) |
|---|---|---|---|---|---|---|
| stock tier 42, two starts | 28 of 42 | 14 | 12 | 0.098 | 12 / 14 of 14 | 0.44 (1.07) |
| stock 26 vs 42 | 27 of 42 | 15 | 11 | 0.103 | 12 / 15 of 15 | 0.57 (1.28) |
| stock 42 vs lane off | 28 of 42 | 14 | 9 | 0.145 | 14 / 14 of 14 | 0.54 (0.95) |
| `q8_1` 42 vs lane off | 24 of 42 | 18 | 2 | 0.171 | 14 / 17 of 18 | 0.59 (1.92) |
| `q8_1d` 42 vs lane off | 26 of 42 | 16 | 6 | 0.104 | 12 / 16 of 16 | 0.64 (1.26) |
| `q8_1d` tier 42, two starts | 24 of 42 | 18 | 10 | 0.100 | 15 / 18 of 18 | 0.65 (1.75) |
| `q8_1` 26 vs 42 | 23 of 42 | 19 | 6 | 0.149 | 19 / 19 of 19 | 0.52 (1.09) |
| `q8_1d` 26 vs 42 | 24 of 42 | 18 | 4 | 0.108 | 13 / 18 of 18 | 0.55 (1.36) |

Every pair of runs parts at a near tie: the winner leads by about a tenth of a logit (most under 0.25, nearly all under 0.5), while the two runs disagree about that very gap by 0.4-0.65 on
median. The token that wins at the first split is not a computation that went wrong; the noise between the two runs is larger than the lead. (Short answers: the suite's outputs are 50-60 tokens, so
the split indices are small; the 6 x 256-token sweeps above show the same.)

Why: the router. With identical routes at the first decoded position the logits already differ by 0.02 between lane-off and
`q8_1d` (`exp13`), and from the next few positions 25-60% of the layers pick a different top-8 (`exp9-fidelity/routes.md`, `scripts/exp9_routes.py`);
median |difference of the top-1 logit| before the first different token: stock vs lane-off 0.12, `q8_1` 0.16, `q8_1d` 0.06, two stock starts 0.17. Layer by layer
(`exp13-determinism`, `scripts/exp13_ffn.py`): a layer whose input is identical differs by 1e-7 in its FFN output when no tie flips, and by 1e-4..3e-3 when one does; later layers
amplify the input difference 5-20x through different expert sets. Any difference above ~1e-6 in the lane is enough; 30x better is not.

## 3. Why two starts with the same settings differ - and a recipe that fixes it (`exp13-determinism/`, `exp14-recipe/`)
Not a race: with the same placement of experts the lane-on runs are **bit-identical** (positions 1762 of 1762, logits and routes: `dfix1`=`dfix2`, `p8`=`p8b`;
lane off: `L0`=`L0b`). What differs between starts is where experts sit: the VRAM expert pool is sized from the free VRAM at start (`tiers warm: N experts`
was 9,453-9,488 over five starts; the log's "only N MiB free once the expert pool ... GB less"), the lane's split comes from a start-up timing that is a near tie
(0.137 ms on the CPU vs 0.141 over PCIe: `... 3 3 3` or `... 3 3 4`), `STRATA_GLM_CPU_RETIME` plans it again in decode and `STRATA_GLM_PROMOTE`'s background moves land when their copies finish.
Pinning those gives repeatable output with the stock lane:

| settings (tier 42 GB) | starts | stream pairs identical |
|---|---|---|
| defaults | 5 | 17 of 70 |
| `--expert-cache 3250`, `PROMOTE=0`, `CPU_RETIME=0`, `CPU_PLAN=001122333` | 5 | **70 of 70** |
| the same with 300 MiB of VRAM held by another process | 3 | 105 of 105 against the five above |
| `--expert-cache auto` with the same 300 MiB held | 3 | 0 of 105 against them (21 of 21 among themselves) |
| `STRATA_GLM_CPU_LANE=0` (any pool) | 5 | 70 of 70 (and identical across tiers 26/42) |

Decode with the recipe 18.31 tok/s (18.29-18.35) vs 18.26 for the defaults; lane off 16.46 (-7.5% vs 17.80 in that sweep). The config's `args` (`--expert-cache auto`) win over `STRATA_GLM_EXPERT_CACHE`,
so the recipe sets the pool in the config. (The `q8_1`/`q8_1d` variants are reproducible under the same recipe too - they are not needed for it.)

## 4. CPU/PCIe split: `STRATA_GLM_PCIE_SHARE` 0.10 vs the default (`exp11-pcie-share/`)
Tier 42 GB, 5 interleaved rounds (order reversed each round), 6 prompts + 2K and 8K prefill, three conditions: engine default (split timed at start), explicit 0.60, explicit 0.10.
Decode 18.13 (17.85-18.36) / 18.14 (+0.0%) / **19.69 (19.66-19.83) +8.6%**; prefill 2K 475 / 478 / 477 tok/s and 8K 1754 / 1758 / 1754 (unchanged); TTFT of a chat prompt -11% with 0.10.
Plans: default `0 0 1 1 2 2 3 3 4` (once re-timed to `... 3 3 3`), 0.60 `0 0 1 1 2 2 2 3 3`, 0.10 `0 1 2 3 4 4 5 6 7` (the CPU takes almost every RAM-tier expert; VRAM hit rate 65% -> 57%, disk waits per token -22%).
The calibrator (`tools/calibrate_glm.py`) had picked 0.10 on a single sample per setting; five rounds confirm it, so no engine change is proposed. Tokens differ between the three (different splits).

## 5. Raw SSD bandwidth (`scripts/raw_read_bench.py`, unbuffered reads, expert shard)
Random 1.1 MB reads: queue depth 1 0.99 GB/s, 4 5.75, 9 6.55, 16 6.73, 32 6.82 GB/s; 6.3 GB/s sustained for 80 s (no throttling). The engine's ~6 GB/s during waits at depth <= 9 is therefore ~92% of what this drive delivers for such reads.

## 6. Where the ~36 ms outside the SSD goes (`exp15-nsys/`)
(see `exp15-nsys/SUMMARY.md`)

## What is published, what is not
Published here: the measurements, the harness, the analysis scripts, the Windows task harness. The engine patches (audit, trace, `q8_1`, `q8_1d`) are not proposed upstream:
the accuracy gain is real but does not change a token-level result, `q8_1d` costs 2-4% of decode, and `q8_1` is only a cheaper half-step. A reference branch is on the fork
(see README). The one upstream proposal is documentation (section 3) - see the pull request linked from the README.
