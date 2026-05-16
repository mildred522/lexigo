package com.aiproduct.vocab.data.`package`

data class DictionaryPackageManifest(
    val schemaVersion: Int,
    val dbFilename: String,
    val entryCount: Int,
    val dbByteCount: Long? = null,
    val searchCapabilities: SearchCapabilities,
) {
    data class SearchCapabilities(
        val fts: Boolean,
    )
}
