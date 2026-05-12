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
                prompt = item.word.lemma,
                options = buildOptions(item.word.meaningZh, distractorPool),
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

    private fun buildOptions(
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

    private fun promptKey(word: StudyWordItem): String = word.lemma.trim().lowercase()
}
