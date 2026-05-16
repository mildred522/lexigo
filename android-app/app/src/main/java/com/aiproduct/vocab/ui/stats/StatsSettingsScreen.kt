package com.aiproduct.vocab.ui.stats

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
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.aiproduct.vocab.R
import com.aiproduct.vocab.domain.learning.LearningBand
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.ui.BackgroundTheme
import com.aiproduct.vocab.ui.StatsSettingsUiState
import com.aiproduct.vocab.ui.debug.DebugLogEntry
import com.aiproduct.vocab.ui.learning.QuietStudyButton
import com.aiproduct.vocab.ui.learning.StudyInk
import com.aiproduct.vocab.ui.learning.StudyLine
import com.aiproduct.vocab.ui.learning.StudyMuted
import com.aiproduct.vocab.ui.learning.StudyPaper
import com.aiproduct.vocab.ui.learning.StudySage
import com.aiproduct.vocab.ui.personalization.AchievementSummary

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun StatsSettingsScreen(
    uiState: StatsSettingsUiState,
    onSelectDefaultLanguage: (LearningLanguage) -> Unit,
    onToggleAutoResume: (Boolean) -> Unit,
    onToggleFrenchAccentInsensitive: (Boolean) -> Unit,
    onSelectBackgroundTheme: (BackgroundTheme) -> Unit,
    onPickCustomBackground: () -> Unit,
    onClearCustomBackground: () -> Unit,
    onToggleUseCustomBackground: (Boolean) -> Unit,
    onToggleDailyCover: (Boolean) -> Unit,
    debugLogs: List<DebugLogEntry>,
    onToggleDebugMode: (Boolean) -> Unit,
    onDebugSelectLearningBand: (LearningBand) -> Unit,
    onClearDebugLogs: () -> Unit,
    onTestJapaneseTts: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(StudyPaper)
            .navigationBarsPadding()
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(22.dp),
    ) {
        Text(
            text = stringResource(id = R.string.stats_title),
            style = MaterialTheme.typography.titleLarge,
            color = StudyInk,
        )

        AchievementSummary(stats = uiState.stats)

        SectionCard(title = stringResource(id = R.string.settings_personalization_title)) {
            Text(
                text = stringResource(id = R.string.settings_background_title),
                style = MaterialTheme.typography.titleMedium,
            )
            FlowRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                BackgroundTheme.entries.forEach { theme ->
                    val selected = uiState.preferences.backgroundTheme == theme && !uiState.preferences.useCustomBackground
                    QuietStudyButton(
                        text = theme.label(),
                        onClick = { onSelectBackgroundTheme(theme) },
                        emphasized = selected,
                    )
                }
            }

            val hasCustomBackground = !uiState.preferences.customBackgroundUri.isNullOrBlank()
            Text(
                text = stringResource(
                    id = if (hasCustomBackground) {
                        R.string.settings_background_custom_ready
                    } else {
                        R.string.settings_background_custom_empty
                    },
                ),
                style = MaterialTheme.typography.bodyMedium,
                color = StudyMuted,
            )
            QuietStudyButton(
                text = stringResource(id = R.string.settings_background_pick_image),
                onClick = onPickCustomBackground,
                modifier = Modifier.fillMaxWidth(),
            )
            QuietStudyButton(
                text = stringResource(id = R.string.settings_background_restore_default),
                onClick = onClearCustomBackground,
                modifier = Modifier.fillMaxWidth(),
            )
            SettingsToggleRow(
                title = stringResource(id = R.string.settings_background_use_custom),
                checked = hasCustomBackground && uiState.preferences.useCustomBackground,
                onCheckedChange = onToggleUseCustomBackground,
            )
            SettingsToggleRow(
                title = stringResource(id = R.string.settings_daily_cover_toggle),
                checked = uiState.preferences.showDailyCover,
                onCheckedChange = onToggleDailyCover,
            )
        }

        SectionCard(title = stringResource(id = R.string.settings_title)) {
            Text(
                text = stringResource(
                    id = R.string.settings_default_language,
                    if (uiState.preferences.defaultLearningLanguage == LearningLanguage.JAPANESE) {
                        stringResource(id = R.string.language_japanese)
                    } else {
                        stringResource(id = R.string.language_french)
                    },
                ),
                style = MaterialTheme.typography.bodyLarge,
                color = StudyInk,
            )
            QuietStudyButton(
                text = stringResource(id = R.string.settings_default_japanese),
                onClick = { onSelectDefaultLanguage(LearningLanguage.JAPANESE) },
                emphasized = uiState.preferences.defaultLearningLanguage == LearningLanguage.JAPANESE,
                modifier = Modifier.fillMaxWidth(),
            )
            QuietStudyButton(
                text = stringResource(id = R.string.settings_default_french),
                onClick = { onSelectDefaultLanguage(LearningLanguage.FRENCH) },
                emphasized = uiState.preferences.defaultLearningLanguage == LearningLanguage.FRENCH,
                modifier = Modifier.fillMaxWidth(),
            )
            SettingsToggleRow(
                title = stringResource(id = R.string.settings_auto_resume),
                checked = uiState.preferences.autoResumeSessions,
                onCheckedChange = onToggleAutoResume,
            )
            SettingsToggleRow(
                title = stringResource(id = R.string.settings_french_accent_insensitive),
                checked = uiState.preferences.frenchAccentInsensitive,
                onCheckedChange = onToggleFrenchAccentInsensitive,
            )
            SettingsToggleRow(
                title = "Debug mode",
                checked = uiState.preferences.debugModeEnabled,
                onCheckedChange = onToggleDebugMode,
            )
        }

        if (uiState.preferences.debugModeEnabled) {
            SectionCard(title = "Debug") {
                Text(
                    text = "Recent logs are kept in memory. Use this to diagnose TTS and learning startup.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = StudyMuted,
                )
                FlowRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    QuietStudyButton(text = "Test Japanese TTS", onClick = onTestJapaneseTts, emphasized = true)
                    QuietStudyButton(text = "Clear logs", onClick = onClearDebugLogs)
                }
                Text(
                    text = "Learning band override",
                    style = MaterialTheme.typography.titleSmall,
                    color = StudyInk,
                )
                FlowRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    LearningBand.entries.forEach { band ->
                        QuietStudyButton(
                            text = band.debugLabel(),
                            onClick = { onDebugSelectLearningBand(band) },
                            emphasized = uiState.preferences.learningBand == band,
                        )
                    }
                }
                if (debugLogs.isEmpty()) {
                    Text(
                        text = "No logs yet.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = StudyMuted,
                    )
                } else {
                    debugLogs.take(60).forEach { entry ->
                        Text(
                            text = "${entry.timestamp} [${entry.tag}] ${entry.message}",
                            style = MaterialTheme.typography.bodySmall,
                            color = StudyMuted,
                        )
                    }
                }
            }
        }

        SectionCard(title = stringResource(id = R.string.achievement_title)) {
            Text(
                text = stringResource(id = R.string.stats_starred_count, uiState.stats.starredCount),
                style = MaterialTheme.typography.bodyLarge,
                color = StudyInk,
            )
            uiState.stats.byLanguage.forEach { (language, stat) ->
                Text(
                    text = stringResource(
                        id = R.string.stats_language_summary,
                        if (language == LearningLanguage.JAPANESE) {
                            stringResource(id = R.string.language_japanese)
                        } else {
                            stringResource(id = R.string.language_french)
                        },
                        stat.learnedCount,
                        stat.dueCount,
                    ),
                    style = MaterialTheme.typography.bodyLarge,
                    color = StudyInk,
                )
            }
        }
    }
}

private fun LearningBand.debugLabel(): String = when (this) {
    LearningBand.BEGINNER -> "新手"
    LearningBand.INTERMEDIATE -> "进阶"
    LearningBand.ADVANCED -> "高级"
}

@Composable
private fun SectionCard(
    title: String,
    content: @Composable () -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(StudyLine),
        )
        Text(text = title, style = MaterialTheme.typography.titleMedium, color = StudySage)
        content()
    }
}

@Composable
private fun SettingsToggleRow(
    title: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.bodyLarge,
            color = StudyInk,
            modifier = Modifier.weight(1f),
        )
        Switch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

@Composable
private fun BackgroundTheme.label(): String = when (this) {
    BackgroundTheme.AURORA -> stringResource(id = R.string.background_theme_aurora)
    BackgroundTheme.SUNRISE -> stringResource(id = R.string.background_theme_sunrise)
    BackgroundTheme.FOREST -> stringResource(id = R.string.background_theme_forest)
    BackgroundTheme.NIGHTFALL -> stringResource(id = R.string.background_theme_nightfall)
}
