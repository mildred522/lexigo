package com.aiproduct.vocab.data.`package`

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class DictionaryManifestReaderTest {

    @Test
    fun read_parsesRequiredFieldsFromManifestJson() {
        val json = """
            {
              "schema_version": 1,
              "db_filename": "dictionary.db",
              "entry_count": 2359088,
              "search_capabilities": {
                "exact_lookup": true,
                "fts": true
              }
            }
        """.trimIndent()

        val manifest = DictionaryManifestReader().read(json.byteInputStream())

        assertEquals(1, manifest.schemaVersion)
        assertEquals("dictionary.db", manifest.dbFilename)
        assertEquals(2359088, manifest.entryCount)
        assertTrue(manifest.searchCapabilities.fts)
    }

    @Test
    fun read_throwsClearErrorWhenRequiredFieldIsMissing() {
        val json = """
            {
              "schema_version": 1,
              "db_filename": "dictionary.db",
              "entry_count": 2359088,
              "search_capabilities": {}
            }
        """.trimIndent()

        val error = assertThrows(IllegalArgumentException::class.java) {
            DictionaryManifestReader().read(json.byteInputStream())
        }
        assertTrue(error.message!!.contains("search_capabilities.fts"))
    }

    @Test
    fun read_throwsWhenSchemaVersionIsUnsupported() {
        val json = """
            {
              "schema_version": 999,
              "db_filename": "dictionary.db",
              "entry_count": 2359088,
              "search_capabilities": {
                "fts": true
              }
            }
        """.trimIndent()

        val error = assertThrows(IllegalArgumentException::class.java) {
            DictionaryManifestReader().read(json.byteInputStream())
        }

        assertTrue(error.message!!.contains("Unsupported dictionary schema_version"))
    }

    @Test
    fun read_throwsClearErrorWhenManifestJsonIsMalformed() {
        val malformedJson = "{"

        val error = assertThrows(IllegalArgumentException::class.java) {
            DictionaryManifestReader().read(malformedJson.byteInputStream())
        }

        assertTrue(error.message!!.contains("Malformed dictionary manifest"))
    }

    @Test
    fun read_throwsClearErrorWhenEntryCountIsMissing() {
        val json = """
            {
              "schema_version": 1,
              "db_filename": "dictionary.db",
              "search_capabilities": {
                "fts": true
              }
            }
        """.trimIndent()

        val error = assertThrows(IllegalArgumentException::class.java) {
            DictionaryManifestReader().read(json.byteInputStream())
        }

        assertTrue(error.message!!.contains("entry_count"))
    }
}
