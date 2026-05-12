package com.aiproduct.vocab.ui.personalization

import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class DailyCoverCatalogTest {
    @Test
    fun coverFor_sameDateIsStable() {
        val date = LocalDate.of(2026, 4, 4)

        val first = DailyCoverCatalog.coverFor(date)
        val second = DailyCoverCatalog.coverFor(date)

        assertEquals(first, second)
    }

    @Test
    fun coverFor_differentDatesRotateThroughCatalog() {
        val first = DailyCoverCatalog.coverFor(LocalDate.of(2026, 4, 4))
        val second = DailyCoverCatalog.coverFor(LocalDate.of(2026, 4, 5))

        assertNotEquals(first, second)
    }
}
