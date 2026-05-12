package com.aiproduct.vocab.data.starred

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

class StarredWordStore(
    context: Context,
) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE starred_words (
                word_id INTEGER PRIMARY KEY,
                starred_at_millis INTEGER NOT NULL
            )
            """.trimIndent(),
        )
        db.execSQL(
            """
            CREATE INDEX idx_starred_words_starred_at
            ON starred_words(starred_at_millis DESC)
            """.trimIndent(),
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS starred_words")
        onCreate(db)
    }

    fun starWord(wordId: Long, nowMillis: Long) {
        writableDatabase.insertWithOnConflict(
            TABLE_NAME,
            null,
            ContentValues().apply {
                put("word_id", wordId)
                put("starred_at_millis", nowMillis)
            },
            SQLiteDatabase.CONFLICT_REPLACE,
        )
    }

    fun unstarWord(wordId: Long) {
        writableDatabase.delete(TABLE_NAME, "word_id = ?", arrayOf(wordId.toString()))
    }

    fun isStarred(wordId: Long): Boolean = readableDatabase.rawQuery(
        """
        SELECT 1
        FROM starred_words
        WHERE word_id = ?
        LIMIT 1
        """.trimIndent(),
        arrayOf(wordId.toString()),
    ).use { cursor ->
        cursor.moveToFirst()
    }

    fun starredWordIds(): List<Long> = readableDatabase.rawQuery(
        """
        SELECT word_id
        FROM starred_words
        ORDER BY starred_at_millis DESC
        """.trimIndent(),
        emptyArray(),
    ).use { cursor ->
        buildList {
            while (cursor.moveToNext()) {
                add(cursor.getLong(0))
            }
        }
    }

    fun starredCount(): Int = readableDatabase.rawQuery(
        """
        SELECT COUNT(*)
        FROM starred_words
        """.trimIndent(),
        emptyArray(),
    ).use { cursor ->
        if (!cursor.moveToFirst()) 0 else cursor.getInt(0)
    }

    companion object {
        private const val DATABASE_NAME = "starred-words.db"
        private const val DATABASE_VERSION = 1
        private const val TABLE_NAME = "starred_words"
    }
}

class InMemoryStarredWordStore {
    private val items = linkedMapOf<Long, Long>()

    fun starWord(wordId: Long, nowMillis: Long) {
        items[wordId] = nowMillis
    }

    fun unstarWord(wordId: Long) {
        items.remove(wordId)
    }

    fun isStarred(wordId: Long): Boolean = items.containsKey(wordId)

    fun starredWordIds(): List<Long> = items.entries
        .sortedByDescending { it.value }
        .map { it.key }

    fun starredCount(): Int = items.size
}
