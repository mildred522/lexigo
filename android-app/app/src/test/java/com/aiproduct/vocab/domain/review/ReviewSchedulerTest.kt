package com.aiproduct.vocab.domain.review

import com.aiproduct.vocab.domain.model.ReviewGrade
import com.aiproduct.vocab.domain.model.StudyRecord
import com.aiproduct.vocab.domain.model.StudyStatus
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ReviewSchedulerTest {
    private val scheduler = ReviewScheduler(dayMillis = 1000L)

    @Test
    fun schedule_forgot_resetsRepetitionAndKeepsWordDueNow() {
        val current = StudyRecord(
            wordId = 1L,
            status = StudyStatus.REVIEWING,
            repetitionCount = 3,
            easeFactor = 2.5,
            intervalDays = 6,
            nextReviewAtMillis = 0L,
            addedAtMillis = 0L,
        )

        val updated = scheduler.schedule(current, ReviewGrade.FORGOT, nowMillis = 5_000L)

        assertEquals(StudyStatus.LEARNING, updated.status)
        assertEquals(0, updated.repetitionCount)
        assertEquals(0, updated.intervalDays)
        assertEquals(5_000L, updated.nextReviewAtMillis)
        assertTrue(updated.easeFactor < 2.5)
    }

    @Test
    fun schedule_know_growsIntervalAndEventuallyMastersWord() {
        val current = StudyRecord(
            wordId = 2L,
            status = StudyStatus.REVIEWING,
            repetitionCount = 5,
            easeFactor = 2.6,
            intervalDays = 8,
            nextReviewAtMillis = 0L,
            addedAtMillis = 0L,
        )

        val updated = scheduler.schedule(current, ReviewGrade.KNOW, nowMillis = 10_000L)

        assertEquals(StudyStatus.MASTERED, updated.status)
        assertEquals(6, updated.repetitionCount)
        assertTrue(updated.intervalDays >= 20)
        assertEquals(10_000L + updated.intervalDays * 1000L, updated.nextReviewAtMillis)
    }
}
