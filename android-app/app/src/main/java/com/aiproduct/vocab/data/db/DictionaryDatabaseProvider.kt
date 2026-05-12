package com.aiproduct.vocab.data.db

import android.database.sqlite.SQLiteDatabase
import com.aiproduct.vocab.data.`package`.InstallState
import java.io.File

class DictionaryDatabaseProvider {
    fun open(installState: InstallState): SQLiteDatabase = open(installState.databaseFile)

    fun open(databaseFile: File): SQLiteDatabase {
        require(databaseFile.exists()) {
            "Dictionary database file does not exist: ${databaseFile.absolutePath}"
        }
        return SQLiteDatabase.openDatabase(
            databaseFile.absolutePath,
            null,
            SQLiteDatabase.OPEN_READONLY,
        )
    }
}
