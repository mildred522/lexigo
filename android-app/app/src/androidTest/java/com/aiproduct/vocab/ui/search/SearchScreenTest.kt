package com.aiproduct.vocab.ui.search

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.aiproduct.vocab.ui.study.StudyWordItem
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SearchScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun rendersSearchResultItem() {
        val uiState = SearchUiState(
            query = "bonjour",
            isLoading = false,
            results = listOf(
                SearchResultItem(
                    id = 1L,
                    lemma = "bonjour",
                    readingOrIpa = "/bɔ̃.ʒuʁ/",
                    language = "fr",
                    meaningZh = "你好",
                    meaningSourceText = "hello",
                ),
            ),
        )

        rule.setContent {
            SearchScreen(
                uiState = uiState,
                onQueryChanged = {},
                onOpenDetail = {},
                onDismissDetail = {},
                onToggleStar = {},
                onSpeak = {},
            )
        }

        rule.onNodeWithTag("search_input").fetchSemanticsNode()
        rule.onNodeWithText("bonjour").fetchSemanticsNode()
        rule.onNodeWithText("/bɔ̃.ʒuʁ/").fetchSemanticsNode()
        rule.onNodeWithText("fr").fetchSemanticsNode()
        rule.onNodeWithText("你好").fetchSemanticsNode()
        rule.onNodeWithText("hello").fetchSemanticsNode()
    }
}
