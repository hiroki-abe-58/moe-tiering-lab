# Nsight Systems capture of ~12 s of steady decode (tier 42 GB, default settings) through the engine's non-interactive `generate`
# command (nsys does not pass a pipe's stdin/stdout through, so the --serve protocol cannot be profiled), then the stats as CSV.
param([string]$Out = "E:\oss\moe-tiering-lab\results\phase4\exp15-nsys", [int]$Delay = 55, [int]$Duration = 12, [string]$Name = "t42", [int]$MaxNew = 500, [string]$ExtraEnv = "")
$py = 'E:\oss\project-maya\.venv\Scripts\python.exe'
$nsys = 'C:\Program Files\NVIDIA Corporation\Nsight Systems 2025.5.2\target-windows-x64\nsys.exe'
$exe = 'E:\oss\maya-dev\build\strata.exe'
$pack = 'E:\oss\maya-models\Maya-S-v2-IQ2_XXS\pack'
Set-Location E:\oss\moe-tiering-lab
New-Item -ItemType Directory -Force -Path $Out, E:\oss\maya-logs | Out-Null
$ids = & $py -c "import sys; sys.path.insert(0, r'E:\oss\maya-dev'); sys.path.insert(0, r'E:\oss\maya-dev\tools'); import strata_tokenizer as ST; t = ST.Tokenizer.from_dir(r'$pack\tokenizer'); print(','.join(map(str, t.encode('[gMASK]<sop><|user|>\nWrite a Python function that parses a CSV file into a list of dictionaries, with type hints and a docstring.<|assistant|>\n</think>', parse_special=True))))"
"prompt ids: $ids"
$env:STRATA_GLM_RAM_GB = '42'
foreach ($kv in ($ExtraEnv -split ',' | Where-Object { $_ })) { $k, $v = $kv -split '=', 2; [Environment]::SetEnvironmentVariable($k, $v, 'Process') }
$env:PATH = 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\x64;' + $env:PATH
$rep = "E:\oss\maya-logs\nsys-$Name"
$eargs = @('--glm-pack', $pack, '--tokens', $ids, '--max-new', "$MaxNew", '--max-context', '32768', '--expert-cache', 'auto', '--prefill', 'auto',
           '--kv-streaming', 'on', '--expert-profile', 'E:\oss\maya-dev\data\expert-profile-glm.bin')
if ($Delay -gt 0) {
    & $nsys profile --trace=cuda,nvtx --sample=none --cpuctxsw=none --delay=$Delay --duration=$Duration --force-overwrite=true -o $rep $exe @eargs 2>&1 | Select-Object -Last 25
} else {
    & $exe @eargs 2>&1 | Select-Object -Last 25
}
"engine exit $LASTEXITCODE $(Get-Date -Format s)"
if ($Delay -gt 0) {
    foreach ($r in 'cuda_gpu_kern_sum', 'cuda_api_sum', 'cuda_gpu_mem_time_sum', 'cuda_gpu_mem_size_sum', 'cuda_gpu_sum') {
        & $nsys stats --force-export=true --report $r --format csv --force-overwrite=true --output "$Out\$Name" "$rep.nsys-rep" 2>&1 | Select-Object -Last 1
    }
}
Get-ChildItem $Out | Select-Object Name, Length
