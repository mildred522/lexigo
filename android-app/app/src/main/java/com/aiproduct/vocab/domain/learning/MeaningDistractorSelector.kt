package com.aiproduct.vocab.domain.learning

import kotlin.math.abs
import kotlin.random.Random

class MeaningDistractorSelector(
    private val random: Random = Random.Default,
) {
    fun select(
        correctMeaning: String,
        distractorPool: List<String>,
        desiredCount: Int = 3,
    ): List<String> {
        val normalizedCorrect = normalizeMeaning(correctMeaning)
        val candidates = distractorPool
            .asSequence()
            .map(::normalizeMeaning)
            .filter { it.isNotBlank() }
            .distinct()
            .filterNot { candidate ->
                candidate == normalizedCorrect ||
                    candidate.contains(normalizedCorrect) ||
                    normalizedCorrect.contains(candidate)
            }
            .sortedWith(compareBy<String> { abs(it.length - normalizedCorrect.length) }.thenBy { it })
            .toList()

        val selected = candidates
            .take(12)
            .shuffled(random)
            .sortedWith(compareBy<String> { abs(it.length - normalizedCorrect.length) }.thenBy { it })
            .take(desiredCount)
            .toMutableList()

        while (selected.size < desiredCount) {
            selected += "干扰项${selected.size + 1}"
        }
        return selected
    }

    private fun normalizeMeaning(raw: String): String = raw
        .trim()
        .split(MEANING_SPLIT_REGEX)
        .firstOrNull()
        .orEmpty()
        .trim()
}

private val MEANING_SPLIT_REGEX = Regex("[,，;；/、（）()]")
