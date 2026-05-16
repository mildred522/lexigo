package com.aiproduct.vocab.ui

import android.content.Context
import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import com.aiproduct.vocab.ui.audio.AndroidWordSpeaker
import com.aiproduct.vocab.ui.debug.AppDebugLog
import com.aiproduct.vocab.ui.learning.LearningScreen
import com.aiproduct.vocab.ui.learning.StudyInk
import com.aiproduct.vocab.ui.learning.StudyMuted
import com.aiproduct.vocab.ui.learning.StudyPaper
import com.aiproduct.vocab.ui.learning.StudySage
import com.aiproduct.vocab.ui.personalization.AppBackground
import com.aiproduct.vocab.ui.review.ReviewScreen
import com.aiproduct.vocab.ui.search.SearchScreen
import com.aiproduct.vocab.ui.starred.StarredScreen
import com.aiproduct.vocab.ui.stats.StatsSettingsScreen
import com.aiproduct.vocab.ui.study.StudyWordItem

@Composable
fun AppRoot() {
    val context = LocalContext.current
    val appContext = context.applicationContext
    val factory = remember(appContext) { appViewModelFactory(appContext) }
    val speaker = remember(appContext) { AndroidWordSpeaker(appContext) }
    val viewModel: AppViewModel = viewModel(factory = factory)
    val uiState by viewModel.uiState.collectAsState()
    val debugLogs by AppDebugLog.entries.collectAsState()
    val swipeBackThreshold = with(LocalDensity.current) { 96.dp.toPx() }
    val pickBackgroundLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri != null) {
            runCatching {
                context.contentResolver.takePersistableUriPermission(
                    uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION,
                )
            }
            viewModel.onCustomBackgroundSelected(uri.toString())
        }
    }

    DisposableEffect(speaker) {
        onDispose { speaker.shutdown() }
    }

    LaunchedEffect(speaker, viewModel) {
        speaker.warmUp("ja")
        viewModel.warmUpLearningEngine()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(swipeBackThreshold) {
                var horizontalDrag = 0f
                detectHorizontalDragGestures(
                    onDragStart = { horizontalDrag = 0f },
                    onHorizontalDrag = { _, dragAmount ->
                        horizontalDrag += dragAmount
                    },
                    onDragEnd = {
                        if (horizontalDrag > swipeBackThreshold) {
                            viewModel.onNavigateBackBySwipe()
                        }
                    },
                    onDragCancel = { horizontalDrag = 0f },
                )
            },
    ) {
        AppBackground(
            preferences = uiState.statsSettings.preferences,
            modifier = Modifier.fillMaxSize(),
        )
        Scaffold(
            containerColor = Color.Transparent,
            bottomBar = {
                NavigationBar(
                    containerColor = StudyPaper.copy(alpha = 0.96f),
                    tonalElevation = 0.dp,
                ) {
                    AppTab.entries.forEach { tab ->
                        NavigationBarItem(
                            selected = uiState.selectedTab == tab,
                            onClick = { viewModel.onSelectTab(tab) },
                            icon = { Text(text = tab.iconText) },
                            label = { Text(text = stringResource(id = tab.labelRes)) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = StudySage,
                                selectedTextColor = StudyInk,
                                indicatorColor = Color.Transparent,
                                unselectedIconColor = StudyMuted,
                                unselectedTextColor = StudyMuted,
                            ),
                        )
                    }
                }
            },
        ) { paddingValues ->
            when (uiState.selectedTab) {
                AppTab.SEARCH -> SearchScreen(
                    modifier = Modifier.padding(paddingValues),
                    uiState = uiState.search,
                    onQueryChanged = viewModel::onQueryChanged,
                    onOpenDetail = viewModel::onOpenDetail,
                    onDismissDetail = viewModel::onDismissDetail,
                    onToggleStar = viewModel::onToggleStar,
                    onSpeak = { word -> speaker.speak(word.language, word.speechText()) },
                )

                AppTab.LEARNING -> LearningScreen(
                    modifier = Modifier.padding(paddingValues),
                    uiState = uiState.learning,
                    stats = uiState.statsSettings.stats,
                    showDailyCover = uiState.statsSettings.preferences.showDailyCover,
                    learningBand = uiState.statsSettings.preferences.learningBand,
                    promotionPerfectPasses = uiState.statsSettings.preferences.currentPromotionPerfectPasses(),
                    onSelectLanguage = viewModel::onSelectLearningLanguage,
                    onStartPromotionTest = viewModel::onStartPromotionTest,
                    onChooseMeaning = viewModel::onChooseLearningMeaning,
                    onSubmitSpelling = viewModel::onSubmitLearningSpelling,
                    onRequestHint = viewModel::onRequestLearningHint,
                    onSkipCurrentWord = viewModel::onSkipLearningWord,
                    onContinue = viewModel::onContinueLearning,
                    onRestart = viewModel::onRestartLearning,
                    onSpeak = { word -> speaker.speak(word.language, word.speechText()) },
                )

                AppTab.STARRED -> StarredScreen(
                    modifier = Modifier.padding(paddingValues),
                    uiState = uiState.starred,
                    onToggleStar = viewModel::onToggleStar,
                    onSpeak = { word -> speaker.speak(word.language, word.speechText()) },
                )

                AppTab.REVIEW -> ReviewScreen(
                    modifier = Modifier.padding(paddingValues),
                    uiState = uiState.review,
                    onChooseMeaning = viewModel::onChooseReviewMeaning,
                    onSubmitSpelling = viewModel::onSubmitReviewSpelling,
                    onRequestHint = viewModel::onRequestReviewHint,
                    onSkipCurrentWord = viewModel::onSkipReviewWord,
                    onContinue = viewModel::onContinueReview,
                    onRestart = viewModel::onRestartReview,
                    onSelectLanguage = viewModel::onSelectReviewLanguage,
                    onSpeak = { word -> speaker.speak(word.language, word.speechText()) },
                )

                AppTab.STATS -> StatsSettingsScreen(
                    modifier = Modifier.padding(paddingValues),
                    uiState = uiState.statsSettings,
                    onSelectDefaultLanguage = viewModel::onSelectDefaultLearningLanguage,
                    onToggleAutoResume = viewModel::onToggleAutoResumeSessions,
                    onToggleFrenchAccentInsensitive = viewModel::onToggleFrenchAccentInsensitive,
                    onSelectBackgroundTheme = viewModel::onSelectBackgroundTheme,
                    onPickCustomBackground = { pickBackgroundLauncher.launch(arrayOf("image/*")) },
                    onClearCustomBackground = { viewModel.onCustomBackgroundSelected(null) },
                    onToggleUseCustomBackground = viewModel::onToggleUseCustomBackground,
                    onToggleDailyCover = viewModel::onToggleDailyCover,
                    debugLogs = debugLogs,
                    onToggleDebugMode = viewModel::onToggleDebugMode,
                    onClearDebugLogs = AppDebugLog::clear,
                    onTestJapaneseTts = { speaker.speak("ja", "\u306b\u307b\u3093") },
                )
            }
        }
    }
}

private fun StudyWordItem.speechText(): String = if (
    language.equals("ja", ignoreCase = true) ||
    language.equals("jpn", ignoreCase = true)
) {
    readingOrIpa.ifBlank { lemma }
} else {
    lemma
}

private fun UserPreferences.currentPromotionPerfectPasses(): Int = when (learningBand) {
    com.aiproduct.vocab.domain.learning.LearningBand.BEGINNER -> beginnerPromotionPerfectPasses
    com.aiproduct.vocab.domain.learning.LearningBand.INTERMEDIATE -> intermediatePromotionPerfectPasses
    com.aiproduct.vocab.domain.learning.LearningBand.ADVANCED -> 0
}

private fun appViewModelFactory(context: Context): ViewModelProvider.Factory =
    object : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            check(modelClass.isAssignableFrom(AppViewModel::class.java))
            @Suppress("UNCHECKED_CAST")
            return AppViewModel(
                gateway = DictionaryVocabGateway(context = context),
            ) as T
        }
    }
