# One recipe start after 30 minutes of idle (no engine, no GPU use): same tokens as the warm starts?
param([int]$IdleSeconds = 1800)
$py = 'E:\oss\project-maya\.venv\Scripts\python.exe'
Set-Location E:\oss\moe-tiering-lab
"idle $IdleSeconds s from $(Get-Date -Format s)"
Start-Sleep -Seconds $IdleSeconds
"start $(Get-Date -Format s)"
& $py scripts\maya_probe.py --maya-dir E:\oss\maya-dev --config E:\oss\maya-dev\maya-dev-s-pool3250.json --no-long --label cold --out results\phase4\exp14-recipe\cold\cold-r0.json --env STRATA_GLM_RAM_GB=42 --env STRATA_GLM_PROMOTE=0 --env STRATA_GLM_CPU_RETIME=0 --env STRATA_GLM_CPU_PLAN=001122333
"exit $LASTEXITCODE $(Get-Date -Format s)"
