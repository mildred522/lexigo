package com.aiproduct.vocab.ui.study

import com.aiproduct.vocab.domain.model.ExampleSentence
import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.parseExampleSentences
import com.aiproduct.vocab.domain.model.resolveDisplayMeaning

data class StudyWordItem(
    val id: Long,
    val language: String,
    val lemma: String,
    val surface: String,
    val readingOrIpa: String,
    val pos: String,
    val meaningZh: String,
    val meaningSourceText: String,
    val examples: List<ExampleSentence>,
    val sourceName: String,
    val sourceEntryId: String,
) {
    companion object {
        fun from(detail: WordDetail): StudyWordItem = StudyWordItem(
            id = detail.id,
            language = detail.language,
            lemma = detail.lemma,
            surface = detail.surface,
            readingOrIpa = detail.readingOrIpa,
            pos = detail.pos,
            meaningZh = resolveDisplayMeaning(
                meaningZh = detail.meaningZh,
                meaningSourceText = detail.meaningSourceText,
            ),
            meaningSourceText = detail.meaningSourceText,
            examples = parseExampleSentences(detail.exampleSentencesJson).take(2),
            sourceName = detail.sourceName,
            sourceEntryId = detail.sourceEntryId,
        )
    }
}
