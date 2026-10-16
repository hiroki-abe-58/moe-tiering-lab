# Runs ONE job from a spec file, as a Windows scheduled task (job_submit.ps1 makes the task), so it does not belong to the
# interactive session (or the Claude Code process tree) that started it.
#
# spec.json: { "name", "exe", "args": [..], "cwd", "out_dir", "timeout_min", "env": {K: V},
#              "stop_strata": bool, "restore_strata": bool,
#              "gpu_temp_stop": 85, "min_phys_gb": 4, "min_commit_gb": 5 }
# Writes into out_dir: status.json (state, pids, times, exit code), heartbeat.txt (every 10 s), stdout.log, stderr.log,
# runner.log.  A file named STOP in out_dir ends the job (its process tree is killed) and the runner still cleans up.
# The runner: keeps the system awake while the job lives; kills the job's process tree on timeout, STOP, GPU >= limit for
# 3 samples, or free RAM / commit headroom below the limits for 3 samples; restores Strata at the end only if it stopped
# it, nothing else holds the GPU, and the headroom allows.  It never reboots, never touches settings.
param([Parameter(Mandatory = $true)][string]$SpecFile)
$ErrorActionPreference = "Stop"
$spec = Get-Content -Raw $SpecFile | ConvertFrom-Json
$out = $spec.out_dir
New-Item -ItemType Directory -Force -Path $out | Out-Null
$statusFile = Join-Path $out "status.json"
$runnerLog = Join-Path $out "runner.log"
$status = [ordered]@{ name = $spec.name; state = "starting"; runner_pid = $PID; job_pid = $null; started = (Get-Date -Format s); ended = $null;
                      exit_code = $null; reason = ""; strata_stopped = $false; strata_restored = $null; notes = @() }
function Save-Status { ($status | ConvertTo-Json -Depth 5) | Set-Content -Path $statusFile -Encoding utf8 }
function Log([string]$m) { "{0} {1}" -f (Get-Date -Format s), $m | Add-Content -Path $runnerLog -Encoding utf8 }
Add-Type -Namespace Win -Name Pwr -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
[void][Win.Pwr]::SetThreadExecutionState([uint32]2147483649)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED, released on exit
Save-Status

# (no CIM/WMI here: in Windows PowerShell 5.1 on this PC its first call took ~35 s)
function Stop-Strata {
    $roots = @(Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like 'E:\Strata\.venv\*' })
    if ($roots.Count -eq 0) { Log "strata: not running"; return $false }
    $shells = @(Get-Process cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*Strata IQ2_XS*' })
    foreach ($r in $roots) { & taskkill.exe /T /F /PID $r.Id | Out-Null }
    foreach ($s in $shells) { & taskkill.exe /T /F /PID $s.Id | Out-Null }
    Log "strata: stopped"
    return $true
}
function Read-Gauges {
    $g = (& nvidia-smi --query-gpu=temperature.gpu,memory.used --format=csv,noheader,nounits) -split ',\s*'
    $c = Get-Counter '\Memory\Available Bytes', '\Memory\Committed Bytes', '\Memory\Commit Limit'
    [pscustomobject]@{ temp = [double]$g[0]; vram_mib = [double]$g[1]; phys_free_gb = $c.CounterSamples[0].CookedValue / 1GB
                       commit_avail_gb = ($c.CounterSamples[2].CookedValue - $c.CounterSamples[1].CookedValue) / 1GB }
}
try {
    if ($spec.stop_strata) {
        $status.strata_stopped = Stop-Strata
        if ($status.strata_stopped) {
            for ($i = 0; $i -lt 60; $i++) { Start-Sleep -Seconds 2; if ((Read-Gauges).vram_mib -lt 3000) { break } }
            Log ("gpu memory after stopping strata: {0} MiB" -f (Read-Gauges).vram_mib)
        }
    }
    if ($spec.env) { foreach ($p in $spec.env.PSObject.Properties) { [Environment]::SetEnvironmentVariable($p.Name, [string]$p.Value, "Process") } }
    $argLine = if ($spec.args) { ($spec.args | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join " " } else { "" }
    $sp = @{ FilePath = $spec.exe; WorkingDirectory = $spec.cwd; PassThru = $true; NoNewWindow = $true
             RedirectStandardOutput = (Join-Path $out "stdout.log"); RedirectStandardError = (Join-Path $out "stderr.log") }
    if ($argLine) { $sp.ArgumentList = $argLine }
    $job = Start-Process @sp; $null = $job.Handle
    $status.job_pid = $job.Id; $status.state = "running"; Save-Status
    Log "job started pid $($job.Id): $($spec.exe) $argLine"
    $deadline = (Get-Date).AddMinutes([double]$spec.timeout_min)
    $tempLim = if ($spec.gpu_temp_stop) { [double]$spec.gpu_temp_stop } else { 85 }
    $minPhys = if ($spec.min_phys_gb) { [double]$spec.min_phys_gb } else { 4 }
    $minCommit = if ($spec.min_commit_gb) { [double]$spec.min_commit_gb } else { 5 }
    $bad = 0; $tick = 0; $reason = ""
    while (-not $job.HasExited) {
        "{0} pid={1}" -f (Get-Date -Format s), $job.Id | Set-Content -Path (Join-Path $out "heartbeat.txt")
        if ((Get-Date) -gt $deadline) { $reason = "timeout"; break }
        if (Test-Path (Join-Path $out "STOP")) { $reason = "stop-file"; break }
        if ($tick % 3 -eq 0) {
            try {
                $g = Read-Gauges
                if ($g.temp -ge $tempLim -or $g.phys_free_gb -lt $minPhys -or $g.commit_avail_gb -lt $minCommit) { $bad++ } else { $bad = 0 }
                if ($bad -ge 3) { $reason = ("safety: gpu {0} C, phys free {1:N1} GB, commit avail {2:N1} GB" -f $g.temp, $g.phys_free_gb, $g.commit_avail_gb); break }
            } catch { Log "gauge error: $($_.Exception.Message)" }
        }
        $tick++
        Start-Sleep -Seconds 5; $job.Refresh()
    }
    if ($reason) {
        Log "ending the job: $reason"
        & taskkill.exe /T /F /PID $job.Id | Out-Null
        Start-Sleep -Seconds 3; $job.Refresh()
        $status.state = if ($reason -eq "timeout") { "timeout" } elseif ($reason -eq "stop-file") { "stopped" } else { "safety-stop" }
        $status.reason = $reason
    } else {
        $status.state = "finished"
    }
    $status.exit_code = if ($job.HasExited) { $job.ExitCode } else { $null }
} catch {
    $status.state = "runner-error"; $status.reason = $_.Exception.Message
    Log "runner error: $($_.Exception.Message)"
} finally {
    $status.ended = (Get-Date -Format s)
    if ($spec.restore_strata -and $status.strata_stopped) {
        try {
            $g = Read-Gauges
            $mayaUp = @(Get-Process strata -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "E:\oss\*" }).Count -gt 0
            if (-not $mayaUp -and $g.vram_mib -lt 3000 -and $g.phys_free_gb -gt 30 -and $g.commit_avail_gb -gt 30) {
                Start-Process -FilePath "E:\Strata\run-iq2_xs.bat" -WorkingDirectory "E:\Strata" -WindowStyle Minimized
                $status.strata_restored = "started"
                Log "strata: restore started"
            } else {
                $status.strata_restored = "not restored: mayaUp=$mayaUp vram=$($g.vram_mib) physfree=$([math]::Round($g.phys_free_gb,1)) commitavail=$([math]::Round($g.commit_avail_gb,1))"
                Log $status.strata_restored
            }
        } catch { $status.strata_restored = "restore error: $($_.Exception.Message)" }
    }
    Save-Status
    [void][Win.Pwr]::SetThreadExecutionState([uint32]2147483648)
    Log "runner done: $($status.state)"
}




