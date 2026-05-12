package com.aiproduct.vocab.domain.model

data class WordSummary(
    val id: Long,
    val language: String,
    val lemma: String,
    val surface: String,
    val readingOrIpa: String,
    val meaningZh: String,
    val meaningSourceText: String,
)
