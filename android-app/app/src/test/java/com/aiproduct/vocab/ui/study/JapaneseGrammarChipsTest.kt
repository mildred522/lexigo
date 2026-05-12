package com.aiproduct.vocab.ui.study

import org.junit.Assert.assertEquals
import org.junit.Test

class JapaneseGrammarChipsTest {
    @Test
    fun resolve_returnsOrderedJapaneseVerbChips() {
        val chips = JapaneseGrammarChips.resolve(
            language = "ja",
            pos = "Godan verb with ru ending, transitive verb",
        )

        assertEquals(listOf("五段动词", "他动词"), chips)
    }

    @Test
    fun resolve_returnsJapaneseAdjectiveChips() {
        val chips = JapaneseGrammarChips.resolve(
            language = "jpn",
            pos = "adjective (keiyoushi), adverb",
        )

        assertEquals(listOf("い形容词", "副词"), chips)
    }

    @Test
    fun resolve_deduplicatesAndCapsChips() {
        val chips = JapaneseGrammarChips.resolve(
            language = "ja",
            pos = "noun, noun, prefix, suffix, expressions, pronoun, interjection",
        )

        assertEquals(listOf("名词", "表达", "代词", "接头词"), chips)
    }

    @Test
    fun resolve_returnsRawPartOfSpeechForNonJapaneseWords() {
        val chips = JapaneseGrammarChips.resolve(
            language = "fr",
            pos = "noun",
        )

        assertEquals(listOf("noun"), chips)
    }
}
