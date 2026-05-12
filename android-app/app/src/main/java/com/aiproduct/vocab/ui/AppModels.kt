package com.aiproduct.vocab.ui

import com.aiproduct.vocab.domain.learning.LearningLanguage

enum class BackgroundTheme {
    AURORA,
    SUNRISE,
    FOREST,
    NIGHTFALL,
}

data class ReviewLanguageOption(
    val language: LearningLanguage,
    val dueCount: Int,
)

data class LanguageProgressStats(
    val learnedCount: Int = 0,
    val dueCount: Int = 0,
)

data class AppStats(
    val starredCount: Int = 0,
    val streakDays: Int = 0,
    val todayStudiedCount: Int = 0,
    val dueTodayCount: Int = 0,
    val byLanguage: Map<LearningLanguage, LanguageProgressStats> = emptyMap(),
)

data class UserPreferences(
    val defaultLearningLanguage: LearningLanguage = LearningLanguage.JAPANESE,
    val autoResumeSessions: Boolean = true,
    val frenchAccentInsensitive: Boolean = true,
    val backgroundTheme: BackgroundTheme = BackgroundTheme.AURORA,
    val customBackgroundUri: String? = null,
    val useCustomBackground: Boolean = false,
    val showDailyCover: Boolean = true,
    val debugModeEnabled: Boolean = false,
)

data class StatsSettingsUiState(
    val stats: AppStats = AppStats(),
    val preferences: UserPreferences = UserPreferences(),
    val isLoading: Boolean = false,
)
