package com.aiproduct.vocab.domain.learning

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class JapaneseReadingRomanizerTest {
    @Test
    fun romanizeHiraganaReading() {
        assertEquals("gakkou", JapaneseReadingRomanizer.romanizeOrNull("がっこう"))
        assertEquals("nihon", JapaneseReadingRomanizer.romanizeOrNull("にほん"))
    }

    @Test
    fun romanizeKatakanaReading() {
        assertEquals("konpyuutaa", JapaneseReadingRomanizer.romanizeOrNull("コンピューター"))
    }

    @Test
    fun returnsNullForNonKanaReadings() {
        assertNull(JapaneseReadingRomanizer.romanizeOrNull("bonjour"))
        assertNull(JapaneseReadingRomanizer.romanizeOrNull("/bɔ̃.ʒuʁ/"))
    }
}
