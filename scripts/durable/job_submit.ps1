# Submit a job (spec file, see job_runner.ps1) as a one-shot Windows scheduled task for the current user and start it.
#   powershell -File scripts\durable\job_submit.ps1 -SpecFile spec.json
# The task runs outside the caller's process tree (Task Scheduler is its parent), with no execution time limit of its own
# (the spec's timeout_min is enforced by the runner). Priority 4 = normal: a task's default is 7 (below normal), which slowed the engine's CPU lane and SSD reads ~2-3x.  It runs while this user is logged on; it does not survive a log-off
# or a reboot.  Remove a finished task with job_submit.ps1 -SpecFile spec.json -Remove.
param([Parameter(Mandatory = $true)][string]$SpecFile, [switch]$Remove)
$ErrorActionPreference = "Stop"
$spec = Get-Content -Raw $SpecFile | ConvertFrom-Json
$task = "moelab-" + $spec.name
if ($Remove) { Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue; "removed $task"; return }
$runner = Join-Path $PSScriptRoot "job_runner.ps1"
$spec.out_dir | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null; Remove-Item (Join-Path $_ "STOP") -ErrorAction SilentlyContinue }
$act = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ('-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -SpecFile "{1}"' -f $runner, (Resolve-Path $SpecFile))
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -Priority 4
$pri = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $task -Action $act -Settings $set -Principal $pri -Force | Out-Null
Start-ScheduledTask -TaskName $task
"started task $task; status: " + (Join-Path $spec.out_dir "status.json")

