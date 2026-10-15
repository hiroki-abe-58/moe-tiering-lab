<#
.SYNOPSIS
  Read-only snapshot of everything that decides how much memory Windows will let a process pin:
  page file configuration, commit limit / committed bytes, crash-dump settings, free disk, GPU memory in use.

.EXAMPLE
  powershell -NoProfile -File scripts\pagefile_state.ps1 -OutFile results\phase2\state-before.json -Label before
#>
param([string]$OutFile, [string]$Label = '')

$ErrorActionPreference = 'SilentlyContinue'
$GiB = 1GB
function Scrub([string]$s) { if ($null -eq $s) { return $s }; $s.Replace($env:USERPROFILE, '~').Replace($env:USERNAME, '<user>') }

$cs  = Get-CimInstance Win32_ComputerSystem
$pfu = Get-CimInstance Win32_PageFileUsage
$pfs = Get-CimInstance Win32_PageFileSetting
$os  = Get-CimInstance Win32_OperatingSystem
$mm  = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management'
$cc  = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl'
$ctr = Get-Counter '\Memory\Committed Bytes', '\Memory\Commit Limit'
$committed = ($ctr.CounterSamples | Where-Object Path -like '*committed bytes').CookedValue
$limit     = ($ctr.CounterSamples | Where-Object Path -like '*commit limit').CookedValue

$vram = $null
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  $vram = (& nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits) -split ',\s*'
}

$state = [ordered]@{
  label = $Label
  collected_utc = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
  is_admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  ram_total_gb = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
  ram_free_gb  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
  commit_limit_gb = [math]::Round($limit / $GiB, 2)
  committed_gb    = [math]::Round($committed / $GiB, 2)
  commit_available_gb = [math]::Round(($limit - $committed) / $GiB, 2)
  vram_used_mib  = if ($vram) { [int]$vram[0] } else { $null }
  vram_total_mib = if ($vram) { [int]$vram[1] } else { $null }
  automatic_managed_pagefile = [bool]$cs.AutomaticManagedPagefile
  registry_PagingFiles = @($mm.PagingFiles)
  registry_ExistingPageFiles = @($mm.ExistingPageFiles | ForEach-Object { Scrub $_ })
  pagefile_usage = @($pfu | ForEach-Object { [ordered]@{ name = (Scrub $_.Name); allocated_mb = $_.AllocatedBaseSize; current_mb = $_.CurrentUsage; peak_mb = $_.PeakUsage } })
  pagefile_setting = @($pfs | ForEach-Object { [ordered]@{ name = (Scrub $_.Name); initial_mb = $_.InitialSize; maximum_mb = $_.MaximumSize } })
  crash_control = [ordered]@{ CrashDumpEnabled = $cc.CrashDumpEnabled; DumpFile = (Scrub $cc.DumpFile); AutoReboot = $cc.AutoReboot; Overwrite = $cc.Overwrite; DedicatedDumpFile = $cc.DedicatedDumpFile }
  clear_pagefile_at_shutdown = $mm.ClearPageFileAtShutdown
  volumes = @([System.IO.DriveInfo]::GetDrives() | Where-Object { $_.DriveType -eq 'Fixed' -and $_.IsReady } | ForEach-Object { [ordered]@{ drive = $_.Name.TrimEnd('\'); size_gb = [math]::Round($_.TotalSize / $GiB); free_gb = [math]::Round($_.AvailableFreeSpace / $GiB, 1) } })
}
$json = $state | ConvertTo-Json -Depth 6
if ($OutFile) { New-Item -ItemType Directory -Force (Split-Path $OutFile) | Out-Null; Set-Content -Path $OutFile -Value $json -Encoding utf8 } else { $json }
