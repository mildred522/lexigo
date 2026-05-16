package com.aiproduct.vocab.data.session

import android.content.Context
import com.aiproduct.vocab.domain.learning.ChoiceQuestion
import com.aiproduct.vocab.domain.learning.LearningLanguage
import com.aiproduct.vocab.domain.learning.LearningSession
import com.aiproduct.vocab.domain.learning.LearningStage
import com.aiproduct.vocab.domain.learning.LearningWordProgress
import com.aiproduct.vocab.domain.learning.MeaningOption
import com.aiproduct.vocab.domain.learning.SessionFeedback
import com.aiproduct.vocab.domain.model.ExampleSentence
import com.aiproduct.vocab.ui.study.StudyWordItem
import org.json.JSONArray
import org.json.JSONObject

class SessionDraftStore(
    context: Context,
) {
    private val prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    fun loadLearningDraft(): LearningSession? = load(KEY_LEARNING_DRAFT)

    fun saveLearningDraft(session: LearningSession?) {
        save(KEY_LEARNING_DRAFT, session)
    }

    fun loadReviewDraft(): LearningSession? = load(KEY_REVIEW_DRAFT)

    fun saveReviewDraft(session: LearningSession?) {
        save(KEY_REVIEW_DRAFT, session)
    }

    private fun load(key: String): LearningSession? {
        val raw = prefs.getString(key, null) ?: return null
        return runCatching { raw.toLearningSession() }.getOrNull()
    }

    private fun save(
        key: String,
        session: LearningSession?,
    ) {
        if (session == null) {
            prefs.edit().remove(key).apply()
            return
        }
        prefs.edit().putString(key, session.toJson().toString()).apply()
    }

    companion object {
        private const val PREFS_NAME = "session-drafts"
        private const val KEY_LEARNING_DRAFT = "learning_draft"
        private const val KEY_REVIEW_DRAFT = "review_draft"
    }
}

private fun LearningSession.toJson(): JSONObject = JSONObject().apply {
    put("language", language.name)
    put("stage", stage.name)
    put("words", JSONArray().apply {
        words.forEach { progress ->
            put(progress.toJson())
        }
    })
    put("choice_queue", JSONArray(choiceQueue))
    put("choice_questions", JSONObject().apply {
        choiceQuestions.forEach { (wordId, question) ->
            put(wordId.toString(), question.toJson())
        }
    })
    put("spelling_order", JSONArray(spellingOrder))
    put("spelling_index", spellingIndex)
    put("current_hint", currentHint)
    feedback?.let { put("feedback", it.toJson()) }
    put("last_choice_correct", lastChoiceCorrect)
    put("last_spelling_correct", lastSpellingCorrect)
}

private fun LearningWordProgress.toJson(): JSONObject = JSONObject().apply {
    put("word", word.toJson())
    put("choice_correct_count", choiceCorrectCount)
    put("choice_wrong_count", choiceWrongCount)
    put("spelling_correct_count", spellingCorrectCount)
    put("spelling_wrong_count", spellingWrongCount)
    put("hint_used_count", hintUsedCount)
}

private fun StudyWordItem.toJson(): JSONObject = JSONObject().apply {
    put("id", id)
    put("language", language)
    put("lemma", lemma)
    put("surface", surface)
    put("reading_or_ipa", readingOrIpa)
    put("pos", pos)
    put("meaning_zh", meaningZh)
    put("meaning_source_text", meaningSourceText)
    put("examples", JSONArray().apply {
        examples.forEach { example ->
            put(JSONObject().apply {
                put("sentence_foreign", example.sentenceForeign)
                put("sentence_zh", example.sentenceZh)
            })
        }
    })
    put("source_name", sourceName)
    put("source_entry_id", sourceEntryId)
}

private fun ChoiceQuestion.toJson(): JSONObject = JSONObject().apply {
    put("word_id", wordId)
    put("prompt", prompt)
    put("options", JSONArray().apply {
        options.forEach { option -> put(option.toJson()) }
    })
}

private fun MeaningOption.toJson(): JSONObject = JSONObject().apply {
    put("label", label)
    put("meaning_zh", meaningZh)
    put("is_correct", isCorrect)
    put("value", value)
    put("secondary_text", secondaryText)
}

private fun SessionFeedback.toJson(): JSONObject = JSONObject().apply {
    put("word_id", wordId)
    put("stage", stage.name)
    put("is_correct", isCorrect)
    put("show_next_summary", showNextSummary)
}

private fun String.toLearningSession(): LearningSession {
    val root = JSONObject(this)
    val wordsArray = root.getJSONArray("words")
    val words = buildList {
        for (index in 0 until wordsArray.length()) {
            add(wordsArray.getJSONObject(index).toLearningWordProgress())
        }
    }
    val questionsJson = root.getJSONObject("choice_questions")
    val questions = buildMap {
        questionsJson.keys().forEach { key ->
            put(key.toLong(), questionsJson.getJSONObject(key).toChoiceQuestion())
        }
    }
    return LearningSession(
        language = LearningLanguage.valueOf(root.getString("language")),
        stage = LearningStage.valueOf(root.getString("stage")),
        words = words,
        choiceQueue = root.getJSONArray("choice_queue").toLongList(),
        choiceQuestions = questions,
        spellingOrder = root.getJSONArray("spelling_order").toLongList(),
        spellingIndex = root.optInt("spelling_index", 0),
        currentHint = root.optString("current_hint").takeIf { it.isNotBlank() },
        feedback = root.optJSONObject("feedback")?.toSessionFeedback(),
        lastChoiceCorrect = root.optBooleanOrNull("last_choice_correct"),
        lastSpellingCorrect = root.optBooleanOrNull("last_spelling_correct"),
    )
}

private fun JSONObject.toLearningWordProgress(): LearningWordProgress = LearningWordProgress(
    word = getJSONObject("word").toStudyWordItem(),
    choiceCorrectCount = optInt("choice_correct_count", 0),
    choiceWrongCount = optInt("choice_wrong_count", 0),
    spellingCorrectCount = optInt("spelling_correct_count", 0),
    spellingWrongCount = optInt("spelling_wrong_count", 0),
    hintUsedCount = optInt("hint_used_count", 0),
)

private fun JSONObject.toStudyWordItem(): StudyWordItem = StudyWordItem(
    id = getLong("id"),
    language = optString("language"),
    lemma = optString("lemma"),
    surface = optString("surface"),
    readingOrIpa = optString("reading_or_ipa"),
    pos = optString("pos"),
    meaningZh = optString("meaning_zh"),
    meaningSourceText = optString("meaning_source_text"),
    examples = getJSONArray("examples").toExampleSentences(),
    sourceName = optString("source_name"),
    sourceEntryId = optString("source_entry_id"),
)

private fun JSONObject.toChoiceQuestion(): ChoiceQuestion = ChoiceQuestion(
    wordId = getLong("word_id"),
    prompt = optString("prompt"),
    options = getJSONArray("options").toMeaningOptions(),
)

private fun JSONObject.toSessionFeedback(): SessionFeedback = SessionFeedback(
    wordId = getLong("word_id"),
    stage = LearningStage.valueOf(getString("stage")),
    isCorrect = getBoolean("is_correct"),
    showNextSummary = optBoolean("show_next_summary", false),
)

private fun JSONArray.toMeaningOptions(): List<MeaningOption> = buildList {
    for (index in 0 until length()) {
        val option = getJSONObject(index)
        add(
            MeaningOption(
                label = option.optString("label"),
                meaningZh = option.optString("meaning_zh"),
                isCorrect = option.optBoolean("is_correct", false),
                value = option.optString("value", option.optString("meaning_zh")),
                secondaryText = option.optString("secondary_text").takeIf { it.isNotBlank() },
            ),
        )
    }
}

private fun JSONArray.toLongList(): List<Long> = buildList {
    for (index in 0 until length()) {
        add(getLong(index))
    }
}

private fun JSONArray.toExampleSentences(): List<ExampleSentence> = buildList {
    for (index in 0 until length()) {
        val item = getJSONObject(index)
        add(
            ExampleSentence(
                sentenceForeign = item.optString("sentence_foreign"),
                sentenceZh = item.optString("sentence_zh"),
            ),
        )
    }
}

private fun JSONObject.optBooleanOrNull(key: String): Boolean? = if (has(key) && !isNull(key)) {
    getBoolean(key)
} else {
    null
}
