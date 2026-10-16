#!/usr/bin/env python3
"""Hold some VRAM for a while (CUDA runtime via ctypes, Windows): to test that a result does not depend on how much VRAM happens to
be free when an engine starts.   python scripts/vram_hog.py --mib 300 --seconds 3600
Allocates and touches --mib MiB on GPU 0, prints 'holding' and sleeps; ends with the process (or after --seconds)."""
import argparse
import ctypes
import time

ap = argparse.ArgumentParser()
ap.add_argument("--mib", type=int, default=300)
ap.add_argument("--seconds", type=float, default=3600)
ap.add_argument("--dll", default=r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\x64\cudart64_13.dll")
a = ap.parse_args()
rt = ctypes.CDLL(a.dll)
ptr = ctypes.c_void_p()
assert rt.cudaSetDevice(0) == 0
assert rt.cudaMalloc(ctypes.byref(ptr), ctypes.c_size_t(a.mib << 20)) == 0
assert rt.cudaMemset(ptr, 0, ctypes.c_size_t(a.mib << 20)) == 0
rt.cudaDeviceSynchronize()
print(f"holding {a.mib} MiB", flush=True)
time.sleep(a.seconds)
