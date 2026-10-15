<#
.SYNOPSIS
  Pin C:\pagefile.sys to a fixed size (initial = maximum) so Windows' commit limit is large enough for Maya's pinned
  RAM tier plus the VRAM it is charged for. Needs an elevated shell. Never restarts the PC.

.DESCRIPTION
  - refuses unless the drive keeps >= -MinFreeGB free after the page file,
  - refuses sizes outside 32768-131072 MB,
  - does not touch crash-dump settings, the registry directly, or any other page file,
  - writes the state it found to -StateFile first so scripts\pagefile_rollback.ps1 has something to compare with.
  The change is applied by Windows at the NEXT BOOT. Until then nothing changes.

.EXAMPLE
  powershell -NoProfile -File scripts\pagefile_set.ps1 -SizeMB 49152 -StateFile results\phase2\state-before-apply.json
#>
param(
  [int]$SizeMB = 49152,
  [string]$Drive = 'C:',
  [int]$MinFreeGB = 200,
  [Parameter(Mandatory = $true)][string]$StateFile
)
$ErrorActionPreference = 'Stop'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw 'Run this from an elevated (administrator) PowerShell.' }
if ($SizeMB -lt 32768 -or $SizeMB -gt 131072) { throw "SizeMB $SizeMB is outside 32768-131072." }

$di = [System.IO.DriveInfo]::new($Drive)
if (-not $di.IsReady -or $di.DriveType -ne 'Fixed') { throw "$Drive is not a ready fixed drive." }
$freeGB = $di.AvailableFreeSpace / 1GB
$cur = Get-CimInstance Win32_PageFileUsage | Where-Object { $_.Name -like "$Drive*" } | Select-Object -First 1
$curGB = if ($cur) { $cur.AllocatedBaseSize / 1024 } else { 0 }
$needGB = $SizeMB / 1024 - $curGB     # the file already holds curGB of the drive
if ($freeGB - $needGB -lt $MinFreeGB) { throw ("Only {0:N0} GB free on {1}; need {2:N0} GB more and a {3} GB reserve." -f $freeGB, $Drive, $needGB, $MinFreeGB) }

& (Join-Path $PSScriptRoot 'pagefile_state.ps1') -OutFile $StateFile -Label 'before-apply'
Write-Host "State saved to $StateFile"

$cs = Get-CimInstance Win32_ComputerSystem
if ($cs.AutomaticManagedPagefile) {
  Set-CimInstance -InputObject $cs -Property @{ AutomaticManagedPagefile = $false }
  Write-Host 'Automatic page file management: off'
}
$name = "$Drive\pagefile.sys"
$setting = Get-CimInstance Win32_PageFileSetting | Where-Object { $_.Name -ieq $name }
if ($setting) {
  Set-CimInstance -InputObject $setting -Property @{ InitialSize = [uint32]$SizeMB; MaximumSize = [uint32]$SizeMB }
} else {
  New-CimInstance -ClassName Win32_PageFileSetting -Property @{ Name = $name; InitialSize = [uint32]$SizeMB; MaximumSize = [uint32]$SizeMB } | Out-Null
}
Get-CimInstance Win32_PageFileSetting | Select-Object Name, InitialSize, MaximumSize | Format-Table -AutoSize | Out-String | Write-Host
Write-Host "Done. $name will be $SizeMB MB after the next restart. NOTHING was restarted."
