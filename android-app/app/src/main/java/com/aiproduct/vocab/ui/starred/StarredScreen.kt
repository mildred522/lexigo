package com.aiproduct.vocab.ui.starred

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.R
import com.aiproduct.vocab.ui.StarredUiState
import com.aiproduct.vocab.ui.learning.QuietStudyButton
import com.aiproduct.vocab.ui.learning.StudyInk
import com.aiproduct.vocab.ui.learning.StudyLine
import com.aiproduct.vocab.ui.learning.StudyMuted
import com.aiproduct.vocab.ui.learning.StudyPaper
import com.aiproduct.vocab.ui.study.ReadingLines
import com.aiproduct.vocab.ui.study.StudyWordItem

@Composable
fun StarredScreen(
    uiState: StarredUiState,
    onToggleStar: (Long) -> Unit,
    onSpeak: (StudyWordItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(StudyPaper)
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(
            text = stringResource(id = R.string.starred_title),
            style = MaterialTheme.typography.titleLarge,
            color = StudyInk,
        )

        if (uiState.words.isEmpty()) {
            Text(
                text = stringResource(id = R.string.starred_empty),
                style = MaterialTheme.typography.bodyLarge,
                color = StudyMuted,
            )
            return
        }

        LazyColumn(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(0.dp),
        ) {
            items(
                items = uiState.words,
                key = { it.id },
            ) { item ->
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text(text = item.lemma, style = MaterialTheme.typography.titleLarge, color = StudyInk)
                    ReadingLines(word = item, color = StudyMuted)
                    Text(text = item.meaningZh, style = MaterialTheme.typography.bodyLarge, color = StudyInk)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        QuietStudyButton(
                            text = stringResource(id = R.string.action_speak),
                            onClick = { onSpeak(item) },
                            modifier = Modifier.weight(1f),
                        )
                        QuietStudyButton(
                            text = stringResource(id = R.string.starred_remove),
                            onClick = { onToggleStar(item.id) },
                            emphasized = true,
                            modifier = Modifier.weight(1f),
                        )
                    }
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 12.dp)
                            .height(1.dp)
                            .background(StudyLine),
                    )
                }
            }
        }
    }
}
