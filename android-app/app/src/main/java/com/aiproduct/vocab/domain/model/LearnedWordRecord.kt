package com.aiproduct.vocab.domain.model

data class LearnedWordRecord(
    val wordId: Long,
    val language: String,
    val choiceCorrectCount: Int,
    val choiceWrongCount: Int,
    val spellingCorrectCount: Int,
    val spellingWrongCount: Int,
    val hintUsedCount: Int,
    val reviewStage: Int,
    val lastLearnedAtMillis: Long,
    val nextReviewAtMillis: Long,
    val addedAtMillis: Long = lastLearnedAtMillis,
)
