package com.aiproduct.vocab.data.study

import com.aiproduct.vocab.domain.model.LearnedWordRecord
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StudyRecordStoreTest {

    @Test
    fun memoryStore_returnsStoredRecordAndPreservesLearningOrder() {
        val store = InMemoryLearnedWordStore()
        val first = LearnedWordRecord(
            wordId = 10L,
            language = "JA",
            choiceCorrectCount = 1,
            choiceWrongCount = 0,
            spellingCorrectCount = 1,
            spellingWrongCount = 0,
            hintUsedCount = 0,
            reviewStage = 1,
            lastLearnedAtMillis = 1_000L,
            nextReviewAtMillis = 2_000L,
            addedAtMillis = 900L,
        )
        val second = LearnedWordRecord(
            wordId = 20L,
            language = "FR",
            choiceCorrectCount = 1,
            choiceWrongCount = 0,
            spellingCorrectCount = 1,
            spellingWrongCount = 0,
            hintUsedCount = 1,
            reviewStage = 2,
            lastLearnedAtMillis = 2_000L,
            nextReviewAtMillis = 3_000L,
            addedAtMillis = 1_500L,
        )

        store.upsert(second)
        store.upsert(first)

        assertEquals(first, store.getLearnedRecord(10L))
        assertEquals(listOf(10L, 20L), store.learnedWordIds())
    }

    @Test
    fun memoryStore_returnsUnlearnedIdsByLanguage() {
        val store = InMemoryLearnedWordStore()

        store.upsert(
            LearnedWordRecord(
                wordId = 1L,
                language = "JA",
                choiceCorrectCount = 1,
                choiceWrongCount = 0,
                spellingCorrectCount = 1,
                spellingWrongCount = 0,
                hintUsedCount = 0,
                reviewStage = 1,
                lastLearnedAtMillis = 1_000L,
                nextReviewAtMillis = 2_000L,
            ),
        )

        val candidates = listOf(
            1L to "JA",
            2L to "JA",
            3L to "FR",
            4L to "JA",
        )

        assertEquals(listOf(2L, 4L), store.filterUnlearnedWordIds(candidates, "JA"))
    }

    @Test
    fun memoryStore_dueWordIds_onlyIncludesDueLearnedWords() {
        val store = InMemoryLearnedWordStore()
        store.upsert(
            LearnedWordRecord(
                wordId = 7L,
                language = "FR",
                choiceCorrectCount = 1,
                choiceWrongCount = 0,
                spellingCorrectCount = 1,
                spellingWrongCount = 0,
                hintUsedCount = 0,
                reviewStage = 2,
                lastLearnedAtMillis = 1_000L,
                nextReviewAtMillis = 1_500L,
            ),
        )
        store.upsert(
            LearnedWordRecord(
                wordId = 8L,
                language = "FR",
                choiceCorrectCount = 1,
                choiceWrongCount = 0,
                spellingCorrectCount = 1,
                spellingWrongCount = 0,
                hintUsedCount = 0,
                reviewStage = 3,
                lastLearnedAtMillis = 1_000L,
                nextReviewAtMillis = 5_000L,
            ),
        )

        assertEquals(listOf(7L), store.dueWordIds(nowMillis = 2_000L))
        assertTrue(store.hasLearnedWord(7L))
        assertFalse(store.hasLearnedWord(99L))
    }

    @Test
    fun memoryStore_groupsDueCountsByLanguage() {
        val store = InMemoryLearnedWordStore()
        store.upsert(
            LearnedWordRecord(
                wordId = 100L,
                language = "JA",
                choiceCorrectCount = 1,
                choiceWrongCount = 0,
                spellingCorrectCount = 1,
                spellingWrongCount = 0,
                hintUsedCount = 0,
                reviewStage = 1,
                lastLearnedAtMillis = 1_000L,
                nextReviewAtMillis = 2_000L,
            ),
        )
        store.upsert(
            LearnedWordRecord(
                wordId = 200L,
                language = "FR",
                choiceCorrectCount = 1,
                choiceWrongCount = 0,
                spellingCorrectCount = 1,
                spellingWrongCount = 0,
                hintUsedCount = 0,
                reviewStage = 2,
                lastLearnedAtMillis = 1_500L,
                nextReviewAtMillis = 2_000L,
            ),
        )
        store.upsert(
            LearnedWordRecord(
                wordId = 300L,
                language = "JA",
                choiceCorrectCount = 1,
                choiceWrongCount = 0,
                spellingCorrectCount = 1,
                spellingWrongCount = 0,
                hintUsedCount = 0,
                reviewStage = 3,
                lastLearnedAtMillis = 2_000L,
                nextReviewAtMillis = 9_000L,
            ),
        )

        assertEquals(mapOf("JA" to 1, "FR" to 1), store.dueCountsByLanguage(nowMillis = 3_000L))
        assertEquals(listOf(100L), store.dueWordIds(nowMillis = 3_000L, language = "JA"))
    }
}
