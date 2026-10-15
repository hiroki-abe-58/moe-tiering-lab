# Night-shift monitor: keeps the system awake (SetThreadExecutionState, released when this process exits),
# logs GPU/RAM/commit/SSD every 30 s and stops the Maya engine if a safety limit is hit.
param(
  [string]$Out = "E:\oss\moe-tiering-lab\results\phase3\logs\monitor.csv",
  [string]$Deadline = "",
  [double]$GpuTempStop = 85,
  [double]$MinPhysGb = 5,
  [double]$MinCommitGb = 5,
  [int]$Strikes = 3
)
Add-Type -Namespace Win -Name Pwr -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
# ES_CONTINUOUS | ES_SYSTEM_REQUIRED  (display may turn off)
[void][Win.Pwr]::SetThreadExecutionState(0x80000001)
$dl = if ($Deadline) { [datetime]$Deadline } else { (Get-Date).AddHours(10) }
if (-not (Test-Path $Out)) { "time,gpu_temp,gpu_util,gpu_power_w,vram_mib,gpu_throttle,phys_free_gb,commit_avail_gb,commit_used_pct,note" | Set-Content $Out }
$bad = 0
while ((Get-Date) -lt $dl) {
  try {
    $g = (& nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,power.draw,memory.used,clocks_throttle_reasons.active --format=csv,noheader,nounits) -split ',\s*'
    $os = Get-CimInstance Win32_OperatingSystem
    $phys = $os.FreePhysicalMemory / 1MB
    $c = Get-Counter '\Memory\Committed Bytes','\Memory\Commit Limit'
    $used = $c.CounterSamples[0].CookedValue / 1GB; $lim = $c.CounterSamples[1].CookedValue / 1GB
    $note = ""
    $thr = $g[4].Trim()
    $hot = [double]$g[0] -ge $GpuTempStop
    $low = ($phys -lt $MinPhysGb) -or (($lim - $used) -lt $MinCommitGb)
    if ($hot -or $low) { $bad++ } else { $bad = 0 }
    if ($bad -ge $Strikes) {
      $procs = Get-Process strata -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "E:\oss\project-maya\*" }
      foreach ($p in $procs) { Stop-Process -Id $p.Id -Force; $note += "KILLED maya pid $($p.Id) " }
      $note += "SAFETY(hot=$hot low=$low)"; $bad = 0
    }
    "{0},{1},{2},{3},{4},{5},{6:N1},{7:N1},{8:N1},{9}" -f (Get-Date -Format s), $g[0], $g[1], $g[2], $g[3], $thr, $phys, ($lim - $used), (100 * $used / $lim), $note | Add-Content $Out
  } catch { "{0},,,,,,,,,ERR $($_.Exception.Message)" -f (Get-Date -Format s) | Add-Content $Out }
  Start-Sleep -Seconds 30
}
[void][Win.Pwr]::SetThreadExecutionState(0x80000000)
