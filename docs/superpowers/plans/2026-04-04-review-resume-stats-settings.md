# Review Resume Stats Settings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add language-separated review sessions, recoverable in-progress sessions, fixed bottom action bars for study flows, stronger spelling/distractor logic, and a combined stats/settings page.

**Architecture:** Keep the existing Compose shell and SQLite-backed progress store, but add a lightweight local preferences/session-draft layer via `SharedPreferences`. Split review state into language selection plus active session, move spelling evaluation and distractor selection into dedicated domain helpers, and expose a new stats/settings tab driven by small gateway/store queries.

**Tech Stack:** Kotlin, Jetpack Compose, Android SQLiteOpenHelper, SharedPreferences, Gradle, JUnit4

---

### Task 1: Add Review Language Stats And Session Draft Storage

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\data\study\StudyRecordStore.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\data\session\SessionDraftStore.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\data\settings\UserPreferencesStore.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\data\study\StudyRecordStoreTest.kt`

- [ ] Add failing in-memory tests for due counts by language and language-filtered due IDs.
- [ ] Compile tests to confirm new APIs are missing.
- [ ] Implement grouped due-count and filtered due-word helpers in `StudyRecordStore`.
- [ ] Add session draft serialization and preference storage classes.
- [ ] Re-run Kotlin test compilation.

### Task 2: Extend Gateway And App State For Review Language Split And Recovery

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\VocabGateway.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppUiState.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppViewModel.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\ui\AppViewModelTest.kt`

- [ ] Add failing tests for review language grouping and restoring a saved learning session.
- [ ] Compile test Kotlin to verify missing state/API surface.
- [ ] Add gateway methods for due counts by language, due words by language, stats, and session draft persistence.
- [ ] Refactor `AppUiState` to include review language choices, stats/settings state, and restored-session flags.
- [ ] Rework `AppViewModel` to restore drafts on startup, save drafts on each mutation, and build review sessions only for the selected language.
- [ ] Re-run Kotlin test compilation.

### Task 3: Fix Study Flow Layout With Fixed Bottom Actions

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\learning\LearningScreen.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\review\ReviewScreen.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppRoot.kt`

- [ ] Add failing UI expectations in screen tests or compile-sensitive call sites for a fixed action section.
- [ ] Implement a shared “scrollable content + fixed bottom action bar” structure in learning and review screens.
- [ ] Add a review-language picker state before starting a review session.
- [ ] Re-run Android test Kotlin compilation.

### Task 4: Improve Spelling Evaluation And Distractor Selection

**Files:**
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\learning\SpellingAnswerEvaluator.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\learning\MeaningDistractorSelector.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\learning\LearningSessionBuilder.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppViewModel.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\domain\learning\LearningSessionReducerTest.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\domain\learning\SpellingAnswerEvaluatorTest.kt`

- [ ] Add failing tests for accent-insensitive French matching, Japanese width normalization, and distractor de-duplication.
- [ ] Compile test Kotlin to confirm missing helpers.
- [ ] Implement spelling normalization/evaluation and wire it into the ViewModel path.
- [ ] Replace random distractor fallback logic with a selector that filters duplicate/overlapping meanings and prefers closer-length distractors.
- [ ] Re-run Kotlin test compilation.

### Task 5: Add Stats And Settings Tab

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppUiState.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppRoot.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\stats\StatsSettingsScreen.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\res\values\strings.xml`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\androidTest\java\com\aiproduct\vocab\AppLaunchTest.kt`

- [ ] Add failing test expectations for the new stats tab label.
- [ ] Compile Android test Kotlin to verify navigation is incomplete.
- [ ] Add a `STATS` tab and a screen that shows learned/due/starred counts plus settings toggles.
- [ ] Persist settings changes and apply them to learning/review behavior.
- [ ] Re-run Android test Kotlin compilation and `assembleDebug`.
