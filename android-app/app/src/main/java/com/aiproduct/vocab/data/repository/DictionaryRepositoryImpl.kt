package com.aiproduct.vocab.data.repository

import com.aiproduct.vocab.data.db.WordSearchDao
import com.aiproduct.vocab.domain.learning.LearningBand
import com.aiproduct.vocab.domain.model.WordDetail
import com.aiproduct.vocab.domain.model.WordSummary

class DictionaryRepositoryImpl(
    private val wordSearchDao: WordSearchDao,
) : DictionaryRepository {
    override suspend fun search(query: String): List<WordSummary> = wordSearchDao.search(query)

    override suspend fun detail(id: Long): WordDetail? = wordSearchDao.detail(id)

    override suspend fun countWordsByLanguage(language: String): Int = wordSearchDao.countWordsByLanguage(language)

    override suspend fun wordIdsByLanguage(language: String, limit: Int, offset: Int): List<Long> =
        wordSearchDao.wordIdsByLanguage(language, limit, offset)

    override suspend fun randomWordIdsByLanguage(language: String, limit: Int): List<Long> =
        wordSearchDao.randomWordIdsByLanguage(language, limit)

    override suspend fun leveledWordIdsByLanguage(language: String, band: LearningBand, limit: Int, offset: Int): List<Long> =
        wordSearchDao.leveledWordIdsByLanguage(language, band, limit, offset)

    override suspend fun meaningsByLanguage(language: String, limit: Int, offset: Int): List<String> =
        wordSearchDao.meaningsByLanguage(language, limit, offset)
}
