package com.aiproduct.vocab.ui

import com.aiproduct.vocab.domain.learning.ChoiceQuestion
import com.aiproduct.vocab.domain.learning.LearningBand
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningSession
import com.aiproduct.vocab.domain.learning.LearningStage
import com.aiproduct.vocab.domain.learning.LearningWordProgress
import com.aiproduct.vocab.domain.learning.MeaningOption
import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.WordSummary
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AppViewModelTest {
    @Test
    fun init_loadsPersonalizationPreferencesAndExpandedStats() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val gateway = FakeVocabGateway(
                preferences = UserPreferences(
                    backgroundTheme = BackgroundTheme.FOREST,
                    customBackgroundUri = "content://demo/background",
                    useCustomBackground = true,
                    showDailyCover = false,
                ),
                stats = AppStats(
                    starredCount = 3,
                    streakDays = 5,
                    todayStudiedCount = 7,
                    dueTodayCount = 2,
                ),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 5000L },
            )

            advanceUntilIdle()

            val uiState = viewModel.uiState.value.statsSettings
            assertEquals(BackgroundTheme.FOREST, uiState.preferences.backgroundTheme)
            assertEquals("content://demo/background", uiState.preferences.customBackgroundUri)
            assertTrue(uiState.preferences.useCustomBackground)
            assertFalse(uiState.preferences.showDailyCover)
            assertEquals(5, uiState.stats.streakDays)
            assertEquals(7, uiState.stats.todayStudiedCount)
            assertEquals(2, uiState.stats.dueTodayCount)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun personalizationActions_updatePreferencesInStateAndGateway() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val gateway = FakeVocabGateway()
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 6_000L },
            )

            advanceUntilIdle()
            viewModel.onSelectBackgroundTheme(BackgroundTheme.NIGHTFALL)
            viewModel.onCustomBackgroundSelected("content://demo/cover")
            viewModel.onToggleUseCustomBackground(true)
            viewModel.onToggleDailyCover(false)
            advanceUntilIdle()

            val preferences = viewModel.uiState.value.statsSettings.preferences
            assertEquals(BackgroundTheme.NIGHTFALL, preferences.backgroundTheme)
            assertEquals("content://demo/cover", preferences.customBackgroundUri)
            assertTrue(preferences.useCustomBackground)
            assertFalse(preferences.showDailyCover)
            assertEquals(BackgroundTheme.NIGHTFALL, gateway.savedPreferencesHistory.last().backgroundTheme)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun defaultTab_isSearchAndStarToggleRefreshesStarredState() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val bonjour = sampleWordDetail(id = 1L, language = "fr", lemma = "bonjour", meaningZh = "你好")
            val gateway = FakeVocabGateway(
                searchResultsByQuery = mapOf("bonjour" to listOf(summaryFrom(bonjour))),
                detailsById = mutableMapOf(bonjour.id to bonjour),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 1_000L },
            )

            advanceUntilIdle()
            assertEquals(AppTab.SEARCH, viewModel.uiState.value.selectedTab)

            viewModel.onQueryChanged("bonjour")
            advanceUntilIdle()
            assertFalse(viewModel.uiState.value.search.results.first().isStarred)

            viewModel.onToggleStar(bonjour.id)
            advanceUntilIdle()

            val state = viewModel.uiState.value
            assertTrue(state.search.results.first().isStarred)
            assertEquals(listOf("bonjour"), state.starred.words.map { it.lemma })
            assertEquals(setOf(bonjour.id), gateway.starredIds)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun startLearningSession_buildsJapaneseSessionWithoutUsingStarredWords() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val starredWord = sampleWordDetail(id = 10L, language = "ja", lemma = "さくら", meaningZh = "樱花")
            val learningWord = sampleWordDetail(id = 11L, language = "ja", lemma = "ねこ", meaningZh = "猫")
            val gateway = FakeVocabGateway(
                detailsById = mutableMapOf(starredWord.id to starredWord, learningWord.id to learningWord),
                learningWordsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf(learningWord)),
                distractorMeaningsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf("猫", "狗", "学校", "天气")),
                starredIds = linkedSetOf(starredWord.id),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 2_000L },
            )

            advanceUntilIdle()
            viewModel.onSelectLearningLanguage(LearningLanguage.JAPANESE)
            advanceUntilIdle()

            val session = requireNotNull(viewModel.uiState.value.learning.session)
            assertEquals(listOf("ねこ"), session.words.map { it.word.lemma })
            assertEquals(LearningLanguage.JAPANESE, viewModel.uiState.value.learning.selectedLanguage)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun reviewTab_groupsDueWordsByLanguageBeforeStartingSession() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val jaWord = sampleWordDetail(id = 21L, language = "ja", lemma = "ねこ", meaningZh = "猫")
            val frWord = sampleWordDetail(id = 22L, language = "fr", lemma = "bonjour", meaningZh = "你好")
            val gateway = FakeVocabGateway(
                detailsById = mutableMapOf(jaWord.id to jaWord, frWord.id to frWord),
                dueCountsByLanguage = mapOf(LearningLanguage.JAPANESE to 1, LearningLanguage.FRENCH to 1),
                dueWordsByLanguage = mapOf(
                    LearningLanguage.JAPANESE to listOf(jaWord),
                    LearningLanguage.FRENCH to listOf(frWord),
                ),
                distractorMeaningsByLanguage = mapOf(
                    LearningLanguage.JAPANESE to listOf("猫", "狗", "学校", "天气"),
                    LearningLanguage.FRENCH to listOf("你好", "再见", "谢谢", "学校"),
                ),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 3_000L },
            )

            advanceUntilIdle()
            viewModel.onSelectTab(AppTab.REVIEW)
            advanceUntilIdle()

            val reviewState = viewModel.uiState.value.review
            assertEquals(listOf(LearningLanguage.JAPANESE, LearningLanguage.FRENCH), reviewState.availableLanguages.map { it.language })
            assertNull(reviewState.session)

            viewModel.onSelectReviewLanguage(LearningLanguage.FRENCH)
            advanceUntilIdle()

            assertEquals(LearningLanguage.FRENCH, viewModel.uiState.value.review.selectedLanguage)
            assertEquals(listOf("bonjour"), viewModel.uiState.value.review.session?.words?.map { it.word.lemma })
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun init_restoresLearningDraftWhenAutoResumeEnabled() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val restoredWord = sampleWordDetail(id = 30L, language = "ja", lemma = "いぬ", meaningZh = "狗")
            val restoredSession = sampleSession(LearningLanguage.JAPANESE, restoredWord)
            val gateway = FakeVocabGateway(
                detailsById = mutableMapOf(restoredWord.id to restoredWord),
                storedLearningDraft = restoredSession,
                preferences = UserPreferences(autoResumeSessions = true),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 4_000L },
            )

            advanceUntilIdle()

            assertNotNull(viewModel.uiState.value.learning.session)
            assertEquals("いぬ", viewModel.uiState.value.learning.session?.currentChoiceWord?.word?.lemma)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun learningAnswer_showsFeedbackCardUntilUserContinues() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val first = sampleWordDetail(id = 31L, language = "ja", lemma = "ねこ", meaningZh = "猫")
            val second = sampleWordDetail(id = 32L, language = "ja", lemma = "いぬ", meaningZh = "狗")
            val gateway = FakeVocabGateway(
                detailsById = mutableMapOf(first.id to first, second.id to second),
                learningWordsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf(first, second)),
                distractorMeaningsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf("猫", "狗", "学校", "天气")),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 4_000L },
            )

            advanceUntilIdle()
            viewModel.onSelectLearningLanguage(LearningLanguage.JAPANESE)
            advanceUntilIdle()

            viewModel.onChooseLearningMeaning("猫")
            advanceUntilIdle()

            val feedbackState = requireNotNull(viewModel.uiState.value.learning.session)
            assertEquals(31L, feedbackState.feedback?.wordId)
            assertNotNull(viewModel.uiState.value.learning.feedbackWord)
            assertEquals("ねこ", viewModel.uiState.value.learning.feedbackWord?.lemma)

            viewModel.onContinueLearning()
            advanceUntilIdle()

            val continued = requireNotNull(viewModel.uiState.value.learning.session)
            assertEquals(null, continued.feedback)
            assertEquals("いぬ", continued.currentChoiceWord?.word?.lemma)
        } finally {
            Dispatchers.resetMain()
        }
    }
    @Test
    fun startLearningSession_usesSourceMeaningWhenChineseMeaningIsBlank() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val word = sampleWordDetail(
                id = 40L,
                language = "ja",
                lemma = "hello",
                meaningZh = "",
            ).copy(meaningSourceText = "hello meaning")
            val gateway = FakeVocabGateway(
                detailsById = mutableMapOf(word.id to word),
                learningWordsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf(word)),
                distractorMeaningsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf("one", "two", "three")),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 4_000L },
            )

            advanceUntilIdle()
            viewModel.onSelectLearningLanguage(LearningLanguage.JAPANESE)
            advanceUntilIdle()

            val question = requireNotNull(viewModel.uiState.value.learning.session?.currentChoiceQuestion)
            assertTrue(question.options.any { it.isCorrect && it.meaningZh == "hello meaning" })
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun promotionTest_usesNextBandAndCountsPerfectPass() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val word = sampleWordDetail(id = 50L, language = "ja", lemma = "neko", meaningZh = "cat")
            val gateway = FakeVocabGateway(
                detailsById = mutableMapOf(word.id to word),
                learningWordsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf(word)),
                distractorMeaningsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf("dog", "school", "weather")),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 5_000L },
            )

            advanceUntilIdle()
            viewModel.onStartPromotionTest()
            advanceUntilIdle()
            viewModel.onChooseLearningMeaning("cat")
            advanceUntilIdle()
            viewModel.onContinueLearning()
            advanceUntilIdle()
            viewModel.onSubmitLearningSpelling("neko")
            advanceUntilIdle()

            assertEquals(listOf(LearningBand.INTERMEDIATE), gateway.requestedLearningBands)
            assertEquals(LearningBand.BEGINNER, viewModel.uiState.value.statsSettings.preferences.learningBand)
            assertEquals(1, viewModel.uiState.value.statsSettings.preferences.beginnerPromotionPerfectPasses)
            assertTrue(gateway.savedLearningSessions.isEmpty())
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun promotionTest_thirdPerfectPassPromotesBand() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val word = sampleWordDetail(id = 51L, language = "ja", lemma = "inu", meaningZh = "dog")
            val gateway = FakeVocabGateway(
                detailsById = mutableMapOf(word.id to word),
                learningWordsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf(word)),
                distractorMeaningsByLanguage = mapOf(LearningLanguage.JAPANESE to listOf("cat", "school", "weather")),
                preferences = UserPreferences(beginnerPromotionPerfectPasses = 2),
            )
            val viewModel = AppViewModel(
                gateway = gateway,
                dispatcher = dispatcher,
                nowMillisProvider = { 5_000L },
            )

            advanceUntilIdle()
            viewModel.onStartPromotionTest()
            advanceUntilIdle()
            viewModel.onChooseLearningMeaning("dog")
            advanceUntilIdle()
            viewModel.onContinueLearning()
            advanceUntilIdle()
            viewModel.onSubmitLearningSpelling("inu")
            advanceUntilIdle()

            val preferences = viewModel.uiState.value.statsSettings.preferences
            assertEquals(LearningBand.INTERMEDIATE, preferences.learningBand)
            assertEquals(0, preferences.beginnerPromotionPerfectPasses)
            assertTrue(gateway.savedLearningSessions.isEmpty())
        } finally {
            Dispatchers.resetMain()
        }
    }
}

private fun sampleWordDetail(
    id: Long,
    language: String,
    lemma: String,
    meaningZh: String,
) = WordDetail(
    id = id,
    language = language,
    lemma = lemma,
    surface = lemma,
    readingOrIpa = "/$lemma/",
    pos = "noun",
    meaningZh = meaningZh,
    meaningSourceText = meaningZh,
    exampleSentencesJson = "[]",
    sourceName = "test",
    sourceEntryId = "$language-$lemma",
)

private fun summaryFrom(detail: WordDetail) = WordSummary(
    id = detail.id,
    language = detail.language,
    lemma = detail.lemma,
    surface = detail.surface,
    readingOrIpa = detail.readingOrIpa,
    meaningZh = detail.meaningZh,
    meaningSourceText = detail.meaningSourceText,
)

private fun sampleSession(
    language: LearningLanguage,
    word: WordDetail,
): LearningSession {
    val item = com.aiproduct.vocab.ui.study.StudyWordItem.from(word)
    return LearningSession(
        language = language,
        stage = LearningStage.CHOICE,
        words = listOf(LearningWordProgress(item)),
        choiceQueue = listOf(item.id),
        choiceQuestions = mapOf(
            item.id to ChoiceQuestion(
                wordId = item.id,
                prompt = item.lemma,
                options = listOf(
                    MeaningOption("A", item.meaningZh, true),
                    MeaningOption("B", "干扰1", false),
                    MeaningOption("C", "干扰2", false),
                    MeaningOption("D", "干扰3", false),
                ),
            ),
        ),
        spellingOrder = listOf(item.id),
    )
}

private class FakeVocabGateway(
    private val searchResultsByQuery: Map<String, List<WordSummary>> = emptyMap(),
    private val detailsById: MutableMap<Long, WordDetail> = mutableMapOf(),
    private val learningWordsByLanguage: Map<LearningLanguage, List<WordDetail>> = emptyMap(),
    private val distractorMeaningsByLanguage: Map<LearningLanguage, List<String>> = emptyMap(),
    private val dueCountsByLanguage: Map<LearningLanguage, Int> = emptyMap(),
    private val dueWordsByLanguage: Map<LearningLanguage, List<WordDetail>> = emptyMap(),
    starredIds: LinkedHashSet<Long> = linkedSetOf(),
    private var storedLearningDraft: LearningSession? = null,
    private var storedReviewDraft: LearningSession? = null,
    private var preferences: UserPreferences = UserPreferences(),
    private var stats: AppStats = AppStats(),
) : VocabGateway {
    val starredIds = starredIds
    val savedLearningSessions = mutableListOf<List<LearningWordProgress>>()
    val savedReviewSessions = mutableListOf<List<LearningWordProgress>>()
    val savedPreferencesHistory = mutableListOf<UserPreferences>()
    val requestedLearningBands = mutableListOf<LearningBand>()

    override suspend fun search(query: String): List<WordSummary> = searchResultsByQuery[query].orEmpty()

    override suspend fun detail(id: Long): WordDetail? = detailsById[id]

    override suspend fun starredWordIds(): Set<Long> = starredIds.toSet()

    override suspend fun starWord(wordId: Long, nowMillis: Long) {
        starredIds += wordId
    }

    override suspend fun unstarWord(wordId: Long) {
        starredIds -= wordId
    }

    override suspend fun starredWords(): List<WordDetail> = starredIds.mapNotNull(detailsById::get)

    override suspend fun learningWords(language: LearningLanguage, band: LearningBand, limit: Int): List<WordDetail> {
        requestedLearningBands += band
        return learningWordsByLanguage[language].orEmpty().take(limit)
    }

    override suspend fun distractorMeanings(language: LearningLanguage, limit: Int): List<String> =
        distractorMeaningsByLanguage[language].orEmpty().take(limit)

    override suspend fun saveLearningSession(
        language: LearningLanguage,
        progress: List<LearningWordProgress>,
        nowMillis: Long,
    ) {
        savedLearningSessions += progress
        storedLearningDraft = null
    }

    override suspend fun dueCountsByLanguage(nowMillis: Long): Map<LearningLanguage, Int> = dueCountsByLanguage

    override suspend fun dueWords(language: LearningLanguage, nowMillis: Long): List<WordDetail> =
        dueWordsByLanguage[language].orEmpty()

    override suspend fun dueWords(nowMillis: Long): List<WordDetail> = dueWordsByLanguage.values.flatten()

    override suspend fun saveReviewSession(
        progress: List<LearningWordProgress>,
        nowMillis: Long,
    ) {
        savedReviewSessions += progress
        storedReviewDraft = null
    }

    override suspend fun loadLearningDraft(): LearningSession? = storedLearningDraft

    override suspend fun saveLearningDraft(session: LearningSession?) {
        storedLearningDraft = session
    }

    override suspend fun loadReviewDraft(): LearningSession? = storedReviewDraft

    override suspend fun saveReviewDraft(session: LearningSession?) {
        storedReviewDraft = session
    }

    override suspend fun loadPreferences(): UserPreferences = preferences

    override suspend fun savePreferences(preferences: UserPreferences) {
        this.preferences = preferences
        savedPreferencesHistory += preferences
    }

    override suspend fun loadStats(nowMillis: Long): AppStats = stats

    override fun close() = Unit
}
