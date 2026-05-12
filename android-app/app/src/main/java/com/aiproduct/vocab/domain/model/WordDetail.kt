package com.aiproduct.vocab.domain.model

data class WordDetail(
    val id: Long,
    val language: String,
    val lemma: String,
    val surface: String,
    val readingOrIpa: String,
    val pos: String,
    val meaningZh: String,
    val meaningSourceText: String,
    val exampleSentencesJson: String,
    val sourceName: String,
    val sourceEntryId: String,
)
