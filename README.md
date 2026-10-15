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
| Where does a decode token go? | **~54%** is waiting for the SSD (19.5 waits/token x 2.07 ms). Default decode 11.3-11.7 tokens/s, prefill ~1050 tokens/s at 8K. |
| Does P-core / E-core placement of the CPU lane help on a Core Ultra 9 285K? | **No.** Five arms x 3 interleaved runs: +1.8% (just fewer threads) to -7.1% (P-cores only). No pull request made. |
| What moves the number? | **RAM-tier size.** 10 / 18 / 26 GB tier -> 6.9 / 8.8 / 11.2 tokens/s. On Windows the page file bounds the tier (commit limit); here it was ~21-26 GB. |
| Is there a "WDDM caps pinned RAM at ~70%" limit? ([Maya #185](https://github.com/mw00/project-maya/issues/185)) | **Not on this PC:** 44.5 GB (70.2% of RAM) pinned with no refusal on an RTX 5090, VBS/HVCI on. Pinned memory is charged to the commit limit 1:1. |

Not tested (see findings): output equality between arms, a larger page file / tier above 26 GB, 64K+ context, Linux, AMD,
other CPUs. The gain from a larger tier is only extrapolated, not measured.

## What is here

| | |
|---|---|
| [`scripts/maya_ab.py`](scripts/maya_ab.py) | interleaved, order-reversing A/B driver around Maya's `--bench`; median / range / % / "above noise"; warns if the RAM tier differed between runs; never edits your config |
| [`src/moelab/`](src/moelab) | parsers for `maya-bench.txt` and the engine's `glm stat:` lines, statistics, CPU core classes and affinity (Windows) |
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
