package com.aiproduct.vocab.ui.learning

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.aiproduct.vocab.R
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningStage
import com.aiproduct.vocab.domain.learning.MeaningOption
import com.aiproduct.vocab.ui.AppStats
import com.aiproduct.vocab.ui.LearningUiState
import com.aiproduct.vocab.ui.study.StudyWordCard
import com.aiproduct.vocab.ui.study.StudyWordItem
import com.aiproduct.vocab.ui.study.ReadingLines

internal val StudyPaper = Color(0xFFF7F2EA)
internal val StudyInk = Color(0xFF25231F)
internal val StudyMuted = Color(0xFF777067)
internal val StudyLine = Color(0x1F25231F)
internal val StudySage = Color(0xFF6F8B75)
internal val StudySageSoft = Color(0x1A6F8B75)

@OptIn(ExperimentalLayoutApi::class)
@Suppress("UNUSED_PARAMETER")
@Composable
fun LearningScreen(
    uiState: LearningUiState,
    stats: AppStats,
    showDailyCover: Boolean,
    onSelectLanguage: (LearningLanguage) -> Unit,
    onChooseMeaning: (String) -> Unit,
    onSubmitSpelling: (String) -> Unit,
    onRequestHint: () -> Unit,
    onSkipCurrentWord: () -> Unit,
    onContinue: () -> Unit,
    onRestart: () -> Unit,
    onSpeak: (StudyWordItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    val session = uiState.session

    StudyFlowLayout(
        modifier = modifier,
        header = {
            StudyFlowHeader(
                title = stringResource(id = R.string.learning_title),
                showSkip = session != null && session.feedback == null && session.stage != LearningStage.SUMMARY,
                onSkipCurrentWord = onSkipCurrentWord,
            )
        },
        body = {
            if (uiState.isLoading) {
                LoadingBlock(text = "正在准备词库...")
                return@StudyFlowLayout
            }

            if (session == null) {
                Text(
                    text = uiState.message ?: stringResource(id = R.string.learning_pick_language),
                    style = MaterialTheme.typography.bodyLarge,
                    color = StudyMuted,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth(),
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
                        progressText = studyProgressText(
                            current = session.spellingIndex + 1,
                            total = session.spellingOrder.size,
                        ),
                        showMeaning = true,
                        promptOverride = currentWord.meaningZh,
                        onSpeak = { onSpeak(currentWord) },
                    )
                }

                LearningStage.SUMMARY -> {
                    Text(
                        text = stringResource(id = R.string.learning_summary_title),
                        style = MaterialTheme.typography.titleLarge,
                        color = StudyInk,
                    )
                    Text(
                        text = stringResource(id = R.string.learning_summary_body, session.words.size),
                        style = MaterialTheme.typography.bodyLarge,
                        color = StudyMuted,
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
                FlowRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    QuietStudyButton(
                        text = stringResource(id = R.string.language_japanese),
                        onClick = { onSelectLanguage(LearningLanguage.JAPANESE) },
                        emphasized = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    QuietStudyButton(
                        text = stringResource(id = R.string.language_french),
                        onClick = { onSelectLanguage(LearningLanguage.FRENCH) },
                        modifier = Modifier.fillMaxWidth(),
                    )
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
                            R.string.learning_finish_feedback
                        } else {
                            R.string.learning_continue
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
                    val question = session.currentChoiceQuestion ?: return@StudyFlowLayout
                    MinimalMeaningOptions(
                        options = question.options,
                        onChooseMeaning = onChooseMeaning,
                    )
                    Text(
                        text = stringResource(id = R.string.action_speak),
                        modifier = Modifier
                            .align(Alignment.CenterHorizontally)
                            .clip(RoundedCornerShape(999.dp))
                            .clickable { session.currentChoiceWord?.word?.let(onSpeak) }
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
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
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
                        text = stringResource(id = R.string.learning_restart),
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

@Composable
internal fun StudyFlowHeader(
    title: String,
    showSkip: Boolean,
    onSkipCurrentWord: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = StudyMuted,
        )
        if (showSkip) {
            TextButton(onClick = onSkipCurrentWord) {
                Text(text = "跳过", color = StudyMuted)
            }
        }
    }
}

@Composable
internal fun LoadingBlock(text: String) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        CircularProgressIndicator(color = StudySage)
        Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            color = StudyMuted,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
internal fun StudyFlowLayout(
    modifier: Modifier = Modifier,
    header: @Composable () -> Unit,
    body: @Composable () -> Unit,
    actions: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(StudyPaper)
            .imePadding()
            .navigationBarsPadding()
            .padding(horizontal = 24.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        header()
        Column(
            modifier = Modifier
                .weight(1f, fill = true)
                .fillMaxWidth()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(18.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            body()
        }
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            content = actions,
        )
    }
}

@Composable
internal fun StudyWordPrompt(
    word: StudyWordItem,
    progressText: String,
    showMeaning: Boolean,
    onSpeak: () -> Unit,
    modifier: Modifier = Modifier,
    promptOverride: String? = null,
) {
    val prompt = promptOverride ?: word.lemma
    Column(
        modifier = modifier
            .fillMaxWidth()
            .testTag("study_word_prompt")
            .padding(top = 30.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        StudyProgress(text = progressText)
        Spacer(modifier = Modifier.height(18.dp))
        Text(
            text = prompt,
            style = MaterialTheme.typography.displayMedium.copy(
                fontSize = if (prompt.length > 12) 34.sp else 48.sp,
                fontWeight = FontWeight.Light,
                letterSpacing = 0.sp,
            ),
            color = StudyInk,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        Row(
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (word.readingOrIpa.isNotBlank()) {
                ReadingLines(
                    word = word,
                    color = StudyMuted,
                    textAlign = TextAlign.Center,
                )
                Spacer(modifier = Modifier.width(10.dp))
            }
            Surface(
                modifier = Modifier
                    .size(34.dp)
                    .semantics { contentDescription = "Speak word" },
                shape = CircleShape,
                color = Color.Transparent,
                border = BorderStroke(1.dp, StudyLine),
                onClick = onSpeak,
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(text = "♪", color = StudyMuted, style = MaterialTheme.typography.labelMedium)
                }
            }
        }
        if (showMeaning) {
            RevealedMeaning(word = word)
        }
    }
}

@Composable
private fun StudyProgress(text: String) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelMedium,
            color = StudyMuted,
        )
        Box(
            modifier = Modifier
                .width(72.dp)
                .height(1.dp)
                .background(StudyLine),
        )
    }
}

@Composable
private fun RevealedMeaning(word: StudyWordItem) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 8.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        if (word.pos.isNotBlank()) {
            Text(
                text = word.pos,
                style = MaterialTheme.typography.labelMedium,
                color = StudySage,
            )
        }
        Text(
            text = word.meaningZh.ifBlank { word.meaningSourceText },
            style = MaterialTheme.typography.titleLarge.copy(fontWeight = FontWeight.Normal),
            color = StudyInk,
            textAlign = TextAlign.Center,
            modifier = Modifier.fillMaxWidth(),
        )
        word.examples.firstOrNull()?.let { example ->
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(StudyLine),
                )
                Text(
                    text = example.sentenceForeign,
                    style = MaterialTheme.typography.bodyMedium,
                    color = StudyInk,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 10.dp),
                )
                if (example.sentenceZh.isNotBlank()) {
                    Text(
                        text = example.sentenceZh,
                        style = MaterialTheme.typography.bodySmall,
                        color = StudyMuted,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        }
    }
}

@Composable
internal fun MinimalMeaningOptions(
    options: List<MeaningOption>,
    onChooseMeaning: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(0.dp),
    ) {
        options.forEach { option ->
            MeaningOptionRow(
                option = option,
                onClick = { onChooseMeaning(option.meaningZh) },
            )
        }
    }
}

@Composable
private fun MeaningOptionRow(
    option: MeaningOption,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .testTag("meaning_option_${option.label}")
            .clip(RoundedCornerShape(2.dp))
            .clickable(onClick = onClick)
            .padding(vertical = 17.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            modifier = Modifier
                .width(3.dp)
                .height(28.dp)
                .background(StudySageSoft),
        )
        Text(
            text = option.label,
            modifier = Modifier
                .width(44.dp)
                .padding(start = 16.dp),
            style = MaterialTheme.typography.labelLarge,
            color = StudySage,
        )
        Text(
            text = option.meaningZh,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.bodyLarge,
            color = StudyInk,
        )
    }
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(1.dp)
            .background(StudyLine),
    )
}

@Composable
internal fun QuietStudyButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    emphasized: Boolean = false,
) {
    if (emphasized) {
        Button(
            onClick = onClick,
            modifier = modifier,
            shape = RoundedCornerShape(4.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = StudySage,
                contentColor = StudyPaper,
            ),
        ) {
            Text(text = text)
        }
    } else {
        OutlinedButton(
            onClick = onClick,
            modifier = modifier,
            shape = RoundedCornerShape(4.dp),
            border = BorderStroke(1.dp, StudyLine),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = StudyInk),
        ) {
            Text(text = text)
        }
    }
}

internal fun studyProgressText(current: Int, total: Int): String =
    "${current.coerceAtLeast(1).toString().padStart(2, '0')} / ${total.coerceAtLeast(1).toString().padStart(2, '0')}"
