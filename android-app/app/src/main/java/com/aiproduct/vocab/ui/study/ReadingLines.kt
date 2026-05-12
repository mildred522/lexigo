package com.aiproduct.vocab.ui.study

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.domain.learning.JapaneseReadingRomanizer

@Composable
fun ReadingLines(
    word: StudyWordItem,
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.onSurfaceVariant,
    textAlign: TextAlign = TextAlign.Start,
) {
    ReadingLines(
        language = word.language,
        readingOrIpa = word.readingOrIpa,
        modifier = modifier,
        color = color,
        textAlign = textAlign,
    )
}

@Composable
fun ReadingLines(
    language: String,
    readingOrIpa: String,
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.onSurfaceVariant,
    textAlign: TextAlign = TextAlign.Start,
) {
    if (readingOrIpa.isBlank()) {
        return
    }

    val romanized = if (language.equals("ja", ignoreCase = true) || language.equals("jpn", ignoreCase = true)) {
        JapaneseReadingRomanizer.romanizeOrNull(readingOrIpa)
    } else {
        null
    }

    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(2.dp),
    ) {
        Text(
            text = readingOrIpa,
            style = MaterialTheme.typography.bodyMedium,
            color = color,
            textAlign = textAlign,
        )
        if (!romanized.isNullOrBlank() && !romanized.equals(readingOrIpa, ignoreCase = true)) {
            Text(
                text = romanized,
                style = MaterialTheme.typography.bodySmall,
                color = color.copy(alpha = 0.78f),
                textAlign = textAlign,
            )
        }
    }
}
