package com.aiproduct.vocab.data.study

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.aiproduct.vocab.domain.learning.ReviewOutcome
import com.aiproduct.vocab.domain.model.LearnedWordRecord
import com.aiproduct.vocab.domain.model.ReviewGrade
import com.aiproduct.vocab.domain.review.ReviewScheduler

class StudyRecordStore(
    context: Context,
    private val scheduler: ReviewScheduler = ReviewScheduler(),
) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
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
                next_review_at_millis INTEGER NOT NULL,
                added_at_millis INTEGER NOT NULL
            )
            """.trimIndent(),
        )
        db.execSQL(
            """
            CREATE INDEX idx_study_records_next_review
            ON study_records(next_review_at_millis, added_at_millis)
            """.trimIndent(),
        )
        db.execSQL(
            """
            CREATE INDEX idx_study_records_language_added
            ON study_records(language, added_at_millis)
            """.trimIndent(),
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS study_records")
        onCreate(db)
    }

    fun upsert(record: LearnedWordRecord) {
        writableDatabase.insertWithOnConflict(
            TABLE_NAME,
            null,
            record.toContentValues(),
            SQLiteDatabase.CONFLICT_REPLACE,
        )
    }

    fun getLearnedRecord(wordId: Long): LearnedWordRecord? = readableDatabase.rawQuery(
        """
        SELECT word_id,
               language,
               choice_correct_count,
               choice_wrong_count,
               spelling_correct_count,
               spelling_wrong_count,
               hint_used_count,
               review_stage,
               last_learned_at_millis,
               next_review_at_millis,
               added_at_millis
        FROM study_records
        WHERE word_id = ?
        LIMIT 1
        """.trimIndent(),
        arrayOf(wordId.toString()),
    ).use { cursor ->
        if (!cursor.moveToFirst()) {
            return null
        }
        LearnedWordRecord(
            wordId = cursor.getLong(0),
            language = cursor.getString(1).orEmpty(),
            choiceCorrectCount = cursor.getInt(2),
            choiceWrongCount = cursor.getInt(3),
            spellingCorrectCount = cursor.getInt(4),
            spellingWrongCount = cursor.getInt(5),
            hintUsedCount = cursor.getInt(6),
            reviewStage = cursor.getInt(7),
            lastLearnedAtMillis = cursor.getLong(8),
            nextReviewAtMillis = cursor.getLong(9),
            addedAtMillis = cursor.getLong(10),
        )
    }

    fun hasLearnedWord(wordId: Long): Boolean = readableDatabase.rawQuery(
        """
        SELECT 1
        FROM study_records
        WHERE word_id = ?
        LIMIT 1
        """.trimIndent(),
        arrayOf(wordId.toString()),
    ).use { cursor ->
        cursor.moveToFirst()
    }

    fun learnedWordIds(): List<Long> = readableDatabase.rawQuery(
        """
        SELECT word_id
        FROM study_records
        ORDER BY added_at_millis ASC, word_id ASC
        """.trimIndent(),
        emptyArray(),
    ).use { cursor ->
        buildList {
            while (cursor.moveToNext()) {
                add(cursor.getLong(0))
            }
        }
    }

    fun learnedCountsByLanguage(): Map<String, Int> = readableDatabase.rawQuery(
        """
        SELECT language, COUNT(*)
        FROM study_records
        GROUP BY language
        """.trimIndent(),
        emptyArray(),
    ).use { cursor ->
        buildMap {
            while (cursor.moveToNext()) {
                put(cursor.getString(0).orEmpty(), cursor.getInt(1))
            }
        }
    }

    fun dueWordIds(
        nowMillis: Long,
        language: String? = null,
    ): List<Long> {
        val whereClause = buildString {
            append("WHERE next_review_at_millis <= ?")
            if (!language.isNullOrBlank()) {
                append(" AND LOWER(language) = LOWER(?)")
            }
        }
        val args = buildList {
            add(nowMillis.toString())
            if (!language.isNullOrBlank()) {
                add(language)
            }
        }.toTypedArray()
        return readableDatabase.rawQuery(
            """
            SELECT word_id
            FROM study_records
            $whereClause
            ORDER BY next_review_at_millis ASC, added_at_millis ASC, word_id ASC
            """.trimIndent(),
            args,
        ).use { cursor ->
            buildList {
                while (cursor.moveToNext()) {
                    add(cursor.getLong(0))
                }
            }
        }
    }

    fun dueCountsByLanguage(nowMillis: Long): Map<String, Int> = readableDatabase.rawQuery(
        """
        SELECT language, COUNT(*)
        FROM study_records
        WHERE next_review_at_millis <= ?
        GROUP BY language
        """.trimIndent(),
        arrayOf(nowMillis.toString()),
    ).use { cursor ->
        buildMap {
            while (cursor.moveToNext()) {
                put(cursor.getString(0).orEmpty(), cursor.getInt(1))
            }
        }
    }

    fun activityCountBetween(
        startMillis: Long,
        endMillisExclusive: Long,
    ): Int = readableDatabase.rawQuery(
        """
        SELECT COUNT(*)
        FROM study_records
        WHERE last_learned_at_millis >= ?
          AND last_learned_at_millis < ?
        """.trimIndent(),
        arrayOf(startMillis.toString(), endMillisExclusive.toString()),
    ).use { cursor ->
        if (!cursor.moveToFirst()) {
            0
        } else {
            cursor.getInt(0)
        }
    }

    fun activityTimestampsDesc(): List<Long> = readableDatabase.rawQuery(
        """
        SELECT DISTINCT last_learned_at_millis
        FROM study_records
        ORDER BY last_learned_at_millis DESC
        """.trimIndent(),
        emptyArray(),
    ).use { cursor ->
        buildList {
            while (cursor.moveToNext()) {
                add(cursor.getLong(0))
            }
        }
    }

    fun filterUnlearnedWordIds(
        candidates: List<Pair<Long, String>>,
        language: String,
    ): List<Long> {
        val candidateIds = candidates
            .filter { (_, candidateLanguage) -> candidateLanguage.equals(language, ignoreCase = true) }
            .map { it.first }
        if (candidateIds.isEmpty()) {
            return emptyList()
        }
        val learnedIds = queryLearnedIdSet(candidateIds)
        return candidateIds.filterNot(learnedIds::contains)
    }

    fun addWord(wordId: Long, nowMillis: Long) {
        if (hasLearnedWord(wordId)) {
            return
        }
        upsert(placeholderRecord(wordId = wordId, nowMillis = nowMillis))
    }

    fun learningWordIds(): List<Long> = learnedWordIds()

    fun applyReview(wordId: Long, grade: ReviewGrade, nowMillis: Long) {
        val current = getLearnedRecord(wordId) ?: placeholderRecord(wordId = wordId, nowMillis = nowMillis)
        val updated = scheduler.scheduleLearnedWord(
            current = current,
            outcome = grade.toReviewOutcome(),
            nowMillis = nowMillis,
        )
        upsert(
            updated.copy(
                choiceCorrectCount = current.choiceCorrectCount + if (grade == ReviewGrade.KNOW) 1 else 0,
                choiceWrongCount = current.choiceWrongCount + if (grade != ReviewGrade.KNOW) 1 else 0,
                lastLearnedAtMillis = nowMillis,
            ),
        )
    }

    private fun queryLearnedIdSet(wordIds: List<Long>): Set<Long> {
        val placeholders = List(wordIds.size) { "?" }.joinToString(", ")
        return readableDatabase.rawQuery(
            """
            SELECT word_id
            FROM study_records
            WHERE word_id IN ($placeholders)
            """.trimIndent(),
            wordIds.map(Long::toString).toTypedArray(),
        ).use { cursor ->
            buildSet {
                while (cursor.moveToNext()) {
                    add(cursor.getLong(0))
                }
            }
        }
    }

    private fun placeholderRecord(wordId: Long, nowMillis: Long): LearnedWordRecord = LearnedWordRecord(
        wordId = wordId,
        language = "",
        choiceCorrectCount = 0,
        choiceWrongCount = 0,
        spellingCorrectCount = 0,
        spellingWrongCount = 0,
        hintUsedCount = 0,
        reviewStage = 0,
        lastLearnedAtMillis = nowMillis,
        nextReviewAtMillis = Long.MAX_VALUE,
        addedAtMillis = nowMillis,
    )

    private fun LearnedWordRecord.toContentValues(): ContentValues = ContentValues().apply {
        put("word_id", wordId)
        put("language", language)
        put("choice_correct_count", choiceCorrectCount)
        put("choice_wrong_count", choiceWrongCount)
        put("spelling_correct_count", spellingCorrectCount)
        put("spelling_wrong_count", spellingWrongCount)
        put("hint_used_count", hintUsedCount)
        put("review_stage", reviewStage)
        put("last_learned_at_millis", lastLearnedAtMillis)
        put("next_review_at_millis", nextReviewAtMillis)
        put("added_at_millis", addedAtMillis)
    }

    companion object {
        private const val DATABASE_NAME = "study-records.db"
        private const val DATABASE_VERSION = 2
        private const val TABLE_NAME = "study_records"
    }
}

class InMemoryLearnedWordStore {
    private val items = linkedMapOf<Long, LearnedWordRecord>()

    fun upsert(record: LearnedWordRecord) {
        items[record.wordId] = record
    }

    fun getLearnedRecord(wordId: Long): LearnedWordRecord? = items[wordId]

    fun hasLearnedWord(wordId: Long): Boolean = items.containsKey(wordId)

    fun learnedWordIds(): List<Long> = items.values
        .sortedWith(compareBy<LearnedWordRecord> { it.addedAtMillis }.thenBy { it.wordId })
        .map { it.wordId }

    fun learnedCountsByLanguage(): Map<String, Int> = items.values
        .groupingBy { it.language.uppercase() }
        .eachCount()

    fun dueWordIds(
        nowMillis: Long,
        language: String? = null,
    ): List<Long> = items.values
        .filter { it.nextReviewAtMillis <= nowMillis }
        .filter { language.isNullOrBlank() || it.language.equals(language, ignoreCase = true) }
        .sortedWith(
            compareBy<LearnedWordRecord> { it.nextReviewAtMillis }
                .thenBy { it.addedAtMillis }
                .thenBy { it.wordId },
        )
        .map { it.wordId }

    fun dueCountsByLanguage(nowMillis: Long): Map<String, Int> = items.values
        .filter { it.nextReviewAtMillis <= nowMillis }
        .groupingBy { it.language.uppercase() }
        .eachCount()

    fun activityCountBetween(
        startMillis: Long,
        endMillisExclusive: Long,
    ): Int = items.values.count { it.lastLearnedAtMillis in startMillis until endMillisExclusive }

    fun activityTimestampsDesc(): List<Long> = items.values
        .map { it.lastLearnedAtMillis }
        .distinct()
        .sortedDescending()

    fun filterUnlearnedWordIds(
        candidates: List<Pair<Long, String>>,
        language: String,
    ): List<Long> = candidates
        .filter { (_, candidateLanguage) -> candidateLanguage.equals(language, ignoreCase = true) }
        .map { it.first }
        .filterNot(::hasLearnedWord)
}

private fun ReviewGrade.toReviewOutcome(): ReviewOutcome = when (this) {
    ReviewGrade.KNOW -> ReviewOutcome.PERFECT
    ReviewGrade.HARD -> ReviewOutcome.PARTIAL
    ReviewGrade.FORGOT -> ReviewOutcome.FAIL
}
