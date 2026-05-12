package com.aiproduct.vocab.ui.personalization

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.R
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.ui.AppStats
import com.aiproduct.vocab.ui.learning.StudyInk
import com.aiproduct.vocab.ui.learning.StudyLine
import com.aiproduct.vocab.ui.learning.StudyMuted
import com.aiproduct.vocab.ui.learning.StudySage

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AchievementSummary(
    stats: AppStats,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text(
            text = stringResource(id = R.string.achievement_title),
            style = MaterialTheme.typography.titleMedium,
            color = StudySage,
        )
        FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
            maxItemsInEachRow = 2,
        ) {
            AchievementTile(
                label = stringResource(id = R.string.achievement_streak),
                value = stringResource(id = R.string.achievement_unit_day, stats.streakDays),
            )
            AchievementTile(
                label = stringResource(id = R.string.achievement_today_studied),
                value = stringResource(id = R.string.achievement_unit_word, stats.todayStudiedCount),
            )
            AchievementTile(
                label = stringResource(id = R.string.achievement_due_today),
                value = stringResource(id = R.string.achievement_unit_word, stats.dueTodayCount),
            )
            AchievementTile(
                label = stringResource(id = R.string.achievement_starred),
                value = stringResource(id = R.string.achievement_unit_word, stats.starredCount),
            )
            AchievementTile(
                label = stringResource(id = R.string.achievement_japanese_total),
                value = stringResource(
                    id = R.string.achievement_unit_word,
                    stats.byLanguage[LearningLanguage.JAPANESE]?.learnedCount ?: 0,
                ),
            )
            AchievementTile(
                label = stringResource(id = R.string.achievement_french_total),
                value = stringResource(
                    id = R.string.achievement_unit_word,
                    stats.byLanguage[LearningLanguage.FRENCH]?.learnedCount ?: 0,
                ),
            )
        }
    }
}

@Composable
private fun AchievementTile(
    label: String,
    value: String,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth(0.48f)
            .padding(vertical = 2.dp),
        verticalArrangement = Arrangement.spacedBy(7.dp),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(StudyLine),
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelLarge,
            color = StudyMuted,
        )
        Text(
            text = value,
            style = MaterialTheme.typography.titleLarge,
            color = StudyInk,
        )
    }
}
