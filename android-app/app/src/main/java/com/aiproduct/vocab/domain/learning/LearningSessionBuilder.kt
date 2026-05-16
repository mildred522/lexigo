package com.aiproduct.vocab.domain.learning

import com.aiproduct.vocab.ui.study.StudyWordItem
import kotlin.random.Random

class LearningSessionBuilder(
    private val random: Random = Random.Default,
    private val distractorSelector: MeaningDistractorSelector = MeaningDistractorSelector(random),
) {
    fun build(
        language: LearningLanguage,
        words: List<StudyWordItem>,
        distractorPool: List<String>,
        wordDistractorPool: List<StudyWordItem> = emptyList(),
        choiceOptionDisplayMode: ChoiceOptionDisplayMode = ChoiceOptionDisplayMode.MEANING,
        deduplicatePrompts: Boolean = false,
    ): LearningSession {
        val sessionWords = words
            .filter { it.meaningZh.isNotBlank() }
            .let { candidates ->
                if (!deduplicatePrompts) {
                    candidates
                } else {
                    candidates.distinctBy(::promptKey)
                }
            }
        val progress = sessionWords.map(::LearningWordProgress)
        val questions = progress.associate { item ->
            item.word.id to ChoiceQuestion(
                wordId = item.word.id,
                prompt = if (choiceOptionDisplayMode == ChoiceOptionDisplayMode.MEANING) {
                    item.word.lemma
                } else {
                    item.word.meaningZh
                },
                options = if (choiceOptionDisplayMode == ChoiceOptionDisplayMode.MEANING) {
                    buildMeaningOptions(item.word.meaningZh, distractorPool)
                } else {
                    buildWordFormOptions(
                        correctWord = item.word,
                        distractorWords = (wordDistractorPool + sessionWords).filterNot { it.id == item.word.id },
                        displayMode = choiceOptionDisplayMode,
                    )
                },
            )
        }
        return LearningSession(
            language = language,
            stage = if (progress.isEmpty()) LearningStage.SUMMARY else LearningStage.CHOICE,
            words = progress,
            choiceQueue = progress.map { it.word.id },
            choiceQuestions = questions,
            spellingOrder = progress.map { it.word.id },
        )
    }

    private fun buildMeaningOptions(
        correctMeaning: String,
        distractorPool: List<String>,
    ): List<MeaningOption> {
        val labels = listOf("A", "B", "C", "D")
        val distractors = distractorSelector.select(correctMeaning, distractorPool).toMutableList()
        val allMeanings = (distractors + correctMeaning).shuffled(random)
        return allMeanings.mapIndexed { index, meaning ->
            MeaningOption(
                label = labels[index],
                meaningZh = meaning,
                isCorrect = meaning == correctMeaning,
            )
        }
    }

    private fun buildWordFormOptions(
        correctWord: StudyWordItem,
        distractorWords: List<StudyWordItem>,
        displayMode: ChoiceOptionDisplayMode,
    ): List<MeaningOption> {
        val labels = listOf("A", "B", "C", "D")
        val correct = correctWord.toWordOption(displayMode, isCorrect = true)
        val distractors = distractorWords
            .asSequence()
            .sortedWith(
                compareBy<StudyWordItem>(
                    { phoneticDistance(correctWord.readingKey(), it.readingKey()) },
                    { it.lemma.length },
                ),
            )
            .map { it.toWordOption(displayMode, isCorrect = false) }
            .filter { it.value != correct.value && it.meaningZh != correct.meaningZh }
            .distinctBy { it.value }
            .take(3)
            .toList()
        return (distractors + correct)
            .shuffled(random)
            .mapIndexed { index, option ->
                option.copy(label = labels[index])
            }
    }

    private fun StudyWordItem.toWordOption(
        displayMode: ChoiceOptionDisplayMode,
        isCorrect: Boolean,
    ): MeaningOption {
        val kana = readingOrIpa.trim().ifBlank { lemma.trim() }
        val kanji = surface.trim().ifBlank { lemma.trim() }
        val hasDistinctKana = kana.isNotBlank() && kana != kanji
        val primary = when (displayMode) {
            ChoiceOptionDisplayMode.MEANING -> meaningZh
            ChoiceOptionDisplayMode.KANA_ONLY -> kana
            ChoiceOptionDisplayMode.KANJI_KANA,
            ChoiceOptionDisplayMode.KANJI_ONLY -> kanji
        }.ifBlank { lemma.trim() }
        val secondary = when (displayMode) {
            ChoiceOptionDisplayMode.KANJI_KANA -> kana.takeIf { hasDistinctKana }
            else -> null
        }
        return MeaningOption(
            label = "",
            meaningZh = primary,
            isCorrect = isCorrect,
            value = id.toString(),
            secondaryText = secondary,
        )
    }

    private fun promptKey(word: StudyWordItem): String = word.lemma.trim().lowercase()

    private fun StudyWordItem.readingKey(): String = readingOrIpa
        .ifBlank { lemma }
        .trim()
        .lowercase()

    private fun phoneticDistance(left: String, right: String): Int {
        if (left == right) return 0
        if (left.isEmpty()) return right.length
        if (right.isEmpty()) return left.length
        val previous = IntArray(right.length + 1) { it }
        val current = IntArray(right.length + 1)
        for (leftIndex in left.indices) {
            current[0] = leftIndex + 1
            for (rightIndex in right.indices) {
                val substitutionCost = if (left[leftIndex] == right[rightIndex]) 0 else 1
                current[rightIndex + 1] = minOf(
                    current[rightIndex] + 1,
                    previous[rightIndex + 1] + 1,
                    previous[rightIndex] + substitutionCost,
                )
            }
            for (index in previous.indices) {
                previous[index] = current[index]
            }
        }
        return previous[right.length]
    }
}
