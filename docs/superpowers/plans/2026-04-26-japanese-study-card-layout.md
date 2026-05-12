# Japanese Study Card Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Japanese-only grammar-aware study card layout for learning and review flows.

**Architecture:** Keep learning/review state machines unchanged. Add a pure Kotlin grammar chip resolver under `ui.study`, then let `StudyWordCard` render language, reading, grammar chips, answer feedback, meanings, examples, and source in one stable immersive card. `LearningScreen` and `ReviewScreen` keep their existing action logic and stop rendering the daily cover inside the study flow.

**Tech Stack:** Kotlin, Jetpack Compose Material3, JUnit4.

---

### Task 1: Japanese Grammar Chip Resolver

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/study/JapaneseGrammarChips.kt`
- Create: `android-app/app/src/test/java/com/aiproduct/vocab/ui/study/JapaneseGrammarChipsTest.kt`

- [x] Write tests for Japanese verb chips, adjective chips, dedupe/cap behavior, and non-Japanese fallback.
- [x] Verify RED with `.\gradlew.bat testDebugUnitTest --tests com.aiproduct.vocab.ui.study.JapaneseGrammarChipsTest`.
- [x] Implement `JapaneseGrammarChips.resolve(language: String, pos: String): List<String>`.
- [x] Compile unit-test sources with `.\gradlew.bat compileDebugUnitTestKotlin`.

### Task 2: Immersive Study Word Card

**Files:**
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/study/StudyWordCard.kt`

- [x] Replace the plain card with an elevated card.
- [x] Make lemma the visual center and reading the secondary line.
- [x] Render language and grammar chips through `JapaneseGrammarChips`.
- [x] Keep answer feedback, meanings, examples, and source inside the same card.

### Task 3: Learning And Review Integration

**Files:**
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/learning/LearningScreen.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/review/ReviewScreen.kt`

- [x] Remove `DailyCoverCard` from the learning study flow.
- [x] Use `StudyWordCard` for choice-stage prompts in learning and review.
- [x] Do not use `StudyWordCard` for spelling-stage prompts because it would reveal the lemma answer.

### Task 4: Verification

- [x] `.\gradlew.bat compileDebugKotlin` succeeded.
- [x] `.\gradlew.bat compileDebugUnitTestKotlin` succeeded.
- [x] `.\gradlew.bat assembleDebug` succeeded.
- [ ] `.\gradlew.bat testDebugUnitTest --tests ...` is blocked in this environment by `ClassNotFoundException`, including existing unrelated tests.

### Self-Review

- Spec coverage: Japanese-only grammar chips, no daily cover in study flow, shared learning/review card treatment, and unchanged learning logic are covered.
- Safety correction: spelling prompts intentionally do not render the lemma card to avoid answer leakage.
- Residual risk: Compose visual appearance has build verification only; device/emulator visual inspection is still needed.
