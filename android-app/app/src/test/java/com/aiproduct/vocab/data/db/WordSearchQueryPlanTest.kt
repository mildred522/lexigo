package com.aiproduct.vocab.data.db

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class WordSearchQueryPlanTest {
    @Test
    fun buildSearchSpecs_prefixQueryUsesPrefixMatchingAndWildcardFts() {
        val specs = buildSearchSpecs("bo")

        assertEquals(EXACT_SEARCH_SQL.trimIndent(), specs[0].sql.trimIndent())
        assertEquals(listOf("bo", "bo"), specs[0].args.toList())

        assertEquals(PREFIX_SEARCH_SQL.trimIndent(), specs[1].sql.trimIndent())
        assertEquals(listOf("bo%", "bo%"), specs[1].args.toList())

        assertEquals(MEANING_LIKE_SEARCH_SQL.trimIndent(), specs[2].sql.trimIndent())
        assertEquals(listOf("%bo%", "%bo%"), specs[2].args.toList())

        assertEquals(FTS_SEARCH_SQL.trimIndent(), specs[3].sql.trimIndent())
        assertEquals(listOf("bo*"), specs[3].args.toList())
    }

    @Test
    fun buildSearchSpecs_escapesLikeCharactersAndKeepsMeaningLookup() {
        val specs = buildSearchSpecs("100%")

        assertEquals(listOf("100\\%%", "100\\%%"), specs[1].args.toList())
        assertEquals(listOf("%100\\%%", "%100\\%%"), specs[2].args.toList())
    }

    @Test
    fun buildSafeFtsQuery_appendsWildcardPerToken() {
        assertEquals("bonjour*", buildSafeFtsQuery("bonjour"))
        assertEquals("bon* jour*", buildSafeFtsQuery("bon jour"))
        assertEquals(null, buildSafeFtsQuery("!!!"))
    }

    @Test
    fun buildSearchSpecs_alwaysIncludesMeaningSearchForChineseQueries() {
        val specs = buildSearchSpecs("你好")

        assertTrue(specs.any { it.sql.trimIndent() == MEANING_LIKE_SEARCH_SQL.trimIndent() })
        assertEquals(listOf("%你好%", "%你好%"), specs[2].args.toList())
    }
}
