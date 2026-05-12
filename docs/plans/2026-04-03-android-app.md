# Android App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Android app inside this repository with a working local dictionary lookup loop backed by the packaged SQLite dictionary.

**Architecture:** Add a new `android-app/` project using a single Android application module with internal `data`, `domain`, and `ui` boundaries. The app consumes the packaged `dictionary.db` and `manifest.json`, installs them into app-private storage, queries SQLite directly for exact and FTS lookups, and renders Compose search and detail screens.

**Tech Stack:** Kotlin, Jetpack Compose, AndroidX Lifecycle ViewModel, Navigation Compose, coroutines, direct SQLite access, JUnit4, Compose UI tests, Android instrumented tests.

---

### Task 1: Bootstrap The Android App Skeleton

**Files:**
- Create: `android-app/settings.gradle.kts`
- Create: `android-app/build.gradle.kts`
- Create: `android-app/gradle.properties`
- Create: `android-app/app/build.gradle.kts`
- Create: `android-app/app/proguard-rules.pro`
- Create: `android-app/app/src/main/AndroidManifest.xml`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/MainActivity.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppRoot.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/theme/Color.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/theme/Theme.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/theme/Type.kt`
- Test: `android-app/app/src/androidTest/java/com/aiproduct/vocab/AppLaunchTest.kt`

- [ ] **Step 1: Write the failing launch test**

```kotlin
package com.aiproduct.vocab

import androidx.compose.ui.test.assertExists
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AppLaunchTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Test
    fun showsSearchShell() {
        rule.onNodeWithText("词库查询").assertExists()
        rule.onNodeWithText("输入单词或释义").assertExists()
    }
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.AppLaunchTest`
Expected: FAIL because the Android project, `MainActivity`, and Compose UI do not exist yet.

- [ ] **Step 3: Write the minimal Android scaffold**

```kotlin
// android-app/app/src/main/java/com/aiproduct/vocab/MainActivity.kt
package com.aiproduct.vocab

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.aiproduct.vocab.ui.AppRoot
import com.aiproduct.vocab.ui.theme.VocabTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            VocabTheme {
                AppRoot()
            }
        }
    }
}
```

```kotlin
// android-app/app/src/main/java/com/aiproduct/vocab/ui/AppRoot.kt
package com.aiproduct.vocab.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun AppRoot() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("词库查询", style = MaterialTheme.typography.headlineMedium)
        OutlinedTextField(
            value = remember { "" },
            onValueChange = {},
            label = { Text("输入单词或释义") },
        )
    }
}
```

```kotlin
// android-app/app/build.gradle.kts
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.aiproduct.vocab"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.aiproduct.vocab"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures {
        compose = true
    }
}
```

- [ ] **Step 4: Run the launch test to verify it passes**

Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.AppLaunchTest`
Expected: PASS, with the app launching and rendering the initial search shell.

- [ ] **Step 5: Commit**

```bash
git add android-app
git commit -m "feat: bootstrap android app shell"
```

### Task 2: Sync The Packaged Dictionary Into Android Assets

**Files:**
- Create: `scripts/sync_android_dictionary_assets.py`
- Create: `android-app/app/src/main/assets/dictionary/.gitkeep`
- Modify: `android-app/app/build.gradle.kts`
- Test: `tests/test_sync_android_dictionary_assets.py`

- [ ] **Step 1: Write the failing sync test**

```python
from pathlib import Path

from sync_android_dictionary_assets import sync_android_assets


def test_sync_android_assets_copies_dictionary_package(tmp_path: Path) -> None:
    package_dir = tmp_path / "package"
    assets_dir = tmp_path / "assets" / "dictionary"
    package_dir.mkdir(parents=True)
    (package_dir / "dictionary.db").write_bytes(b"db")
    (package_dir / "manifest.json").write_text('{"schema_version":1}', encoding="utf-8")

    sync_android_assets(package_dir=package_dir, assets_dir=assets_dir)

    assert (assets_dir / "dictionary.db").exists()
    assert (assets_dir / "manifest.json").exists()
```

- [ ] **Step 2: Run the test to verify it fails**

Run from repository root: `python -m pytest -v tests/test_sync_android_dictionary_assets.py`
Expected: FAIL because the sync script and callable do not exist yet.

- [ ] **Step 3: Implement the asset sync script and Gradle prebuild hook**

```python
# scripts/sync_android_dictionary_assets.py
from pathlib import Path
import shutil


def sync_android_assets(*, package_dir: Path, assets_dir: Path) -> None:
    assets_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("dictionary.db", "manifest.json"):
        shutil.copy2(package_dir / filename, assets_dir / filename)
```

```kotlin
// android-app/app/build.gradle.kts
tasks.register<Exec>("syncDictionaryAssets") {
    workingDir = rootDir.parentFile
    commandLine("python", "scripts/sync_android_dictionary_assets.py")
}

tasks.named("preBuild") {
    dependsOn("syncDictionaryAssets")
}
```

- [ ] **Step 4: Run the sync test to verify it passes**

Run from repository root: `python -m pytest -v tests/test_sync_android_dictionary_assets.py`
Expected: PASS, with both packaged files copied into `android-app/app/src/main/assets/dictionary/`.

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_android_dictionary_assets.py tests/test_sync_android_dictionary_assets.py android-app/app/build.gradle.kts android-app/app/src/main/assets/dictionary/.gitkeep
git commit -m "feat: sync packaged dictionary assets into android app"
```

### Task 3: Install And Open The Packaged Dictionary

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/data/package/DictionaryPackageManifest.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/data/package/DictionaryManifestReader.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/data/package/DictionaryAssetInstaller.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/data/db/DictionaryDatabaseProvider.kt`
- Test: `android-app/app/src/test/java/com/aiproduct/vocab/data/package/DictionaryManifestReaderTest.kt`
- Test: `android-app/app/src/androidTest/java/com/aiproduct/vocab/data/package/DictionaryAssetInstallerTest.kt`

- [ ] **Step 1: Write the failing manifest and installer tests**

```kotlin
package com.aiproduct.vocab.data.package

import org.junit.Assert.assertEquals
import org.junit.Test

class DictionaryManifestReaderTest {
    @Test
    fun parsesManifestFields() {
        val json = """
            {"schema_version":1,"db_filename":"dictionary.db","search_capabilities":{"fts":true}}
        """.trimIndent()

        val manifest = DictionaryManifestReader().read(json)

        assertEquals(1, manifest.schemaVersion)
        assertEquals("dictionary.db", manifest.dbFilename)
        assertEquals(true, manifest.ftsEnabled)
    }
}
```

```kotlin
package com.aiproduct.vocab.data.package

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DictionaryAssetInstallerTest {
    @Test
    fun copiesPackagedFilesIntoAppStorage() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val installer = DictionaryAssetInstaller(context)

        val installState = installer.ensureInstalled()

        assertTrue(installState.databaseFile.exists())
        assertTrue(installState.manifestFile.exists())
    }
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run from `android-app/`: `.\gradlew.bat :app:testDebugUnitTest --tests com.aiproduct.vocab.data.package.DictionaryManifestReaderTest`
Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.data.package.DictionaryAssetInstallerTest`
Expected: FAIL because manifest parsing and asset installation code do not exist yet.

- [ ] **Step 3: Implement manifest parsing, installation, and database provider**

```kotlin
// DictionaryPackageManifest.kt
package com.aiproduct.vocab.data.package

data class DictionaryPackageManifest(
    val schemaVersion: Int,
    val dbFilename: String,
    val ftsEnabled: Boolean,
)
```

```kotlin
// DictionaryAssetInstaller.kt
package com.aiproduct.vocab.data.package

import android.content.Context
import java.io.File

class DictionaryAssetInstaller(private val context: Context) {
    fun ensureInstalled(): InstallState {
        val outDir = File(context.filesDir, "dictionary")
        outDir.mkdirs()
        val dbFile = File(outDir, "dictionary.db")
        val manifestFile = File(outDir, "manifest.json")
        if (!dbFile.exists()) {
            context.assets.open("dictionary/dictionary.db").use { input ->
                dbFile.outputStream().use(input::copyTo)
            }
        }
        if (!manifestFile.exists()) {
            context.assets.open("dictionary/manifest.json").use { input ->
                manifestFile.outputStream().use(input::copyTo)
            }
        }
        return InstallState(dbFile, manifestFile)
    }
}

data class InstallState(val databaseFile: File, val manifestFile: File)
```

```kotlin
// DictionaryDatabaseProvider.kt
package com.aiproduct.vocab.data.db

import android.database.sqlite.SQLiteDatabase
import java.io.File

class DictionaryDatabaseProvider {
    fun open(databaseFile: File): SQLiteDatabase {
        return SQLiteDatabase.openDatabase(
            databaseFile.absolutePath,
            null,
            SQLiteDatabase.OPEN_READONLY,
        )
    }
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run from `android-app/`: `.\gradlew.bat :app:testDebugUnitTest --tests com.aiproduct.vocab.data.package.DictionaryManifestReaderTest`
Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.data.package.DictionaryAssetInstallerTest`
Expected: PASS, with manifest parsing succeeding and packaged files copied into app-private storage.

- [ ] **Step 5: Commit**

```bash
git add android-app/app/src/main/java/com/aiproduct/vocab/data/package android-app/app/src/main/java/com/aiproduct/vocab/data/db/DictionaryDatabaseProvider.kt android-app/app/src/test/java/com/aiproduct/vocab/data/package/DictionaryManifestReaderTest.kt android-app/app/src/androidTest/java/com/aiproduct/vocab/data/package/DictionaryAssetInstallerTest.kt
git commit -m "feat: install packaged dictionary into android storage"
```

### Task 4: Implement SQLite Query Access And Repository Mapping

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/domain/model/WordSummary.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/domain/model/WordDetail.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/data/db/WordSearchDao.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/data/repository/DictionaryRepository.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/data/repository/DictionaryRepositoryImpl.kt`
- Test: `android-app/app/src/androidTest/java/com/aiproduct/vocab/data/db/WordSearchDaoTest.kt`

- [ ] **Step 1: Write the failing DAO test**

```kotlin
package com.aiproduct.vocab.data.db

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.aiproduct.vocab.data.package.DictionaryAssetInstaller
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class WordSearchDaoTest {
    @Test
    fun findsKnownWordFromPackagedDatabase() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val installState = DictionaryAssetInstaller(context).ensureInstalled()
        val database = DictionaryDatabaseProvider().open(installState.databaseFile)
        val dao = WordSearchDao(database)

        val results = dao.search("bonjour")

        assertTrue(results.isNotEmpty())
    }
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.data.db.WordSearchDaoTest`
Expected: FAIL because `WordSearchDao` and repository mapping do not exist yet.

- [ ] **Step 3: Implement direct SQLite queries and repository mapping**

```kotlin
// WordSearchDao.kt
package com.aiproduct.vocab.data.db

import android.database.sqlite.SQLiteDatabase
import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.WordSummary

class WordSearchDao(private val database: SQLiteDatabase) {
    fun search(query: String): List<WordSummary> {
        val sql = """
            select rowid, language, lemma, surface, reading_or_ipa, meaning_zh, meaning_source_text
            from words_fts
            where words_fts match ?
            limit 20
        """.trimIndent()
        return database.rawQuery(sql, arrayOf(query)).use { cursor ->
            buildList {
                while (cursor.moveToNext()) {
                    add(
                        WordSummary(
                            id = cursor.getLong(0),
                            language = cursor.getString(1),
                            lemma = cursor.getString(2),
                            surface = cursor.getString(3),
                            readingOrIpa = cursor.getString(4),
                            meaningZh = cursor.getString(5),
                            meaningSourceText = cursor.getString(6),
                        ),
                    )
                }
            }
        }
    }

    fun detail(id: Long): WordDetail? {
        val sql = """
            select rowid, language, lemma, surface, reading_or_ipa, pos, meaning_zh, meaning_source_text, source_name
            from words
            where rowid = ?
        """.trimIndent()
        return database.rawQuery(sql, arrayOf(id.toString())).use { cursor ->
            if (!cursor.moveToFirst()) {
                return null
            }
            WordDetail(
                id = cursor.getLong(0),
                language = cursor.getString(1),
                lemma = cursor.getString(2),
                surface = cursor.getString(3),
                readingOrIpa = cursor.getString(4),
                pos = cursor.getString(5),
                meaningZh = cursor.getString(6),
                meaningSourceText = cursor.getString(7),
                sourceName = cursor.getString(8),
            )
        }
    }
}
```

```kotlin
// DictionaryRepository.kt
package com.aiproduct.vocab.data.repository

import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.WordSummary

interface DictionaryRepository {
    suspend fun search(query: String): List<WordSummary>
    suspend fun detail(id: Long): WordDetail?
}
```

- [ ] **Step 4: Run the DAO test to verify it passes**

Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.data.db.WordSearchDaoTest`
Expected: PASS, with a known packaged term returning at least one result from the local database.

- [ ] **Step 5: Commit**

```bash
git add android-app/app/src/main/java/com/aiproduct/vocab/domain/model android-app/app/src/main/java/com/aiproduct/vocab/data/db/WordSearchDao.kt android-app/app/src/main/java/com/aiproduct/vocab/data/repository android-app/app/src/androidTest/java/com/aiproduct/vocab/data/db/WordSearchDaoTest.kt
git commit -m "feat: add android dictionary query repository"
```

### Task 5: Implement Search State, Use Cases, And Search Screen

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/domain/usecase/SearchWordsUseCase.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/search/SearchUiState.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/search/SearchViewModel.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/search/SearchScreen.kt`
- Test: `android-app/app/src/test/java/com/aiproduct/vocab/ui/search/SearchViewModelTest.kt`
- Test: `android-app/app/src/androidTest/java/com/aiproduct/vocab/ui/search/SearchScreenTest.kt`

- [ ] **Step 1: Write the failing ViewModel and screen tests**

```kotlin
package com.aiproduct.vocab.ui.search

import com.aiproduct.vocab.domain.model.WordSummary
import com.aiproduct.vocab.domain.usecase.SearchWordsUseCase
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class SearchViewModelTest {
    @Test
    fun updatesResultsWhenQueryChanges() = runTest {
        val viewModel = SearchViewModel(
            searchWords = SearchWordsUseCase { query ->
                listOf(WordSummary(1, "FR", "bonjour", "bonjour", "bOn.zur", "你好", "salutation"))
            },
        )

        viewModel.onQueryChanged("bonjour")

        assertEquals(1, viewModel.uiState.value.results.size)
    }
}
```

```kotlin
package com.aiproduct.vocab.ui.search

import androidx.compose.ui.test.assertExists
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test

class SearchScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun rendersResultItem() {
        rule.setContent {
            SearchScreen(
                state = SearchUiState(
                    query = "bonjour",
                    results = listOf(
                        SearchResultItem(
                            id = 1,
                            lemma = "bonjour",
                            readingOrIpa = "bOn.zur",
                            language = "FR",
                            meaningZh = "你好",
                            meaningSourceText = "salutation",
                        ),
                    ),
                ),
                onQueryChanged = {},
                onResultClick = {},
            )
        }

        rule.onNodeWithText("bonjour").assertExists()
        rule.onNodeWithText("你好").assertExists()
    }
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run from `android-app/`: `.\gradlew.bat :app:testDebugUnitTest --tests com.aiproduct.vocab.ui.search.SearchViewModelTest`
Run from `android-app/`: `.\gradlew.bat :app:testDebugUnitTest --tests com.aiproduct.vocab.ui.search.SearchScreenTest`
Expected: FAIL because the search use case, state models, ViewModel, and screen do not exist yet.

- [ ] **Step 3: Implement search use case, ViewModel, and Compose screen**

```kotlin
// SearchWordsUseCase.kt
package com.aiproduct.vocab.domain.usecase

import com.aiproduct.vocab.domain.model.WordSummary

fun interface SearchWordsUseCase {
    suspend operator fun invoke(query: String): List<WordSummary>
}
```

```kotlin
// SearchViewModel.kt
package com.aiproduct.vocab.ui.search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aiproduct.vocab.domain.usecase.SearchWordsUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class SearchViewModel(
    private val searchWords: SearchWordsUseCase,
) : ViewModel() {
    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState

    fun onQueryChanged(query: String) {
        _uiState.value = _uiState.value.copy(query = query, isLoading = true)
        viewModelScope.launch {
            val results = if (query.isBlank()) emptyList() else searchWords(query).map(SearchResultItem::from)
            _uiState.value = _uiState.value.copy(isLoading = false, results = results)
        }
    }
}
```

```kotlin
// SearchScreen.kt
package com.aiproduct.vocab.ui.search

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun SearchScreen(
    state: SearchUiState,
    onQueryChanged: (String) -> Unit,
    onResultClick: (Long) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text("词库查询")
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = state.query,
            onValueChange = onQueryChanged,
            label = { Text("输入单词或释义") },
        )
        LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(state.results, key = { it.id }) { item ->
                Card(modifier = Modifier.fillMaxWidth().clickable { onResultClick(item.id) }) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(item.lemma)
                        Text(item.readingOrIpa)
                        Text(item.meaningZh)
                        Text(item.meaningSourceText)
                    }
                }
            }
        }
    }
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run from `android-app/`: `.\gradlew.bat :app:testDebugUnitTest --tests com.aiproduct.vocab.ui.search.SearchViewModelTest`
Run from `android-app/`: `.\gradlew.bat :app:testDebugUnitTest --tests com.aiproduct.vocab.ui.search.SearchScreenTest`
Expected: PASS, with search state updates and Compose rendering verified.

- [ ] **Step 5: Commit**

```bash
git add android-app/app/src/main/java/com/aiproduct/vocab/domain/usecase/SearchWordsUseCase.kt android-app/app/src/main/java/com/aiproduct/vocab/ui/search android-app/app/src/test/java/com/aiproduct/vocab/ui/search
git commit -m "feat: add android search presentation layer"
```

### Task 6: Add Detail Navigation And End-To-End Smoke Coverage

**Files:**
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/domain/usecase/GetWordDetailUseCase.kt`
- Create: `android-app/app/src/main/java/com/aiproduct/vocab/ui/detail/WordDetailScreen.kt`
- Modify: `android-app/app/src/main/java/com/aiproduct/vocab/ui/AppRoot.kt`
- Test: `android-app/app/src/androidTest/java/com/aiproduct/vocab/DictionaryFlowSmokeTest.kt`

- [ ] **Step 1: Write the failing end-to-end smoke test**

```kotlin
package com.aiproduct.vocab

import androidx.compose.ui.test.assertExists
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DictionaryFlowSmokeTest {
    @get:Rule
    val rule = createAndroidComposeRule<MainActivity>()

    @Test
    fun searchesAndOpensDetail() {
        rule.onNodeWithText("输入单词或释义").performTextInput("bonjour")
        rule.onNodeWithText("bonjour").assertExists()
        rule.onNodeWithText("bonjour").performClick()
        rule.onNodeWithText("来源释义").assertExists()
    }
}
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.DictionaryFlowSmokeTest`
Expected: FAIL because there is no detail navigation or detail screen yet.

- [ ] **Step 3: Implement detail use case, detail screen, and navigation**

```kotlin
// WordDetailScreen.kt
package com.aiproduct.vocab.ui.detail

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.domain.model.WordDetail

@Composable
fun WordDetailScreen(detail: WordDetail) {
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(detail.lemma)
        Text(detail.readingOrIpa)
        Text(detail.meaningZh)
        Text("来源释义")
        Text(detail.meaningSourceText)
        Text(detail.sourceName)
    }
}
```

```kotlin
// AppRoot.kt
package com.aiproduct.vocab.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController

@Composable
fun AppRoot() {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = "search") {
        composable("search") {
            val viewModel = rememberSearchViewModel()
            val state by viewModel.uiState.collectAsState()
            SearchScreen(
                state = state,
                onQueryChanged = viewModel::onQueryChanged,
                onResultClick = { id -> navController.navigate("detail/$id") },
            )
        }
        composable("detail/{id}") { backStackEntry ->
            val id = backStackEntry.arguments?.getString("id")?.toLongOrNull() ?: return@composable
            val detail = rememberWordDetail(id) ?: return@composable
            WordDetailScreen(detail = detail)
        }
    }
}
```

- [ ] **Step 4: Run the smoke test and the full Android test suite**

Run from `android-app/`: `.\gradlew.bat :app:connectedDebugAndroidTest --tests com.aiproduct.vocab.DictionaryFlowSmokeTest`
Run from `android-app/`: `.\gradlew.bat :app:testDebugUnitTest :app:connectedDebugAndroidTest`
Expected: PASS, with the app launching, searching the local dictionary, and opening a readable detail page.

- [ ] **Step 5: Commit**

```bash
git add android-app/app/src/main/java/com/aiproduct/vocab/domain/usecase/GetWordDetailUseCase.kt android-app/app/src/main/java/com/aiproduct/vocab/ui/detail android-app/app/src/main/java/com/aiproduct/vocab/ui/AppRoot.kt android-app/app/src/androidTest/java/com/aiproduct/vocab/DictionaryFlowSmokeTest.kt
git commit -m "feat: complete android local dictionary lookup flow"
```
