# Translation Checkpointing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add periodic checkpoint output and progress summary updates for long-running translation jobs so partial results are persisted before the final write.

**Architecture:** Keep the existing per-chunk translation pipeline intact and add a thin orchestration layer that slices the input into checkpoint-sized chunks, reuses the shared cache/provider, appends translated rows to a checkpoint JSONL, and refreshes a progress summary JSON after each chunk. The CLI script wires these options in without changing default behavior when checkpointing is disabled.

**Tech Stack:** Python 3, existing `dict_feasibility` translation pipeline, pytest

---

### Task 1: Add failing checkpoint orchestration tests

**Files:**
- Modify: `tests/test_translation_pipeline.py`
- Test: `tests/test_translation_pipeline.py`

- [ ] **Step 1: Write a failing test for chunked checkpoint output and progress summary**

```python
def test_run_translation_job_writes_checkpoint_output_and_progress(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_translation_pipeline.py -k checkpoint -q`
Expected: FAIL because `run_translation_job` and checkpoint helpers do not exist yet.

### Task 2: Implement chunked checkpoint orchestration

**Files:**
- Modify: `src/dict_feasibility/translation_pipeline.py`
- Test: `tests/test_translation_pipeline.py`

- [ ] **Step 1: Add minimal chunked orchestration and checkpoint helpers**

```python
def run_translation_job(...):
    ...
```

- [ ] **Step 2: Run focused tests to verify checkpoint behavior**

Run: `python -m pytest tests/test_translation_pipeline.py -k checkpoint -q`
Expected: PASS

### Task 3: Expose checkpoint options in the translation script

**Files:**
- Modify: `scripts/translate_normalized_words.py`
- Modify: `tests/test_translation_pipeline.py`
- Test: `tests/test_translation_pipeline.py`

- [ ] **Step 1: Add a failing script integration test for checkpoint args**

```python
def test_translate_normalized_words_script_writes_checkpoint_files(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_translation_pipeline.py -k checkpoint_files -q`
Expected: FAIL because the script does not parse the new args yet.

- [ ] **Step 3: Wire `--checkpoint-every`, `--checkpoint-output`, and `--checkpoint-report` into the script**

```python
translated_words, summary = run_translation_job(...)
```

- [ ] **Step 4: Run focused tests to verify script checkpoint behavior**

Run: `python -m pytest tests/test_translation_pipeline.py -q`
Expected: PASS

### Task 4: Verify end-to-end behavior

**Files:**
- Modify: none
- Test: `tests/test_translation_pipeline.py`

- [ ] **Step 1: Run focused test file**

Run: `python -m pytest tests/test_translation_pipeline.py -q`
Expected: PASS

- [ ] **Step 2: Run a small real smoke command**

Run:

```powershell
$env:OPENAI_BASE_URL='http://127.0.0.1:8080/v1'
$env:OPENAI_API_KEY='local'
python scripts\translate_normalized_words.py `
  --provider llama_cpp `
  --model qwen2.5:3b `
  --input artifacts\smoke-4.jsonl `
  --output artifacts\smoke-4.out.jsonl `
  --report artifacts\smoke-4.report.json `
  --checkpoint-every 2 `
  --checkpoint-output artifacts\smoke-4.checkpoint.jsonl `
  --checkpoint-report artifacts\smoke-4.progress.json `
  --cache artifacts\reports\translation-cache-qwen2.5-llamacpp-smoke4.json
```

Expected: PASS, checkpoint files created during the run, final output/report still written.
