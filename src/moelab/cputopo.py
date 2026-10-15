"""CPU topology on Windows: which logical CPUs are performance cores and which are efficiency cores.

Uses ``GetSystemCpuSetInformation`` (Windows 10+). ``parse_cpu_sets`` is pure so it is tested without Windows.
Efficiency class: a higher number is a faster class; on Intel hybrid parts P-cores report 1 and E-cores 0.
"""
from __future__ import annotations

import struct
import sys
from dataclasses import dataclass
from typing import Dict, List

# SYSTEM_CPU_SET_INFORMATION, CpuSet member: Size, Type, Id, Group(u16), LogicalProcessorIndex, CoreIndex,
# LastLevelCacheIndex, NumaNodeIndex, EfficiencyClass, AllFlags (u8 each)
_HEAD = struct.Struct("<IIIHBBBBBB")
_CPU_SET_TYPE = 0   # CpuSetInformation


@dataclass(frozen=True)
class LogicalCpu:
    index: int          # logical processor index within its group
    group: int
    core: int
    llc: int
    numa: int
    efficiency_class: int


def parse_cpu_sets(buf: bytes) -> List[LogicalCpu]:
    out: List[LogicalCpu] = []
    off = 0
    while off + _HEAD.size <= len(buf):
        size, typ, _id, group, lp, core, llc, numa, eff, _flags = _HEAD.unpack_from(buf, off)
        if size < _HEAD.size:
            raise ValueError(f"bad record size {size} at offset {off}")
        if typ == _CPU_SET_TYPE:
            out.append(LogicalCpu(lp, group, core, llc, numa, eff))
        off += size
    return out


def classify(cpus: List[LogicalCpu]) -> Dict[str, List[int]]:
    """{'P': [...], 'E': [...], 'all': [...]} of logical indices (group 0). A non-hybrid CPU has only 'P'."""
    classes = sorted({c.efficiency_class for c in cpus})
    top = classes[-1] if classes else 0
    res: Dict[str, List[int]] = {"P": [], "E": [], "all": []}
    for c in cpus:
        if c.group != 0:
            continue
        res["all"].append(c.index)
        (res["P"] if c.efficiency_class == top else res["E"]).append(c.index)
    return res


def mask(indices: List[int]) -> int:
    m = 0
    for i in indices:
        m |= 1 << i
    return m


def read_system() -> List[LogicalCpu]:
    if sys.platform != "win32":
        raise OSError("cpu sets are read through the Windows API only")
    import ctypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    need = ctypes.c_ulong(0)
    k32.GetSystemCpuSetInformation(None, 0, ctypes.byref(need), None, 0)
    buf = ctypes.create_string_buffer(need.value)
    if not k32.GetSystemCpuSetInformation(buf, need.value, ctypes.byref(need), None, 0):
        raise OSError(ctypes.get_last_error(), "GetSystemCpuSetInformation failed")
    return parse_cpu_sets(buf.raw[:need.value])


def get_process_affinity() -> int:
    import ctypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    proc, system = ctypes.c_size_t(0), ctypes.c_size_t(0)
    k32.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    if not k32.GetProcessAffinityMask(k32.GetCurrentProcess(), ctypes.byref(proc), ctypes.byref(system)):
        raise OSError(ctypes.get_last_error(), "GetProcessAffinityMask failed")
    return proc.value


def resolve_affinity(spec: str, cpus: List[LogicalCpu]) -> int:
    """'P' | 'E' | 'all' | '0xMASK' -> a mask. P/E raise on a CPU that is not hybrid."""
    if spec.lower().startswith("0x"):
        return int(spec, 16)
    cls = classify(cpus)
    if spec == "all":
        return mask(cls["all"])
    if spec in ("P", "E"):
        if not cls["E"]:
            raise ValueError("this CPU has a single core class: AFFINITY=P/E is meaningless here")
        return mask(cls[spec])
    raise ValueError(f"AFFINITY must be P, E, all or 0xMASK, got {spec!r}")


def set_process_affinity(m: int) -> None:
    """Restrict THIS process (and the children it starts afterwards) to the logical CPUs in mask m."""
    import ctypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    k32.SetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    if not k32.SetProcessAffinityMask(k32.GetCurrentProcess(), m):
        raise OSError(ctypes.get_last_error(), "SetProcessAffinityMask failed")


if __name__ == "__main__":
    import json
    cpus = read_system()
    cls = classify(cpus)
    print(json.dumps({"logical": len(cpus), "P": cls["P"], "E": cls["E"],
                      "mask_P": hex(mask(cls["P"])), "mask_E": hex(mask(cls["E"])), "mask_all": hex(mask(cls["all"])),
                      "classes": sorted({c.efficiency_class for c in cpus}),
                      "llc_groups": sorted({c.llc for c in cpus}), "numa_nodes": sorted({c.numa for c in cpus})}))
