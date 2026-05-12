package com.aiproduct.vocab.domain.model

data class StudyRecord(
    val wordId: Long,
    val status: StudyStatus,
    val repetitionCount: Int,
    val easeFactor: Double,
    val intervalDays: Int,
    val nextReviewAtMillis: Long,
    val addedAtMillis: Long,
)
