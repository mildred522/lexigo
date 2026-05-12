package com.aiproduct.vocab.ui.learning

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.aiproduct.vocab.domain.learning.ChoiceQuestion
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningSession
import com.aiproduct.vocab.domain.learning.LearningStage
import com.aiproduct.vocab.domain.learning.LearningWordProgress
import com.aiproduct.vocab.domain.learning.MeaningOption
import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.ui.AppStats
import com.aiproduct.vocab.ui.LearningUiState
import com.aiproduct.vocab.ui.study.StudyWordItem
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LearningScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun choiceStageRendersMinimalOptionRows() {
        val word = studyWord(id = 1L, lemma = "ねこ", reading = "ねこ", meaningZh = "猫")
        val session = LearningSession(
            language = LearningLanguage.JAPANESE,
            stage = LearningStage.CHOICE,
            words = listOf(LearningWordProgress(word)),
            choiceQueue = listOf(word.id),
            choiceQuestions = mapOf(
                word.id to ChoiceQuestion(
                    wordId = word.id,
                    prompt = word.lemma,
                    options = listOf(
                        MeaningOption(label = "A", meaningZh = "猫", isCorrect = true),
                        MeaningOption(label = "B", meaningZh = "犬", isCorrect = false),
                        MeaningOption(label = "C", meaningZh = "鳥", isCorrect = false),
                        MeaningOption(label = "D", meaningZh = "本", isCorrect = false),
                    ),
                ),
            ),
            spellingOrder = listOf(word.id),
        )

        rule.setContent {
            LearningScreen(
                uiState = LearningUiState(session = session),
                stats = AppStats(),
                showDailyCover = false,
                onSelectLanguage = {},
                onChooseMeaning = {},
                onSubmitSpelling = {},
                onRequestHint = {},
                onSkipCurrentWord = {},
                onContinue = {},
                onRestart = {},
                onSpeak = {},
            )
        }

        rule.onNodeWithTag("study_word_prompt").fetchSemanticsNode()
        rule.onNodeWithTag("meaning_option_A").fetchSemanticsNode()
        rule.onNodeWithTag("meaning_option_B").fetchSemanticsNode()
        rule.onNodeWithTag("meaning_option_C").fetchSemanticsNode()
        rule.onNodeWithTag("meaning_option_D").fetchSemanticsNode()
        rule.onNodeWithText("ねこ").fetchSemanticsNode()
        rule.onNodeWithText("neko").fetchSemanticsNode()
        rule.onNodeWithText("猫").fetchSemanticsNode()
    }
}

private fun studyWord(
    id: Long,
    lemma: String,
    reading: String,
    meaningZh: String,
): StudyWordItem = StudyWordItem.from(
    WordDetail(
        id = id,
        language = "ja",
        lemma = lemma,
        surface = lemma,
        readingOrIpa = reading,
        pos = "noun",
        meaningZh = meaningZh,
        meaningSourceText = meaningZh,
        exampleSentencesJson = "[]",
        sourceName = "test",
        sourceEntryId = "ja-$lemma",
    ),
)
