# Local Translation Script Design

## Goal

Add a repo-local PowerShell helper that downloads a local Ollama model, points the existing translation pipeline at the local OpenAI-compatible endpoint, and runs the main translation stages without changing the Python translation implementation.

## Scope

In scope:

- one PowerShell entry script under `scripts/`
- support for model pull and endpoint environment setup
- support for running validation, Japanese translation, French translation, database rebuild, and a combined pipeline mode
- safe defaults for cache/report/output paths so local-model runs do not overwrite prior ad hoc evaluation files by accident

Out of scope:

- changing the Python provider abstraction
- adding a new translation backend
- changing packaged manifest semantics
- solving missing French source gloss rows

## Approach

Use the existing OpenAI-compatible provider path already implemented in Python. The PowerShell helper will:

1. validate local prerequisites
2. optionally pull the requested Ollama model
3. export `OPENAI_BASE_URL=http://127.0.0.1:11434/v1` and `OPENAI_API_KEY=ollama`
4. activate `.venv` if present
5. run one of several supported stages via the existing Python scripts

This keeps all translation behavior inside the current Python codepaths and makes the new helper an orchestration layer only.

## Interface

Script path:

- `scripts/run_local_translation.ps1`

Parameters:

- `-Stage` with values `validate`, `japanese`, `french`, `build`, `all`
- `-Model` default `qwen3:4b`
- `-BatchSizeJa` default `16`
- `-BatchSizeFr` default `8`
- `-SampleLimit` default `50`
- `-SkipPull` to skip `ollama pull`
- `-SkipVenv` to avoid auto-activating `.venv`

## Error Handling

- Fail fast if `ollama` or `python` is missing.
- Fail fast if the repo-local `scripts/` targets do not exist.
- Do not try to start or manage `ollama serve`; require the user to have it running and surface a clear message if the endpoint is unavailable.
- Use `Set-StrictMode -Version Latest` and `$ErrorActionPreference = 'Stop'`.

## Testing

Add a focused pytest that verifies the PowerShell helper exists and contains the expected stages, environment variable setup, Ollama pull command, and Python script invocations. This is intentionally lightweight because the repository test suite is Python-based and we want a stable contract test rather than a brittle process integration test.
