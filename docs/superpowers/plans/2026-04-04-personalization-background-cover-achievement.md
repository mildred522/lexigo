# Personalization Background Cover Achievement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add built-in backgrounds, custom gallery background selection, a daily cover on the learning flow, and practical achievement widgets in stats/settings.

**Architecture:** Extend `UserPreferences` so personalization stays local and survives restarts, surface that state through `AppViewModel`, and render it from a single global background host in `AppRoot`. Keep the learning-page cover and stats-page achievement widgets as focused Compose components so the feature remains incremental and testable.

**Tech Stack:** Kotlin, Jetpack Compose Material3, SharedPreferences, Activity Result API, Android URI permissions

---

### Task 1: Preferences and state model

**Files:**
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppModels.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/data/settings/UserPreferencesStore.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppViewModel.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/VocabGateway.kt`
- Test: `android-app/app/src/test/java/com/aiproduct/vocab/ui/AppViewModelTest.kt`

- [ ] Add personalization fields to `UserPreferences` and derived stats fields to `AppStats`.
- [ ] Write a failing `AppViewModelTest` that verifies personalization preferences are loaded and can be updated from the settings actions.
- [ ] Run `./gradlew.bat compileDebugUnitTestKotlin` to verify the new test references fail before implementation.
- [ ] Implement the minimal preference plumbing in gateway, store, and view-model.
- [ ] Re-run `./gradlew.bat compileDebugUnitTestKotlin` and confirm the test compiles green.

### Task 2: Built-in background rendering

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/personalization/AppBackground.kt`
- Create: `android-app/app/src/main/res/drawable/bg_theme_aurora.xml`
- Create: `android-app/app/src/main/res/drawable/bg_theme_sunrise.xml`
- Create: `android-app/app/src/main/res/drawable/bg_theme_forest.xml`
- Create: `android-app/app/src/main/res/drawable/bg_theme_nightfall.xml`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppRoot.kt`
- Modify: `android-app/app/src/main/res/values/strings.xml`

- [ ] Add a failing UI compile step by referencing a not-yet-created background host from `AppRoot`.
- [ ] Implement background theme mapping, overlay scrim, and safe fallback behavior.
- [ ] Keep the background host global so Search, Learning, Review, Starred, and Stats inherit the same visual layer.
- [ ] Run `./gradlew.bat compileDebugKotlin` to confirm the background host and resources compile.

### Task 3: Daily cover and achievement widgets

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/personalization/DailyCoverCard.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/personalization/AchievementSummary.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/learning/LearningScreen.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/stats/StatsSettingsScreen.kt`
- Modify: `android-app/app/src/main/res/values/strings.xml`

- [ ] Write failing view-model assertions for expanded stats data used by the achievement widgets.
- [ ] Implement a deterministic daily-cover content resolver keyed by local date.
- [ ] Render the daily cover at the top of the learning screen without breaking the existing study flow.
- [ ] Render the achievement summary in stats/settings with streak, today learned, due today, starred total, and language totals.
- [ ] Run `./gradlew.bat compileDebugKotlin` and `./gradlew.bat compileDebugUnitTestKotlin`.

### Task 4: Gallery image selection and custom background

**Files:**
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppRoot.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/stats/StatsSettingsScreen.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppViewModel.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppModels.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/data/settings/UserPreferencesStore.kt`
- Modify: `android-app/app/src/main/AndroidManifest.xml`

- [ ] Write a failing compile step for settings callbacks that expose custom background actions.
- [ ] Switch from a transient picker contract to a persistable document flow and store the selected URI string in preferences.
- [ ] Take persistable read permission in the activity-result callback before saving the URI.
- [ ] Add “use custom background” and “restore default” actions in settings.
- [ ] Run `./gradlew.bat compileDebugKotlin` and confirm the picker path compiles.

### Task 5: Final verification and APK handoff

**Files:**
- Modify: `android-app/app/src/androidTest/...` only if UI verification needs extra coverage
- Output: `android-app/app/build/outputs/apk/debug/app-debug.apk`
- Output copy: `C:\Users\10379\Desktop\沉浸背词-debug.apk`

- [ ] Run `./gradlew.bat compileDebugKotlin`
- [ ] Run `./gradlew.bat compileDebugUnitTestKotlin`
- [ ] Run `./gradlew.bat compileDebugAndroidTestKotlin`
- [ ] Run `./gradlew.bat assembleDebug`
- [ ] Copy the generated debug APK to the desktop handoff path.
