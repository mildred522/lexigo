package com.aiproduct.vocab.domain.learning

import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.ui.study.StudyWordItem
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class LearningSessionReducerTest {
    private val reducer = LearningSessionReducer()

    @Test
    fun submitChoice_keepsAnsweredWordInFeedbackBeforeShowingNextQuestion() {
        val first = learningWord(id = 1L, lemma = "ねこ", meaningZh = "猫")
        val second = learningWord(id = 2L, lemma = "いぬ", meaningZh = "狗")
        val session = LearningSession(
            language = LearningLanguage.JAPANESE,
            stage = LearningStage.CHOICE,
            words = listOf(LearningWordProgress(first), LearningWordProgress(second)),
            choiceQueue = listOf(first.id, second.id),
            choiceQuestions = mapOf(
                first.id to choiceQuestion(first, "猫"),
                second.id to choiceQuestion(second, "狗"),
            ),
            spellingOrder = listOf(first.id, second.id),
        )

        val updated = reducer.submitChoice(session, selectedMeaning = "猫")

        val feedback = requireNotNull(updated.feedback)
        assertEquals(first.id, feedback.wordId)
        assertEquals(LearningStage.CHOICE, feedback.stage)
        assertFalse(feedback.showNextSummary)
        assertEquals(listOf(second.id), updated.choiceQueue)
    }

    @Test
    fun buildSession_avoidsDuplicateAndOverlappingDistractors() {
        val builder = LearningSessionBuilder(random = kotlin.random.Random(0))
        val word = learningWord(id = 10L, lemma = "bonjour", meaningZh = "你好")

        val session = builder.build(
            language = LearningLanguage.FRENCH,
            words = listOf(word),
            distractorPool = listOf("你好", "你好吗", "你好", "再见", "谢谢", "学校"),
        )

        val options = requireNotNull(session.currentChoiceQuestion).options
        assertEquals(4, options.size)
        assertEquals(4, options.map { it.meaningZh }.distinct().size)
        assertTrue(options.none { !it.isCorrect && (it.meaningZh.contains("你好") || "你好".contains(it.meaningZh)) })
    }
    @Test
    fun buildSession_forLearning_skipsDuplicatePrompts() {
        val builder = LearningSessionBuilder(random = kotlin.random.Random(0))
        val first = learningWord(id = 100L, lemma = "same", meaningZh = "first")
        val duplicatePrompt = learningWord(id = 101L, lemma = "same", meaningZh = "second")
        val third = learningWord(id = 102L, lemma = "other", meaningZh = "third")

        val session = builder.build(
            language = LearningLanguage.FRENCH,
            words = listOf(first, duplicatePrompt, third),
            distractorPool = listOf("first", "second", "third", "fourth"),
            deduplicatePrompts = true,
        )

        assertEquals(listOf(100L, 102L), session.words.map { it.word.id })
        assertEquals(listOf(100L, 102L), session.choiceQueue)
    }

    @Test
    fun skipCurrentWord_inChoiceStageRemovesWordWithoutScoringIt() {
        val first = learningWord(id = 201L, lemma = "first", meaningZh = "one")
        val second = learningWord(id = 202L, lemma = "second", meaningZh = "two")
        val session = LearningSession(
            language = LearningLanguage.JAPANESE,
            stage = LearningStage.CHOICE,
            words = listOf(LearningWordProgress(first), LearningWordProgress(second)),
            choiceQueue = listOf(first.id, second.id),
            choiceQuestions = mapOf(
                first.id to choiceQuestion(first, "one"),
                second.id to choiceQuestion(second, "two"),
            ),
            spellingOrder = listOf(first.id, second.id),
        )

        val updated = reducer.skipCurrentWord(session)

        assertEquals(listOf(second.id), updated.choiceQueue)
        assertEquals(LearningStage.CHOICE, updated.stage)
        assertEquals(second.id, updated.currentChoiceWord?.word?.id)
        assertEquals(listOf(second.id), updated.words.map { it.word.id })
        assertEquals(listOf(second.id), updated.spellingOrder)
        assertEquals(0, updated.words.first().choiceCorrectCount)
        assertEquals(0, updated.words.first().choiceWrongCount)
    }

    @Test
    fun skipCurrentWord_inSpellingStageAdvancesWithoutScoringIt() {
        val first = learningWord(id = 301L, lemma = "first", meaningZh = "one")
        val second = learningWord(id = 302L, lemma = "second", meaningZh = "two")
        val session = LearningSession(
            language = LearningLanguage.JAPANESE,
            stage = LearningStage.SPELLING,
            words = listOf(LearningWordProgress(first), LearningWordProgress(second)),
            choiceQueue = emptyList(),
            choiceQuestions = mapOf(
                first.id to choiceQuestion(first, "one"),
                second.id to choiceQuestion(second, "two"),
            ),
            spellingOrder = listOf(first.id, second.id),
        )

        val updated = reducer.skipCurrentWord(session)

        assertEquals(1, updated.spellingIndex)
        assertEquals(LearningStage.SPELLING, updated.stage)
        assertEquals(second.id, updated.currentSpellingWord?.word?.id)
        assertEquals(listOf(second.id), updated.words.map { it.word.id })
        assertEquals(listOf(second.id), updated.spellingOrder)
        assertEquals(0, updated.words.first().spellingCorrectCount)
        assertEquals(0, updated.words.first().spellingWrongCount)
    }
}

private fun learningWord(
    id: Long,
    lemma: String,
    meaningZh: String,
): StudyWordItem = StudyWordItem.from(
    WordDetail(
        id = id,
        language = "ja",
        lemma = lemma,
        surface = lemma,
        readingOrIpa = lemma,
        pos = "noun",
        meaningZh = meaningZh,
        meaningSourceText = meaningZh,
        exampleSentencesJson = "[]",
        sourceName = "test",
        sourceEntryId = "ja-$lemma",
    ),
)

private fun choiceQuestion(
    word: StudyWordItem,
    correctMeaning: String,
): ChoiceQuestion = ChoiceQuestion(
    wordId = word.id,
    prompt = word.lemma,
    options = listOf(
        MeaningOption(label = "A", meaningZh = correctMeaning, isCorrect = true),
        MeaningOption(label = "B", meaningZh = "干扰1", isCorrect = false),
        MeaningOption(label = "C", meaningZh = "干扰2", isCorrect = false),
        MeaningOption(label = "D", meaningZh = "干扰3", isCorrect = false),
    ),
)
