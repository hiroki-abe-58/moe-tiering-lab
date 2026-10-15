// pin_probe: how much page-locked host memory can this Windows/Linux box pin through the CUDA driver?
//
// Project Maya's RAM tier is cudaHostAlloc memory; on Windows the driver refuses past a cap (Maya #67, #147, #185).
// This tool measures that cap in isolation, next to the numbers that could explain it (physical RAM, commit
// limit/available, free VRAM), so a cap can be told apart from a commit-limit shortfall.
//
//   pin_probe [--chunk-mb N] [--max-gb N] [--mode alloc|register] [--hold]
//
// Output is one `key=value` line per fact plus a final `RESULT` line, easy to paste into an issue.
// MIT licensed (see LICENSE of this repository).
#include <cuda_runtime.h>

#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#else
#include <sys/mman.h>
#include <unistd.h>
#endif

static const double GiB = 1073741824.0;

struct MemInfo {
    double phys_total = 0, phys_avail = 0, commit_limit = 0, commit_avail = 0;
};

static MemInfo mem_info() {
    MemInfo m;
#ifdef _WIN32
    MEMORYSTATUSEX s{};
    s.dwLength = sizeof s;
    if (GlobalMemoryStatusEx(&s)) {
        m.phys_total = (double) s.ullTotalPhys / GiB;
        m.phys_avail = (double) s.ullAvailPhys / GiB;
        m.commit_limit = (double) s.ullTotalPageFile / GiB;   // commit limit (RAM + page file)
        m.commit_avail = (double) s.ullAvailPageFile / GiB;
    }
#else
    const long pages = sysconf(_SC_PHYS_PAGES), avail = sysconf(_SC_AVPHYS_PAGES), ps = sysconf(_SC_PAGESIZE);
    m.phys_total = (double) pages * ps / GiB;
    m.phys_avail = (double) avail * ps / GiB;
#endif
    return m;
}

static void print_mem(const char* tag) {
    const MemInfo m = mem_info();
    std::printf("%s phys_total_gb=%.2f phys_avail_gb=%.2f commit_limit_gb=%.2f commit_avail_gb=%.2f\n", tag, m.phys_total,
                m.phys_avail, m.commit_limit, m.commit_avail);
}

int main(int argc, char** argv) {
    size_t chunk_mb = 1024;
    double max_gb = 1e9;
    std::string mode = "alloc";
    bool hold = false;
    for (int i = 1; i < argc; ++i) {
        if (!std::strcmp(argv[i], "--chunk-mb") && i + 1 < argc) chunk_mb = (size_t) std::atoll(argv[++i]);
        else if (!std::strcmp(argv[i], "--max-gb") && i + 1 < argc) max_gb = std::atof(argv[++i]);
        else if (!std::strcmp(argv[i], "--mode") && i + 1 < argc) mode = argv[++i];
        else if (!std::strcmp(argv[i], "--hold")) hold = true;
        else { std::fprintf(stderr, "usage: pin_probe [--chunk-mb N] [--max-gb N] [--mode alloc|register] [--hold]\n"); return 2; }
    }
    if (mode != "alloc" && mode != "register") { std::fprintf(stderr, "bad --mode\n"); return 2; }

    int dev = 0;
    cudaDeviceProp prop{};
    if (cudaGetDevice(&dev) != cudaSuccess || cudaGetDeviceProperties(&prop, dev) != cudaSuccess) {
        std::fprintf(stderr, "no CUDA device\n");
        return 1;
    }
    size_t vfree = 0, vtotal = 0;
    cudaMemGetInfo(&vfree, &vtotal);
    std::printf("device=%s vram_total_gb=%.2f vram_free_gb=%.2f\n", prop.name, (double) vtotal / GiB, (double) vfree / GiB);
    std::printf("mode=%s chunk_mb=%zu\n", mode.c_str(), chunk_mb);
    print_mem("before");

    const size_t chunk = chunk_mb << 20;
    std::vector<void*> held;
    std::vector<bool> from_os;
    double pinned_gb = 0;
    cudaError_t last = cudaSuccess;
    const auto t0 = std::chrono::steady_clock::now();
    while (pinned_gb + (double) chunk / GiB <= max_gb) {
        void* p = nullptr;
        if (mode == "alloc") {
            last = cudaHostAlloc(&p, chunk, cudaHostAllocPortable);
        } else {
#ifdef _WIN32
            p = VirtualAlloc(nullptr, chunk, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
#else
            p = mmap(nullptr, chunk, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
            if (p == MAP_FAILED) p = nullptr;
#endif
            if (p == nullptr) { last = cudaErrorMemoryAllocation; }
            else {
                std::memset(p, 1, chunk);   // touch: make it resident before registering
                last = cudaHostRegister(p, chunk, cudaHostRegisterPortable);
                if (last != cudaSuccess) {
#ifdef _WIN32
                    VirtualFree(p, 0, MEM_RELEASE);
#else
                    munmap(p, chunk);
#endif
                    p = nullptr;
                }
            }
        }
        if (last != cudaSuccess || p == nullptr) break;
        held.push_back(p);
        pinned_gb += (double) chunk / GiB;
    }
    const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    const std::string why = last == cudaSuccess ? "reached --max-gb" : cudaGetErrorString(last);
    cudaGetLastError();
    print_mem("at_refusal");
    const MemInfo m = mem_info();
    std::printf("RESULT mode=%s chunk_mb=%zu pinned_gb=%.2f pct_of_phys=%.1f seconds=%.1f stopped_by=\"%s\"\n", mode.c_str(),
                chunk_mb, pinned_gb, m.phys_total > 0 ? 100.0 * pinned_gb / m.phys_total : 0.0, secs, why.c_str());
    if (hold) { std::printf("holding; press Enter to release\n"); std::fflush(stdout); std::getchar(); }

    for (void* p : held) {
        if (mode == "alloc") cudaFreeHost(p);
        else {
            cudaHostUnregister(p);
#ifdef _WIN32
            VirtualFree(p, 0, MEM_RELEASE);
#else
            munmap(p, chunk);
#endif
        }
    }
    print_mem("after_release");
    return 0;
}
