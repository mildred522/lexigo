# Mainline Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Converge the validated Python pipeline, documentation, and Android search baseline from `task-2-shared-models` back into a single mainline-ready workspace.

**Architecture:** Execute convergence in an isolated branch off `master`, using the validated worktree as the source of truth. First bring over tests so the target branch fails for the right reasons, then sync Python implementation, then sync the Android project, and finally clean ignore rules and verify the unified baseline.

**Tech Stack:** Git worktrees, Python 3.12, pytest, Kotlin/Gradle project files, PowerShell file sync

---

### Task 1: Create An Isolated Convergence Workspace

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\.gitignore`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\...`

- [ ] **Step 1: Verify `.worktrees` is ignored, and add it if missing**

```gitignore
__pycache__/
.pytest_cache/
.venv/
.worktrees/
sources/
artifacts/
*.sqlite
*.db
pytest_cache/
pytest_temp_root/
pytest_temp_root_simple2/
```

- [ ] **Step 2: Verify the ignore rule is active**

Run: `git -C "E:\aiproduct\安卓单词软件\content" -c safe.directory="E:/aiproduct/安卓单词软件/content" check-ignore -v .worktrees`
Expected: output points at `.gitignore` and exit code `0`

- [ ] **Step 3: Create the isolated worktree branch**

Run: `git -C "E:\aiproduct\安卓单词软件\content" -c safe.directory="E:/aiproduct/安卓单词软件/content" worktree add "E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence" -b task-a-mainline-convergence`
Expected: new worktree created from `master`

- [ ] **Step 4: Run the current mainline Python baseline**

Run: `python -m pytest -q`
Workdir: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence`
Expected: current minimal suite passes (`1 passed`)

### Task 2: Bring Over The Python Tests First

**Files:**
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\conftest.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\fixtures\jmdict_sample.json`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\fixtures\kaikki_fr_sample.jsonl`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\fixtures\tatoeba_sample.tsv`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\fixtures\translation_glossary.json`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_examples.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_feasibility_report.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_jmdict_parser.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_kaikki_parser.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_package_export.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_paths.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_query_service.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_real_source_translation_validation.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_real_source_validation.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_reporting.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_source_registry.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_sqlite_builder.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_sync_android_dictionary_assets.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_translation.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_translation_pipeline.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_translation_runtime.py`

- [ ] **Step 1: Copy the validated Python tests and fixtures from the source worktree**

```powershell
$src = 'E:\aiproduct\安卓单词软件\content\.worktrees\task-2-shared-models\tests'
$dst = 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests'
Copy-Item -Recurse -Force "$src\*" $dst
```

- [ ] **Step 2: Run the copied suite to verify it fails for missing implementation**

Run: `python -m pytest -q`
Workdir: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence`
Expected: FAIL with missing modules or missing scripts from `dict_feasibility`

### Task 3: Sync The Python Pipeline And Supporting Docs

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\README.md`
- Modify: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\pyproject.toml`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\scripts\*.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\src\dict_feasibility\*.py`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\feasibility-report.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\real-source-validation.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\real-source-translation-validation.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\specs\2026-04-03-translation-pipeline-design.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\specs\2026-04-03-package-export-design.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\specs\2026-04-03-dictionary-search-design.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\specs\2026-04-03-android-app-design.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\plans\2026-04-03-translation-pipeline.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\plans\2026-04-03-package-export.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\plans\2026-04-03-dictionary-search.md`
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs\superpowers\plans\2026-04-03-android-app.md`

- [ ] **Step 1: Copy the validated Python source tree**

```powershell
$src = 'E:\aiproduct\安卓单词软件\content\.worktrees\task-2-shared-models\src\dict_feasibility'
$dst = 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\src\dict_feasibility'
Copy-Item -Recurse -Force "$src\*" $dst
```

- [ ] **Step 2: Copy scripts and update project metadata/docs**

```powershell
Copy-Item -Recurse -Force 'E:\aiproduct\安卓单词软件\content\.worktrees\task-2-shared-models\scripts' 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence'
Copy-Item -Force 'E:\aiproduct\安卓单词软件\content\.worktrees\task-2-shared-models\README.md' 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\README.md'
Copy-Item -Force 'E:\aiproduct\安卓单词软件\content\.worktrees\task-2-shared-models\pyproject.toml' 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\pyproject.toml'
Copy-Item -Recurse -Force 'E:\aiproduct\安卓单词软件\content\.worktrees\task-2-shared-models\docs\*' 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\docs'
```

- [ ] **Step 3: Remove stale packaging residue from the target branch**

```powershell
Remove-Item -Recurse -Force 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\src\dict_feasibility.egg-info' -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\build' -ErrorAction SilentlyContinue
```

- [ ] **Step 4: Run the Python suite again to verify the implementation now satisfies the copied tests**

Run: `python -m pytest -q`
Workdir: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence`
Expected: PASS for the Python convergence suite

- [ ] **Step 5: Verify the code still compiles cleanly**

Run: `python -m compileall src scripts`
Workdir: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence`
Expected: exit code `0`

### Task 4: Add An Android Layout Regression Test

**Files:**
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\tests\test_android_project_layout.py`

- [ ] **Step 1: Write the failing regression test for Android project presence**

```python
from pathlib import Path


def test_android_project_layout_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "android-app" / "settings.gradle.kts").exists()
    assert (root / "android-app" / "app" / "build.gradle.kts").exists()
    assert (root / "android-app" / "app" / "src" / "main" / "AndroidManifest.xml").exists()
    assert (root / "android-app" / "app" / "src" / "main" / "java" / "com" / "aiproduct" / "vocab" / "MainActivity.kt").exists()
```

- [ ] **Step 2: Run the Android layout regression test and verify it fails**

Run: `python -m pytest tests/test_android_project_layout.py -q`
Workdir: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence`
Expected: FAIL because `android-app/` is still missing

### Task 5: Sync The Android Project Into Mainline

**Files:**
- Create: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence\android-app\...`

- [ ] **Step 1: Copy the Android project from the validated source worktree**

```powershell
Copy-Item -Recurse -Force 'E:\aiproduct\安卓单词软件\content\.worktrees\task-2-shared-models\android-app' 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence'
```

- [ ] **Step 2: Re-run the Android layout regression**

Run: `python -m pytest tests/test_android_project_layout.py -q`
Workdir: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence`
Expected: PASS

- [ ] **Step 3: Re-run the full Python suite to verify the unified repo baseline still passes**

Run: `python -m pytest -q`
Workdir: `E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence`
Expected: PASS

### Task 6: Bring The Unified Baseline Back To The Main Workspace

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\README.md`
- Modify: `E:\aiproduct\安卓单词软件\content\pyproject.toml`
- Create: `E:\aiproduct\安卓单词软件\content\scripts\*.py`
- Create: `E:\aiproduct\安卓单词软件\content\src\dict_feasibility\*.py`
- Create: `E:\aiproduct\安卓单词软件\content\tests\*.py`
- Create: `E:\aiproduct\安卓单词软件\content\tests\fixtures\*`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\...`
- Create: `E:\aiproduct\安卓单词软件\content\docs\...`

- [ ] **Step 1: Mirror the unified branch workspace back into the main workspace**

```powershell
$src = 'E:\aiproduct\安卓单词软件\content\.worktrees\mainline-convergence'
$dst = 'E:\aiproduct\安卓单词软件\content'

Copy-Item -Recurse -Force "$src\src" $dst
Copy-Item -Recurse -Force "$src\tests" $dst
Copy-Item -Recurse -Force "$src\scripts" $dst
Copy-Item -Recurse -Force "$src\docs" $dst
Copy-Item -Recurse -Force "$src\android-app" $dst
Copy-Item -Force "$src\README.md" "$dst\README.md"
Copy-Item -Force "$src\pyproject.toml" "$dst\pyproject.toml"
Copy-Item -Force "$src\.gitignore" "$dst\.gitignore"
```

- [ ] **Step 2: Remove stale generated residue from the main workspace**

```powershell
Remove-Item -Recurse -Force 'E:\aiproduct\安卓单词软件\content\src\dict_feasibility.egg-info' -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force 'E:\aiproduct\安卓单词软件\content\build' -ErrorAction SilentlyContinue
```

- [ ] **Step 3: Run the final main-workspace verification**

Run: `python -m pytest -q`
Workdir: `E:\aiproduct\安卓单词软件\content`
Expected: PASS for the full Python suite

- [ ] **Step 4: Verify syntax in the main workspace**

Run: `python -m compileall src scripts`
Workdir: `E:\aiproduct\安卓单词软件\content`
Expected: exit code `0`

- [ ] **Step 5: Record the new mainline-visible file layout**

Run: `rg --files . -g '!**/.git/**' -g '!**/.worktrees/**' -g '!**/.gradle-local/**' -g '!**/.android-local/**' -g '!**/.pytest_cache/**' -g '!**/pytest-cache-files-*/*' | Select-Object -First 300`
Workdir: `E:\aiproduct\安卓单词软件\content`
Expected: visible `scripts/`, expanded `src/`, expanded `tests/`, and `android-app/`
