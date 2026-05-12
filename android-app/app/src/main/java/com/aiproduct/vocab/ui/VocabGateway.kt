package com.aiproduct.vocab.ui

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.os.SystemClock
import android.util.Log
import com.aiproduct.vocab.data.db.DictionaryDatabaseProvider
import com.aiproduct.vocab.data.db.WordSearchDao
import com.aiproduct.vocab.data.`package`.DictionaryAssetInstaller
import com.aiproduct.vocab.data.repository.DictionaryRepository
import com.aiproduct.vocab.data.repository.DictionaryRepositoryImpl
import com.aiproduct.vocab.data.session.SessionDraftStore
import com.aiproduct.vocab.data.settings.UserPreferencesStore
import com.aiproduct.vocab.data.starred.StarredWordStore
import com.aiproduct.vocab.data.study.StudyRecordStore
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningSession
import com.aiproduct.vocab.domain.learning.LearningWordProgress
import com.aiproduct.vocab.domain.learning.ReviewOutcome
import com.aiproduct.vocab.domain.model.LearnedWordRecord
import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.WordSummary
import com.aiproduct.vocab.domain.review.ReviewScheduler
import com.aiproduct.vocab.util.measureDurationMillis
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import kotlin.math.max

interface VocabGateway : AutoCloseable {
    suspend fun search(query: String): List<WordSummary>

    suspend fun detail(id: Long): WordDetail?

    suspend fun starredWordIds(): Set<Long>

    suspend fun starWord(wordId: Long, nowMillis: Long)

    suspend fun unstarWord(wordId: Long)

    suspend fun starredWords(): List<WordDetail>

    suspend fun learningWords(language: LearningLanguage, limit: Int = 10): List<WordDetail>

    suspend fun distractorMeanings(language: LearningLanguage, limit: Int = 32): List<String>

    suspend fun saveLearningSession(
        language: LearningLanguage,
        progress: List<LearningWordProgress>,
        nowMillis: Long,
    )

    suspend fun dueCountsByLanguage(nowMillis: Long): Map<LearningLanguage, Int>

    suspend fun dueWords(language: LearningLanguage, nowMillis: Long): List<WordDetail>

    suspend fun dueWords(nowMillis: Long): List<WordDetail>

    suspend fun saveReviewSession(
        progress: List<LearningWordProgress>,
        nowMillis: Long,
    )

    suspend fun loadLearningDraft(): LearningSession?

    suspend fun saveLearningDraft(session: LearningSession?)

    suspend fun loadReviewDraft(): LearningSession?

    suspend fun saveReviewDraft(session: LearningSession?)

    suspend fun loadPreferences(): UserPreferences

    suspend fun savePreferences(preferences: UserPreferences)

    suspend fun loadStats(nowMillis: Long): AppStats

    override fun close()
}

class DictionaryVocabGateway(
    context: Context,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
    private val reviewScheduler: ReviewScheduler = ReviewScheduler(),
) : VocabGateway {
    private val appContext = context.applicationContext
    private val initMutex = Mutex()
    private var clients: GatewayClients? = null

    override suspend fun search(query: String): List<WordSummary> = withContext(ioDispatcher) {
        val measured = measureDurationMillis(SystemClock::elapsedRealtime) {
            clients().repository.search(query)
        }
        Log.i(TAG, "search(\"$query\") finished in ${measured.durationMillis}ms with ${measured.value.size} results")
        measured.value
    }

    override suspend fun detail(id: Long): WordDetail? = withContext(ioDispatcher) {
        val measured = measureDurationMillis(SystemClock::elapsedRealtime) {
            clients().repository.detail(id)
        }
        Log.i(TAG, "detail($id) finished in ${measured.durationMillis}ms (found=${measured.value != null})")
        measured.value
    }

    override suspend fun starredWordIds(): Set<Long> = withContext(ioDispatcher) {
        clients().starredWordStore.starredWordIds().toSet()
    }

    override suspend fun starWord(wordId: Long, nowMillis: Long) = withContext(ioDispatcher) {
        clients().starredWordStore.starWord(wordId = wordId, nowMillis = nowMillis)
    }

    override suspend fun unstarWord(wordId: Long) = withContext(ioDispatcher) {
        clients().starredWordStore.unstarWord(wordId)
    }

    override suspend fun starredWords(): List<WordDetail> = withContext(ioDispatcher) {
        val current = clients()
        current.starredWordStore.starredWordIds()
            .mapNotNull { current.repository.detail(it) }
    }

    override suspend fun learningWords(language: LearningLanguage, limit: Int): List<WordDetail> = withContext(ioDispatcher) {
        val current = clients()
        val starredIds = current.starredWordStore.starredWordIds().toSet()
        val selected = mutableListOf<WordDetail>()
        val selectedPromptKeys = mutableSetOf<String>()
        val rejectedIds = mutableSetOf<Long>()
        val batchSize = max(limit * 12, 80)

        repeat(LEARNING_PICK_ATTEMPTS) { attempt ->
            if (selected.size >= limit) {
                return@repeat
            }
            val candidateIds = current.repository.learningCandidateIds(
                language = language,
                limit = batchSize,
                offset = attempt * batchSize,
            )
                .filterNot(rejectedIds::contains)
                .filterNot(starredIds::contains)
            if (candidateIds.isEmpty()) {
                return@repeat
            }
            val unlearnedIds = current.studyRecordStore.filterUnlearnedWordIds(
                candidates = candidateIds.map { it to language.code },
                language = language.code,
            )
            for (wordId in unlearnedIds) {
                if (selected.size >= limit) break
                val detail = current.repository.detail(wordId) ?: continue
                rejectedIds += wordId
                val promptKey = detail.lemma.trim().lowercase()
                if (!detail.isLearnableForSession(language.code) || promptKey in selectedPromptKeys) {
                    continue
                }
                selected += detail
                selectedPromptKeys += promptKey
            }
        }

        selected
    }

    override suspend fun distractorMeanings(language: LearningLanguage, limit: Int): List<String> = withContext(ioDispatcher) {
            clients().repository.meaningsByLanguage(language.code, limit, 0)
    }

    override suspend fun saveLearningSession(
        language: LearningLanguage,
        progress: List<LearningWordProgress>,
        nowMillis: Long,
    ) = withContext(ioDispatcher) {
        val current = clients()
        val initialStage = reviewScheduler.initialReviewStage()
        progress.forEach { item ->
            current.studyRecordStore.upsert(
                LearnedWordRecord(
                    wordId = item.word.id,
                    language = item.word.language.ifBlank { language.code },
                    choiceCorrectCount = item.choiceCorrectCount,
                    choiceWrongCount = item.choiceWrongCount,
                    spellingCorrectCount = item.spellingCorrectCount,
                    spellingWrongCount = item.spellingWrongCount,
                    hintUsedCount = item.hintUsedCount,
                    reviewStage = initialStage,
                    lastLearnedAtMillis = nowMillis,
                    nextReviewAtMillis = reviewScheduler.nextReviewTimeForStage(initialStage, nowMillis),
                    addedAtMillis = current.studyRecordStore.getLearnedRecord(item.word.id)?.addedAtMillis ?: nowMillis,
                ),
            )
        }
    }

    override suspend fun dueCountsByLanguage(nowMillis: Long): Map<LearningLanguage, Int> = withContext(ioDispatcher) {
        clients().studyRecordStore.dueCountsByLanguage(nowMillis)
            .mapKeys { (language, _) -> language.toLearningLanguage() }
    }

    override suspend fun dueWords(language: LearningLanguage, nowMillis: Long): List<WordDetail> = withContext(ioDispatcher) {
        val current = clients()
        current.studyRecordStore.dueWordIds(nowMillis, language.code)
            .mapNotNull { current.repository.detail(it) }
    }

    override suspend fun dueWords(nowMillis: Long): List<WordDetail> = withContext(ioDispatcher) {
        val current = clients()
        current.studyRecordStore.dueWordIds(nowMillis)
            .mapNotNull { current.repository.detail(it) }
    }

    override suspend fun saveReviewSession(
        progress: List<LearningWordProgress>,
        nowMillis: Long,
    ) = withContext(ioDispatcher) {
        val current = clients()
        progress.forEach { item ->
            val existing = current.studyRecordStore.getLearnedRecord(item.word.id) ?: return@forEach
            val scheduled = reviewScheduler.scheduleLearnedWord(
                current = existing,
                outcome = item.toReviewOutcome(),
                nowMillis = nowMillis,
            )
            current.studyRecordStore.upsert(
                scheduled.copy(
                    language = existing.language.ifBlank { item.word.language },
                    choiceCorrectCount = existing.choiceCorrectCount + item.choiceCorrectCount,
                    choiceWrongCount = existing.choiceWrongCount + item.choiceWrongCount,
                    spellingCorrectCount = existing.spellingCorrectCount + item.spellingCorrectCount,
                    spellingWrongCount = existing.spellingWrongCount + item.spellingWrongCount,
                    hintUsedCount = existing.hintUsedCount + item.hintUsedCount,
                    lastLearnedAtMillis = nowMillis,
                    addedAtMillis = existing.addedAtMillis,
                ),
            )
        }
    }

    override suspend fun loadLearningDraft(): LearningSession? = withContext(ioDispatcher) {
        clients().sessionDraftStore.loadLearningDraft()
    }

    override suspend fun saveLearningDraft(session: LearningSession?) = withContext(ioDispatcher) {
        clients().sessionDraftStore.saveLearningDraft(session)
    }

    override suspend fun loadReviewDraft(): LearningSession? = withContext(ioDispatcher) {
        clients().sessionDraftStore.loadReviewDraft()
    }

    override suspend fun saveReviewDraft(session: LearningSession?) = withContext(ioDispatcher) {
        clients().sessionDraftStore.saveReviewDraft(session)
    }

    override suspend fun loadPreferences(): UserPreferences = withContext(ioDispatcher) {
        clients().preferencesStore.load()
    }

    override suspend fun savePreferences(preferences: UserPreferences) = withContext(ioDispatcher) {
        clients().preferencesStore.save(preferences)
    }

    override suspend fun loadStats(nowMillis: Long): AppStats = withContext(ioDispatcher) {
        val current = clients()
        val learnedByLanguage = current.studyRecordStore.learnedCountsByLanguage()
        val dueByLanguage = current.studyRecordStore.dueCountsByLanguage(nowMillis)
        val zoneId = ZoneId.systemDefault()
        val today = Instant.ofEpochMilli(nowMillis).atZone(zoneId).toLocalDate()
        val startOfToday = today.atStartOfDay(zoneId).toInstant().toEpochMilli()
        val startOfTomorrow = today.plusDays(1).atStartOfDay(zoneId).toInstant().toEpochMilli()
        val languages = (learnedByLanguage.keys + dueByLanguage.keys)
            .map(String::toLearningLanguage)
            .distinct()
        AppStats(
            starredCount = current.starredWordStore.starredCount(),
            streakDays = current.studyRecordStore.activityTimestampsDesc().toStudyStreakDays(zoneId, today),
            todayStudiedCount = current.studyRecordStore.activityCountBetween(
                startMillis = startOfToday,
                endMillisExclusive = startOfTomorrow,
            ),
            dueTodayCount = dueByLanguage.values.sum(),
            byLanguage = languages.associateWith { language ->
                LanguageProgressStats(
                    learnedCount = learnedByLanguage[language.code] ?: 0,
                    dueCount = dueByLanguage[language.code] ?: 0,
                )
            },
        )
    }

    override fun close() {
        val current = clients ?: return
        clients = null
        runCatching { current.studyRecordStore.close() }
        runCatching { current.starredWordStore.close() }
        runCatching { current.database.close() }
    }

    private suspend fun clients(): GatewayClients {
        clients?.let { return it }
        return initMutex.withLock {
            clients?.let { return it }
            val installState = DictionaryAssetInstaller(appContext).ensureInstalled()
            val database = DictionaryDatabaseProvider().open(installState)
            GatewayClients(
                repository = DictionaryRepositoryImpl(WordSearchDao(database)),
                database = database,
                studyRecordStore = StudyRecordStore(appContext),
                starredWordStore = StarredWordStore(appContext),
                sessionDraftStore = SessionDraftStore(appContext),
                preferencesStore = UserPreferencesStore(appContext),
            ).also {
                clients = it
            }
        }
    }
}

private data class GatewayClients(
    val repository: DictionaryRepository,
    val database: SQLiteDatabase,
    val studyRecordStore: StudyRecordStore,
    val starredWordStore: StarredWordStore,
    val sessionDraftStore: SessionDraftStore,
    val preferencesStore: UserPreferencesStore,
)

private fun LearningWordProgress.toReviewOutcome(): ReviewOutcome = when {
    spellingWrongCount > 0 -> ReviewOutcome.FAIL
    choiceWrongCount > 0 || hintUsedCount > 0 -> ReviewOutcome.PARTIAL
    else -> ReviewOutcome.PERFECT
}

private fun String.toLearningLanguage(): LearningLanguage = if (
    equals(LearningLanguage.FRENCH.code, ignoreCase = true) || equals("FR", ignoreCase = true)
) {
    LearningLanguage.FRENCH
} else {
    LearningLanguage.JAPANESE
}

private const val TAG = "DictionaryVocabGateway"
private const val LEARNING_PICK_ATTEMPTS = 6

private suspend fun DictionaryRepository.learningCandidateIds(
    language: LearningLanguage,
    limit: Int,
    offset: Int,
): List<Long> {
    if (language == LearningLanguage.JAPANESE) {
        val leveledIds = leveledWordIdsByLanguage(language.code, limit, offset)
        if (leveledIds.isNotEmpty()) {
            return leveledIds
        }
    }
    return randomWordIdsByLanguage(language.code, limit)
}

private fun WordDetail.isLearnableForSession(language: String): Boolean {
    val lemma = lemma.trim()
    val meaning = meaningZh.ifBlank { meaningSourceText }.trim()
    if (!this.language.equals(language, ignoreCase = true)) return false
    if (lemma.length < 2 || meaning.isBlank()) return false
    if (lemma.any(Char::isWhitespace)) return false
    if (lemma.contains(';') || lemma.contains(',') || lemma.contains('/')) return false
    if (lemma.startsWith("-") || lemma.endsWith("-")) return false
    return true
}

private fun List<Long>.toStudyStreakDays(
    zoneId: ZoneId,
    today: LocalDate,
): Int {
    val activeDays = asSequence()
        .map { Instant.ofEpochMilli(it).atZone(zoneId).toLocalDate() }
        .distinct()
        .toSet()
    if (today !in activeDays) {
        return 0
    }
    var streak = 0
    var cursor = today
    while (cursor in activeDays) {
        streak += 1
        cursor = cursor.minusDays(1)
    }
    return streak
}
