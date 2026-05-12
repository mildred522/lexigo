# Dictionary Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SQLite-backed local dictionary search for translated entries so the packaged database is directly usable by app-side consumers.

**Architecture:** Extend SQLite packaging with an FTS table while keeping the `words` table canonical. Add a small query service and CLI that operate on the packaged database and return both source and translated meanings.

**Tech Stack:** Python 3.13, pytest, SQLite, FTS5, JSONL, standard library

---

### Task 1: Add Search Tests

**Files:**
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_query_service.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\tests\test_sqlite_builder.py`

### Task 2: Implement Query Service

**Files:**
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\query_service.py`
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\src\dict_feasibility\sqlite_builder.py`

### Task 3: Add Search CLI

**Files:**
- Create: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\scripts\search_words.py`

### Task 4: Verify And Document

**Files:**
- Modify: `C:\Users\10379\安卓单词软件\.worktrees\task-2-shared-models\README.md`

**Verification:**
- `python -m pytest tests/test_query_service.py tests/test_sqlite_builder.py -v`
- `python scripts/search_words.py --query 你好`
- `python -m pytest -v`
- `python -m compileall src scripts`
