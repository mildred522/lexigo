package com.aiproduct.vocab.domain.learning

import com.aiproduct.vocab.ui.study.StudyWordItem

object SpellingHintResolver {
    fun resolve(word: StudyWordItem): String = when (word.language.uppercase()) {
        "JA" -> word.readingOrIpa.ifBlank { word.lemma.take(1) }
        "FR" -> word.readingOrIpa.ifBlank { word.lemma.take(1) }
        else -> word.lemma.take(1)
    }
}
