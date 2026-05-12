# Learning Review Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the learning/review redesign so the app uses four tabs, replaces the old learning-card flow with a ten-word staged learning session, keeps starred words separate, and fixes packaged dictionary reinstall detection.

**Architecture:** Reuse the existing app shell, dictionary repository, and local SQLite-backed progress storage, but expand the local user-data layer into separate starred and learned-word concerns. Build a dedicated learning-session state machine in the ViewModel layer, use a simple interval-ladder scheduler for review, and keep search as the default tab.

**Tech Stack:** Kotlin, Jetpack Compose, Android SQLiteOpenHelper, Gradle, JUnit4, Compose UI tests

---

### Task 1: Fix Dictionary Reinstall Detection

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\data\package\DictionaryAssetInstaller.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\data\package\DictionaryAssetInstallerTest.kt`

- [ ] **Step 1: Write the failing test for entry-count mismatch reinstall**

```kotlin
@Test
fun ensureInstalled_reinstallsWhenEntryCountChanges() {
    // create installed manifest with old entry_count
    // create asset manifest with new entry_count
    // assert ensureInstalled().didInstall is true
}
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.data.package.DictionaryAssetInstallerTest`

Expected: FAIL because `entry_count` is not part of the install contract yet.

- [ ] **Step 3: Add `entry_count` to the compatibility check**

```kotlin
return installedManifest.schemaVersion == assetManifest.schemaVersion &&
    installedManifest.dbFilename == assetManifest.dbFilename &&
    installedManifest.searchCapabilities.fts == assetManifest.searchCapabilities.fts &&
    installedManifest.entryCount == assetManifest.entryCount
```

- [ ] **Step 4: Re-run the targeted test**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.data.package.DictionaryAssetInstallerTest`

Expected: PASS.

### Task 2: Split Starred Data From Learning Progress

**Files:**
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\data\starred\StarredWordStore.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\data\study\StudyRecordStore.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\VocabGateway.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\data\study\StudyRecordStoreTest.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\data\starred\StarredWordStoreTest.kt`

- [ ] **Step 1: Write failing tests for separate star and learning storage**

```kotlin
@Test
fun starringWord_doesNotCreateLearningRecord() { /* ... */ }

@Test
fun learnedWord_doesNotAppearInStarredListUnlessStarred() { /* ... */ }
```

- [ ] **Step 2: Run the two targeted test classes and verify they fail**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.data.study.StudyRecordStoreTest --tests com.aiproduct.vocab.data.starred.StarredWordStoreTest`

Expected: FAIL because starred storage does not exist and study storage still represents the old model.

- [ ] **Step 3: Expand the study schema for learned-word metadata and add the starred store**

```kotlin
CREATE TABLE study_records (
    word_id INTEGER PRIMARY KEY,
    language TEXT NOT NULL,
    choice_correct_count INTEGER NOT NULL,
    choice_wrong_count INTEGER NOT NULL,
    spelling_correct_count INTEGER NOT NULL,
    spelling_wrong_count INTEGER NOT NULL,
    hint_used_count INTEGER NOT NULL,
    review_stage INTEGER NOT NULL,
    last_learned_at_millis INTEGER NOT NULL,
    next_review_at_millis INTEGER NOT NULL
)
```

```kotlin
CREATE TABLE starred_words (
    word_id INTEGER PRIMARY KEY,
    starred_at_millis INTEGER NOT NULL
)
```

- [ ] **Step 4: Add gateway methods for starring, unstarring, and listing starred words**

```kotlin
suspend fun starWord(wordId: Long, nowMillis: Long)
suspend fun unstarWord(wordId: Long)
suspend fun starredWords(): List<WordDetail>
```

- [ ] **Step 5: Re-run the targeted data-layer tests**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.data.study.StudyRecordStoreTest --tests com.aiproduct.vocab.data.starred.StarredWordStoreTest`

Expected: PASS.

### Task 3: Add Learning Session Domain Models

**Files:**
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\learning\LearningSessionModels.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\learning\LearningSessionBuilder.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\learning\LearningSessionReducer.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\domain\learning\LearningSessionBuilderTest.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\domain\learning\LearningSessionReducerTest.kt`

- [ ] **Step 1: Write failing tests for ten-word session creation and wrong-answer recycling**

```kotlin
@Test
fun buildSession_returnsUpToTenUnlearnedWordsForLanguage() { /* ... */ }

@Test
fun wrongChoice_keepsWordPendingInSameSession() { /* ... */ }

@Test
fun allChoiceQuestionsCorrect_transitionsToSpellingStage() { /* ... */ }
```

- [ ] **Step 2: Run the targeted learning-session tests and verify they fail**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.domain.learning.LearningSessionBuilderTest --tests com.aiproduct.vocab.domain.learning.LearningSessionReducerTest`

Expected: FAIL because the learning-session domain does not exist yet.

- [ ] **Step 3: Implement minimal session models and reducer**

```kotlin
enum class LearningStage { LANGUAGE_PICKER, CHOICE, SPELLING, SUMMARY }

data class ChoiceQuestion(...)
data class SpellingQuestion(...)
data class LearningSession(...)
```

- [ ] **Step 4: Re-run the targeted learning-session tests**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.domain.learning.LearningSessionBuilderTest --tests com.aiproduct.vocab.domain.learning.LearningSessionReducerTest`

Expected: PASS.

### Task 4: Add Hint And Review Scheduling Logic

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\review\ReviewScheduler.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\domain\learning\SpellingHintResolver.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\domain\review\ReviewSchedulerTest.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\domain\learning\SpellingHintResolverTest.kt`

- [ ] **Step 1: Write failing tests for the interval ladder and hint rules**

```kotlin
@Test
fun schedule_afterSuccessfulReview_advancesAlongIntervalLadder() { /* ... */ }

@Test
fun japaneseHint_prefersReading() { /* ... */ }

@Test
fun frenchHint_fallsBackToFirstLetterWhenIpaMissing() { /* ... */ }
```

- [ ] **Step 2: Run the targeted scheduler/hint tests and verify they fail**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.domain.review.ReviewSchedulerTest --tests com.aiproduct.vocab.domain.learning.SpellingHintResolverTest`

Expected: FAIL because the old scheduler model and hint resolver do not match the redesign.

- [ ] **Step 3: Implement the ladder and hint resolver**

```kotlin
private val intervalsDays = listOf(0, 1, 2, 4, 7, 15, 30)
```

```kotlin
fun resolveHint(word: StudyWordItem): String
```

- [ ] **Step 4: Re-run the targeted tests**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.domain.review.ReviewSchedulerTest --tests com.aiproduct.vocab.domain.learning.SpellingHintResolverTest`

Expected: PASS.

### Task 5: Refactor App State And Gateway For Four Tabs

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppUiState.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppViewModel.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\VocabGateway.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\res\values\strings.xml`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\ui\AppViewModelTest.kt`

- [ ] **Step 1: Write failing ViewModel tests for the new navigation and language-based session start**

```kotlin
@Test
fun defaultTab_isSearch() { /* ... */ }

@Test
fun startLearningSession_buildsJapaneseSessionWithoutUsingStarredWords() { /* ... */ }
```

- [ ] **Step 2: Run the targeted ViewModel tests and verify they fail**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.ui.AppViewModelTest`

Expected: FAIL because AppViewModel still uses the old learning-list model.

- [ ] **Step 3: Replace the old learning and review state in `AppUiState` with redesign-specific state**

```kotlin
enum class AppTab { SEARCH, LEARNING, STARRED, REVIEW }
```

```kotlin
data class StarredUiState(...)
data class LearningUiState(
    val selectedLanguage: LearningLanguage? = null,
    val session: LearningSession? = null
)
```

- [ ] **Step 4: Update AppViewModel to orchestrate starring, session start, choice answers, spelling answers, and due review loading**

```kotlin
fun onSelectLearningLanguage(language: LearningLanguage)
fun onChooseMeaning(optionIndex: Int)
fun onSubmitSpelling(answer: String)
fun onRequestHint()
fun onToggleStar(wordId: Long)
```

- [ ] **Step 5: Re-run the ViewModel tests**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.ui.AppViewModelTest`

Expected: PASS.

### Task 6: Update Search To Use Stars Instead Of “加入学习”

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\search\SearchScreen.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\search\SearchUiState.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\search\SearchViewModel.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\androidTest\java\com\aiproduct\vocab\ui\search\SearchScreenTest.kt`

- [ ] **Step 1: Write the failing UI test update for star actions**

```kotlin
rule.onNodeWithText("加入星标").assertExists()
```

- [ ] **Step 2: Compile the instrumentation test or run the targeted screen test and verify it fails**

Run: `.\gradlew.bat compileDebugAndroidTestKotlin`

Expected: FAIL or missing text because search still renders the old “加入学习” action.

- [ ] **Step 3: Replace search add/remove behavior with star toggle behavior**

```kotlin
string name="search_star">加入星标</string>
string name="search_starred">已星标</string>
```

- [ ] **Step 4: Re-run instrumentation test compilation**

Run: `.\gradlew.bat compileDebugAndroidTestKotlin`

Expected: PASS.

### Task 7: Implement Learning And Starred Screens

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppRoot.kt`
- Replace: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\learning\LearningScreen.kt`
- Create: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\starred\StarredScreen.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\androidTest\java\com\aiproduct\vocab\AppLaunchTest.kt`

- [ ] **Step 1: Write failing UI expectations for the four-tab shell**

```kotlin
rule.onNodeWithText("星标").assertExists()
rule.onNodeWithText("学习").assertExists()
rule.onNodeWithText("复习").assertExists()
```

- [ ] **Step 2: Run instrumentation test compilation and verify it fails or does not match the current shell**

Run: `.\gradlew.bat compileDebugAndroidTestKotlin`

Expected: current shell does not expose the full redesign yet.

- [ ] **Step 3: Implement the new Compose shells**

```kotlin
when (uiState.selectedTab) {
    AppTab.SEARCH -> SearchScreen(...)
    AppTab.LEARNING -> LearningScreen(...)
    AppTab.STARRED -> StarredScreen(...)
    AppTab.REVIEW -> ReviewScreen(...)
}
```

- [ ] **Step 4: Re-run instrumentation test compilation**

Run: `.\gradlew.bat compileDebugAndroidTestKotlin`

Expected: PASS.

### Task 8: Implement Review Screen Over Due Learned Words

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\review\ReviewScreen.kt`
- Modify: `E:\aiproduct\安卓单词软件\content\android-app\app\src\main\java\com\aiproduct\vocab\ui\AppViewModel.kt`
- Test: `E:\aiproduct\安卓单词软件\content\android-app\app\src\test\java\com\aiproduct\vocab\ui\AppViewModelTest.kt`

- [ ] **Step 1: Write failing tests for due-only review loading and review result application**

```kotlin
@Test
fun reviewQueue_containsOnlyDueLearnedWords() { /* ... */ }
```

- [ ] **Step 2: Run the targeted ViewModel tests and verify they fail**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.ui.AppViewModelTest`

Expected: FAIL because review still reflects the old queue semantics.

- [ ] **Step 3: Wire review screen and ViewModel to the new due queue**

```kotlin
fun onSubmitReviewChoice(...)
fun onSubmitReviewSpelling(...)
```

- [ ] **Step 4: Re-run the targeted tests**

Run: `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.ui.AppViewModelTest`

Expected: PASS.

### Task 9: Final Verification

**Files:**
- Modify: `E:\aiproduct\安卓单词软件\content\README.md`

- [ ] **Step 1: Update README smoke commands for the redesigned app**

```md
.\gradlew.bat compileDebugUnitTestKotlin compileDebugAndroidTestKotlin assembleDebug
```

- [ ] **Step 2: Run fresh Python verification**

Run: `python -m pytest -q`
Workdir: `E:\aiproduct\安卓单词软件\content`
Expected: PASS.

- [ ] **Step 3: Run fresh Android verification**

Run: `.\gradlew.bat compileDebugUnitTestKotlin compileDebugAndroidTestKotlin assembleDebug`
Workdir: `E:\aiproduct\安卓单词软件\content\android-app`
Expected: `BUILD SUCCESSFUL`

- [ ] **Step 4: Run release-path verification**

Run: `.\gradlew.bat assembleRelease`
Workdir: `E:\aiproduct\安卓单词软件\content\android-app`
Expected: `BUILD SUCCESSFUL`
