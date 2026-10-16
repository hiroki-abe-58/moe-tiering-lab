# moe-tiering-lab

Measurements, tools and negative results from running a ~300B-parameter mixture-of-experts model (GLM-5.3-Flash through
[Project Maya](https://github.com/mw00/project-maya)) on one Windows PC with an RTX 5090 (32 GB VRAM) and 64 GB RAM, where
the experts live in a VRAM / pinned-RAM / SSD hierarchy.

[日本語 README](README.ja.md)

This is not a fork and contains no engine code. It contains what was built to measure someone else's engine honestly,
and what the measurements said.

## What we found (one PC, one model; details and caveats in [docs/findings.md](docs/findings.md))

| Question | Result |
|---|---|
| Where does a decode token go? | At the default 26 GB RAM tier **~54%** of the decode wall time is the engine's service thread blocked on SSD reads (19.5 waits/token x 2.07 ms; a wait = one layer's route with a miss; definition in [findings §1](docs/findings.md)). Default decode 11.3-11.7 tokens/s, prefill ~1050 tokens/s at 8K. |
| Does P-core / E-core placement of the CPU lane help on a Core Ultra 9 285K? | **No.** Five arms x 3 interleaved runs: +1.8% (just fewer threads) to -7.1% (P-cores only). No pull request made. |
| What moves the number? | **RAM-tier size.** Measured: 10 / 18 / 26 GB -> 6.9 / 8.8 / 11.2 tokens/s; after raising the page file to 48 GiB, 26 / 32 / 38 / 42 GB -> **11.7 / 13.8 / 16.7 / 18.8 tokens/s (+61%)**, n = 3 per arm, spread <= ~1%. On Windows the commit limit (RAM + page file) bounded the tier here (~21-26 GB before). Tiers above 42 GB were not tried (free RAM was down to 10 GB). |
| Do different tiers give different tokens? | **Yes, with the default CPU lane** (greedy tokens diverge between tier 26 and 42), **no with `STRATA_GLM_CPU_LANE=0`** (bit-identical, also with MTP forced on). The CPU path and the GPU path of an expert differ at quantisation level (2.9% vs 1.6% L2 error against a double reference on one expert), so which experts the lane takes changes the text. Lane off costs 4-10% decode. 42-task quality suite: 39/42 lane off, 40/42 lane on - no difference detected, none could be at this size. [Details](results/phase3/exp5-determinism/SUMMARY.md). |
| Is there a "WDDM caps pinned RAM at ~70%" limit? ([Maya #185](https://github.com/mw00/project-maya/issues/185)) | **Unproven either way.** All that was shown: 44.5 GB (70.2% of RAM) was pinned with no refusal on an RTX 5090, VBS/HVCI on; the probe stopped because free RAM ran out, so a cap above 44.5 GB is neither shown nor excluded. Pinned memory is charged to the commit limit 1:1. |

| Is the SSD wait something reader tuning can fix? | **Not on this PC.** The drive delivers ~6 GB/s during waits at every tier (bandwidth-bound), and the rest of a token stays ~36 ms. Screens (mostly 2 rounds): CPU-lane/SSD overlap +0.7%, reader threads 0%, 4 chunks +2.1%, promotion knobs 0%. A CPU/PCIe split change gave +7.3% (and Maya's calibrator +8.8%, one sample), but my baseline was uncalibrated, so this is a per-machine tuning point, not a bug; nothing was proposed upstream. [Exp6](results/phase3/exp6-io/SUMMARY.md), [Exp7](results/phase3/exp7-opt/SUMMARY.md). |

| Why do two starts with the same settings give different tokens, and can that be fixed? ([Phase 4](results/phase4/SUMMARY.md)) | **Where the experts sit, not a race.** The VRAM pool is sized from the free VRAM at start (9,453-9,488 experts warmed in five starts), the lane's split comes from a near-tie timing, and decode re-times it / moves experts in the background. With the same placement the lane-on runs are bit-identical (1762 of 1762 positions); pinning pool size, split and background moves gave 70 of 70 identical stream pairs over 5 starts (also after 30 minutes of idle, and with 300 MiB less free VRAM) at the same speed (18.31 vs 18.26 tok/s), where the defaults gave 17 of 70. Proposed upstream as a documentation section: [mw00/project-maya#224](https://github.com/mw00/project-maya/pull/224). |
| Does a more exact CPU lane make the tokens agree with the GPU's? | **No.** Quantising the lane's activations like the device (blocks of 32) cuts its error vs a double-precision reference from 1.73% to 1.09% and its distance to the GPU's expert from 1.94% to 0.06% (9.8e-8 with the device's integer steps too), at -0.5% / -3.6% decode. But the router's top-8 turns any difference above ~1e-6 into a different expert set in 25-60% of the layers within a few tokens, so tokens still part (median 11-17 tokens from the lane-off run in all variants) and the 42-task quality suite does not move. Not proposed upstream; a [reference branch](https://github.com/hiroki-abe-58/project-maya/tree/feat/cpu-lane-act-q8_1) (unit tests pass, -2.6% decode on the latest `main`) is on the fork. |
| `STRATA_GLM_PCIE_SHARE=0.10` vs the default split | **+8.6% decode** (18.13 -> 19.69 tok/s, 5 interleaved rounds, ranges do not overlap), prefill unchanged; Maya's own calibrator had picked 0.10, so no engine change. |
| Where does the rest of a token go? (Nsight Systems, 46 tokens) | At 42 GB: SSD wait 17 ms, PCIe fetch of RAM-tier experts 15 ms, dense compute 8 ms, device idle gaps ~12 ms, CPU lane hidden (0.5 ms). With `PCIE_SHARE=0.10` the fetch shrinks to 4 ms and the device waits 11.7 ms for the lane. [Details](results/phase4/exp15-nsys/SUMMARY.md). |
| Is "the SSD gives ~6 GB/s" the drive's limit? | Measured now: unbuffered random 1.1 MB reads give 6.55 GB/s at queue depth 9 (6.82 at 32), 6.3 GB/s sustained for 80 s. |

Not tested (see findings): tiers above 42 GB, 64K+ context and long-run soak tests (a soak script exists but was never run, so it is not published), DFlash2 / MTP / several GPUs, Linux, AMD, other CPUs.

## What is here

| | |
|---|---|
| [`scripts/maya_ab.py`](scripts/maya_ab.py) | interleaved, order-reversing A/B driver around Maya's `--bench`; median / range / % / "above noise"; warns if the RAM tier differed between runs; never edits your config |
| [`src/moelab/`](src/moelab) | parsers for `maya-bench.txt` and the engine's `glm stat:` lines, statistics, CPU core classes and affinity (Windows) |
| [`scripts/maya_probe.py`](scripts/maya_probe.py), [`scripts/maya_tier_sweep.py`](scripts/maya_tier_sweep.py) | one engine start per run: token ids, TTFT, SSD GB/s, memory / commit / VRAM; interleaved sweeps with token-stream diffing |
| [`scripts/maya_quality.py`](scripts/maya_quality.py) | 42 programmatically graded tasks (math, code, JSON, Japanese, English) for A/B arms of the same engine |
| [`scripts/durable/`](scripts/durable) | run a long job as a Windows scheduled task so it survives the session that started it: runner (timeout, STOP file, safety limits, keep-awake, optional Strata stop/restore), submit, status. A task runs at below-normal priority by default - `job_submit.ps1` sets normal |
| [`scripts/exp9_*.py`](scripts), [`exp10_pairs.py`](scripts/exp10_pairs.py), [`exp13_*.py`](scripts), [`audit_summary.py`](scripts/audit_summary.py) | analysis of the Phase 4 runs: logit/route comparison of two runs, pairwise token-stream diffs, per-layer FFN differences, lane-audit summaries (they read files written by the engine debug patches in `results/phase4/patches/`) |
| [`scripts/pagefile_*.ps1`](scripts) | read / set / roll back the page file (admin; never reboots) - Phase 2 used these |
| [`tools/pin_probe/`](tools/pin_probe) | CUDA program: how much page-locked host memory can a process pin, next to RAM and commit numbers |
| [`scripts/audit_windows.ps1`](scripts/audit_windows.ps1) | read-only machine audit with user names and paths scrubbed (avoids the slow Storage cmdlets) |
| [`results/`](results) | raw per-run JSON and tables for both sweeps, the machine audit, Strata's own benchmark report |
| [`docs/`](docs) | [methodology](docs/methodology.md), [architecture](docs/architecture.md), [findings](docs/findings.md), [reproduction](docs/reproduction.md) |

Tests need no GPU and no model: `python -I -m unittest discover -s tests` (Python 3.10+, standard library only). CI runs
them on Linux and Windows.

## Reproduce

[docs/reproduction.md](docs/reproduction.md) has the exact commit hashes, the model, and the commands. In short:

```powershell
python scripts\maya_ab.py --maya-dir C:\path\to\project-maya --config maya-maya-s-v2-iq2_xxs.json `
    --common STRATA_GLM_RAM_GB=26 --cond base --cond lane8:STRATA_GLM_CPU_LANE=8 --rounds 3 --out results\my-run.json
```

## Limits

One machine, one model (`Maya-S-v2-IQ2_XXS`), 32K context, Maya v1.1.11 only. Runs are n = 3 per arm: the "above noise"
flag is a conservative screen, not a significance test. The Strata benchmark in `results/` is a different model and says
nothing about Strata vs Maya. Model weights are not distributed here.

## Upstream

- Project Maya: https://github.com/mw00/project-maya (MIT) - the engine measured here.
- Strata: https://github.com/Niko1221/Strata (MIT) - the engine Maya's GLM code is built on; Qwen3.8-Flash-Next is its scope.
- Discussion: Maya [#185](https://github.com/mw00/project-maya/issues/185) (pinning; [our comment with the `pin_probe` data](https://github.com/mw00/project-maya/issues/185#issuecomment-6191964007)), Maya
  [#65](https://github.com/mw00/project-maya/issues/65) / [#67](https://github.com/mw00/project-maya/issues/67) (Windows SSD reads, fixed in v1.0.30),
  Strata [#2067](https://github.com/Niko1221/Strata/issues/2067) (GLM request; no maintainer answer when checked).
- Other Strata derivatives checked: [PolyStrata](https://github.com/VecSzn/PolyStrata), [lighttransport/Strata](https://github.com/lighttransport/Strata) (both MIT).

## Credits and license

All engine work belongs to the Strata and Project Maya authors; this repository only measures it. MIT, see [LICENSE](LICENSE).
Parts of this repository were prepared with an AI coding assistant (Claude Code) and reviewed and run by the author.
