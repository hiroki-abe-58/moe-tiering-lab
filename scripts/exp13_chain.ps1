# Controlled determinism runs: maya_probe (6 chat prompts x 256 tokens) with logit trace + route log, one engine start per condition.
# Dev build only (STRATA_GLM_LOGIT_TRACE).  Run as a durable job:
#   python scripts/durable/submit.py --name x13 --timeout-min 120 -- powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\exp13_chain.ps1 -OnlyCsv a,b
param([string]$Out = "E:\oss\moe-tiering-lab\results\phase4\exp13-determinism", [string]$OnlyCsv = "")
$py = 'E:\oss\project-maya\.venv\Scripts\python.exe'
Set-Location E:\oss\moe-tiering-lab
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$t42 = 'STRATA_GLM_RAM_GB=42'
$fixed = @('STRATA_GLM_PROMOTE=0', 'STRATA_GLM_CPU_RETIME=0', 'STRATA_GLM_CPU_PLAN=001122333')
$conds = @(
    @{ n = 'L0';      env = @($t42, 'STRATA_GLM_CPU_LANE=0') },
    @{ n = 'L0b';     env = @($t42, 'STRATA_GLM_CPU_LANE=0') },
    @{ n = 'dfix1';   env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d') + $fixed },
    @{ n = 'dfix2';   env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d') + $fixed },
    @{ n = 'dfix3';   env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d') + $fixed },
    @{ n = 'dfixnp1'; env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d', 'STRATA_GLM_PREFILL_CPU=0') + $fixed },
    @{ n = 'fix1';    env = @($t42) + $fixed },
    @{ n = 'fix2';    env = @($t42) + $fixed },
    @{ n = 'p0';      env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d', 'STRATA_GLM_PROMOTE=0', 'STRATA_GLM_CPU_RETIME=0', 'STRATA_GLM_CPU_PLAN=000000000') },
    @{ n = 'p8';      env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d', 'STRATA_GLM_PROMOTE=0', 'STRATA_GLM_CPU_RETIME=0', 'STRATA_GLM_CPU_PLAN=012345678') },
    @{ n = 'p8b';     env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d', 'STRATA_GLM_PROMOTE=0', 'STRATA_GLM_CPU_RETIME=0', 'STRATA_GLM_CPU_PLAN=012345678') },
    @{ n = 'p8plain'; env = @($t42, 'STRATA_GLM_PROMOTE=0', 'STRATA_GLM_CPU_RETIME=0', 'STRATA_GLM_CPU_PLAN=012345678') },
    @{ n = 'fL0';     env = @($t42, 'STRATA_GLM_CPU_LANE=0') },
    @{ n = 'fp8';     env = @($t42, 'STRATA_GLM_CPU_ACT=q8_1d', 'STRATA_GLM_PROMOTE=0', 'STRATA_GLM_CPU_RETIME=0', 'STRATA_GLM_CPU_PLAN=012345678') },
    @{ n = 'fp8plain'; env = @($t42, 'STRATA_GLM_PROMOTE=0', 'STRATA_GLM_CPU_RETIME=0', 'STRATA_GLM_CPU_PLAN=012345678') }
)
$Only = @($OnlyCsv -split ',' | Where-Object { $_ })
foreach ($c in $conds) {
    $name = $c.n
    if ($Only.Count -gt 0 -and $Only -notcontains $name) { continue }
    $trace = Join-Path $Out "$name.trace.jsonl"
    $route = Join-Path $Out "route-$name"
    [IO.File]::Delete($trace)
    [IO.File]::Delete("$route.0")
    $a = @('scripts\maya_probe.py', '--maya-dir', 'E:\oss\maya-dev', '--config', 'E:\oss\maya-dev\maya-dev-s.json', '--no-long',
           '--label', $name, '--out', (Join-Path $Out "$name.json"),
           '--env', "STRATA_GLM_LOGIT_TRACE=$trace", '--env', "STRATA_GLM_ROUTE_LOG=$route")
    if ($name.StartsWith('f')) {
        $ffn = Join-Path $Out "$name.ffn"
        [IO.File]::Delete($ffn)
        $a += @('--env', "STRATA_GLM_DUMP_FFN=$ffn", '--env', 'STRATA_GLM_DUMP_FFN_N=252')
    }
    foreach ($e in $c.env) { $a += @('--env', $e) }
    "=== $name $(Get-Date -Format s)"
    & $py @a
    "exit $LASTEXITCODE"
}
"chain done $(Get-Date -Format s)"
