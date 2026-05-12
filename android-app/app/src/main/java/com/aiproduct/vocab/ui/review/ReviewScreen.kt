package com.aiproduct.vocab.ui.review

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.R
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningStage
import com.aiproduct.vocab.ui.learning.LoadingBlock
import com.aiproduct.vocab.ui.learning.MinimalMeaningOptions
import com.aiproduct.vocab.ui.learning.QuietStudyButton
import com.aiproduct.vocab.ui.ReviewUiState
import com.aiproduct.vocab.ui.learning.StudyFlowHeader
import com.aiproduct.vocab.ui.learning.StudyFlowLayout
import com.aiproduct.vocab.ui.learning.StudyMuted
import com.aiproduct.vocab.ui.learning.StudyWordPrompt
import com.aiproduct.vocab.ui.learning.studyProgressText
import com.aiproduct.vocab.ui.study.StudyWordCard
import com.aiproduct.vocab.ui.study.StudyWordItem

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ReviewScreen(
    uiState: ReviewUiState,
    onChooseMeaning: (String) -> Unit,
    onSubmitSpelling: (String) -> Unit,
    onRequestHint: () -> Unit,
    onSkipCurrentWord: () -> Unit,
    onContinue: () -> Unit,
    onRestart: () -> Unit,
    onSelectLanguage: (LearningLanguage) -> Unit = {},
    onSpeak: (StudyWordItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    val session = uiState.session

    StudyFlowLayout(
        modifier = modifier,
        header = {
            StudyFlowHeader(
                title = stringResource(id = R.string.review_title),
                showSkip = session != null && session.feedback == null && session.stage != LearningStage.SUMMARY,
                onSkipCurrentWord = onSkipCurrentWord,
            )
        },
        body = {
            if (uiState.isLoading) {
                LoadingBlock(text = "正在准备复习词库...")
                return@StudyFlowLayout
            }

            if (session == null) {
                Text(
                    text = uiState.message ?: stringResource(id = R.string.review_empty),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                return@StudyFlowLayout
            }

            val feedback = session.feedback
            if (feedback != null && uiState.feedbackWord != null) {
                StudyWordCard(
                    word = uiState.feedbackWord,
                    showAnswer = true,
                    answerResult = feedback.isCorrect,
                )
                return@StudyFlowLayout
            }

            when (session.stage) {
                LearningStage.CHOICE -> {
                    val currentWord = session.currentChoiceWord?.word ?: return@StudyFlowLayout
                    StudyWordPrompt(
                        word = currentWord,
                        progressText = studyProgressText(
                            current = session.words.size - session.choiceQueue.size + 1,
                            total = session.words.size,
                        ),
                        showMeaning = false,
                        onSpeak = { onSpeak(currentWord) },
                    )
                }

                LearningStage.SPELLING -> {
                    val currentWord = session.currentSpellingWord?.word ?: return@StudyFlowLayout
                    StudyWordPrompt(
                        word = currentWord,
                        progressText = stringResource(id = R.string.review_queue_count, uiState.pendingCount),
                        showMeaning = true,
                        promptOverride = currentWord.meaningZh,
                        onSpeak = { onSpeak(currentWord) },
                    )
                }

                LearningStage.SUMMARY -> {
                    Text(
                        text = stringResource(id = R.string.review_summary_title),
                        style = MaterialTheme.typography.titleLarge,
                    )
                    Text(
                        text = stringResource(id = R.string.review_summary_body, session.words.size),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }

                LearningStage.LANGUAGE_PICKER -> Unit
            }
        },
        actions = {
            if (uiState.isLoading) {
                return@StudyFlowLayout
            }

            if (session == null) {
                if (uiState.availableLanguages.isEmpty()) {
                    QuietStudyButton(
                        text = stringResource(id = R.string.review_reload),
                        onClick = onRestart,
                        modifier = Modifier.fillMaxWidth(),
                    )
                } else {
                    FlowRow(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        uiState.availableLanguages.forEach { option ->
                            val label = if (option.language == LearningLanguage.JAPANESE) {
                                stringResource(id = R.string.language_japanese)
                            } else {
                                stringResource(id = R.string.language_french)
                            }
                            QuietStudyButton(
                                text = "$label (${option.dueCount})",
                                onClick = { onSelectLanguage(option.language) },
                                emphasized = option.language == LearningLanguage.JAPANESE,
                                modifier = Modifier.fillMaxWidth(),
                            )
                        }
                    }
                }
                return@StudyFlowLayout
            }

            val feedback = session.feedback
            if (feedback != null && uiState.feedbackWord != null) {
                QuietStudyButton(
                    text = stringResource(id = R.string.action_speak),
                    onClick = { onSpeak(uiState.feedbackWord) },
                    modifier = Modifier.fillMaxWidth(),
                )
                QuietStudyButton(
                    text = stringResource(
                        id = if (feedback.showNextSummary) {
                            R.string.review_finish_feedback
                        } else {
                            R.string.review_continue
                        },
                    ),
                    onClick = onContinue,
                    emphasized = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                return@StudyFlowLayout
            }

            when (session.stage) {
                LearningStage.CHOICE -> {
                    val currentWord = session.currentChoiceWord?.word ?: return@StudyFlowLayout
                    val question = session.currentChoiceQuestion ?: return@StudyFlowLayout
                    MinimalMeaningOptions(
                        options = question.options,
                        onChooseMeaning = onChooseMeaning,
                    )
                    Text(
                        text = stringResource(id = R.string.action_speak),
                        modifier = Modifier
                            .align(androidx.compose.ui.Alignment.CenterHorizontally)
                            .clip(RoundedCornerShape(999.dp))
                            .clickable { onSpeak(currentWord) }
                            .padding(horizontal = 18.dp, vertical = 8.dp),
                        style = MaterialTheme.typography.labelLarge,
                        color = StudyMuted,
                    )
                }

                LearningStage.SPELLING -> {
                    val currentWord = session.currentSpellingWord?.word ?: return@StudyFlowLayout
                    var answer by remember(currentWord.id, session.spellingIndex) { mutableStateOf("") }
                    OutlinedTextField(
                        value = answer,
                        onValueChange = { answer = it },
                        modifier = Modifier.fillMaxWidth(),
                        label = { Text(text = stringResource(id = R.string.learning_spelling_input)) },
                        singleLine = true,
                    )
                    session.currentHint?.let { hint ->
                        Text(
                            text = stringResource(id = R.string.learning_hint_value, hint),
                            style = MaterialTheme.typography.bodyMedium,
                            color = StudyMuted,
                        )
                    }
                    androidx.compose.foundation.layout.Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        QuietStudyButton(
                            text = stringResource(id = R.string.learning_hint),
                            onClick = onRequestHint,
                            modifier = Modifier.weight(1f),
                        )
                        QuietStudyButton(
                            text = stringResource(id = R.string.action_speak),
                            onClick = { onSpeak(currentWord) },
                            modifier = Modifier.weight(1f),
                        )
                        QuietStudyButton(
                            text = stringResource(id = R.string.learning_submit),
                            onClick = { onSubmitSpelling(answer) },
                            emphasized = true,
                            modifier = Modifier.weight(1f),
                        )
                    }
                }

                LearningStage.SUMMARY -> {
                    QuietStudyButton(
                        text = stringResource(id = R.string.review_reload),
                        onClick = onRestart,
                        emphasized = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }

                LearningStage.LANGUAGE_PICKER -> Unit
            }
        },
    )
}
