# Dictionary Package Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Export the generated dictionary database as an app-facing package with a stable manifest.

**Architecture:** Keep SQLite as the packaged data payload and add a manifest derived from current reports and database counts. Provide a single export script so downstream consumers always read a stable package directory instead of raw build artifacts.

**Tech Stack:** Python 3.13, pytest, SQLite, JSON, shutil, standard library

---

### Task 1: Add Package Export Tests

**Files:**
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_package_export.py`

### Task 2: Implement Package Export Module

**Files:**
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\package_export.py`
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\scripts\export_dictionary_package.py`

### Task 3: Verify And Document

**Files:**
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\README.md`

**Verification:**
- `python -m pytest tests/test_package_export.py -v`
- `python scripts/export_dictionary_package.py`
- `python -m pytest -v`
- `python -m compileall src scripts`
