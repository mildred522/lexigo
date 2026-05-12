package com.aiproduct.vocab.ui.search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.aiproduct.vocab.domain.usecase.SearchWordsUseCase
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class SearchViewModel(
    private val searchWords: SearchWordsUseCase,
    private val searchDispatcher: CoroutineDispatcher = Dispatchers.IO,
    private val onClearedAction: () -> Unit = {},
) : ViewModel() {
    private val _uiState = MutableStateFlow(SearchUiState())
    val uiState: StateFlow<SearchUiState> = _uiState.asStateFlow()

    private var searchJob: Job? = null

    fun onQueryChanged(query: String) {
        _uiState.update { it.copy(query = query) }
        searchJob?.cancel()

        if (query.isBlank()) {
            _uiState.update { it.copy(isLoading = false, results = emptyList()) }
            return
        }

        searchJob = viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, results = emptyList()) }
            try {
                val results = withContext(searchDispatcher) { searchWords(query) }
                    .map(SearchResultItem::from)
                _uiState.update { current ->
                    if (current.query != query) {
                        current
                    } else {
                        current.copy(isLoading = false, results = results)
                    }
                }
            } catch (cancellationException: CancellationException) {
                throw cancellationException
            } catch (_: Throwable) {
                _uiState.update { current ->
                    if (current.query != query) {
                        current
                    } else {
                        current.copy(isLoading = false, results = emptyList())
                    }
                }
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        runCatching { onClearedAction() }
    }
}
