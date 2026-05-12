package com.aiproduct.vocab.data.repository

import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.WordSummary

interface DictionaryRepository {
    suspend fun search(query: String): List<WordSummary>

    suspend fun detail(id: Long): WordDetail?

    suspend fun countWordsByLanguage(language: String): Int

    suspend fun wordIdsByLanguage(language: String, limit: Int, offset: Int): List<Long>

    suspend fun randomWordIdsByLanguage(language: String, limit: Int): List<Long>

    suspend fun leveledWordIdsByLanguage(language: String, limit: Int, offset: Int): List<Long>

    suspend fun meaningsByLanguage(language: String, limit: Int, offset: Int): List<String>
}
