$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$backendEnv = Join-Path $root "Source code\backend\.env"
if (-not (Test-Path $backendEnv)) {
    throw "Backend .env not found: $backendEnv"
}

$config = @{}
Get-Content $backendEnv | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#") -or -not $line.Contains("=")) {
        return
    }
    $parts = $line.Split("=", 2)
    $config[$parts[0].Trim()] = $parts[1].Trim()
}

if ($config.ContainsKey("DEFAULT_TOP_K")) {
    $topK = [int]$config["DEFAULT_TOP_K"]
} else {
    $topK = 5
}

if ($config.ContainsKey("OLLAMA_NUM_CTX")) {
    $numCtx = [int]$config["OLLAMA_NUM_CTX"]
} else {
    $numCtx = 4096
}

if ($config.ContainsKey("LLM_TEMPERATURE")) {
    $temperature = [double]$config["LLM_TEMPERATURE"]
} else {
    $temperature = 0.1
}

if ($config.ContainsKey("LLM_MAX_TOKENS")) {
    $numPredict = [int]$config["LLM_MAX_TOKENS"]
} else {
    $numPredict = 1024
}

if ($config.ContainsKey("LLM_REQUEST_TIMEOUT")) {
    $ollamaTimeout = [int][double]$config["LLM_REQUEST_TIMEOUT"]
} else {
    $ollamaTimeout = 240
}
$judge = "qwen2.5:7b-instruct"
$sample = 50
$retrieval = "hybrid"
$embeddings = "e5"

$runs = @(
    @{
        Model = "llama3.1:8b-instruct-q4_K_M"
        Name = "ragas_llama31_8b_instruct_q4_K_M_backendcfg"
    },
    @{
        Model = "qwen3.5:4b-q4_K_M"
        Name = "ragas_qwen35_4b_q4_K_M_backendcfg"
    }
)

$logDir = Join-Path $root "knowledge_layer\eval\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

foreach ($run in $runs) {
    $model = $run.Model
    $target = Join-Path $root ("knowledge_layer\eval\" + $run.Name)
    $logFile = Join-Path $logDir ($run.Name + ".log")

    "[$(Get-Date -Format s)] START model=$model judge=$judge sample=$sample retrieval=$retrieval top_k=$topK num_ctx=$numCtx temperature=$temperature num_predict=$numPredict timeout=$ollamaTimeout" |
        Tee-Object -FilePath $logFile -Append

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    python evaluate_ragas.py `
        --sample $sample `
        --top-k $topK `
        --retrieval $retrieval `
        --judge $judge `
        --gen-model $model `
        --embeddings $embeddings `
        --num-ctx $numCtx `
        --temperature $temperature `
        --num-predict $numPredict `
        --ollama-timeout $ollamaTimeout `
        --judge-num-predict $numPredict `
        --judge-timeout $ollamaTimeout 2>&1 |
        Tee-Object -FilePath $logFile -Append
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    if ($exitCode -ne 0) {
        throw "evaluate_ragas.py failed for model=$model with exit code $exitCode"
    }

    if (Test-Path $target) {
        Remove-Item -Recurse -Force $target
    }
    Copy-Item -Recurse -Force (Join-Path $root "knowledge_layer\eval\ragas") $target

    "[$(Get-Date -Format s)] DONE copied_to=$target" |
        Tee-Object -FilePath $logFile -Append
}
