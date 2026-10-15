# Methodology

Rules this repository follows when it states a number. Where a rule could not be followed, the result says so.

## What is compared

- **Same model, same quant, same context, same machine** for any A/B. Numbers from different models (for example a
  Maya GLM-5.3-Flash run against a llama.cpp GLM-4.5-Air run) are never presented as an engine ranking.
- **One variable per comparison.** A condition differs from the baseline in exactly one setting.
- The **RAM tier is pinned** (`STRATA_GLM_RAM_GB`) for every condition. Maya sizes the tier from free RAM at start;
  a tier that differs by a few GB changes the number of SSD reads per token and would be mistaken for the setting
  under test. `scripts/maya_ab.py` records each run's tier and warns when it varied by more than 1 GB.

## Run order

Conditions are interleaved and reversed each round (`A B | B A | A B ...`, `moelab.stats.interleave`), so slow drift
(heat, OS file cache, background load) lands on every condition alike. At least three rounds (three runs per
condition) are taken; more when the spread is large.

## What is reported

- **Median** of the runs, with min-max and the MAD (median absolute deviation). Means are not used.
- The change is flagged **above noise** only when the medians differ by more than the larger of the two MADs
  (`moelab.stats.noise_exceeded`). This is a deliberately conservative screen, not a significance test; with three
  runs per arm no p-value is claimed.
- A change is called an improvement in a write-up only if it is above noise **and** reproduced in a second sweep.
  The adoption bar used for upstream pull requests is a median gain of about 10% or a clear observability/feature
  gain with no regression elsewhere.

## Metrics

Taken from the engine's own output, not re-derived:

| Metric | Source |
|---|---|
| Decode tokens/s (greedy, three 256-token answers) | Maya `--bench` -> `maya-bench.txt` |
| Prefill tokens/s at 2048 and 8192 tokens | same |
| Disk ms/token, waits/token, reads/token, VRAM hit %, RAM fetches/token, CPU-lane ms/token | the engine's `glm stat:` lines (`maya-bench.log`) |
| SSD wait share of a token | `disk ms/tok / decode ms/tok` (derived, `moelab.mayaparse`) |
| ms per disk wait | `disk ms/tok / waits/tok` (derived) |
| RAM tier GB | the engine's `glm fast: CUDAn RAM tier ... GB pinned` line |
| Pinnable host memory | `tools/pin_probe` |
| CPU core classes | `moelab.cputopo` (Windows `GetSystemCpuSetInformation`) |

## Controls and caveats recorded with every result

- Machine facts from `scripts/audit_windows.ps1` (RAM, commit limit, page file, VBS/HVCI, GPU, PCIe link, drives).
- Other programs holding the GPU or SSD during a run are listed; a run with a competing heavy process is discarded.
- Cold versus warm: the first answer after a start is slower (Maya's `--bench` does its own warm-up); the OS file cache
  state is noted. Where a result depends on a cold cache, the model files are not pre-read.
- Output correctness: greedy decoding makes token streams comparable, so A/B runs compare the generated text; a
  setting that changes it (expert placement between CPU and GPU can change the last bits) is reported as such.
- Anything not run is listed under "not tested" in the result, never omitted.
