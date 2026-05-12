package com.aiproduct.vocab.ui.debug

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class DebugLogEntry(
    val timestamp: String,
    val tag: String,
    val message: String,
)

object AppDebugLog {
    private const val MAX_ENTRIES = 160
    private val timestampFormat = SimpleDateFormat("HH:mm:ss.SSS", Locale.US)
    private val _entries = MutableStateFlow<List<DebugLogEntry>>(emptyList())
    val entries: StateFlow<List<DebugLogEntry>> = _entries.asStateFlow()

    fun add(tag: String, message: String) {
        val entry = DebugLogEntry(
            timestamp = timestampFormat.format(Date()),
            tag = tag,
            message = message,
        )
        _entries.update { current -> (listOf(entry) + current).take(MAX_ENTRIES) }
    }

    fun clear() {
        _entries.value = emptyList()
    }
}
