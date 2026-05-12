package com.aiproduct.vocab.ui.search

import com.aiproduct.vocab.domain.model.resolveDisplayMeaning
import com.aiproduct.vocab.domain.model.WordSummary
import com.aiproduct.vocab.ui.study.StudyWordItem

data class SearchUiState(
    val query: String = "",
    val isLoading: Boolean = false,
    val results: List<SearchResultItem> = emptyList(),
    val selectedDetail: StudyWordItem? = null,
    val isSelectedDetailStarred: Boolean = false,
    val isDetailLoading: Boolean = false,
)

data class SearchResultItem(
    val id: Long,
    val lemma: String,
    val readingOrIpa: String,
    val language: String,
    val meaningZh: String,
    val meaningSourceText: String,
    val isStarred: Boolean = false,
) {
    companion object {
        fun from(
            summary: WordSummary,
            isStarred: Boolean = false,
        ): SearchResultItem = SearchResultItem(
            id = summary.id,
            lemma = summary.lemma,
            readingOrIpa = summary.readingOrIpa,
            language = summary.language,
            meaningZh = resolveDisplayMeaning(
                meaningZh = summary.meaningZh,
                meaningSourceText = summary.meaningSourceText,
            ),
            meaningSourceText = summary.meaningSourceText,
            isStarred = isStarred,
        )
    }
}
