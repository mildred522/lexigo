package com.aiproduct.vocab.ui.search

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.R
import com.aiproduct.vocab.ui.learning.StudyInk
import com.aiproduct.vocab.ui.learning.StudyLine
import com.aiproduct.vocab.ui.learning.StudyMuted
import com.aiproduct.vocab.ui.learning.StudyPaper
import com.aiproduct.vocab.ui.learning.StudySage
import com.aiproduct.vocab.ui.learning.QuietStudyButton
import com.aiproduct.vocab.ui.study.ReadingLines
import com.aiproduct.vocab.ui.study.StudyWordCard
import com.aiproduct.vocab.ui.study.StudyWordItem

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SearchScreen(
    uiState: SearchUiState,
    onQueryChanged: (String) -> Unit,
    onOpenDetail: (Long) -> Unit,
    onDismissDetail: () -> Unit,
    onToggleStar: (Long) -> Unit,
    onSpeak: (StudyWordItem) -> Unit,
    modifier: Modifier = Modifier,
) {
    val title = stringResource(id = R.string.search_title)
    val hint = stringResource(id = R.string.search_hint)

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(StudyPaper)
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Text(text = title, style = MaterialTheme.typography.titleLarge, color = StudyInk)
        OutlinedTextField(
            modifier = Modifier
                .fillMaxWidth()
                .testTag("search_input"),
            value = uiState.query,
            onValueChange = onQueryChanged,
            label = { Text(text = hint) },
            singleLine = true,
        )

        if (uiState.isLoading) {
            CircularProgressIndicator(modifier = Modifier.testTag("search_loading"))
        }

        if (uiState.isDetailLoading) {
            CircularProgressIndicator(modifier = Modifier.testTag("search_detail_loading"))
        }

        uiState.selectedDetail?.let { detail ->
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    text = stringResource(id = R.string.search_detail_title),
                    style = MaterialTheme.typography.titleLarge,
                )
                StudyWordCard(
                    word = detail,
                    showAnswer = true,
                )
                FlowRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    QuietStudyButton(
                        text = stringResource(
                            id = if (uiState.isSelectedDetailStarred) {
                                R.string.search_starred
                            } else {
                                R.string.search_star
                            },
                        ),
                        onClick = { onToggleStar(detail.id) },
                        emphasized = !uiState.isSelectedDetailStarred,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    QuietStudyButton(
                        text = stringResource(id = R.string.action_speak),
                        onClick = { onSpeak(detail) },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    QuietStudyButton(
                        text = stringResource(id = R.string.search_detail_close),
                        onClick = onDismissDetail,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        }

        if (!uiState.isLoading && uiState.query.isBlank()) {
            Text(
                text = stringResource(id = R.string.search_idle),
                style = MaterialTheme.typography.bodyLarge,
                color = StudyMuted,
            )
        }

        if (!uiState.isLoading && uiState.query.isNotBlank() && uiState.results.isEmpty()) {
            Text(
                text = stringResource(id = R.string.search_empty),
                style = MaterialTheme.typography.bodyLarge,
                color = StudyMuted,
            )
        }

        LazyColumn(
            modifier = Modifier
                .weight(1f, fill = true)
                .fillMaxWidth()
                .testTag("search_results"),
            verticalArrangement = Arrangement.spacedBy(0.dp),
        ) {
            items(
                items = uiState.results,
                key = { it.id },
            ) { item ->
                SearchResultRow(
                    item = item,
                    onOpenDetail = onOpenDetail,
                    onToggleStar = onToggleStar,
                )
            }
        }
    }
}

@Composable
private fun SearchResultRow(
    item: SearchResultItem,
    onOpenDetail: (Long) -> Unit,
    onToggleStar: (Long) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .testTag("search_result_${item.id}"),
        verticalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Text(text = item.lemma, style = MaterialTheme.typography.titleLarge, color = StudyInk)
        ReadingLines(language = item.language, readingOrIpa = item.readingOrIpa, color = StudyMuted)
        Text(text = item.language.uppercase(), style = MaterialTheme.typography.labelMedium, color = StudySage)
        Text(text = item.meaningZh, style = MaterialTheme.typography.bodyLarge, color = StudyInk)
        if (item.meaningSourceText.isNotBlank()) {
            Text(text = item.meaningSourceText, style = MaterialTheme.typography.bodySmall, color = StudyMuted)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            QuietStudyButton(text = stringResource(id = R.string.search_detail_action), onClick = { onOpenDetail(item.id) })
            QuietStudyButton(
                text = stringResource(
                    id = if (item.isStarred) {
                        R.string.search_starred
                    } else {
                        R.string.search_star
                    },
                ),
                onClick = { onToggleStar(item.id) },
                emphasized = !item.isStarred,
            )
        }
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 10.dp)
                .height(1.dp)
                .background(StudyLine),
        )
    }
}
