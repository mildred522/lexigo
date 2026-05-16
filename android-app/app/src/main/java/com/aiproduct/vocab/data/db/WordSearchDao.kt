package com.aiproduct.vocab.data.db

import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteException
import com.aiproduct.vocab.domain.learning.LearningBand
import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.WordSummary

class WordSearchDao(
    private val database: SQLiteDatabase,
) {
    fun search(query: String): List<WordSummary> {
        val normalizedQuery = query.trim()
        if (normalizedQuery.isEmpty()) {
            return emptyList()
        }

        val resultsById = LinkedHashMap<Long, WordSummary>(SEARCH_LIMIT)
        for (spec in buildSearchSpecs(normalizedQuery)) {
            if (resultsById.size >= SEARCH_LIMIT) {
                break
            }
            addSearchResults(
                sql = spec.sql,
                args = spec.args,
                resultsById = resultsById,
            )
        }
        return resultsById.values.take(SEARCH_LIMIT)
    }

    fun detail(id: Long): WordDetail? {
        val cursor = database.rawQuery(
            DETAIL_SQL,
            arrayOf(id.toString()),
        )
        cursor.use {
            if (!it.moveToFirst()) {
                return null
            }
            return WordDetail(
                id = it.getLong(0),
                language = it.getString(1).orEmpty(),
                lemma = it.getString(2).orEmpty(),
                surface = it.getString(3).orEmpty(),
                readingOrIpa = it.getString(4).orEmpty(),
                pos = it.getString(5).orEmpty(),
                meaningZh = it.getString(6).orEmpty(),
                meaningSourceText = it.getString(7).orEmpty(),
                exampleSentencesJson = it.getString(8).orEmpty(),
                sourceName = it.getString(9).orEmpty(),
                sourceEntryId = it.getString(10).orEmpty(),
            )
        }
    }

    fun countWordsByLanguage(language: String): Int = database.rawQuery(
        """
        SELECT COUNT(*)
        FROM words
        WHERE LOWER(language) = LOWER(?)
        """.trimIndent(),
        arrayOf(language),
    ).use { cursor ->
        if (!cursor.moveToFirst()) 0 else cursor.getInt(0)
    }

    fun wordIdsByLanguage(
        language: String,
        limit: Int,
        offset: Int,
    ): List<Long> = database.rawQuery(
        """
        SELECT id
        FROM words
        WHERE LOWER(language) = LOWER(?)
        ORDER BY id
        LIMIT ? OFFSET ?
        """.trimIndent(),
        arrayOf(language, limit.toString(), offset.toString()),
    ).use { cursor ->
        buildList {
            while (cursor.moveToNext()) {
                add(cursor.getLong(0))
            }
        }
    }

    fun randomWordIdsByLanguage(
        language: String,
        limit: Int,
    ): List<Long> = database.rawQuery(
        """
        SELECT id
        FROM words
        WHERE LOWER(language) = LOWER(?)
          AND TRIM(COALESCE(lemma, '')) != ''
          AND (
                TRIM(COALESCE(meaning_zh, '')) != ''
                OR TRIM(COALESCE(meaning_source_text, '')) != ''
              )
        ORDER BY RANDOM()
        LIMIT ?
        """.trimIndent(),
        arrayOf(language, limit.toString()),
    ).use { cursor ->
        buildList {
            while (cursor.moveToNext()) {
                add(cursor.getLong(0))
            }
        }
    }

    fun leveledWordIdsByLanguage(
        language: String,
        band: LearningBand,
        limit: Int,
        offset: Int,
    ): List<Long> {
        if (!hasTable(WORD_LEARNING_LEVELS_TABLE)) {
            return emptyList()
        }
        return database.rawQuery(
            """
            SELECT w.id
            FROM word_learning_levels l
            JOIN words w ON w.id = l.word_id
            WHERE LOWER(l.language) = LOWER(?)
              AND ${band.sqlPredicate()}
              AND TRIM(COALESCE(w.lemma, '')) != ''
              AND (
                    TRIM(COALESCE(w.meaning_zh, '')) != ''
                    OR TRIM(COALESCE(w.meaning_source_text, '')) != ''
                  )
            ORDER BY l.level_rank ASC,
                     l.confidence DESC,
                     w.id ASC
            LIMIT ? OFFSET ?
            """.trimIndent(),
            arrayOf(language, limit.toString(), offset.toString()),
        ).use { cursor ->
            buildList {
                while (cursor.moveToNext()) {
                    add(cursor.getLong(0))
                }
            }
        }
    }

    fun meaningsByLanguage(
        language: String,
        limit: Int,
        offset: Int,
    ): List<String> = database.rawQuery(
        """
        SELECT CASE
                   WHEN TRIM(COALESCE(meaning_zh, '')) != '' THEN TRIM(meaning_zh)
                   ELSE TRIM(COALESCE(meaning_source_text, ''))
               END AS display_meaning
        FROM words
        WHERE LOWER(language) = LOWER(?)
          AND (
                TRIM(COALESCE(meaning_zh, '')) != ''
                OR TRIM(COALESCE(meaning_source_text, '')) != ''
              )
        ORDER BY id
        LIMIT ? OFFSET ?
        """.trimIndent(),
        arrayOf(language, limit.toString(), offset.toString()),
    ).use { cursor ->
        buildList {
            while (cursor.moveToNext()) {
                val meaning = cursor.getString(0).orEmpty().trim()
                if (meaning.isNotBlank()) {
                    add(meaning)
                }
            }
        }
    }

    private fun addSearchResults(
        sql: String,
        args: Array<String>,
        resultsById: LinkedHashMap<Long, WordSummary>,
    ) {
        try {
            val cursor = database.rawQuery(sql, args)
            cursor.use {
                while (it.moveToNext() && resultsById.size < SEARCH_LIMIT) {
                    val summary = WordSummary(
                        id = it.getLong(0),
                        language = it.getString(1).orEmpty(),
                        lemma = it.getString(2).orEmpty(),
                        surface = it.getString(3).orEmpty(),
                        readingOrIpa = it.getString(4).orEmpty(),
                        meaningZh = it.getString(5).orEmpty(),
                        meaningSourceText = it.getString(6).orEmpty(),
                    )
                    resultsById.putIfAbsent(summary.id, summary)
                }
            }
        } catch (_: SQLiteException) {
            // Treat malformed FTS syntax as a no-result path instead of crashing search.
        }
    }

    private fun hasTable(tableName: String): Boolean = database.rawQuery(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        LIMIT 1
        """.trimIndent(),
        arrayOf(tableName),
    ).use { cursor -> cursor.moveToFirst() }
}

private fun LearningBand.sqlPredicate(): String = when (this) {
    LearningBand.BEGINNER ->
        """
        (
          l.review_status = 'accepted'
          AND (
            l.level = 'N5'
            OR (l.level = 'N4' AND l.confidence >= 0.90)
          )
        )
        """.trimIndent()

    LearningBand.INTERMEDIATE ->
        """
        (
          l.review_status = 'accepted'
          AND (
            l.level IN ('N4', 'N3')
            OR (l.level = 'N2' AND l.confidence >= 0.85)
          )
        )
        """.trimIndent()

    LearningBand.ADVANCED ->
        """
        (
          (
            l.review_status = 'accepted'
            AND l.level IN ('N2', 'N1')
          )
          OR (
            l.review_status = 'advanced'
            AND l.confidence >= 0.85
          )
        )
        """.trimIndent()
}

internal data class SearchSpec(
    val sql: String,
    val args: Array<String>,
)

internal const val SEARCH_LIMIT = 20
private const val WORD_LEARNING_LEVELS_TABLE = "word_learning_levels"
internal val FTS_TOKEN_REGEX = Regex("[\\p{L}\\p{N}_]+")

internal const val EXACT_SEARCH_SQL =
    """
    SELECT id,
           language,
           lemma,
           surface,
           reading_or_ipa,
           meaning_zh,
           meaning_source_text
    FROM words
    WHERE lemma = ? COLLATE NOCASE
       OR surface = ? COLLATE NOCASE
    ORDER BY id
    LIMIT 20
    """

internal const val PREFIX_SEARCH_SQL =
    """
    SELECT id,
           language,
           lemma,
           surface,
           reading_or_ipa,
           meaning_zh,
           meaning_source_text
    FROM words
    WHERE lemma LIKE ? ESCAPE '\' COLLATE NOCASE
       OR surface LIKE ? ESCAPE '\' COLLATE NOCASE
    ORDER BY id
    LIMIT 20
    """

internal const val MEANING_LIKE_SEARCH_SQL =
    """
    SELECT id,
           language,
           lemma,
           surface,
           reading_or_ipa,
           meaning_zh,
           meaning_source_text
    FROM words
    WHERE meaning_zh LIKE ? ESCAPE '\'
       OR meaning_source_text LIKE ? ESCAPE '\' COLLATE NOCASE
    ORDER BY id
    LIMIT 20
    """

internal const val FTS_SEARCH_SQL =
    """
    SELECT w.id,
           w.language,
           w.lemma,
           w.surface,
           w.reading_or_ipa,
           w.meaning_zh,
           w.meaning_source_text
    FROM words_fts f
    JOIN words w ON w.id = f.rowid
    WHERE words_fts MATCH ?
    LIMIT 20
    """

private const val DETAIL_SQL =
    """
    SELECT id,
           language,
           lemma,
           surface,
           reading_or_ipa,
           pos,
           meaning_zh,
           meaning_source_text,
           example_sentences_json,
           source_name,
           source_entry_id
    FROM words
    WHERE id = ?
    LIMIT 1
    """

internal fun buildSearchSpecs(query: String): List<SearchSpec> {
    val escaped = escapeLikePattern(query)
    val specs = mutableListOf(
        SearchSpec(
            sql = EXACT_SEARCH_SQL,
            args = arrayOf(query, query),
        ),
        SearchSpec(
            sql = PREFIX_SEARCH_SQL,
            args = arrayOf("$escaped%", "$escaped%"),
        ),
        SearchSpec(
            sql = MEANING_LIKE_SEARCH_SQL,
            args = arrayOf("%$escaped%", "%$escaped%"),
        ),
    )
    buildSafeFtsQuery(query)?.let { ftsQuery ->
        specs += SearchSpec(
            sql = FTS_SEARCH_SQL,
            args = arrayOf(ftsQuery),
        )
    }
    return specs
}

internal fun buildSafeFtsQuery(query: String): String? {
    val tokens = FTS_TOKEN_REGEX.findAll(query)
        .map { "${it.value}*" }
        .toList()
    if (tokens.isEmpty()) {
        return null
    }
    return tokens.joinToString(" ")
}

private fun escapeLikePattern(query: String): String = buildString(query.length) {
    query.forEach { char ->
        if (char == '%' || char == '_' || char == '\\') {
            append('\\')
        }
        append(char)
    }
}
