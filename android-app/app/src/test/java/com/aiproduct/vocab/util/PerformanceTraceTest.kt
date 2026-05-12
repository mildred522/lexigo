package com.aiproduct.vocab.util

import org.junit.Assert.assertEquals
import org.junit.Test

class PerformanceTraceTest {
    @Test
    fun measureDurationMillis_returnsValueAndElapsedTime() {
        val timeline = ArrayDeque(listOf(1_000L, 1_145L))

        val measured = measureDurationMillis(
            nowMillis = { timeline.removeFirst() },
        ) {
            "ready"
        }

        assertEquals("ready", measured.value)
        assertEquals(145L, measured.durationMillis)
    }
}
