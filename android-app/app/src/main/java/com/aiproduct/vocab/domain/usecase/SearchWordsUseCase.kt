package com.aiproduct.vocab.domain.usecase

import com.aiproduct.vocab.domain.model.WordSummary

fun interface SearchWordsUseCase {
    suspend operator fun invoke(query: String): List<WordSummary>
}
