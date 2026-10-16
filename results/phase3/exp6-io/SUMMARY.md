# Exp6 - where the SSD time goes and what moves with the RAM tier (2026-10-16)

Machine/model as in Exp5 (RTX 5090, 285K, DDR5-5600 4x16 GB, WD_BLACK SN850X 8 TB, Maya-S-v2-IQ2_XXS, 32K ctx, greedy).
Sources: `results/phase2/exp4-tier-sweep-runs` (per-request `glm stat:` lines + OS disk counters), `b1-trace*` (engine trace added on
a dev branch, see below), `scripts/io_analysis.py`. Maya source read: `src/core/glm_fast_path.cu` (service thread, lane, disk reads),
`glm_fast_state.hpp` (`Workers`), `src/platform/direct_file.cpp`.

## 1. How a missed expert is read (from the source)
- One **service thread** per GPU consumes every route in order. For a route with experts that are in neither VRAM nor the RAM tier it reads
  each missing expert as 3 parts (gate, up, down) x `STRATA_GLM_READ_CHUNKS` (8) jobs on a pool of **8 worker threads + itself**; every job is one
  synchronous read (Windows: `FILE_FLAG_NO_BUFFERING`), so the drive's queue depth during a wait is at most 9. The answer (pointers) is published
  to the device only when all chunks of all missing experts are in.
- After that the same thread runs the **CPU lane** (RAM-tier experts computed on the host) while the device computes the fetched ones.
  So read and lane are sequential per route (the lane overlaps the device's compute, not the read).
- Lookahead/prefetch exists (`STRATA_GLM_AHEAD`, opt-in); Phase 2 measured it as no gain on this PC.

## 2. What the numbers say (medians of n = 3; `exp4-tier-sweep`, `io_analysis.py`)
| tier | MB per disk read | GB/s while waiting | waits/tok | ms/wait | disk ms/tok | everything else ms/tok |
|---|---|---|---|---|---|---|
| 26 GB | 8.66 | 6.06 | 24.3 | 2.03 | 49.5 | 36.9 |
| 32 GB | 8.70 | 6.02 | 20.1 | 1.77 | 36.1 | 36.6 |
| 38 GB | 8.71 | 5.93 | 15.7 | 1.52 | 23.9 | 35.9 |
| 42 GB | 8.64 | 5.81 | 13.0 | 1.33 | 17.6 | 35.6 |

1. **During a wait the drive delivers ~6 GB/s whatever the tier** (bytes the OS counter saw on the drive / the engine's wait time; includes
   anything else reading that drive). That is close to what this class of drive does for large reads, so a wait is **bandwidth-bound, not
   latency-bound**: ms per wait falls with the tier only because fewer experts are read per wait (1.42 -> 0.91 per wait).
   (We did not run a raw-I/O benchmark of the drive in this session; "close to the rated sequential read" is the SN850X's data-sheet class, not our measurement.)
2. **The bottleneck moves, it does not disappear:** disk share of a token 57% (26 GB) -> 33% (42 GB); the rest of the token stays at **~36 ms**
   whatever the tier (86.3-49.5, 72.7-36.1, 59.9-23.9, 53.1-17.6). That floor (~28 tokens/s) is what a tier big enough to hold every expert off-card would approach; it is the next
   thing to look at (GPU work, PCIe fetches of RAM-tier experts, the CPU lane, synchronisation) and was not decomposed here.
3. **Reader tuning has little room to give:** at ~6 GB/s the reads are within roughly 10-20% of what the drive can deliver; the knobs below were screened rather than assumed (see `results/phase3/exp7-opt`).

## 3. A trace for the lane/read overlap question (dev branch, `STRATA_GLM_IO_TRACE=1`)
Counts, per token, the routes that read the SSD and then ran the CPU lane, with the lane's time, the read's time in them, and `min(read, lane)` = the most an overlap could hide.
| tier | routes/tok with both | lane ms/tok in them | read ms/tok in them | `min(read, lane)` ms/tok | of a token |
|---|---|---|---|---|---|
| 26 GB | ~13 | ~3.3 | ~27 | ~3.1 | ~3.6% |
| 42 GB | ~8.5 | ~2.3 | ~12.5 | ~2.0 | ~3.8% |

Trace overhead (same binary, trace off vs on): decode -0.8% (26 GB) and -1.9% (42 GB; ranges overlap).
The overlap itself was built and measured in Exp7: +0.7% / +0.6%, i.e. nowhere near the bound -> not proposed upstream.

## 4. Not done
Per-expert access distributions, host/device synchronisation time, and a GPU timeline decomposition of the ~36 ms floor.
