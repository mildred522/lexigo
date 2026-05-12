package com.aiproduct.vocab.ui.study

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AssistChip
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun StudyWordCard(
    word: StudyWordItem,
    showAnswer: Boolean,
    answerResult: Boolean? = null,
    modifier: Modifier = Modifier,
) {
    ElevatedCard(modifier = modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 22.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            answerResult?.let { isCorrect ->
                AnswerResultPill(isCorrect = isCorrect)
            }

            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(
                    text = word.lemma,
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                ReadingLines(word = word)
            }

            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                AssistChip(onClick = {}, label = { Text(text = word.language.uppercase()) })
                JapaneseGrammarChips.resolve(word.language, word.pos).forEach { chip ->
                    AssistChip(onClick = {}, label = { Text(text = chip) })
                }
            }

            if (showAnswer) {
                LabeledText(label = "中文释义", value = word.meaningZh)
                if (word.meaningSourceText.isNotBlank()) {
                    LabeledText(label = "原始释义", value = word.meaningSourceText)
                }
                if (word.examples.isNotEmpty()) {
                    Text(text = "例句", style = MaterialTheme.typography.titleMedium)
                    word.examples.forEach { example ->
                        ExampleSentenceBlock(
                            sentenceForeign = example.sentenceForeign,
                            sentenceZh = example.sentenceZh,
                            highlight = word.surface.ifBlank { word.lemma },
                        )
                    }
                }
                Text(
                    text = "来源：${word.sourceName} · ${word.sourceEntryId}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            } else {
                Text(
                    text = "先听发音、回忆释义，再作答。",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun AnswerResultPill(isCorrect: Boolean) {
    val containerColor = if (isCorrect) {
        MaterialTheme.colorScheme.primaryContainer
    } else {
        MaterialTheme.colorScheme.errorContainer
    }
    val contentColor = if (isCorrect) {
        MaterialTheme.colorScheme.onPrimaryContainer
    } else {
        MaterialTheme.colorScheme.onErrorContainer
    }

    Surface(
        color = containerColor,
        contentColor = contentColor,
        shape = MaterialTheme.shapes.large,
    ) {
        Text(
            text = if (isCorrect) "回答正确" else "回答错误",
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
            style = MaterialTheme.typography.titleSmall,
        )
    }
}

@Composable
private fun LabeledText(
    label: String,
    value: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(text = label, style = MaterialTheme.typography.titleSmall)
        Text(text = value, style = MaterialTheme.typography.bodyLarge)
    }
}

@Composable
private fun ExampleSentenceBlock(
    sentenceForeign: String,
    sentenceZh: String,
    highlight: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            text = highlightedSentence(sentenceForeign, highlight, MaterialTheme.colorScheme.primary),
            style = MaterialTheme.typography.bodyLarge,
        )
        Text(
            text = sentenceZh,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

private fun highlightedSentence(
    text: String,
    keyword: String,
    highlightColor: Color,
) = buildAnnotatedString {
    if (keyword.isBlank()) {
        append(text)
        return@buildAnnotatedString
    }
    val normalizedText = text.lowercase()
    val normalizedKeyword = keyword.lowercase()
    var currentIndex = 0
    while (currentIndex < text.length) {
        val matchIndex = normalizedText.indexOf(normalizedKeyword, startIndex = currentIndex)
        if (matchIndex < 0) {
            append(text.substring(currentIndex))
            break
        }
        if (matchIndex > currentIndex) {
            append(text.substring(currentIndex, matchIndex))
        }
        withStyle(
            style = SpanStyle(
                color = highlightColor,
                fontWeight = FontWeight.Bold,
            ),
        ) {
            append(text.substring(matchIndex, matchIndex + keyword.length))
        }
        currentIndex = matchIndex + keyword.length
    }
}
