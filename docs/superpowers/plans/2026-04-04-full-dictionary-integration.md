# Full Dictionary Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest the downloaded full JMdict, Kaikki French, and Tatoeba source bundles into the existing pipeline, rebuild the packaged dictionary, regenerate the Android APK, and write a handoff summary for the next conversation.

**Architecture:** Keep the existing normalized-word pipeline and Android packaging flow, but extend the parsers and source resolution so the same scripts can consume either small fixtures or full downloaded archives. Preserve current fallback behavior for tests while making full-source processing the preferred runtime path.

**Tech Stack:** Python 3.12 scripts, gzip/tar/xml stdlib parsing, SQLite, pytest, Kotlin/Gradle Android app packaging

---

### Task 1: Teach Source Parsers To Consume Full Archives

**Files:**
- Create: `src/dict_feasibility/source_paths.py`
- Modify: `src/dict_feasibility/jmdict_parser.py`
- Modify: `src/dict_feasibility/kaikki_parser.py`
- Modify: `src/dict_feasibility/tatoeba_parser.py`
- Modify: `scripts/parse_jmdict.py`
- Modify: `scripts/parse_kaikki_fr.py`
- Test: `tests/test_jmdict_parser.py`
- Test: `tests/test_kaikki_parser.py`
- Test: `tests/test_examples.py`

### Task 2: Rebuild Full Dictionary Artifacts

**Files:**
- Modify: `scripts/translate_normalized_words.py`
- Modify: `scripts/build_sqlite.py`
- Modify: `scripts/export_dictionary_package.py`
- Modify: `README.md`

### Task 3: Repackage Android App And Record Handoff

**Files:**
- Modify: `android-app/...` (packaged assets via Gradle task)
- Create: `docs/context/2026-04-04-full-dictionary-handoff.md`

