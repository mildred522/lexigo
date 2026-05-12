package com.aiproduct.vocab.domain.learning

class LearningSessionReducer {
    fun submitChoice(
        session: LearningSession,
        selectedMeaning: String,
    ): LearningSession {
        val current = session.currentChoiceWord ?: return session
        val question = session.currentChoiceQuestion ?: return session
        val isCorrect = question.options.any { it.meaningZh == selectedMeaning && it.isCorrect }
        val updatedWords = session.words.map { progress ->
            if (progress.word.id != current.word.id) {
                progress
            } else if (isCorrect) {
                progress.copy(choiceCorrectCount = progress.choiceCorrectCount + 1)
            } else {
                progress.copy(choiceWrongCount = progress.choiceWrongCount + 1)
            }
        }
        val remaining = session.choiceQueue.drop(1).toMutableList()
        if (!isCorrect) {
            remaining += current.word.id
        }
        return session.copy(
            words = updatedWords,
            choiceQueue = remaining,
            stage = if (remaining.isEmpty()) LearningStage.SPELLING else LearningStage.CHOICE,
            currentHint = null,
            feedback = SessionFeedback(
                wordId = current.word.id,
                stage = LearningStage.CHOICE,
                isCorrect = isCorrect,
                showNextSummary = false,
            ),
            lastChoiceCorrect = isCorrect,
            lastSpellingCorrect = null,
        )
    }

    fun submitSpelling(
        session: LearningSession,
        answer: String,
    ): LearningSession {
        val current = session.currentSpellingWord ?: return session
        return submitSpellingResult(
            session = session,
            isCorrect = answer.trim() == current.word.lemma.trim(),
        )
    }

    fun submitSpellingResult(
        session: LearningSession,
        isCorrect: Boolean,
    ): LearningSession {
        val current = session.currentSpellingWord ?: return session
        val updatedWords = session.words.map { progress ->
            if (progress.word.id != current.word.id) {
                progress
            } else if (isCorrect) {
                progress.copy(spellingCorrectCount = progress.spellingCorrectCount + 1)
            } else {
                progress.copy(spellingWrongCount = progress.spellingWrongCount + 1)
            }
        }
        val nextIndex = session.spellingIndex + 1
        return session.copy(
            words = updatedWords,
            spellingIndex = nextIndex,
            stage = if (nextIndex >= session.spellingOrder.size) LearningStage.SUMMARY else LearningStage.SPELLING,
            currentHint = null,
            feedback = SessionFeedback(
                wordId = current.word.id,
                stage = LearningStage.SPELLING,
                isCorrect = isCorrect,
                showNextSummary = nextIndex >= session.spellingOrder.size,
            ),
            lastChoiceCorrect = null,
            lastSpellingCorrect = isCorrect,
        )
    }

    fun registerHint(
        session: LearningSession,
        hint: String,
    ): LearningSession {
        val current = session.currentSpellingWord ?: return session
        val updatedWords = session.words.map { progress ->
            if (progress.word.id != current.word.id) {
                progress
            } else {
                progress.copy(hintUsedCount = progress.hintUsedCount + 1)
            }
        }
        return session.copy(
            words = updatedWords,
            currentHint = hint,
        )
    }

    fun skipCurrentWord(session: LearningSession): LearningSession {
        if (session.feedback != null || session.stage == LearningStage.SUMMARY) {
            return session
        }
        val currentWordId = when (session.stage) {
            LearningStage.CHOICE -> session.choiceQueue.firstOrNull()
            LearningStage.SPELLING -> session.spellingOrder.getOrNull(session.spellingIndex)
            LearningStage.LANGUAGE_PICKER,
            LearningStage.SUMMARY -> null
        } ?: return session

        val updatedWords = session.words.filterNot { it.word.id == currentWordId }
        val updatedChoiceQueue = session.choiceQueue.filterNot { it == currentWordId }
        val updatedSpellingOrder = session.spellingOrder.filterNot { it == currentWordId }
        val updatedSpellingIndex = when (session.stage) {
            LearningStage.SPELLING -> session.spellingIndex.coerceAtMost(updatedSpellingOrder.size)
            else -> session.spellingIndex.coerceAtMost(updatedSpellingOrder.size)
        }
        val nextStage = when {
            updatedWords.isEmpty() -> LearningStage.SUMMARY
            updatedChoiceQueue.isNotEmpty() -> LearningStage.CHOICE
            updatedSpellingIndex < updatedSpellingOrder.size -> LearningStage.SPELLING
            else -> LearningStage.SUMMARY
        }

        return session.copy(
            stage = nextStage,
            words = updatedWords,
            choiceQueue = updatedChoiceQueue,
            spellingOrder = updatedSpellingOrder,
            spellingIndex = updatedSpellingIndex,
            currentHint = null,
            feedback = null,
            lastChoiceCorrect = null,
            lastSpellingCorrect = null,
        )
    }

    fun continueAfterFeedback(session: LearningSession): LearningSession = session.copy(
        feedback = null,
        currentHint = null,
    )
}
