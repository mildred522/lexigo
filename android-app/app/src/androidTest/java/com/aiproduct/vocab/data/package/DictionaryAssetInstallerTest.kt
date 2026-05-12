package com.aiproduct.vocab.data.`package`

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.aiproduct.vocab.data.db.DictionaryDatabaseProvider
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.After
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DictionaryAssetInstallerTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val installDir = File(context.filesDir, "dictionary")

    @Before
    fun setUp() {
        installDir.deleteRecursively()
    }

    @After
    fun tearDown() {
        installDir.deleteRecursively()
    }

    @Test
    fun ensureInstalled_copiesAssetsAndSkipsSecondInstall() {
        val installer = DictionaryAssetInstaller(context)

        val first = installer.ensureInstalled()

        assertTrue(first.didInstall)
        assertTrue(first.installDir.exists())
        assertTrue(first.databaseFile.exists())
        assertTrue(first.manifestFile.exists())
        assertEquals(first.packageManifest.dbFilename, first.databaseFile.name)
        val expectedManifest = context.assets.open("manifest.json").bufferedReader().use { it.readText() }
        val installedManifest = first.manifestFile.bufferedReader().use { it.readText() }
        assertEquals(expectedManifest, installedManifest)

        val second = installer.ensureInstalled()
        assertFalse(second.didInstall)
    }

    @Test
    fun ensureInstalled_reinstallsWhenInstalledManifestContractChanged() {
        val installer = DictionaryAssetInstaller(context)
        val first = installer.ensureInstalled()

        first.manifestFile.writeText(
            """
            {
              "schema_version": 1,
              "db_filename": "${first.packageManifest.dbFilename}",
              "search_capabilities": {
                "fts": false
              }
            }
            """.trimIndent(),
        )

        val reinstall = installer.ensureInstalled()

        assertTrue(reinstall.didInstall)
        val expectedManifest = context.assets.open("manifest.json").bufferedReader().use { it.readText() }
        val installedManifest = reinstall.manifestFile.bufferedReader().use { it.readText() }
        assertEquals(expectedManifest, installedManifest)
    }

    @Test
    fun ensureInstalled_reinstallsWhenManifestMissingButDatabaseExists() {
        val installer = DictionaryAssetInstaller(context)
        val first = installer.ensureInstalled()
        assertTrue(first.databaseFile.exists())

        first.manifestFile.delete()

        val reinstall = installer.ensureInstalled()

        assertTrue(reinstall.didInstall)
        assertTrue(reinstall.databaseFile.exists())
        assertTrue(reinstall.manifestFile.exists())
    }

    @Test
    fun open_withProvider_returnsReadOnlyDatabase() {
        val installer = DictionaryAssetInstaller(context)
        val result = installer.ensureInstalled()

        val database = DictionaryDatabaseProvider().open(result)
        try {
            assertTrue(database.isReadOnly)
        } finally {
            database.close()
        }
    }
}
