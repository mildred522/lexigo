package com.aiproduct.vocab.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningBand
import com.aiproduct.vocab.domain.learning.ChoiceOptionDisplayMode
import com.aiproduct.vocab.domain.learning.LearningSession
import com.aiproduct.vocab.domain.learning.LearningSessionBuilder
import com.aiproduct.vocab.domain.learning.LearningSessionReducer
import com.aiproduct.vocab.domain.learning.LearningStage
import com.aiproduct.vocab.domain.learning.next
import com.aiproduct.vocab.domain.learning.SpellingAnswerEvaluator
import com.aiproduct.vocab.domain.learning.SpellingHintResolver
import com.aiproduct.vocab.ui.debug.AppDebugLog
import com.aiproduct.vocab.ui.search.SearchResultItem
import com.aiproduct.vocab.ui.study.StudyWordItem
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class AppViewModel(
    private val gateway: VocabGateway,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO,
    private val nowMillisProvider: () -> Long = System::currentTimeMillis,
    private val learningSessionBuilder: LearningSessionBuilder = LearningSessionBuilder(),
    private val learningSessionReducer: LearningSessionReducer = LearningSessionReducer(),
) : ViewModel() {
    private val _uiState = MutableStateFlow(AppUiState())
    val uiState: StateFlow<AppUiState> = _uiState.asStateFlow()

    private var searchJob: Job? = null
    private var detailJob: Job? = null
    private val tabHistory = ArrayDeque<AppTab>()

    init {
        viewModelScope.launch {
            bootstrap()
        }
    }

    fun onSelectTab(tab: AppTab) {
        val previousTab = uiState.value.selectedTab
        if (previousTab != tab) {
            tabHistory.remove(tab)
            tabHistory.addLast(previousTab)
        }
        _uiState.update { it.copy(selectedTab = tab) }
        when (tab) {
            AppTab.SEARCH -> Unit
            AppTab.LEARNING -> ensureLearningLanguageSelected()
            AppTab.STARRED -> viewModelScope.launch { refreshStarredStateAndStats() }
            AppTab.REVIEW -> viewModelScope.launch { loadReviewOverview() }
            AppTab.STATS -> viewModelScope.launch { refreshStats() }
        }
    }

    fun warmUpLearningEngine() {
        viewModelScope.launch {
            val language = uiState.value.statsSettings.preferences.defaultLearningLanguage
            AppDebugLog.add("LearningWarmUp", "start language=${language.code}")
            runCatching {
                withContext(dispatcher) {
                    gateway.learningWords(language, uiState.value.statsSettings.preferences.learningBand, limit = 1)
                    gateway.distractorMeanings(language, limit = 8)
                }
            }.onSuccess {
                AppDebugLog.add("LearningWarmUp", "success language=${language.code}")
            }.onFailure {
                AppDebugLog.add("LearningWarmUp", "failed ${it::class.simpleName}: ${it.message}")
            }
        }
    }

    fun onNavigateBackBySwipe() {
        val previousTab = tabHistory.removeLastOrNull() ?: return
        _uiState.update { it.copy(selectedTab = previousTab) }
        when (previousTab) {
            AppTab.SEARCH -> Unit
            AppTab.LEARNING -> ensureLearningLanguageSelected()
            AppTab.STARRED -> viewModelScope.launch { refreshStarredStateAndStats() }
            AppTab.REVIEW -> viewModelScope.launch { loadReviewOverview() }
            AppTab.STATS -> viewModelScope.launch { refreshStats() }
        }
    }

    fun onQueryChanged(query: String) {
        _uiState.update { current ->
            current.copy(
                search = current.search.copy(
                    query = query,
                    selectedDetail = null,
                    isSelectedDetailStarred = false,
                    isDetailLoading = false,
                ),
            )
        }
        searchJob?.cancel()

        if (query.isBlank()) {
            _uiState.update { current ->
                current.copy(search = current.search.copy(isLoading = false, results = emptyList()))
            }
            return
        }

        searchJob = viewModelScope.launch {
            _uiState.update { current ->
                current.copy(search = current.search.copy(isLoading = true, results = emptyList()))
            }
            try {
                val starredIds = withContext(dispatcher) { gateway.starredWordIds() }
                val results = withContext(dispatcher) { gateway.search(query) }
                    .map { SearchResultItem.from(it, isStarred = it.id in starredIds) }
                _uiState.update { current ->
                    if (current.search.query != query) current else {
                        current.copy(search = current.search.copy(isLoading = false, results = results))
                    }
                }
            } catch (cancellationException: CancellationException) {
                throw cancellationException
            } catch (_: Throwable) {
                _uiState.update { current ->
                    if (current.search.query != query) current else {
                        current.copy(search = current.search.copy(isLoading = false, results = emptyList()))
                    }
                }
            }
        }
    }

    fun onOpenDetail(wordId: Long) {
        detailJob?.cancel()
        detailJob = viewModelScope.launch {
            _uiState.update { current ->
                current.copy(
                    search = current.search.copy(
                        isDetailLoading = true,
                        selectedDetail = null,
                        isSelectedDetailStarred = false,
                    ),
                )
            }
            val starredIds = runCatching { withContext(dispatcher) { gateway.starredWordIds() } }.getOrDefault(emptySet())
            val detail = runCatching { withContext(dispatcher) { gateway.detail(wordId) } }.getOrNull()?.let(StudyWordItem::from)
            _uiState.update { current ->
                current.copy(
                    search = current.search.copy(
                        isDetailLoading = false,
                        selectedDetail = detail,
                        isSelectedDetailStarred = wordId in starredIds,
                    ),
                )
            }
        }
    }

    fun onDismissDetail() {
        _uiState.update { current ->
            current.copy(
                search = current.search.copy(
                    isDetailLoading = false,
                    selectedDetail = null,
                    isSelectedDetailStarred = false,
                ),
            )
        }
    }

    fun onToggleStar(wordId: Long) {
        viewModelScope.launch {
            val nowMillis = nowMillisProvider()
            val currentlyStarred = uiState.value.isStarred(wordId)
            withContext(dispatcher) {
                if (currentlyStarred) gateway.unstarWord(wordId) else gateway.starWord(wordId, nowMillis)
            }
            refreshStarredStateAndStats()
        }
    }

    fun onSelectLearningLanguage(language: LearningLanguage) {
        viewModelScope.launch { loadLearningSession(language) }
    }

    fun onStartPromotionTest() {
        val preferences = uiState.value.statsSettings.preferences
        val targetBand = preferences.learningBand.next() ?: return
        val language = uiState.value.learning.selectedLanguage ?: preferences.defaultLearningLanguage
        viewModelScope.launch {
            withContext(dispatcher) { gateway.saveLearningDraft(null) }
            loadLearningSession(language, promotionTestTargetBand = targetBand)
        }
    }

    fun onChooseLearningMeaning(meaningZh: String) {
        val session = uiState.value.learning.session ?: return
        val updated = learningSessionReducer.submitChoice(session, meaningZh)
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    session = updated,
                    feedbackWord = updated.findFeedbackWord(),
                ),
            )
        }
        if (uiState.value.learning.promotionTestTargetBand == null) {
            persistLearningDraft(updated)
        }
    }

    fun onSubmitLearningSpelling(answer: String) {
        val session = uiState.value.learning.session ?: return
        val promotionTestTargetBand = uiState.value.learning.promotionTestTargetBand
        viewModelScope.launch {
            val currentWord = session.currentSpellingWord?.word ?: return@launch
            val updated = learningSessionReducer.submitSpellingResult(
                session = session,
                isCorrect = SpellingAnswerEvaluator.isCorrect(
                    word = currentWord,
                    answer = answer,
                    preferences = uiState.value.statsSettings.preferences,
                ),
            )
            if (session.stage != LearningStage.SUMMARY && updated.stage == LearningStage.SUMMARY) {
                if (promotionTestTargetBand == null) {
                    withContext(dispatcher) {
                        gateway.saveLearningSession(updated.language, updated.words, nowMillisProvider())
                        gateway.saveLearningDraft(null)
                    }
                    refreshStats()
                } else {
                    withContext(dispatcher) { gateway.saveLearningDraft(null) }
                }
            } else {
                if (promotionTestTargetBand == null) {
                    persistLearningDraft(updated)
                }
            }
            val completionMessage = if (updated.stage == LearningStage.SUMMARY) {
                promotionTestTargetBand?.let { applyPromotionTestResult(updated, it) } ?: "本轮学习已完成"
            } else {
                null
            }
            _uiState.update { current ->
                current.copy(
                    learning = current.learning.copy(
                        session = updated,
                        feedbackWord = updated.findFeedbackWord(),
                        message = completionMessage ?: current.learning.message,
                    ),
                )
            }
        }
    }

    fun onRequestLearningHint() {
        val session = uiState.value.learning.session ?: return
        val currentWord = session.currentSpellingWord?.word ?: return
        val hint = SpellingHintResolver.resolve(currentWord)
        val updated = learningSessionReducer.registerHint(session, hint)
        _uiState.update { current ->
            current.copy(learning = current.learning.copy(session = updated))
        }
        if (uiState.value.learning.promotionTestTargetBand == null) {
            persistLearningDraft(updated)
        }
    }

    fun onSkipLearningWord() {
        val session = uiState.value.learning.session ?: return
        val promotionTestTargetBand = uiState.value.learning.promotionTestTargetBand
        val updated = learningSessionReducer.skipCurrentWord(session)
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    session = updated,
                    feedbackWord = null,
                    message = if (updated.stage == LearningStage.SUMMARY) "本轮学习已完成" else current.learning.message,
                ),
            )
        }
        viewModelScope.launch {
            if (updated.stage == LearningStage.SUMMARY) {
                if (promotionTestTargetBand == null) {
                    withContext(dispatcher) {
                        gateway.saveLearningSession(updated.language, updated.words, nowMillisProvider())
                        gateway.saveLearningDraft(null)
                    }
                    refreshStats()
                } else {
                    withContext(dispatcher) { gateway.saveLearningDraft(null) }
                    val message = applyPromotionTestResult(updated, promotionTestTargetBand)
                    _uiState.update { current ->
                        current.copy(learning = current.learning.copy(message = message))
                    }
                }
            } else {
                if (promotionTestTargetBand == null) {
                    withContext(dispatcher) { gateway.saveLearningDraft(updated) }
                }
            }
        }
    }

    fun onContinueLearning() {
        val session = uiState.value.learning.session ?: return
        val updated = learningSessionReducer.continueAfterFeedback(session)
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    session = updated,
                    feedbackWord = null,
                ),
            )
        }
        if (uiState.value.learning.promotionTestTargetBand == null) {
            persistLearningDraft(updated.takeUnless { it.stage == LearningStage.SUMMARY })
        }
    }

    fun onRestartLearning() {
        val language = uiState.value.learning.selectedLanguage ?: uiState.value.statsSettings.preferences.defaultLearningLanguage
        viewModelScope.launch {
            withContext(dispatcher) { gateway.saveLearningDraft(null) }
            loadLearningSession(language)
        }
    }

    fun onSelectReviewLanguage(language: LearningLanguage) {
        viewModelScope.launch { loadReviewSession(language) }
    }

    fun onChooseReviewMeaning(meaningZh: String) {
        val session = uiState.value.review.session ?: return
        val updated = learningSessionReducer.submitChoice(session, meaningZh)
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    session = updated,
                    feedbackWord = updated.findFeedbackWord(),
                ),
            )
        }
        persistReviewDraft(updated)
    }

    fun onSubmitReviewSpelling(answer: String) {
        val session = uiState.value.review.session ?: return
        viewModelScope.launch {
            val currentWord = session.currentSpellingWord?.word ?: return@launch
            val updated = learningSessionReducer.submitSpellingResult(
                session = session,
                isCorrect = SpellingAnswerEvaluator.isCorrect(
                    word = currentWord,
                    answer = answer,
                    preferences = uiState.value.statsSettings.preferences,
                ),
            )
            if (session.stage != LearningStage.SUMMARY && updated.stage == LearningStage.SUMMARY) {
                withContext(dispatcher) {
                    gateway.saveReviewSession(updated.words, nowMillisProvider())
                    gateway.saveReviewDraft(null)
                }
                loadReviewOverview()
                refreshStats()
            } else {
                persistReviewDraft(updated)
            }
            _uiState.update { current ->
                current.copy(
                    review = current.review.copy(
                        session = updated,
                        feedbackWord = updated.findFeedbackWord(),
                        pendingCount = updated.words.size,
                        message = if (updated.stage == LearningStage.SUMMARY) "本轮复习已完成" else current.review.message,
                    ),
                )
            }
        }
    }

    fun onRequestReviewHint() {
        val session = uiState.value.review.session ?: return
        val currentWord = session.currentSpellingWord?.word ?: return
        val hint = SpellingHintResolver.resolve(currentWord)
        val updated = learningSessionReducer.registerHint(session, hint)
        _uiState.update { current ->
            current.copy(review = current.review.copy(session = updated))
        }
        persistReviewDraft(updated)
    }

    fun onSkipReviewWord() {
        val session = uiState.value.review.session ?: return
        val updated = learningSessionReducer.skipCurrentWord(session)
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    session = updated,
                    feedbackWord = null,
                    pendingCount = updated.words.size,
                    message = if (updated.stage == LearningStage.SUMMARY) "本轮复习已完成" else current.review.message,
                ),
            )
        }
        viewModelScope.launch {
            if (updated.stage == LearningStage.SUMMARY) {
                withContext(dispatcher) {
                    gateway.saveReviewSession(updated.words, nowMillisProvider())
                    gateway.saveReviewDraft(null)
                }
                loadReviewOverview()
                refreshStats()
            } else {
                withContext(dispatcher) { gateway.saveReviewDraft(updated) }
            }
        }
    }

    fun onContinueReview() {
        val session = uiState.value.review.session ?: return
        val updated = learningSessionReducer.continueAfterFeedback(session)
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    session = updated,
                    feedbackWord = null,
                ),
            )
        }
        persistReviewDraft(updated.takeUnless { it.stage == LearningStage.SUMMARY })
    }

    fun onRestartReview() {
        viewModelScope.launch {
            withContext(dispatcher) { gateway.saveReviewDraft(null) }
            loadReviewOverview()
        }
    }

    fun onSelectDefaultLearningLanguage(language: LearningLanguage) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(defaultLearningLanguage = language)
            savePreferences(preferences)
        }
    }

    fun onToggleAutoResumeSessions(enabled: Boolean) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(autoResumeSessions = enabled)
            savePreferences(preferences)
            if (!enabled) {
                withContext(dispatcher) {
                    gateway.saveLearningDraft(null)
                    gateway.saveReviewDraft(null)
                }
            }
        }
    }

    fun onToggleFrenchAccentInsensitive(enabled: Boolean) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(frenchAccentInsensitive = enabled)
            savePreferences(preferences)
        }
    }

    fun onSelectBackgroundTheme(theme: BackgroundTheme) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(
                backgroundTheme = theme,
                useCustomBackground = false,
            )
            savePreferences(preferences)
        }
    }

    fun onCustomBackgroundSelected(uri: String?) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(
                customBackgroundUri = uri,
                useCustomBackground = !uri.isNullOrBlank(),
            )
            savePreferences(preferences)
        }
    }

    fun onToggleUseCustomBackground(enabled: Boolean) {
        viewModelScope.launch {
            val current = uiState.value.statsSettings.preferences
            val preferences = current.copy(
                useCustomBackground = enabled && !current.customBackgroundUri.isNullOrBlank(),
            )
            savePreferences(preferences)
        }
    }

    fun onToggleDailyCover(enabled: Boolean) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(showDailyCover = enabled)
            savePreferences(preferences)
        }
    }

    fun onToggleDebugMode(enabled: Boolean) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(debugModeEnabled = enabled)
            savePreferences(preferences)
            AppDebugLog.add("Debug", "debug mode ${if (enabled) "enabled" else "disabled"}")
        }
    }

    fun onDebugSelectLearningBand(band: LearningBand) {
        viewModelScope.launch {
            val preferences = uiState.value.statsSettings.preferences.copy(learningBand = band)
            savePreferences(preferences)
            withContext(dispatcher) { gateway.saveLearningDraft(null) }
            _uiState.update { current ->
                current.copy(
                    learning = current.learning.copy(
                        session = null,
                        feedbackWord = null,
                        promotionTestTargetBand = null,
                        message = "Debug 阶段已切换到${band.displayName()}",
                    ),
                )
            }
            AppDebugLog.add("Debug", "learning band set to ${band.name}")
        }
    }

    override fun onCleared() {
        super.onCleared()
        runCatching { gateway.close() }
    }

    private suspend fun bootstrap() {
        refreshStarredStateAndStats()
        val preferences = withContext(dispatcher) { gateway.loadPreferences() }
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(selectedLanguage = preferences.defaultLearningLanguage),
                statsSettings = current.statsSettings.copy(preferences = preferences),
            )
        }
        if (preferences.autoResumeSessions) {
            restoreLearningDraft()
            restoreReviewDraft()
        }
    }

    private suspend fun restoreLearningDraft() {
        val restored = withContext(dispatcher) { gateway.loadLearningDraft() } ?: return
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    selectedLanguage = restored.language,
                    session = restored,
                    feedbackWord = restored.findFeedbackWord(),
                    message = "已恢复上次学习进度",
                ),
            )
        }
    }

    private suspend fun restoreReviewDraft() {
        val restored = withContext(dispatcher) { gateway.loadReviewDraft() } ?: return
        val overview = withContext(dispatcher) { gateway.dueCountsByLanguage(nowMillisProvider()) }
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    availableLanguages = overview.toOptions(),
                    selectedLanguage = restored.language,
                    session = restored,
                    feedbackWord = restored.findFeedbackWord(),
                    pendingCount = restored.words.size,
                    message = "已恢复上次复习进度",
                ),
            )
        }
    }

    private suspend fun loadLearningSession(
        language: LearningLanguage,
        promotionTestTargetBand: LearningBand? = null,
    ) {
        val learningBand = promotionTestTargetBand ?: uiState.value.statsSettings.preferences.learningBand
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    selectedLanguage = language,
                    session = null,
                    feedbackWord = null,
                    isLoading = true,
                    message = null,
                    promotionTestTargetBand = promotionTestTargetBand,
                ),
            )
        }
        val candidateWords = runCatching { withContext(dispatcher) { gateway.learningWords(language, learningBand, limit = 40) } }.getOrDefault(emptyList())
        val words = candidateWords.take(10)
        val wordDistractors = candidateWords.drop(10).map(StudyWordItem::from)
        val distractors = runCatching { withContext(dispatcher) { gateway.distractorMeanings(language, limit = 64) } }.getOrDefault(emptyList())
        val session = learningSessionBuilder.build(
            language = language,
            words = words.map(StudyWordItem::from),
            distractorPool = distractors,
            wordDistractorPool = wordDistractors,
            choiceOptionDisplayMode = language.choiceOptionDisplayMode(learningBand),
            deduplicatePrompts = true,
        )
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    selectedLanguage = language,
                    session = session.takeIf { it.words.isNotEmpty() },
                    feedbackWord = null,
                    isLoading = false,
                    message = if (session.words.isEmpty()) {
                        if (promotionTestTargetBand == null) "当前语言没有可学习的新词" else "当前没有可用的晋级测试词"
                    } else {
                        null
                    },
                    promotionTestTargetBand = promotionTestTargetBand,
                ),
            )
        }
        if (promotionTestTargetBand == null) {
            persistLearningDraft(session.takeIf { it.words.isNotEmpty() })
        }
    }

    private suspend fun loadReviewOverview() {
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    session = null,
                    feedbackWord = null,
                    pendingCount = 0,
                    isLoading = true,
                    message = null,
                ),
            )
        }
        val dueCounts = runCatching { withContext(dispatcher) { gateway.dueCountsByLanguage(nowMillisProvider()) } }.getOrDefault(emptyMap())
        val options = dueCounts.toOptions()
        if (options.isEmpty()) {
            _uiState.update { current ->
                current.copy(
                    review = current.review.copy(
                        availableLanguages = emptyList(),
                        selectedLanguage = null,
                        session = null,
                        feedbackWord = null,
                        pendingCount = 0,
                        isLoading = false,
                        message = "当前没有到期复习词",
                    ),
                )
            }
            withContext(dispatcher) { gateway.saveReviewDraft(null) }
            return
        }
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    availableLanguages = options,
                    selectedLanguage = if (options.size == 1) options.first().language else null,
                    session = null,
                    feedbackWord = null,
                    pendingCount = options.sumOf { it.dueCount },
                    isLoading = false,
                    message = if (options.size == 1) null else "选择语言后开始复习",
                ),
            )
        }
        if (options.size == 1) {
            loadReviewSession(options.first().language)
        }
    }

    private suspend fun loadReviewSession(language: LearningLanguage) {
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    selectedLanguage = language,
                    session = null,
                    feedbackWord = null,
                    isLoading = true,
                    message = null,
                ),
            )
        }
        val dueWords = runCatching { withContext(dispatcher) { gateway.dueWords(language, nowMillisProvider()) } }.getOrDefault(emptyList())
        val reviewWords = dueWords.map(StudyWordItem::from)
        if (reviewWords.isEmpty()) {
            _uiState.update { current ->
                current.copy(
                    review = current.review.copy(
                        selectedLanguage = language,
                        session = null,
                        feedbackWord = null,
                        pendingCount = 0,
                        isLoading = false,
                        message = "该语言当前没有到期复习词",
                    ),
                )
            }
            withContext(dispatcher) { gateway.saveReviewDraft(null) }
            return
        }
        val distractors = runCatching { withContext(dispatcher) { gateway.distractorMeanings(language, limit = 64) } }.getOrDefault(emptyList())
        val session = learningSessionBuilder.build(
            language = language,
            words = reviewWords,
            distractorPool = distractors,
        )
        _uiState.update { current ->
            current.copy(
                review = current.review.copy(
                    selectedLanguage = language,
                    session = session,
                    feedbackWord = null,
                    pendingCount = reviewWords.size,
                    isLoading = false,
                    message = null,
                ),
            )
        }
        persistReviewDraft(session)
    }

    private suspend fun refreshStarredStateAndStats() {
        val starredIds = runCatching { withContext(dispatcher) { gateway.starredWordIds() } }.getOrDefault(emptySet())
        val starredWords = runCatching { withContext(dispatcher) { gateway.starredWords() } }.getOrDefault(emptyList()).map(StudyWordItem::from)
        val stats = runCatching { withContext(dispatcher) { gateway.loadStats(nowMillisProvider()) } }.getOrDefault(AppStats())
        _uiState.update { current ->
            current.copy(
                search = current.search.copy(
                    results = current.search.results.map { item -> item.copy(isStarred = item.id in starredIds) },
                    isSelectedDetailStarred = current.search.selectedDetail?.id in starredIds,
                ),
                starred = current.starred.copy(words = starredWords, isLoading = false),
                statsSettings = current.statsSettings.copy(stats = stats, isLoading = false),
            )
        }
    }

    private suspend fun refreshStats() {
        val stats = withContext(dispatcher) { gateway.loadStats(nowMillisProvider()) }
        _uiState.update { current ->
            current.copy(statsSettings = current.statsSettings.copy(stats = stats, isLoading = false))
        }
    }

    private suspend fun applyPromotionTestResult(
        session: LearningSession,
        targetBand: LearningBand,
    ): String {
        val currentPreferences = uiState.value.statsSettings.preferences
        val currentBand = currentPreferences.learningBand
        if (targetBand != currentBand.next()) return "晋级测试已结束"

        if (!session.isPerfectPromotionTest()) {
            return "本次晋级测试未全对，继续练习后再试"
        }

        val passCount = currentPreferences.promotionPerfectPasses(currentBand) + 1
        if (passCount >= PromotionRequiredPerfectPasses) {
            savePreferences(
                currentPreferences
                    .withPromotionPerfectPasses(currentBand, 0)
                    .copy(learningBand = targetBand),
            )
            return "已晋级到${targetBand.displayName()}"
        }

        savePreferences(currentPreferences.withPromotionPerfectPasses(currentBand, passCount))
        return "晋级测试通过 $passCount/$PromotionRequiredPerfectPasses"
    }

    private suspend fun savePreferences(preferences: UserPreferences) {
        withContext(dispatcher) { gateway.savePreferences(preferences) }
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    selectedLanguage = current.learning.selectedLanguage ?: preferences.defaultLearningLanguage,
                ),
                statsSettings = current.statsSettings.copy(preferences = preferences),
            )
        }
    }

    private fun ensureLearningLanguageSelected() {
        val currentLanguage = uiState.value.learning.selectedLanguage
        if (currentLanguage != null) return
        _uiState.update { current ->
            current.copy(
                learning = current.learning.copy(
                    selectedLanguage = current.statsSettings.preferences.defaultLearningLanguage,
                ),
            )
        }
    }

    private fun persistLearningDraft(session: LearningSession?) {
        viewModelScope.launch {
            withContext(dispatcher) { gateway.saveLearningDraft(session) }
        }
    }

    private fun persistReviewDraft(session: LearningSession?) {
        viewModelScope.launch {
            withContext(dispatcher) { gateway.saveReviewDraft(session) }
        }
    }
}

private fun AppUiState.isStarred(wordId: Long): Boolean {
    if (search.results.any { it.id == wordId && it.isStarred }) return true
    if (search.selectedDetail?.id == wordId && search.isSelectedDetailStarred) return true
    return starred.words.any { it.id == wordId }
}

private fun Map<LearningLanguage, Int>.toOptions(): List<ReviewLanguageOption> = entries
    .sortedBy { it.key.name }
    .map { ReviewLanguageOption(language = it.key, dueCount = it.value) }

private fun LearningSession.findFeedbackWord(): StudyWordItem? = feedback?.wordId?.let { wordId ->
    words.firstOrNull { it.word.id == wordId }?.word
}

private const val PromotionRequiredPerfectPasses = 3

private fun LearningSession.isPerfectPromotionTest(): Boolean =
    words.isNotEmpty() && words.all {
        it.choiceCorrectCount > 0 &&
            it.spellingCorrectCount > 0 &&
            it.choiceWrongCount == 0 &&
            it.spellingWrongCount == 0 &&
            it.hintUsedCount == 0
    }

private fun UserPreferences.promotionPerfectPasses(band: LearningBand): Int = when (band) {
    LearningBand.BEGINNER -> beginnerPromotionPerfectPasses
    LearningBand.INTERMEDIATE -> intermediatePromotionPerfectPasses
    LearningBand.ADVANCED -> 0
}

private fun UserPreferences.withPromotionPerfectPasses(
    band: LearningBand,
    passCount: Int,
): UserPreferences = when (band) {
    LearningBand.BEGINNER -> copy(beginnerPromotionPerfectPasses = passCount)
    LearningBand.INTERMEDIATE -> copy(intermediatePromotionPerfectPasses = passCount)
    LearningBand.ADVANCED -> this
}

private fun LearningBand.displayName(): String = when (this) {
    LearningBand.BEGINNER -> "新手"
    LearningBand.INTERMEDIATE -> "进阶"
    LearningBand.ADVANCED -> "高级"
}

private fun LearningLanguage.choiceOptionDisplayMode(band: LearningBand): ChoiceOptionDisplayMode =
    if (this != LearningLanguage.JAPANESE) {
        ChoiceOptionDisplayMode.MEANING
    } else {
        when (band) {
            LearningBand.BEGINNER -> ChoiceOptionDisplayMode.KANA_ONLY
            LearningBand.INTERMEDIATE -> ChoiceOptionDisplayMode.KANJI_KANA
            LearningBand.ADVANCED -> ChoiceOptionDisplayMode.KANJI_ONLY
        }
    }
