# Quality suite + logit trace + route log, one engine start per condition, for the divergence analysis (scripts/exp9_divergence.py).
# Run as a durable job (scripts/durable/submit.py).  Dev build only: STRATA_GLM_LOGIT_TRACE is a dev-tree setting.
param([string]$Out = "E:\oss\moe-tiering-lab\results\phase4\exp9-fidelity", [string]$NNew = "256", [string]$OnlyCsv = "")
$py = 'E:\oss\project-maya\.venv\Scripts\python.exe'
Set-Location E:\oss\moe-tiering-lab
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$conds = @(
    @{ n = 't26';    env = @('STRATA_GLM_RAM_GB=26') },
    @{ n = 't42';    env = @('STRATA_GLM_RAM_GB=42') },
    @{ n = 't26a';   env = @('STRATA_GLM_RAM_GB=26', 'STRATA_GLM_CPU_ACT=q8_1') },
    @{ n = 't42a';   env = @('STRATA_GLM_RAM_GB=42', 'STRATA_GLM_CPU_ACT=q8_1') },
    @{ n = 't42L0';  env = @('STRATA_GLM_RAM_GB=42', 'STRATA_GLM_CPU_LANE=0') },
    @{ n = 't42rep'; env = @('STRATA_GLM_RAM_GB=42') },
    @{ n = 't26d';   env = @('STRATA_GLM_RAM_GB=26', 'STRATA_GLM_CPU_ACT=q8_1d') },
    @{ n = 't42d';   env = @('STRATA_GLM_RAM_GB=42', 'STRATA_GLM_CPU_ACT=q8_1d') },
    @{ n = 't42drep'; env = @('STRATA_GLM_RAM_GB=42', 'STRATA_GLM_CPU_ACT=q8_1d') }
)
$Only = @($OnlyCsv -split ',' | Where-Object { $_ })
foreach ($c in $conds) {
    $name = $c.n
    if ($Only.Count -gt 0 -and $Only -notcontains $name) { continue }
    $trace = Join-Path $Out "q-$name.trace.jsonl"
    $route = Join-Path $Out "route-$name"
    [IO.File]::Delete($trace)
    [IO.File]::Delete("$route.0")
    $a = @('scripts\maya_quality.py', '--maya-dir', 'E:\oss\maya-dev', '--config', 'E:\oss\maya-dev\maya-dev-s.json',
           '--label', "q$name", '--n-new', $NNew, '--out', (Join-Path $Out "q-$name.json"),
           '--env', "STRATA_GLM_LOGIT_TRACE=$trace", '--env', "STRATA_GLM_ROUTE_LOG=$route")
    foreach ($e in $c.env) { $a += @('--env', $e) }
    "=== $name $(Get-Date -Format s)"
    & $py @a
    "exit $LASTEXITCODE"
}
"chain done $(Get-Date -Format s)"
