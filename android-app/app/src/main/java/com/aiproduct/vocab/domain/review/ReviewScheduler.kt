package com.aiproduct.vocab.domain.review

import com.aiproduct.vocab.domain.learning.ReviewOutcome
import com.aiproduct.vocab.domain.model.LearnedWordRecord
import com.aiproduct.vocab.domain.model.ReviewGrade
import com.aiproduct.vocab.domain.model.StudyRecord
import com.aiproduct.vocab.domain.model.StudyStatus
import kotlin.math.max
import kotlin.math.roundToInt

class ReviewScheduler(
    private val dayMillis: Long = 24L * 60L * 60L * 1000L,
) {
    private val intervalDaysByStage = listOf(0, 1, 2, 4, 7, 15, 30)

    fun schedule(
        current: StudyRecord,
        grade: ReviewGrade,
        nowMillis: Long,
    ): StudyRecord {
        return when (grade) {
            ReviewGrade.FORGOT -> current.copy(
                status = StudyStatus.LEARNING,
                repetitionCount = 0,
                easeFactor = max(1.3, current.easeFactor - 0.2),
                intervalDays = 0,
                nextReviewAtMillis = nowMillis,
            )

            ReviewGrade.HARD -> {
                val nextRepetition = max(1, current.repetitionCount + 1)
                val nextInterval = when (current.repetitionCount) {
                    0 -> 1
                    else -> max(1, (current.intervalDays * 1.2).roundToInt())
                }
                current.copy(
                    status = StudyStatus.REVIEWING,
                    repetitionCount = nextRepetition,
                    easeFactor = max(1.3, current.easeFactor - 0.15),
                    intervalDays = nextInterval,
                    nextReviewAtMillis = nowMillis + nextInterval * dayMillis,
                )
            }

            ReviewGrade.KNOW -> {
                val nextRepetition = current.repetitionCount + 1
                val nextInterval = when (current.repetitionCount) {
                    0 -> 1
                    1 -> 3
                    else -> max(1, (current.intervalDays * current.easeFactor).roundToInt())
                }
                val nextStatus = if (nextRepetition >= 6) {
                    StudyStatus.MASTERED
                } else {
                    StudyStatus.REVIEWING
                }
                current.copy(
                    status = nextStatus,
                    repetitionCount = nextRepetition,
                    easeFactor = current.easeFactor + 0.1,
                    intervalDays = nextInterval,
                    nextReviewAtMillis = nowMillis + nextInterval * dayMillis,
                )
            }
        }
    }

    fun initialReviewStage(): Int = 1

    fun nextReviewTimeForStage(
        stage: Int,
        nowMillis: Long,
    ): Long {
        val normalizedStage = stage.coerceIn(0, intervalDaysByStage.lastIndex)
        val intervalDays = intervalDaysByStage[normalizedStage]
        return nowMillis + intervalDays * dayMillis
    }

    fun scheduleLearnedWord(
        current: LearnedWordRecord,
        outcome: ReviewOutcome,
        nowMillis: Long,
    ): LearnedWordRecord {
        val nextStage = when (outcome) {
            ReviewOutcome.PERFECT -> (current.reviewStage + 1).coerceAtMost(intervalDaysByStage.lastIndex)
            ReviewOutcome.PARTIAL -> (current.reviewStage - 1).coerceAtLeast(1)
            ReviewOutcome.FAIL -> 0
        }
        return current.copy(
            reviewStage = nextStage,
            nextReviewAtMillis = nextReviewTimeForStage(nextStage, nowMillis),
        )
    }
}
