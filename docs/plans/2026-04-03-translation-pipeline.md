# Translation Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a provider-pluggable batch translation stage that converts source-language glosses into Chinese meanings and feeds translated outputs into SQLite and reporting.

**Architecture:** Keep parser outputs as normalized JSONL, but separate source glosses from Chinese output in the data model. Add a translation stage that loads normalized records, applies cache-aware translations through a pluggable provider, writes translated artifacts, and updates downstream packaging/reporting to consume translated data.

**Tech Stack:** Python 3.13, pytest, JSONL, SQLite, dataclasses, standard library, requests

---

### Task 1: Refactor Normalized Records For Source Gloss Preservation

**Files:**
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\models.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\jmdict_parser.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\kaikki_parser.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_paths.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_jmdict_parser.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_kaikki_parser.py`

### Task 2: Add Batch Translation Pipeline

**Files:**
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\translation_pipeline.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\translation.py`
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_translation_pipeline.py`
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\scripts\translate_normalized_words.py`

### Task 3: Feed Translated Outputs Into SQLite And Reporting

**Files:**
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\sqlite_builder.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\reporting.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_sqlite_builder.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_reporting.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\scripts\build_sqlite.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\scripts\sample_report.py`

### Task 4: Verify And Document The New Pipeline

**Files:**
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\README.md`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\docs\feasibility-report.md`

**Verification:**
- `python -m pytest -v`
- `python scripts/parse_jmdict.py`
- `python scripts/parse_kaikki_fr.py`
- `python scripts/translate_normalized_words.py`
- `python scripts/build_sqlite.py`
- `python scripts/sample_report.py`
- `python -m compileall src scripts`
