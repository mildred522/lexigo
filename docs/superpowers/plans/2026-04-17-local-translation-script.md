# Local Translation Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a PowerShell helper that pulls a local Ollama model and runs the existing translation workflow against the local endpoint.

**Architecture:** Keep the Python translation pipeline unchanged and add only a thin PowerShell orchestration layer. Validate behavior with a Python contract test that checks the script contents and supported stages.

**Tech Stack:** PowerShell 5+, Python 3.12, pytest, existing translation scripts, Ollama OpenAI-compatible endpoint

---

### Task 1: Add a failing script-contract test

**Files:**
- Create: `tests/test_local_translation_script.py`
- Test: `tests/test_local_translation_script.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path


def test_run_local_translation_script_declares_expected_stages_and_commands() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_local_translation.ps1"

    assert script_path.exists()
    script = script_path.read_text(encoding="utf-8")

    assert "validate" in script
    assert "japanese" in script
    assert "french" in script
    assert "build" in script
    assert "all" in script
    assert "ollama pull" in script
    assert '$env:OPENAI_BASE_URL="http://127.0.0.1:11434/v1"' in script
    assert '$env:OPENAI_API_KEY="ollama"' in script
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_local_translation_script.py -q`
Expected: FAIL because `scripts/run_local_translation.ps1` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create `scripts/run_local_translation.ps1` with:

```powershell
param(...)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$env:OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"
$env:OPENAI_API_KEY = "ollama"
```

plus stage dispatch to:

- `python scripts/validate_real_source_translations.py`
- `python scripts/translate_normalized_words.py`
- `python scripts/build_sqlite.py`
- `python scripts/export_dictionary_package.py`
- `python scripts/render_feasibility_report.py`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_local_translation_script.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_local_translation_script.py scripts/run_local_translation.ps1 docs/superpowers/specs/2026-04-17-local-translation-script-design.md docs/superpowers/plans/2026-04-17-local-translation-script.md
git commit -m "feat: add local translation helper script"
```

### Task 2: Expand the helper to cover the full local workflow

**Files:**
- Modify: `scripts/run_local_translation.ps1`
- Test: `tests/test_local_translation_script.py`

- [ ] **Step 1: Write the failing test**

Extend the existing test with assertions for:

```python
assert "validate_real_source_translations.py" in script
assert "translate_normalized_words.py" in script
assert "build_sqlite.py" in script
assert "export_dictionary_package.py" in script
assert "render_feasibility_report.py" in script
assert "translation-cache-qwen3-4b" in script
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_local_translation_script.py -q`
Expected: FAIL because one or more commands or cache paths are not yet present.

- [ ] **Step 3: Write minimal implementation**

Update the PowerShell helper to:

- pull the requested model unless `-SkipPull`
- activate `.venv` unless `-SkipVenv`
- support `validate`, `japanese`, `french`, `build`, `all`
- use dedicated cache/report filenames per model slug
- run the correct Python commands for each stage

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_local_translation_script.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_local_translation_script.py scripts/run_local_translation.ps1
git commit -m "feat: support staged local translation workflow"
```
