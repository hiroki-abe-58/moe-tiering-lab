# Where the ~36 ms outside the SSD go: an Nsight Systems look at 40-46 decoded tokens (2026-10-16)

Tier 42 GB, `Maya-S-v2-IQ2_XXS`, the engine's non-interactive `generate` mode (nsys does not pass the `--serve` pipes through), default settings, one
prompt, capture window 12 s starting 55 s after launch (`scripts/exp15_nsys.ps1`). The window holds 46 (default) and 41 (`STRATA_GLM_PCIE_SHARE=0.10`)
decoded tokens, one capture each - read the numbers as a picture, not as a measurement with an error bar. Raw capture files stay outside the repo
(140 MB); the CSVs here are `nsys stats` output, `scripts/exp15_tokens.py` splits the kernel list at `argmax_kernel` (one per token).

Median device time per token by kernel group (kernel durations on the device; the spin kernels are the device waiting):

| group | default | `PCIE_SHARE=0.10` | what it is |
|---|---|---|---|
| token span (argmax to argmax) | 56.4 ms | 45.4 ms | |
| `moe_wait` | 17.4 ms (31%) | 12.9 ms | the device spins until the host has read missing experts from the SSD |
| `moe_fetch` | **14.9 ms (26%)** | 4.0 ms | the PCIe pull of RAM-tier experts into VRAM (about 41 experts x 7 MB a token) |
| `moe_cpu_wait` | 0.55 ms | **11.7 ms (26%)** | the device waits for the CPU lane's answer |
| expert kernels (gate/up, down) | 1.9 ms | 1.6 ms | |
| route | 1.0 ms | 1.0 ms | |
| dense (attention, projections, hyper-connections, head) | 7.8 ms (14%) | 7.5 ms | |
| sum of all kernels | 44.1 ms | 39.9 ms | |
| device idle inside the span (launch gaps, host syncs) | ~12 ms (22%) | ~5.5 ms | |

* The non-SSD ~36-38 ms of a default token are: PCIe fetches of RAM-tier experts ~15 ms, the dense part ~8 ms, launch gaps / host syncs ~12 ms, the rest ~3 ms.
  The CPU lane is hidden (0.55 ms of waiting) at the default split.
* Sending almost every RAM-tier expert to the CPU (`PCIE_SHARE=0.10`, +8.6% decode in the 5-round sweep) trades ~11 ms of PCIe fetch for ~11.7 ms of waiting for the lane, and
  the idle gaps shrink with the fetch kernels (12 -> 5.5 ms); the net is the +8.6% seen in `exp11-pcie-share`.
* ~740 kernels and 740 launches a token (`cudaLaunchKernel` 4.5 us each = 3.3 ms of host time), 92 `cudaStreamSynchronize` calls in 46 tokens (2 a token, ~5 ms each: the
  service threads' polling `cudaEventQuery` is 4.6 million calls, 60% of the CUDA API time, on other threads).
* Device-to-host copies in the window: 2,514 x 7 MB (17.6 GB): background demotions of VRAM experts to the RAM tier while the tiers settle in the first tokens.

Where a change could still pay: the PCIe fetch (a faster split is a per-machine calibration, see exp11), the ~12 ms of idle gaps (launch overhead - CUDA graphs for the decode
layers), and the SSD wait (bandwidth-bound, Exp6). Nothing here was changed in the engine.
