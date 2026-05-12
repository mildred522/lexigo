package com.aiproduct.vocab.domain.model

import org.json.JSONArray

data class ExampleSentence(
    val sentenceForeign: String,
    val sentenceZh: String,
)

fun parseExampleSentences(json: String): List<ExampleSentence> {
    if (json.isBlank()) {
        return emptyList()
    }
    val array = JSONArray(json)
    return buildList {
        for (index in 0 until array.length()) {
            val item = array.optJSONObject(index) ?: continue
            add(
                ExampleSentence(
                    sentenceForeign = item.optString("sentence_foreign"),
                    sentenceZh = item.optString("sentence_zh"),
                ),
            )
        }
    }
}
