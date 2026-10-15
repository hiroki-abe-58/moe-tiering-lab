<#
.SYNOPSIS
  Read-only audit of a Windows PC for MoE expert-tiering experiments (RAM / commit / VRAM / SSD / security features).

.DESCRIPTION
  Prints one JSON document to stdout (or to -OutFile). It changes nothing. User names and home paths are replaced
  with <user> / ~ so the output can be pasted into a public issue.

.EXAMPLE
  powershell -NoProfile -File scripts\audit_windows.ps1 -OutFile audit.json
#>
param([string]$OutFile)

$ErrorActionPreference = 'SilentlyContinue'
$GiB = 1GB

function Scrub([string]$s) {
  if ($null -eq $s) { return $s }
  $s = $s.Replace($env:USERPROFILE, '~').Replace($env:USERNAME, '<user>')
  return $s
}

$os   = Get-CimInstance Win32_OperatingSystem
$cs   = Get-CimInstance Win32_ComputerSystem
$cpu  = Get-CimInstance Win32_Processor | Select-Object -First 1
$mem  = Get-CimInstance Win32_PhysicalMemory
$pf   = Get-CimInstance Win32_PageFileUsage
$pfs  = Get-CimInstance Win32_PageFileSetting
$dg   = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard

# commit limit / available, the numbers Windows charges pinned memory and VRAM allocations against
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class MemStat {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Auto)]
  public class MEMORYSTATUSEX { public uint dwLength; public uint dwMemoryLoad; public ulong ullTotalPhys; public ulong ullAvailPhys;
    public ulong ullTotalPageFile; public ulong ullAvailPageFile; public ulong ullTotalVirtual; public ulong ullAvailVirtual; public ulong ullAvailExtendedVirtual;
    public MEMORYSTATUSEX() { dwLength = (uint)Marshal.SizeOf(typeof(MEMORYSTATUSEX)); } }
  [DllImport("kernel32.dll", CharSet=CharSet.Auto, SetLastError=true)] public static extern bool GlobalMemoryStatusEx([In, Out] MEMORYSTATUSEX lpBuffer);
}
'@
$ms = New-Object MemStat+MEMORYSTATUSEX
[void][MemStat]::GlobalMemoryStatusEx($ms)

$gpus = @()
$smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($smi) {
  $q = 'name,driver_version,memory.total,memory.used,pcie.link.gen.current,pcie.link.gen.max,pcie.link.width.current,pcie.link.width.max,driver_model.current'
  $gpus = & nvidia-smi --query-gpu=$q --format=csv,noheader,nounits | ForEach-Object {
    $f = $_ -split ',\s*'
    [ordered]@{ name=$f[0]; driver=$f[1]; vram_total_mib=[int]$f[2]; vram_used_mib=[int]$f[3]; pcie_gen_now=$f[4]; pcie_gen_max=$f[5]; pcie_width_now=$f[6]; pcie_width_max=$f[7]; driver_model=$f[8] }
  }
}

# Win32_DiskDrive and DriveInfo answer in milliseconds; Get-PhysicalDisk / Get-Volume (the Storage cmdlets) took
# minutes on a PC with an idle hard disk, so they are not used. Media type (SSD/HDD) is therefore not reported:
# the model name identifies the drive.
$disks = Get-CimInstance Win32_DiskDrive | ForEach-Object {
  [ordered]@{ model=$_.Model; interface=$_.InterfaceType; size_gb=[math]::Round($_.Size/$GiB) }
}
$vols = [System.IO.DriveInfo]::GetDrives() | Where-Object { $_.DriveType -eq 'Fixed' -and $_.IsReady } | ForEach-Object {
  [ordered]@{ drive=$_.Name.TrimEnd('\'); fs=$_.DriveFormat; size_gb=[math]::Round($_.TotalSize/$GiB); free_gb=[math]::Round($_.AvailableFreeSpace/$GiB,1) }
}

$audit = [ordered]@{
  collected_utc = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
  os            = [ordered]@{ caption=$os.Caption; build=$os.BuildNumber; version=$os.Version }
  cpu           = [ordered]@{ name=$cpu.Name.Trim(); cores=$cpu.NumberOfCores; logical=$cpu.NumberOfLogicalProcessors; smt=($cpu.NumberOfLogicalProcessors -gt $cpu.NumberOfCores) }
  ram           = [ordered]@{
    total_gb=[math]::Round($ms.ullTotalPhys/$GiB,1); avail_gb=[math]::Round($ms.ullAvailPhys/$GiB,1)
    commit_limit_gb=[math]::Round($ms.ullTotalPageFile/$GiB,1); commit_avail_gb=[math]::Round($ms.ullAvailPageFile/$GiB,1)
    modules=@($mem | ForEach-Object { [ordered]@{ gb=[math]::Round($_.Capacity/$GiB); speed_mts=$_.Speed; configured_mts=$_.ConfiguredClockSpeed } })
  }
  pagefile      = [ordered]@{
    system_managed = [bool]$cs.AutomaticManagedPagefile
    files = @($pf | ForEach-Object { [ordered]@{ name=(Scrub $_.Name); allocated_mb=$_.AllocatedBaseSize; current_use_mb=$_.CurrentUsage; peak_use_mb=$_.PeakUsage } })
    custom = @($pfs | ForEach-Object { [ordered]@{ name=(Scrub $_.Name); initial_mb=$_.InitialSize; maximum_mb=$_.MaximumSize } })
  }
  security      = [ordered]@{
    hypervisor_present = $cs.HypervisorPresent
    vbs_status         = $dg.VirtualizationBasedSecurityStatus
    services_running   = @($dg.SecurityServicesRunning)   # 2 = HVCI (memory integrity)
  }
  gpus          = @($gpus)
  physical_disks = @($disks)
  volumes       = @($vols)
}

$json = $audit | ConvertTo-Json -Depth 6
if ($OutFile) { Set-Content -Path $OutFile -Value $json -Encoding utf8 } else { $json }
