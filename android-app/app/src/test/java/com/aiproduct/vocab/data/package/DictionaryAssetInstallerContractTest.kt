package com.aiproduct.vocab.data.`package`

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DictionaryAssetInstallerContractTest {

    @Test
    fun hasSameInstallContract_returnsFalseWhenEntryCountChanges() {
        val installedManifest = DictionaryPackageManifest(
            schemaVersion = 1,
            dbFilename = "dictionary.db",
            entryCount = 3,
            searchCapabilities = DictionaryPackageManifest.SearchCapabilities(fts = true),
        )
        val assetManifest = DictionaryPackageManifest(
            schemaVersion = 1,
            dbFilename = "dictionary.db",
            entryCount = 2_359_088,
            searchCapabilities = DictionaryPackageManifest.SearchCapabilities(fts = true),
        )

        assertFalse(hasSameInstallContract(installedManifest, assetManifest))
    }

    @Test
    fun hasSameInstallContract_returnsTrueWhenInstallContractMatches() {
        val manifest = DictionaryPackageManifest(
            schemaVersion = 1,
            dbFilename = "dictionary.db",
            entryCount = 2_359_088,
            searchCapabilities = DictionaryPackageManifest.SearchCapabilities(fts = true),
        )

        assertTrue(hasSameInstallContract(manifest, manifest))
    }
}
