package com.aiproduct.vocab.domain.learning

import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.ui.UserPreferences
import com.aiproduct.vocab.ui.study.StudyWordItem
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SpellingAnswerEvaluatorTest {
    @Test
    fun frenchEvaluation_canIgnoreAccentAndCase() {
        val word = studyWord(language = "fr", lemma = "français", meaningZh = "法语")

        assertTrue(
            SpellingAnswerEvaluator.isCorrect(
                word = word,
                answer = "FRANCAIS",
                preferences = UserPreferences(frenchAccentInsensitive = true),
            ),
        )
        assertFalse(
            SpellingAnswerEvaluator.isCorrect(
                word = word,
                answer = "FRANCAIS",
                preferences = UserPreferences(frenchAccentInsensitive = false),
            ),
        )
    }

    @Test
    fun japaneseEvaluation_normalizesFullWidthAndWhitespace() {
        val word = studyWord(language = "ja", lemma = "ねこ", meaningZh = "猫")

        assertTrue(
            SpellingAnswerEvaluator.isCorrect(
                word = word,
                answer = "  ねこ  ",
                preferences = UserPreferences(),
            ),
        )
    }

    @Test
    fun japaneseEvaluation_acceptsReadingKanaAndRomaji() {
        val word = studyWord(
            language = "ja",
            lemma = "猫",
            surface = "猫",
            readingOrIpa = "ねこ",
            meaningZh = "猫",
        )

        assertTrue(
            SpellingAnswerEvaluator.isCorrect(
                word = word,
                answer = "ねこ",
                preferences = UserPreferences(),
            ),
        )
        assertTrue(
            SpellingAnswerEvaluator.isCorrect(
                word = word,
                answer = "neko",
                preferences = UserPreferences(),
            ),
        )
    }

    @Test
    fun japaneseEvaluation_acceptsSmallTsuAndLongVowelRomaji() {
        val word = studyWord(
            language = "ja",
            lemma = "学校",
            surface = "学校",
            readingOrIpa = "がっこう",
            meaningZh = "学校",
        )

        assertTrue(
            SpellingAnswerEvaluator.isCorrect(
                word = word,
                answer = "gakkou",
                preferences = UserPreferences(),
            ),
        )
    }
}

private fun studyWord(
    language: String,
    lemma: String,
    surface: String = lemma,
    readingOrIpa: String = lemma,
    meaningZh: String,
): StudyWordItem = StudyWordItem.from(
    WordDetail(
        id = 1L,
        language = language,
        lemma = lemma,
        surface = surface,
        readingOrIpa = readingOrIpa,
        pos = "noun",
        meaningZh = meaningZh,
        meaningSourceText = meaningZh,
        exampleSentencesJson = "[]",
        sourceName = "test",
        sourceEntryId = "$language-$lemma",
    ),
)
