# Findings

All numbers: one PC (see [reproduction](reproduction.md#the-machine)), Windows 11 26200, Project Maya v1.1.11
(`d187195`), `Maya-S-v2-IQ2_XXS` (91 GB on disk), 32K context, MTP drafting (Maya's default), `--bench`
(greedy, three 256-token answers, prefill at 2048 and 8192 tokens). Each arm below is **n = 3 runs, interleaved and
reversed per round**. Raw runs: [`results/`](../results/). A single machine, a single model: nothing here is a
claim about other hardware.

## 1. Where a decode token goes on this PC

Default settings, RAM tier left to Maya (it chose 26.7 GB): decode **11.3-11.7 tokens/s**, prefill ~275 (2K) and
~1050 (8K) tokens/s.

- About **19.5 disk waits per token**, **2.07 ms per wait**, i.e. **~40 ms of a ~75-90 ms token (53-54%)** is waiting
  for the SSD.
- 2.07 ms per wait is in the range reported after the Windows slow-read fix (Maya #67/#73: 1.3-1.8 ms per expert-sized
  read on another drive; this PC's SSD was not benchmarked directly with a raw-I/O tool). The slow-read problem of
  Maya #65/#67 (fixed upstream in v1.0.30) is not reproduced here, so the remaining SSD time looks like *how many*
  reads, not how slow each one is. That reading is an inference, not a separate measurement.
- Maya's start-up log says why the tier is small: `Windows' commit limit (RAM + page file) caps the RAM tier 17 GB
  below the free RAM (50.2 GB free, 32.8 GB of commit left)`. The page file here is system-managed, ~21-26 GB.

## 2. Hypothesis: P-core / E-core placement of the CPU lane (negative result)

Core Ultra 9 285K = 8 P-cores + 16 E-cores, no SMT. Maya's CPU lane defaults to 2/3 of the logical CPUs (16 threads)
and is not pinned on Windows, and nothing in the code looks at core classes. Could placement matter? The RAM tier
was pinned to 26 GB for every arm. (`P`/`E` = process affinity to the performance/efficiency cores, from
`GetSystemCpuSetInformation`; the P-core logical CPUs on this PC are `0,1,10-13,22,23`, **not** the first eight.)

| arm | setting | decode tok/s (median, range) | vs base | prefill 2K / 8K |
|---|---|---|---|---|
| base | defaults (16 lane threads, unpinned) | 11.30 (11.00-11.30) | - | 276 / 1049 |
| lane8 | `STRATA_GLM_CPU_LANE=8`, unpinned | 11.50 (11.30-11.50) | +1.8% | 276 / 1046 |
| P6 | affinity P-cores, lane 6 | 11.00 (10.90-11.00) | -2.7% | 274 / 1038 |
| E12 | affinity E-cores, lane 12 | 11.30 (11.20-11.30) | +0.0% | 270 / 1020 |
| P8 | affinity P-cores, lane 8 | 10.50 (10.40-10.50) | -7.1% | 273 / 1034 |

Full table with disk statistics: [`results/exp1-affinity.md`](../results/exp1-affinity.md).

**Conclusion:** no placement beat the default by more than the 1.8% of simply running fewer lane threads, and giving
the disk readers and the lane only the P-cores was 7% worse. Run-to-run spread is ~0.3 tokens/s, so +1.8% is at the
edge of what this harness resolves and is not claimed as an improvement. **No pull request was made from this.**

Not tested: pinning the lane to P-cores *and* the disk readers/main thread to E-cores (it needs an engine change,
not a process mask); a CPU lane that is the bottleneck (here the lane takes 3-5 ms of a token).

## 3. RAM tier size is the lever (and the page file sets the tier)

Same harness, `STRATA_GLM_RAM_GB` pinned per arm (n = 3 each, interleaved):

| RAM tier | decode tok/s | disk ms/tok | disk waits/tok | disk share of a token | prefill 2K / 8K |
|---|---|---|---|---|---|
| 26 GB | 11.20 | 39.2 | 19.5 | 53% | 276 / 1048 |
| 18 GB | 8.80 (-21%) | 55.0 | 24.0 | 62% | 226 / 866 |
| 10 GB | 6.90 (-38%) | 72.7 | 27.4 | 71% | 190 / 733 |

(`results/exp2-tier-size.md`; the tool's "tier varied" warning is expected here: the tier is the variable.)

Roughly **+0.25-0.3 tokens/s per GB of tier** in this range. The VRAM hit rate is unchanged (64%): the tier size moves
experts between RAM and SSD, not onto the card. Extrapolating to the ~45 GB tier that this PC's 63 GB could pin would
suggest on the order of 15-16 tokens/s, but **that is an extrapolation, not a measurement**: raising the page file
needs a system change that was not made. Maya's own README lists 23 tokens/s for an RTX 5090 + i9-13900K + 64 GB
Windows PC at 128K context (@gianbing, #139), another machine and settings.

## 4. Windows pinning: no 70% cap observed on an RTX 5090

Maya #185 reports (RTX 3090, 64 GB, 64 GB page file, VBS/HVCI on) that the RAM tier stops at ~45 GB, ~70% of RAM, and
reads this as a driver cap. [`tools/pin_probe`](../tools/pin_probe/pin_probe.cu) allocates pinned memory in chunks
through `cudaHostAlloc`, outside Maya:

| chunk | pinned | time | stopped by | RAM available at the end |
|---|---|---|---|---|
| 1 GiB | 30.0 GB | 3.6 s | my `--max-gb 30` | 16.7 GB |
| 512 MiB | **44.5 GB (70.2% of 63.4 GB)** | 5.9 s | my `--max-gb 44.5` | 2.1 GB |

- No refusal up to 44.5 GB (**the only thing established**) on RTX 5090 (WDDM), driver 610.88, Windows 11 26200, **with VBS and HVCI running** (the same
  as #185's PC). The probe stopped because free RAM was almost gone, not because the driver said no; whether a cap sits
  above 44.5 GB on this PC is **not known**.
- Pinned memory was charged to the commit limit **1:1** (commit available 62.49 -> 17.56 GB for 44.5 GB pinned), so a
  small page file *is* a cap on the tier, as Maya's start-up warning says.
- This does not disprove #185 (different GPU generation and driver; a 64 GB page file there). It shows that "WDDM
  caps pinning at ~70% of RAM" is not a rule that holds on every Windows PC, and that `pin_probe` separates a driver
  refusal from a commit shortfall in a few seconds.

## 5. Reference: Strata on the same PC

Official `tools/strata_bench.py` (what `BENCH.bat` runs), Strata `296b59d`, Qwen3.8-Flash-Next IQ2_XS:
decode 217.6 tokens/s (median of 9), 4K prompt 5001, 16K prompt 6417 tokens/s
([`results/strata-baseline/README.md`](../results/strata-baseline/README.md); the tool's "Windows 10" label is its own,
build 26200 is Windows 11). **This is a different model with a
different expert layout; it says nothing about Strata versus Maya as engines.** It is included because Strata's
maintainers ask for a same-day control run with reports, and it confirms the PC was healthy.

## Not tested

- Output equality between arms (greedy runs were not diffed token by token).
- A page file of 40 GB or more, or any tier above 26 GB, and therefore the real size of the gain in section 3.
- 64K/128K context, DFlash2, vision, Maya-L, multi-GPU, Linux, AMD/HIP.
- A llama.cpp GLM-4.5-Air run (the model is on disk; it is a different model and was not used for any comparison).
- Anything on the Strata side beyond its stock benchmark. GLM-5.3-Flash is not supported by Strata's maintainers'
  scope (see upstream issues #770, #1191, #2067) and no GLM port to Strata was attempted.
