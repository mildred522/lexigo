package com.aiproduct.vocab.data.`package`

import android.content.res.AssetManager
import java.io.File
import java.io.InputStream
import org.json.JSONException
import org.json.JSONObject

class DictionaryManifestReader {
    fun read(inputStream: InputStream): DictionaryPackageManifest {
        return inputStream.bufferedReader().use { reader ->
            read(reader.readText())
        }
    }

    fun read(file: File): DictionaryPackageManifest {
        return file.inputStream().use(::read)
    }

    fun readFromAssets(
        assetManager: AssetManager,
        assetPath: String = "manifest.json",
    ): DictionaryPackageManifest {
        return assetManager.open(assetPath).use(::read)
    }

    fun read(json: String): DictionaryPackageManifest {
        val root = try {
            JSONObject(json)
        } catch (error: JSONException) {
            throw IllegalArgumentException("Malformed dictionary manifest JSON.", error)
        }

        val schemaVersion = root.requireInt("schema_version")
        if (schemaVersion != SUPPORTED_SCHEMA_VERSION) {
            throw IllegalArgumentException(
                "Unsupported dictionary schema_version: $schemaVersion. " +
                    "Supported: $SUPPORTED_SCHEMA_VERSION.",
            )
        }

        val dbFilename = root.requireString("db_filename").also {
            if (it.isBlank()) {
                throw IllegalArgumentException("Incompatible dictionary manifest: db_filename must not be blank.")
            }
        }
        val entryCount = root.requireInt("entry_count")
        val dbByteCount = root.optionalLong("db_byte_count")
        val searchCapabilities = root.requireObject("search_capabilities")
        val fts = searchCapabilities.requireBoolean("fts")

        return DictionaryPackageManifest(
            schemaVersion = schemaVersion,
            dbFilename = dbFilename,
            entryCount = entryCount,
            dbByteCount = dbByteCount,
            searchCapabilities = DictionaryPackageManifest.SearchCapabilities(fts = fts),
        )
    }

    private fun JSONObject.requireInt(key: String): Int = try {
        getInt(key)
    } catch (error: JSONException) {
        throw IllegalArgumentException("Incompatible dictionary manifest: missing or invalid '$key'.", error)
    }

    private fun JSONObject.requireString(key: String): String = try {
        getString(key)
    } catch (error: JSONException) {
        throw IllegalArgumentException("Incompatible dictionary manifest: missing or invalid '$key'.", error)
    }

    private fun JSONObject.requireObject(key: String): JSONObject = try {
        getJSONObject(key)
    } catch (error: JSONException) {
        throw IllegalArgumentException("Incompatible dictionary manifest: missing or invalid '$key'.", error)
    }

    private fun JSONObject.requireBoolean(key: String): Boolean = try {
        getBoolean(key)
    } catch (error: JSONException) {
        throw IllegalArgumentException("Incompatible dictionary manifest: missing or invalid 'search_capabilities.$key'.", error)
    }

    private fun JSONObject.optionalLong(key: String): Long? = if (has(key)) {
        try {
            getLong(key)
        } catch (error: JSONException) {
            throw IllegalArgumentException("Incompatible dictionary manifest: invalid '$key'.", error)
        }
    } else {
        null
    }

    companion object {
        private const val SUPPORTED_SCHEMA_VERSION = 1
    }
}
