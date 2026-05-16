package com.aiproduct.vocab.domain.learning

import com.aiproduct.vocab.ui.study.StudyWordItem

enum class LearningLanguage(val code: String) {
    JAPANESE("JA"),
    FRENCH("FR"),
}

enum class LearningStage {
    LANGUAGE_PICKER,
    CHOICE,
    SPELLING,
    SUMMARY,
}

data class MeaningOption(
    val label: String,
    val meaningZh: String,
    val isCorrect: Boolean,
    val value: String = meaningZh,
    val secondaryText: String? = null,
)

data class ChoiceQuestion(
    val wordId: Long,
    val prompt: String,
    val options: List<MeaningOption>,
)

data class LearningWordProgress(
    val word: StudyWordItem,
    val choiceCorrectCount: Int = 0,
    val choiceWrongCount: Int = 0,
    val spellingCorrectCount: Int = 0,
    val spellingWrongCount: Int = 0,
    val hintUsedCount: Int = 0,
)

data class SessionFeedback(
    val wordId: Long,
    val stage: LearningStage,
    val isCorrect: Boolean,
    val showNextSummary: Boolean = false,
)

data class LearningSession(
    val language: LearningLanguage,
    val stage: LearningStage,
    val words: List<LearningWordProgress>,
    val choiceQueue: List<Long>,
    val choiceQuestions: Map<Long, ChoiceQuestion>,
    val spellingOrder: List<Long>,
    val spellingIndex: Int = 0,
    val currentHint: String? = null,
    val feedback: SessionFeedback? = null,
    val lastChoiceCorrect: Boolean? = null,
    val lastSpellingCorrect: Boolean? = null,
) {
    val currentChoiceWord: LearningWordProgress?
        get() = words.firstOrNull {
            it.word.id == (feedback?.takeIf { feedback.stage == LearningStage.CHOICE }?.wordId ?: choiceQueue.firstOrNull())
        }

    val currentChoiceQuestion: ChoiceQuestion?
        get() = currentChoiceWord?.word?.id?.let(choiceQuestions::get)

    val currentSpellingWord: LearningWordProgress?
        get() = words.firstOrNull {
            it.word.id == (feedback?.takeIf { feedback.stage == LearningStage.SPELLING }?.wordId ?: spellingOrder.getOrNull(spellingIndex))
        }
}

enum class ReviewOutcome {
    PERFECT,
    PARTIAL,
    FAIL,
}

enum class ChoiceOptionDisplayMode {
    MEANING,
    KANA_ONLY,
    KANJI_KANA,
    KANJI_ONLY,
}
