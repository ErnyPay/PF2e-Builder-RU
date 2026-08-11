package com.pf2ebuilder.ru.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

class CharacterRepository(context: Context) {
    private val appContext = context.applicationContext
    private val database = CharacterDatabase(appContext)
    private val legacyPrefs = appContext.getSharedPreferences("characters-v1", Context.MODE_PRIVATE)

    var characters: List<CharacterRecord> by mutableStateOf(emptyList())
        private set

    init {
        database.writableDatabase
        migrateSharedPreferencesOnce()
        refresh()
    }

    fun create(draft: CharacterRecord): CharacterRecord {
        val item = draft.normalized()
        upsert(item)
        refresh()
        return item
    }

    fun update(item: CharacterRecord) {
        upsert(item.normalized())
        refresh()
    }

    fun import(item: CharacterRecord) {
        upsert(item.normalized())
        refresh()
    }

    fun delete(id: String) {
        database.writableDatabase.delete(TABLE, "$COL_ID = ?", arrayOf(id))
        refresh()
    }

    private fun upsert(item: CharacterRecord) {
        val values = ContentValues().apply {
            put(COL_ID, item.id)
            put(COL_NAME, item.name)
            put(COL_LEVEL, item.level)
            put(COL_ANCESTRY, item.ancestry)
            put(COL_BACKGROUND, item.background)
            put(COL_CLASS, item.className)
            put(COL_NOTES, item.notes)
            put(COL_UPDATED_AT, System.currentTimeMillis())
        }
        database.writableDatabase.insertWithOnConflict(TABLE, null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    private fun refresh() {
        val result = mutableListOf<CharacterRecord>()
        database.readableDatabase.query(
            TABLE,
            arrayOf(COL_ID, COL_NAME, COL_LEVEL, COL_ANCESTRY, COL_BACKGROUND, COL_CLASS, COL_NOTES),
            null,
            null,
            null,
            null,
            "$COL_UPDATED_AT DESC, $COL_NAME COLLATE NOCASE ASC",
        ).use { cursor ->
            val idIndex = cursor.getColumnIndexOrThrow(COL_ID)
            val nameIndex = cursor.getColumnIndexOrThrow(COL_NAME)
            val levelIndex = cursor.getColumnIndexOrThrow(COL_LEVEL)
            val ancestryIndex = cursor.getColumnIndexOrThrow(COL_ANCESTRY)
            val backgroundIndex = cursor.getColumnIndexOrThrow(COL_BACKGROUND)
            val classIndex = cursor.getColumnIndexOrThrow(COL_CLASS)
            val notesIndex = cursor.getColumnIndexOrThrow(COL_NOTES)
            while (cursor.moveToNext()) {
                result += CharacterRecord(
                    id = cursor.getString(idIndex),
                    name = cursor.getString(nameIndex),
                    level = cursor.getInt(levelIndex),
                    ancestry = cursor.getString(ancestryIndex),
                    background = cursor.getString(backgroundIndex),
                    className = cursor.getString(classIndex),
                    notes = cursor.getString(notesIndex),
                ).normalized()
            }
        }
        characters = result
    }

    private fun migrateSharedPreferencesOnce() {
        if (legacyPrefs.getBoolean(MIGRATED_FLAG, false)) return
        val legacy = CharacterJson.decodeCollection(legacyPrefs.getString(LEGACY_KEY, null))
        if (legacy.isNotEmpty()) {
            val db = database.writableDatabase
            db.beginTransaction()
            try {
                legacy.forEach(::upsert)
                db.setTransactionSuccessful()
            } finally {
                db.endTransaction()
            }
        }
        legacyPrefs.edit().remove(LEGACY_KEY).putBoolean(MIGRATED_FLAG, true).apply()
    }

    private class CharacterDatabase(context: Context) : SQLiteOpenHelper(context, DB_NAME, null, DB_VERSION) {
        override fun onCreate(db: SQLiteDatabase) {
            db.execSQL(
                """
                CREATE TABLE $TABLE (
                    $COL_ID TEXT PRIMARY KEY NOT NULL,
                    $COL_NAME TEXT NOT NULL,
                    $COL_LEVEL INTEGER NOT NULL,
                    $COL_ANCESTRY TEXT NOT NULL DEFAULT '',
                    $COL_BACKGROUND TEXT NOT NULL DEFAULT '',
                    $COL_CLASS TEXT NOT NULL DEFAULT '',
                    $COL_NOTES TEXT NOT NULL DEFAULT '',
                    $COL_UPDATED_AT INTEGER NOT NULL
                )
                """.trimIndent()
            )
            db.execSQL("CREATE INDEX idx_characters_updated ON $TABLE($COL_UPDATED_AT DESC)")
        }

        override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
            // Explicit migrations will be added here as the owned schema evolves.
            if (oldVersion != newVersion) {
                error("Missing PF2e Builder RU character DB migration: $oldVersion -> $newVersion")
            }
        }
    }

    private companion object {
        const val DB_NAME = "pf2e-builder-ru.db"
        const val DB_VERSION = 1
        const val TABLE = "characters"
        const val COL_ID = "id"
        const val COL_NAME = "name"
        const val COL_LEVEL = "level"
        const val COL_ANCESTRY = "ancestry"
        const val COL_BACKGROUND = "background"
        const val COL_CLASS = "class_name"
        const val COL_NOTES = "notes"
        const val COL_UPDATED_AT = "updated_at"
        const val LEGACY_KEY = "characters"
        const val MIGRATED_FLAG = "migrated-to-sqlite-v1"
    }
}
