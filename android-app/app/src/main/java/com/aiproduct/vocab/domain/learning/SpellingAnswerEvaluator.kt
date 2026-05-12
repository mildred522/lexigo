package com.aiproduct.vocab.domain.learning

import com.aiproduct.vocab.ui.UserPreferences
import com.aiproduct.vocab.ui.study.StudyWordItem
import java.text.Normalizer

object SpellingAnswerEvaluator {
    fun isCorrect(
        word: StudyWordItem,
        answer: String,
        preferences: UserPreferences,
    ): Boolean {
        val actual = normalize(answer, word.language, preferences)
        return expectedAnswers(word, preferences).any { expected ->
            expected.isNotBlank() && expected == actual
        }
    }

    private fun expectedAnswers(
        word: StudyWordItem,
        preferences: UserPreferences,
    ): Set<String> {
        val baseAnswers = listOf(word.lemma, word.surface, word.readingOrIpa)
            .map { normalize(it, word.language, preferences) }
            .filter(String::isNotBlank)
        if (!word.language.equals("ja", ignoreCase = true) && !word.language.equals("jpn", ignoreCase = true)) {
            return baseAnswers.toSet()
        }

        val romajiAnswers = listOf(word.lemma, word.surface, word.readingOrIpa)
            .mapNotNull(::kanaToRomajiOrNull)
            .map { normalize(it, word.language, preferences) }
        return (baseAnswers + romajiAnswers).toSet()
    }

    private fun normalize(
        value: String,
        language: String,
        preferences: UserPreferences,
    ): String {
        var normalized = Normalizer.normalize(value.trim(), Normalizer.Form.NFKC)
            .replace(WHITESPACE_REGEX, "")
        if (language.equals("fr", ignoreCase = true) && preferences.frenchAccentInsensitive) {
            normalized = Normalizer.normalize(normalized, Normalizer.Form.NFD)
                .replace(DIACRITIC_REGEX, "")
        }
        return normalized.lowercase()
    }

    private fun kanaToRomajiOrNull(value: String): String? {
        val kana = Normalizer.normalize(value.trim(), Normalizer.Form.NFKC)
            .replace(WHITESPACE_REGEX, "")
            .map(::katakanaToHiragana)
            .joinToString("")
        if (kana.isBlank() || kana.any { it !in 'ぁ'..'ん' && it != 'ー' }) {
            return null
        }

        val result = StringBuilder()
        var index = 0
        var doubleNextConsonant = false
        while (index < kana.length) {
            val current = kana[index]
            if (current == 'っ') {
                doubleNextConsonant = true
                index += 1
                continue
            }
            val pair = kana.substring(index, (index + 2).coerceAtMost(kana.length))
            val mapped = KANA_DIGRAPHS[pair]?.also { index += 2 }
                ?: KANA_MONOGRAPHS[current.toString()]?.also { index += 1 }
                ?: if (current == 'ー') {
                    index += 1
                    result.lastVowel()?.toString().orEmpty()
                } else {
                    return null
                }
            if (doubleNextConsonant && mapped.isNotBlank()) {
                mapped.firstConsonantOrNull()?.let(result::append)
                doubleNextConsonant = false
            }
            result.append(mapped)
        }
        return result.toString()
    }

    private fun katakanaToHiragana(char: Char): Char = if (char in 'ァ'..'ン') {
        char - ('ァ' - 'ぁ')
    } else {
        char
    }

    private fun String.firstConsonantOrNull(): Char? {
        val first = firstOrNull() ?: return null
        return first.takeUnless { it in listOf('a', 'i', 'u', 'e', 'o') }
    }

    private fun StringBuilder.lastVowel(): Char? = asSequence()
        .lastOrNull { it in listOf('a', 'i', 'u', 'e', 'o') }
}

private val WHITESPACE_REGEX = Regex("\\s+")
private val DIACRITIC_REGEX = Regex("\\p{Mn}+")

private val KANA_DIGRAPHS = mapOf(
    "きゃ" to "kya", "きゅ" to "kyu", "きょ" to "kyo",
    "しゃ" to "sha", "しゅ" to "shu", "しょ" to "sho",
    "ちゃ" to "cha", "ちゅ" to "chu", "ちょ" to "cho",
    "にゃ" to "nya", "にゅ" to "nyu", "にょ" to "nyo",
    "ひゃ" to "hya", "ひゅ" to "hyu", "ひょ" to "hyo",
    "みゃ" to "mya", "みゅ" to "myu", "みょ" to "myo",
    "りゃ" to "rya", "りゅ" to "ryu", "りょ" to "ryo",
    "ぎゃ" to "gya", "ぎゅ" to "gyu", "ぎょ" to "gyo",
    "じゃ" to "ja", "じゅ" to "ju", "じょ" to "jo",
    "びゃ" to "bya", "びゅ" to "byu", "びょ" to "byo",
    "ぴゃ" to "pya", "ぴゅ" to "pyu", "ぴょ" to "pyo",
)

private val KANA_MONOGRAPHS = mapOf(
    "あ" to "a", "い" to "i", "う" to "u", "え" to "e", "お" to "o",
    "か" to "ka", "き" to "ki", "く" to "ku", "け" to "ke", "こ" to "ko",
    "さ" to "sa", "し" to "shi", "す" to "su", "せ" to "se", "そ" to "so",
    "た" to "ta", "ち" to "chi", "つ" to "tsu", "て" to "te", "と" to "to",
    "な" to "na", "に" to "ni", "ぬ" to "nu", "ね" to "ne", "の" to "no",
    "は" to "ha", "ひ" to "hi", "ふ" to "fu", "へ" to "he", "ほ" to "ho",
    "ま" to "ma", "み" to "mi", "む" to "mu", "め" to "me", "も" to "mo",
    "や" to "ya", "ゆ" to "yu", "よ" to "yo",
    "ら" to "ra", "り" to "ri", "る" to "ru", "れ" to "re", "ろ" to "ro",
    "わ" to "wa", "を" to "wo", "ん" to "n",
    "が" to "ga", "ぎ" to "gi", "ぐ" to "gu", "げ" to "ge", "ご" to "go",
    "ざ" to "za", "じ" to "ji", "ず" to "zu", "ぜ" to "ze", "ぞ" to "zo",
    "だ" to "da", "ぢ" to "ji", "づ" to "zu", "で" to "de", "ど" to "do",
    "ば" to "ba", "び" to "bi", "ぶ" to "bu", "べ" to "be", "ぼ" to "bo",
    "ぱ" to "pa", "ぴ" to "pi", "ぷ" to "pu", "ぺ" to "pe", "ぽ" to "po",
)
