# Reproduction

## The machine

From [`results/audit-rtx5090-285k.json`](../results/audit-rtx5090-285k.json) (`scripts/audit_windows.ps1`):
Windows 11 Pro build 26200; Intel Core Ultra 9 285K (24 cores, 24 threads, no SMT; 8 P + 16 E); 63.4 GB DDR5-5600
(4 x 16 GB); RTX 5090 32 GB, driver 610.88, WDDM, PCIe 5.0 x16; models on a WD_BLACK SN850X 8 TB NVMe; page file
system-managed (~21-26 GB, commit limit ~85-88 GB); VBS and HVCI running; CUDA Toolkit 13.1, Visual Studio 2022 Build
Tools 14.44.

## Software

| | version |
|---|---|
| Project Maya | v1.1.11, `d18719534828bea35dc8b347367e66de59ffb2e1` |
| model | `Maya-S-v2-IQ2_XXS` (3 GGUF files, 96.5 GB listed, 91 GB on disk), installed by Maya's setup with its own sha256 checks |
| Strata (control only) | `296b59d2f73c8f04a805df29c2fa97655adace78` |
| this repository | see `git log` |

## Steps

```powershell
git clone https://github.com/mw00/project-maya.git
cd project-maya
git checkout d18719534828bea35dc8b347367e66de59ffb2e1
.\START-MAYA.bat --check
.\START-MAYA.bat --setup --yes --plain --download-model --model Maya-S-v2-IQ2_XXS `
    --models-dir D:\maya-models --no-start --no-vision --context 32768 --gpu 0
```

Stop anything holding the GPU (Strata, Maya's server). Then, from this repository:

```powershell
# the interleaved sweeps (each ~1 h; the tier pinned so only the setting under test changes)
python scripts\maya_ab.py --maya-dir C:\path\to\project-maya --config maya-maya-s-v2-iq2_xxs.json `
    --common STRATA_GLM_RAM_GB=26 --cond base --cond lane8:STRATA_GLM_CPU_LANE=8 `
    --cond P6:AFFINITY=P,STRATA_GLM_CPU_LANE=6 --cond E12:AFFINITY=E,STRATA_GLM_CPU_LANE=12 `
    --cond P8:AFFINITY=P,STRATA_GLM_CPU_LANE=8 --rounds 3 --out results\exp1-affinity.json

python scripts\maya_ab.py --maya-dir C:\path\to\project-maya --config maya-maya-s-v2-iq2_xxs.json `
    --cond t26:STRATA_GLM_RAM_GB=26 --cond t18:STRATA_GLM_RAM_GB=18 --cond t10:STRATA_GLM_RAM_GB=10 `
    --rounds 3 --out results\exp2-tier-size.json
```

`STRATA_GLM_RAM_GB=26` is what this PC's commit limit allowed; use a value your PC can pin without swapping.
`--common` / `--cond` accept only `STRATA_*`, `MAYA_*` and the pseudo-setting `AFFINITY`. The tool never edits your
Maya config: it writes a temporary copy next to it and deletes it.

### Pinning probe

```powershell
nvcc -O2 -arch=sm_120 -Xcompiler /utf-8 -o build\pin_probe.exe tools\pin_probe\pin_probe.cu   # sm_XX for your GPU
build\pin_probe.exe --max-gb 30 --chunk-mb 1024
```

It pins real memory: keep `--max-gb` below your free RAM (it prints `phys_avail_gb` and `commit_avail_gb` before and at
the end) and close what you cannot afford to have paged out. `--mode register` tests `cudaHostRegister` on
`VirtualAlloc`'d memory instead of `cudaHostAlloc`.

### Machine audit and CPU topology

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\audit_windows.ps1 -OutFile audit.json
set PYTHONPATH=src && python -m moelab.cputopo
```

The audit is read-only and replaces the user name and home folder; read the file once before you post it.

### Tests (no GPU, no model)

```powershell
python -I -m unittest discover -s tests -v
```

### Strata control

`BENCH.bat` (or `python tools\strata_bench.py`) from a Strata checkout, with the Maya server and any other GPU
program stopped.
