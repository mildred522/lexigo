package com.aiproduct.vocab.data.starred

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class StarredWordStoreTest {

    @Test
    fun memoryStore_starAndUnstarTracksIdsIndependently() {
        val store = InMemoryStarredWordStore()

        store.starWord(wordId = 11L, nowMillis = 100L)
        store.starWord(wordId = 22L, nowMillis = 200L)

        assertTrue(store.isStarred(11L))
        assertEquals(listOf(22L, 11L), store.starredWordIds())

        store.unstarWord(11L)

        assertFalse(store.isStarred(11L))
        assertEquals(listOf(22L), store.starredWordIds())
    }
}
