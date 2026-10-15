# What is being measured: expert tiering in Strata-family engines

Strata (Niko1221/Strata, MIT) and Project Maya (mw00/project-maya, MIT, built on Strata's engine code for GLM-5.3-Flash)
run mixture-of-experts models that are larger than VRAM by keeping the always-needed weights on the GPU and treating the
routed experts as a cache hierarchy. Described here only as far as the measurements in this repository rely on it; the
authoritative description is each project's own documentation.

```
 VRAM expert pool  --  RAM tier (pinned host memory)  --  SSD (the model files)
   hit: the GPU          hit: the CPU lane computes          miss: a disk read
   runs the expert       the expert, or it is copied         lands in a pinned staging
                         over PCIe to the pool               buffer ("a wait")
```

- A token's routed experts are looked up per layer. A **VRAM hit** costs nothing extra. A **RAM-tier** expert is either
  computed by the **CPU lane** (a pool of CPU threads) or copied over PCIe, whichever the start-up timing says is
  faster. A miss is read from the SSD, and the layer **waits** for it.
- The engine prints per decode (`glm stat:`): VRAM hit %, RAM fetches/token, disk reads/token, disk waits/token, disk
  ms/token, promotions/token, CPU-lane experts and ms per token. `moelab.mayaparse` parses these.
- **The RAM tier is page-locked memory** (`cudaHostAlloc`). Windows charges it to the commit limit (RAM + page file),
  as it does every allocation on the card, so on Windows the page file size bounds the tier
  (`min(available RAM, available commit)` less headroom, Maya `glm_fast_path.cu`).
- Bigger tier -> fewer experts from the SSD -> fewer waits per token. [Findings, section 3](findings.md#3-ram-tier-size-is-the-lever-and-the-page-file-sets-the-tier)
  measures that slope on one PC.

## What this repository adds

| path | purpose |
|---|---|
| `scripts/maya_ab.py` | interleaved A/B driver around Maya's `--bench`; records every run |
| `src/moelab/mayaparse.py` | parses `maya-bench.txt` and `glm stat:` lines |
| `src/moelab/abreport.py`, `stats.py` | medians, MAD, % change, "above noise" flag, RAM-tier mismatch warning |
| `src/moelab/cputopo.py` | P/E core classes and process affinity from `GetSystemCpuSetInformation` |
| `tools/pin_probe/` | how much page-locked memory the driver lets a process pin, next to commit/RAM numbers |
| `scripts/audit_windows.ps1` | read-only, path-scrubbed machine audit |

Maya's own `--bench`, `--calibrate` and `--report` are not replaced; the driver calls `--bench`.
