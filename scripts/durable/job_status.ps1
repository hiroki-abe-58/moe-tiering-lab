# Print a job's status.json, heartbeat age and the tail of its logs.   powershell -File scripts\durable\job_status.ps1 -OutDir <dir> [-Tail 15]
param([Parameter(Mandatory = $true)][string]$OutDir, [int]$Tail = 15)
$s = Join-Path $OutDir "status.json"
if (-not (Test-Path $s)) { "no status yet"; return }
Get-Content $s
$h = Join-Path $OutDir "heartbeat.txt"
if (Test-Path $h) { "heartbeat age: {0:N0} s" -f ((Get-Date) - (Get-Item $h).LastWriteTime).TotalSeconds }
foreach ($f in "stdout.log", "stderr.log", "runner.log") { $p = Join-Path $OutDir $f; if (Test-Path $p) { "--- $f"; Get-Content $p -Tail $Tail } }
