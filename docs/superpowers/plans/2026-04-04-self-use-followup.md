# Self-Use Follow-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the self-use Android vocabulary app in the requested order: Chinese gloss quality, Japanese examples, Android instrumentation-test health, performance validation support, and release verification.

**Architecture:** Keep the current full-dictionary pipeline and Android app structure, but add targeted improvements that directly help a single-user offline workflow. Focus on low-cost offline data enrichment first, then close the example gap, repair broken Android test coverage, add lightweight performance observability, and finish with a verifiable release build path.

**Tech Stack:** Python 3.12 scripts, pytest, SQLite, Kotlin, Jetpack Compose, Gradle

---

### Task 1: Add Offline Chinese Gloss Overrides

**Files:**
- Modify: `src/dict_feasibility/translation.py`
- Modify: `src/dict_feasibility/translation_pipeline.py`
- Modify: `scripts/translate_normalized_words.py`
- Test: `tests/test_translation_pipeline.py`
- Create: `tests/fixtures/supplemental_translation_overrides.json`

- [ ] Write a failing test proving source-aware offline overrides beat provider translation.
- [ ] Run the translation pipeline test and verify the new case fails for the expected reason.
- [ ] Implement override loading and pipeline application with minimal changes.
- [ ] Re-run the targeted translation tests until they pass.

### Task 2: Teach Japanese Parsing To Consume Full Tatoeba Archives

**Files:**
- Modify: `src/dict_feasibility/source_paths.py`
- Modify: `src/dict_feasibility/tatoeba_parser.py`
- Modify: `scripts/parse_jmdict.py`
- Test: `tests/test_examples.py`
- Test: `tests/test_jmdict_parser.py`
- Test: `tests/test_full_source_parsers.py`

- [ ] Write failing tests for raw `sentences.tar.bz2` and `links.tar.bz2` example extraction.
- [ ] Verify the tests fail before any implementation changes.
- [ ] Implement archive-backed Japanese example resolution while preserving fixture support.
- [ ] Re-run the targeted parser tests until they pass.

### Task 3: Repair Android Instrumentation Test Compilation

**Files:**
- Modify: `android-app/app/src/androidTest/java/com/aiproduct/vocab/AppLaunchTest.kt`
- Modify: `android-app/app/src/androidTest/java/com/aiproduct/vocab/ui/search/SearchScreenTest.kt`

- [ ] Reproduce the failing `compileDebugAndroidTestKotlin` build and capture the exact causes.
- [ ] Adjust the stale tests to the current Compose API and `SearchScreen` signature with minimal scope.
- [ ] Re-run Android instrumentation test compilation until it succeeds.

### Task 4: Add Lightweight Performance Validation Support

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/util/PerformanceTrace.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/data/package/DictionaryAssetInstaller.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/VocabGateway.kt`
- Test: `android-app/app/src/test/java/com/aiproduct/vocab/util/PerformanceTraceTest.kt`

- [ ] Write a failing unit test for the timing helper.
- [ ] Verify the helper test fails first.
- [ ] Implement the helper and wire it into install/search flows for log-based measurement.
- [ ] Re-run the helper and Android unit tests until they pass.

### Task 5: Verify Release Build Path

**Files:**
- Modify: `README.md`

- [ ] Add explicit self-use verification commands for release packaging and smoke validation.
- [ ] Run the fresh Python, Android unit, Android instrumentation compile, and release build commands.
- [ ] Record actual outcomes and leave any residual risk explicit.
