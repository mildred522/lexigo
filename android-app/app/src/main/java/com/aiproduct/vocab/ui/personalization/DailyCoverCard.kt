package com.aiproduct.vocab.ui.personalization

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.R
import com.aiproduct.vocab.ui.AppStats
import com.aiproduct.vocab.ui.learning.StudyInk
import com.aiproduct.vocab.ui.learning.StudyLine
import com.aiproduct.vocab.ui.learning.StudyMuted
import com.aiproduct.vocab.ui.learning.StudySage
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun DailyCoverCard(
    stats: AppStats,
    modifier: Modifier = Modifier,
    date: LocalDate = LocalDate.now(),
) {
    val content = remember(date) { DailyCoverCatalog.coverFor(date) }
    val formatter = remember { DateTimeFormatter.ofPattern("M月d日 EEEE", Locale.CHINA) }

    androidx.compose.foundation.layout.Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(StudyLine),
        )
        Text(
            text = stringResource(id = R.string.daily_cover_date, date.format(formatter)),
            style = MaterialTheme.typography.labelLarge,
            color = StudyMuted,
        )
        Text(
            text = content.title,
            style = MaterialTheme.typography.headlineSmall,
            color = StudyInk,
            fontWeight = FontWeight.Normal,
        )
        Text(
            text = content.subtitle,
            style = MaterialTheme.typography.bodyLarge,
            color = StudyMuted,
        )
        FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            DailyMetricPill(text = stringResource(id = R.string.daily_cover_today_studied, stats.todayStudiedCount))
            DailyMetricPill(text = stringResource(id = R.string.daily_cover_due_today, stats.dueTodayCount))
            DailyMetricPill(text = stringResource(id = R.string.daily_cover_streak, stats.streakDays))
        }
    }
}

@Composable
private fun DailyMetricPill(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.labelLarge,
        color = StudySage,
    )
}
