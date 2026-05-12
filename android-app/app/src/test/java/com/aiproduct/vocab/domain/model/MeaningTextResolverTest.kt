package com.aiproduct.vocab.domain.model

import org.junit.Assert.assertEquals
import org.junit.Test

class MeaningTextResolverTest {
    @Test
    fun resolveDisplayMeaning_prefersChineseMeaningWhenPresent() {
        assertEquals(
            "你好",
            resolveDisplayMeaning(
                meaningZh = " 你好 ",
                meaningSourceText = "hello",
            ),
        )
    }

    @Test
    fun resolveDisplayMeaning_fallsBackToSourceTextWhenChineseMeaningMissing() {
        assertEquals(
            "hello",
            resolveDisplayMeaning(
                meaningZh = " ",
                meaningSourceText = " hello ",
            ),
        )
    }
}
