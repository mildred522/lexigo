[CmdletBinding()]
param(
    [ValidateSet("validate", "japanese", "french", "build", "all")]
    [string]$Stage = "validate",

    [ValidateSet("llama_cpp", "openai")]
    [string]$Provider = "llama_cpp",

    [string]$Model = "qwen2.5:3b",

    [string]$BaseUrl = "",

    [int]$BatchSizeJa = 16,

    [int]$BatchSizeFr = 8,

    [int]$SampleLimit = 50,

    [switch]$SkipPull,

    [switch]$SkipVenv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ReportsDir = Join-Path $RepoRoot "artifacts\reports"
$TranslatedDir = Join-Path $RepoRoot "artifacts\translated"
$ModelSlug = (($Model -replace "[:/\\]", "-") -replace "[^A-Za-z0-9._-]", "-")
$CachePath = Join-Path $ReportsDir ("translation-cache-{0}.json" -f $ModelSlug)
$ValidationReportPath = Join-Path $ReportsDir ("real-source-translation-validation-{0}.json" -f $ModelSlug)
$JaReportPath = Join-Path $ReportsDir ("jmdict-translation-summary-{0}.json" -f $ModelSlug)
$FrReportPath = Join-Path $ReportsDir ("kaikki-fr-translation-summary-{0}.json" -f $ModelSlug)
$JaOutputPath = Join-Path $TranslatedDir "jmdict_words.jsonl"
$FrOutputPath = Join-Path $TranslatedDir "kaikki_fr_words.jsonl"

function Assert-CommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Assert-PathExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Required path not found: $Path"
    }
}

function Assert-OllamaEndpointReady {
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 10
    }
    catch {
        throw "Ollama endpoint is unavailable at http://127.0.0.1:11434. Start Ollama or run 'ollama serve' first."
    }
}

function Get-TranslationBaseUrl {
    if ($BaseUrl.Trim()) {
        return $BaseUrl.Trim()
    }
    if ($Provider -eq "llama_cpp") {
        return "http://127.0.0.1:8080/v1"
    }
    return "http://127.0.0.1:11434/v1"
}

function Enable-RepoVenv {
    $activatePath = Join-Path $RepoRoot ".venv\Scripts\Activate.ps1"
    if (-not (Test-Path $activatePath)) {
        Write-Host "No repo .venv found at $activatePath; using current Python environment."
        return
    }

    . $activatePath
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptRelativePath,

        [string[]]$Arguments = @()
    )

    $scriptPath = Join-Path $RepoRoot $ScriptRelativePath
    Assert-PathExists -Path $scriptPath
    & python $scriptPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python script failed: $ScriptRelativePath"
    }
}

function Invoke-ValidationStage {
    Invoke-PythonScript -ScriptRelativePath "scripts\validate_real_source_translations.py" -Arguments @(
        "--provider", $Provider,
        "--model", $Model,
        "--limit", "$SampleLimit",
        "--cache", $CachePath,
        "--report", $ValidationReportPath
    )
}

function Invoke-JapaneseStage {
    Invoke-PythonScript -ScriptRelativePath "scripts\translate_normalized_words.py" -Arguments @(
        "--provider", $Provider,
        "--model", $Model,
        "--batch-size", "$BatchSizeJa",
        "--input", (Join-Path $RepoRoot "artifacts\normalized\jmdict_words.jsonl"),
        "--output", $JaOutputPath,
        "--report", $JaReportPath,
        "--cache", $CachePath
    )
}

function Invoke-FrenchStage {
    Invoke-PythonScript -ScriptRelativePath "scripts\translate_normalized_words.py" -Arguments @(
        "--provider", $Provider,
        "--model", $Model,
        "--batch-size", "$BatchSizeFr",
        "--input", (Join-Path $RepoRoot "artifacts\normalized\kaikki_fr_words.jsonl"),
        "--output", $FrOutputPath,
        "--report", $FrReportPath,
        "--cache", $CachePath
    )
}

function Invoke-BuildStage {
    Invoke-PythonScript -ScriptRelativePath "scripts\build_sqlite.py"
    Invoke-PythonScript -ScriptRelativePath "scripts\export_dictionary_package.py"
    Invoke-PythonScript -ScriptRelativePath "scripts\render_feasibility_report.py"
}

Assert-CommandExists -Name "python"
Assert-PathExists -Path (Join-Path $RepoRoot "scripts\validate_real_source_translations.py")
Assert-PathExists -Path (Join-Path $RepoRoot "scripts\translate_normalized_words.py")
Assert-PathExists -Path (Join-Path $RepoRoot "scripts\build_sqlite.py")
Assert-PathExists -Path (Join-Path $RepoRoot "scripts\export_dictionary_package.py")
Assert-PathExists -Path (Join-Path $RepoRoot "scripts\render_feasibility_report.py")

if (-not $SkipVenv) {
    Enable-RepoVenv
}

$env:OPENAI_BASE_URL = Get-TranslationBaseUrl
$env:OPENAI_API_KEY = "ollama"

if ($Provider -eq "openai") {
    Assert-CommandExists -Name "ollama"
    Assert-OllamaEndpointReady

    if (-not $SkipPull) {
        & ollama pull $Model
        if ($LASTEXITCODE -ne 0) {
            throw "ollama pull failed for model $Model"
        }
    }
}

switch ($Stage) {
    "validate" {
        Invoke-ValidationStage
    }
    "japanese" {
        Invoke-JapaneseStage
    }
    "french" {
        Invoke-FrenchStage
    }
    "build" {
        Invoke-BuildStage
    }
    "all" {
        Invoke-ValidationStage
        Invoke-JapaneseStage
        Invoke-FrenchStage
        Invoke-BuildStage
    }
    default {
        throw "Unsupported stage: $Stage"
    }
}
