package com.aiproduct.vocab.ui.search

import com.aiproduct.vocab.domain.model.WordSummary
import com.aiproduct.vocab.domain.usecase.SearchWordsUseCase
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class SearchViewModelTest {
    @Test
    fun onQueryChanged_nonBlankQuery_updatesResults() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val viewModel = SearchViewModel(
                searchWords = SearchWordsUseCase { query ->
                    listOf(
                        WordSummary(
                            id = 1L,
                            language = "fr",
                            lemma = query,
                            surface = query,
                            readingOrIpa = "/$query/",
                            meaningZh = "hello zh",
                            meaningSourceText = "hello",
                        ),
                    )
                },
                searchDispatcher = dispatcher,
            )

            viewModel.onQueryChanged("bonjour")
            advanceUntilIdle()

            val state = viewModel.uiState.value
            assertEquals("bonjour", state.query)
            assertFalse(state.isLoading)
            assertEquals(1, state.results.size)
            assertEquals("bonjour", state.results.first().lemma)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun onQueryChanged_blankQuery_clearsResults() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val viewModel = SearchViewModel(
                searchWords = SearchWordsUseCase {
                    listOf(
                        WordSummary(
                            id = 2L,
                            language = "en",
                            lemma = "hello",
                            surface = "hello",
                            readingOrIpa = "/hello/",
                            meaningZh = "hello zh",
                            meaningSourceText = "hello",
                        ),
                    )
                },
                searchDispatcher = dispatcher,
            )
            viewModel.onQueryChanged("hello")
            advanceUntilIdle()

            viewModel.onQueryChanged("  ")
            advanceUntilIdle()

            val state = viewModel.uiState.value
            assertEquals("  ", state.query)
            assertFalse(state.isLoading)
            assertTrue(state.results.isEmpty())
        } finally {
            Dispatchers.resetMain()
        }
    }

    @Test
    fun onQueryChanged_rapidInput_keepsLatestResultAndClearsLoading() = runTest {
        val dispatcher = StandardTestDispatcher(testScheduler)
        Dispatchers.setMain(dispatcher)
        try {
            val deferredByQuery = mutableMapOf<String, CompletableDeferred<List<WordSummary>>>()
            val viewModel = SearchViewModel(
                searchWords = SearchWordsUseCase { query ->
                    deferredByQuery.getValue(query).await()
                },
                searchDispatcher = dispatcher,
            )

            val firstDeferred = CompletableDeferred<List<WordSummary>>()
            val secondDeferred = CompletableDeferred<List<WordSummary>>()
            deferredByQuery["a"] = firstDeferred
            deferredByQuery["ab"] = secondDeferred

            viewModel.onQueryChanged("a")
            runCurrent()
            assertTrue(viewModel.uiState.value.isLoading)

            viewModel.onQueryChanged("ab")
            secondDeferred.complete(
                listOf(
                    WordSummary(
                        id = 20L,
                        language = "en",
                        lemma = "ab",
                        surface = "ab",
                        readingOrIpa = "/ab/",
                        meaningZh = "ab zh",
                        meaningSourceText = "ab src",
                    ),
                ),
            )
            advanceUntilIdle()

            firstDeferred.complete(
                listOf(
                    WordSummary(
                        id = 10L,
                        language = "en",
                        lemma = "a",
                        surface = "a",
                        readingOrIpa = "/a/",
                        meaningZh = "a zh",
                        meaningSourceText = "a src",
                    ),
                ),
            )
            advanceUntilIdle()

            val state = viewModel.uiState.value
            assertEquals("ab", state.query)
            assertFalse(state.isLoading)
            assertEquals(listOf("ab"), state.results.map { it.lemma })
        } finally {
            Dispatchers.resetMain()
        }
    }
}
