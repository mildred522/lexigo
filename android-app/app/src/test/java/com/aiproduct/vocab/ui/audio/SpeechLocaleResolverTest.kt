package com.aiproduct.vocab.ui.audio

import org.junit.Assert.assertEquals
import org.junit.Test

class SpeechLocaleResolverTest {
    @Test
    fun speechLocaleFor_returnsExpectedLocalesForSupportedLanguages() {
        assertEquals("ja-JP", speechLocaleFor("ja").toLanguageTag())
        assertEquals("fr-FR", speechLocaleFor("fr").toLanguageTag())
        assertEquals("en-US", speechLocaleFor("unknown").toLanguageTag())
    }
}
