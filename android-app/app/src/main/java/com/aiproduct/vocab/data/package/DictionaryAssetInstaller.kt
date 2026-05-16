package com.aiproduct.vocab.data.`package`

import android.content.Context
import android.os.SystemClock
import android.util.Log
import com.aiproduct.vocab.util.measureDurationMillis
import java.io.File
import java.io.IOException

class DictionaryAssetInstaller(
    private val context: Context,
    private val manifestReader: DictionaryManifestReader = DictionaryManifestReader(),
) {
    fun ensureInstalled(): InstallState {
        val measured = measureDurationMillis(
            nowMillis = SystemClock::elapsedRealtime,
        ) {
            val installDir = File(context.filesDir, INSTALL_DIR_NAME)
            ensureDirectoryExists(installDir)
            val manifestFile = File(installDir, MANIFEST_FILENAME)

            val assetManifest = manifestReader.readFromAssets(context.assets, MANIFEST_FILENAME)
            val databaseFile = File(installDir, assetManifest.dbFilename)
            val installedManifest = readInstalledManifestOrNull(manifestFile)
            val hasInstalledContract = installedManifest?.let { hasSameInstallContract(it, assetManifest) } ?: false
            val shouldInstall = !hasInstalledContract || !databaseFile.exists()
            if (shouldInstall) {
                copyAsset(
                    assetPath = assetManifest.dbFilename,
                    outputFile = databaseFile,
                )
                copyAsset(
                    assetPath = MANIFEST_FILENAME,
                    outputFile = manifestFile,
                )
                if (installedManifest != null && installedManifest.dbFilename != assetManifest.dbFilename) {
                    File(installDir, installedManifest.dbFilename).delete()
                }
            }

            InstallState(
                installDir = installDir,
                databaseFile = databaseFile,
                manifestFile = manifestFile,
                packageManifest = assetManifest,
                didInstall = shouldInstall,
            )
        }
        Log.i(
            TAG,
            "ensureInstalled finished in ${measured.durationMillis}ms (didInstall=${measured.value.didInstall}, db=${measured.value.packageManifest.dbFilename})",
        )
        return measured.value
    }

    private fun ensureDirectoryExists(directory: File) {
        if (directory.exists()) {
            return
        }
        if (!directory.mkdirs()) {
            throw IOException("Unable to create dictionary install directory: ${directory.absolutePath}")
        }
    }

    private fun readInstalledManifestOrNull(manifestFile: File): DictionaryPackageManifest? {
        if (!manifestFile.exists()) {
            return null
        }
        return try {
            manifestReader.read(manifestFile)
        } catch (_: IllegalArgumentException) {
            null
        }
    }

    private fun copyAsset(
        assetPath: String,
        outputFile: File,
    ) {
        context.assets.open(assetPath).use { input ->
            outputFile.outputStream().use(input::copyTo)
        }
    }

    companion object {
        private const val INSTALL_DIR_NAME = "dictionary"
        private const val MANIFEST_FILENAME = "manifest.json"
        private const val TAG = "DictionaryAssetInstaller"
    }
}

data class InstallState(
    val installDir: File,
    val databaseFile: File,
    val manifestFile: File,
    val packageManifest: DictionaryPackageManifest,
    val didInstall: Boolean,
)

internal fun hasSameInstallContract(
    installedManifest: DictionaryPackageManifest,
    assetManifest: DictionaryPackageManifest,
): Boolean {
    return installedManifest.schemaVersion == assetManifest.schemaVersion &&
        installedManifest.dbFilename == assetManifest.dbFilename &&
        installedManifest.entryCount == assetManifest.entryCount &&
        (assetManifest.dbByteCount == null || installedManifest.dbByteCount == assetManifest.dbByteCount) &&
        installedManifest.searchCapabilities.fts == assetManifest.searchCapabilities.fts
}
