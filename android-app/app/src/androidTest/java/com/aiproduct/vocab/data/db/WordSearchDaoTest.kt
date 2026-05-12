package com.aiproduct.vocab.data.db

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import android.database.sqlite.SQLiteDatabase
import com.aiproduct.vocab.data.`package`.DictionaryAssetInstaller
import java.io.File
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class WordSearchDaoTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext

    private lateinit var databaseProvider: DictionaryDatabaseProvider
    private lateinit var database: android.database.sqlite.SQLiteDatabase
    private lateinit var dao: WordSearchDao

    @Before
    fun setUp() {
        val installState = DictionaryAssetInstaller(context).ensureInstalled()
        databaseProvider = DictionaryDatabaseProvider()
        database = databaseProvider.open(installState)
        dao = WordSearchDao(database)
    }

    @After
    fun tearDown() {
        if (::database.isInitialized) {
            database.close()
        }
    }

    @Test
    fun search_blankQuery_returnsEmptyList() {
        val results = dao.search("   ")

        assertTrue(results.isEmpty())
    }

    @Test
    fun search_queryBonjour_hitsKnownWordByExactLemma() {
        val results = dao.search("bonjour")

        assertFalse(results.isEmpty())
        assertTrue(results.first().lemma.equals("bonjour", ignoreCase = true))
        val matched = results.firstOrNull {
            it.lemma.equals("bonjour", ignoreCase = true) ||
                it.surface.equals("bonjour", ignoreCase = true)
        }
        assertNotNull(matched)
        assertTrue(
            matched!!.meaningZh.isNotBlank() || matched.meaningSourceText.isNotBlank(),
        )
    }

    @Test
    fun search_prefersExactLemmaThenMergesFtsWithoutDuplicateIds() {
        withCustomSearchDatabase(
            wordRows = listOf(
                WordRow(id = 1, lemma = "bonjour-variant", surface = "bonjour-variant"),
                WordRow(id = 10, lemma = "bonjour", surface = "bonjour"),
            ),
            ftsRows = listOf(
                FtsRow(rowId = 1, lemma = "bonjour-variant", surface = "bonjour-variant", meaningSourceText = "bonjour"),
                FtsRow(rowId = 10, lemma = "bonjour", surface = "bonjour", meaningSourceText = "bonjour"),
            ),
        ) { customDao ->
            val results = customDao.search("bonjour")

            assertEquals(listOf(10L, 1L), results.map { it.id })
            assertEquals(1, results.count { it.id == 10L })
        }
    }

    @Test
    fun search_punctuatedQuery_doesNotCrashAndStillFindsTokenizedMatch() {
        withCustomSearchDatabase(
            wordRows = listOf(
                WordRow(id = 10, lemma = "bonjour", surface = "bonjour"),
            ),
            ftsRows = listOf(
                FtsRow(rowId = 10, lemma = "bonjour", surface = "bonjour", meaningSourceText = "salutation"),
            ),
        ) { customDao ->
            val results = customDao.search("bonjour!")

            assertEquals(listOf(10L), results.map { it.id })
        }
    }

    @Test
    fun detail_withSearchHitId_returnsWordDetail() {
        val summary = dao.search("bonjour").first()

        val detail = dao.detail(summary.id)

        assertNotNull(detail)
        assertEquals(summary.id, detail!!.id)
        assertEquals(summary.language, detail.language)
        assertEquals(summary.lemma, detail.lemma)
        assertEquals(summary.surface, detail.surface)
        assertEquals(summary.readingOrIpa, detail.readingOrIpa)
        assertEquals(summary.meaningZh, detail.meaningZh)
        assertEquals(summary.meaningSourceText, detail.meaningSourceText)
    }

    private fun withCustomSearchDatabase(
        wordRows: List<WordRow>,
        ftsRows: List<FtsRow>,
        block: (WordSearchDao) -> Unit,
    ) {
        val tempDbFile = File.createTempFile("word-search-dao-test", ".db", context.cacheDir)
        val tempDb = SQLiteDatabase.openOrCreateDatabase(tempDbFile, null)
        try {
            tempDb.execSQL(
                """
                CREATE TABLE words(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    language TEXT,
                    lemma TEXT,
                    surface TEXT,
                    reading_or_ipa TEXT,
                    pos TEXT,
                    meaning_source TEXT,
                    meaning_source_text TEXT,
                    meaning_source_lang TEXT,
                    meaning_zh TEXT,
                    source_name TEXT,
                    source_entry_id TEXT
                )
                """.trimIndent(),
            )
            tempDb.execSQL(
                """
                CREATE VIRTUAL TABLE words_fts USING fts5(
                    language,
                    lemma,
                    surface,
                    reading_or_ipa,
                    pos,
                    meaning_source,
                    meaning_source_text,
                    meaning_source_lang,
                    meaning_zh,
                    source_name,
                    source_entry_id
                )
                """.trimIndent(),
            )

            wordRows.forEach { row ->
                tempDb.execSQL(
                    """
                    INSERT INTO words(
                        id,
                        language,
                        lemma,
                        surface,
                        reading_or_ipa,
                        pos,
                        meaning_source,
                        meaning_source_text,
                        meaning_source_lang,
                        meaning_zh,
                        source_name,
                        source_entry_id
                    ) VALUES (?, 'FR', ?, ?, '', '', '', '', '', '', '', '')
                    """.trimIndent(),
                    arrayOf(row.id, row.lemma, row.surface),
                )
            }
            ftsRows.forEach { row ->
                tempDb.execSQL(
                    """
                    INSERT INTO words_fts(
                        rowid,
                        language,
                        lemma,
                        surface,
                        reading_or_ipa,
                        pos,
                        meaning_source,
                        meaning_source_text,
                        meaning_source_lang,
                        meaning_zh,
                        source_name,
                        source_entry_id
                    ) VALUES (?, 'FR', ?, ?, '', '', '', ?, '', '', '', '')
                    """.trimIndent(),
                    arrayOf(row.rowId, row.lemma, row.surface, row.meaningSourceText),
                )
            }

            block(WordSearchDao(tempDb))
        } finally {
            tempDb.close()
            tempDbFile.delete()
        }
    }

    private data class WordRow(
        val id: Long,
        val lemma: String,
        val surface: String,
    )

    private data class FtsRow(
        val rowId: Long,
        val lemma: String,
        val surface: String,
        val meaningSourceText: String,
    )
}
