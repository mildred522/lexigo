package com.aiproduct.vocab.ui

import androidx.annotation.StringRes
import com.aiproduct.vocab.R
import com.aiproduct.vocab.domain.learning.LearningBand
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningSession
import com.aiproduct.vocab.ui.search.SearchUiState
import com.aiproduct.vocab.ui.study.StudyWordItem

data class AppUiState(
    val selectedTab: AppTab = AppTab.SEARCH,
    val search: SearchUiState = SearchUiState(),
    val learning: LearningUiState = LearningUiState(),
    val starred: StarredUiState = StarredUiState(),
    val review: ReviewUiState = ReviewUiState(),
    val statsSettings: StatsSettingsUiState = StatsSettingsUiState(),
)

enum class AppTab(
    @StringRes val labelRes: Int,
    val iconText: String,
) {
    SEARCH(R.string.tab_search, "S"),
    LEARNING(R.string.tab_learning, "L"),
    STARRED(R.string.tab_starred, "*"),
    REVIEW(R.string.tab_review, "R"),
    STATS(R.string.tab_stats, "M"),
}

data class LearningUiState(
    val selectedLanguage: LearningLanguage? = null,
    val session: LearningSession? = null,
    val promotionTestTargetBand: LearningBand? = null,
    val feedbackWord: StudyWordItem? = null,
    val isLoading: Boolean = false,
    val message: String? = null,
)

data class StarredUiState(
    val words: List<StudyWordItem> = emptyList(),
    val isLoading: Boolean = false,
)

data class ReviewUiState(
    val availableLanguages: List<ReviewLanguageOption> = emptyList(),
    val selectedLanguage: LearningLanguage? = null,
    val session: LearningSession? = null,
    val feedbackWord: StudyWordItem? = null,
    val pendingCount: Int = 0,
    val isLoading: Boolean = false,
    val message: String? = null,
)
