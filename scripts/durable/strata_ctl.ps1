# Stop / start / check the Strata server (E:\Strata\run-iq2_xs.bat) by hand.   strata_ctl.ps1 stop|start|status
# (job_runner.ps1 does the same around a job when the spec says stop_strata / restore_strata.)
param([Parameter(Mandatory = $true)][ValidateSet("stop", "start", "status")][string]$Action)
$roots = @(Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like 'E:\Strata\.venv\*' })
switch ($Action) {
    "stop" {
        $shells = @(Get-Process cmd -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*Strata IQ2_XS*' })
        foreach ($r in $roots) { & taskkill.exe /T /F /PID $r.Id | Out-Null }
        foreach ($s in $shells) { & taskkill.exe /T /F /PID $s.Id | Out-Null }
        "stopped ($($roots.Count) server process(es))"
    }
    "start" {
        if ($roots.Count -gt 0) { "already running"; return }
        Start-Process -FilePath "E:\Strata\run-iq2_xs.bat" -WorkingDirectory "E:\Strata" -WindowStyle Minimized
        "started"
    }
    "status" {
        $h = try { (Invoke-WebRequest -Uri http://127.0.0.1:8080/health -UseBasicParsing -TimeoutSec 3).StatusCode } catch { "no answer" }
        "server processes: $($roots.Count); health: $h"
    }
}
