package com.aiproduct.vocab.ui.study

object JapaneseGrammarChips {
    private const val MAX_VISIBLE_CHIPS = 4

    private val orderedRules = listOf(
        "noun" to "名词",
        "Ichidan verb" to "一段动词",
        "Godan verb" to "五段动词",
        "suru verb" to "する动词",
        "intransitive verb" to "自动词",
        "transitive verb" to "他动词",
        "adjective (keiyoushi)" to "い形容词",
        "adjectival nouns or quasi-adjectives" to "な形容词",
        "adverb" to "副词",
        "expressions" to "表达",
        "pronoun" to "代词",
        "prefix" to "接头词",
        "suffix" to "接尾词",
        "interjection" to "感叹词",
    )

    fun resolve(
        language: String,
        pos: String,
    ): List<String> {
        val cleaned = pos.trim()
        if (cleaned.isBlank()) return emptyList()

        if (!language.equals("ja", ignoreCase = true) && !language.equals("jpn", ignoreCase = true)) {
            return listOf(cleaned)
        }

        val normalizedPos = cleaned.lowercase()
        return orderedRules
            .filter { (needle, _) -> normalizedPos.contains(needle.lowercase()) }
            .map { (_, label) -> label }
            .distinct()
            .take(MAX_VISIBLE_CHIPS)
    }
}
