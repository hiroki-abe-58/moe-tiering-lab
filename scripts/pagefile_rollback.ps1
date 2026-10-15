<#
.SYNOPSIS
  Undo scripts\pagefile_set.ps1: back to a system-managed page file. Needs an elevated shell; never restarts the PC.
  Takes effect at the next boot.
#>
$ErrorActionPreference = 'Stop'
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) { throw 'Run this from an elevated (administrator) PowerShell.' }

Get-CimInstance Win32_PageFileSetting | ForEach-Object { Remove-CimInstance -InputObject $_ }
$cs = Get-CimInstance Win32_ComputerSystem
Set-CimInstance -InputObject $cs -Property @{ AutomaticManagedPagefile = $true }
Write-Host 'Page file management is system-managed again (applies after the next restart). Nothing was restarted.'
