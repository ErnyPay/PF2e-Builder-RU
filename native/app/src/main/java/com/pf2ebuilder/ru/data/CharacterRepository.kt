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
            put(COL_ANCESTRY_ID, item.ancestryId)
            put(COL_BACKGROUND_ID, item.backgroundId)
            put(COL_CLASS_ID, item.classId)
            put(COL_STR, item.strength)
            put(COL_DEX, item.dexterity)
            put(COL_CON, item.constitution)
            put(COL_INT, item.intelligence)
            put(COL_WIS, item.wisdom)
            put(COL_CHA, item.charisma)
            put(COL_NOTES, item.notes)
            put(COL_UPDATED_AT, System.currentTimeMillis())
        }
        database.writableDatabase.insertWithOnConflict(TABLE, null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    private fun refresh() {
        val result = mutableListOf<CharacterRecord>()
        database.readableDatabase.query(
            TABLE,
            arrayOf(
                COL_ID, COL_NAME, COL_LEVEL, COL_ANCESTRY, COL_BACKGROUND, COL_CLASS,
                COL_ANCESTRY_ID, COL_BACKGROUND_ID, COL_CLASS_ID,
                COL_STR, COL_DEX, COL_CON, COL_INT, COL_WIS, COL_CHA, COL_NOTES,
            ),
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
            val ancestryIdIndex = cursor.getColumnIndexOrThrow(COL_ANCESTRY_ID)
            val backgroundIdIndex = cursor.getColumnIndexOrThrow(COL_BACKGROUND_ID)
            val classIdIndex = cursor.getColumnIndexOrThrow(COL_CLASS_ID)
            val strIndex = cursor.getColumnIndexOrThrow(COL_STR)
            val dexIndex = cursor.getColumnIndexOrThrow(COL_DEX)
            val conIndex = cursor.getColumnIndexOrThrow(COL_CON)
            val intIndex = cursor.getColumnIndexOrThrow(COL_INT)
            val wisIndex = cursor.getColumnIndexOrThrow(COL_WIS)
            val chaIndex = cursor.getColumnIndexOrThrow(COL_CHA)
            val notesIndex = cursor.getColumnIndexOrThrow(COL_NOTES)
            while (cursor.moveToNext()) {
                result += CharacterRecord(
                    id = cursor.getString(idIndex),
                    name = cursor.getString(nameIndex),
                    level = cursor.getInt(levelIndex),
                    ancestry = cursor.getString(ancestryIndex),
                    background = cursor.getString(backgroundIndex),
                    className = cursor.getString(classIndex),
                    ancestryId = cursor.getString(ancestryIdIndex),
                    backgroundId = cursor.getString(backgroundIdIndex),
                    classId = cursor.getString(classIdIndex),
                    strength = cursor.getInt(strIndex),
                    dexterity = cursor.getInt(dexIndex),
                    constitution = cursor.getInt(conIndex),
                    intelligence = cursor.getInt(intIndex),
                    wisdom = cursor.getInt(wisIndex),
                    charisma = cursor.getInt(chaIndex),
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
                    $COL_ANCESTRY_ID TEXT NOT NULL DEFAULT '',
                    $COL_BACKGROUND_ID TEXT NOT NULL DEFAULT '',
                    $COL_CLASS_ID TEXT NOT NULL DEFAULT '',
                    $COL_STR INTEGER NOT NULL DEFAULT 0,
                    $COL_DEX INTEGER NOT NULL DEFAULT 0,
                    $COL_CON INTEGER NOT NULL DEFAULT 0,
                    $COL_INT INTEGER NOT NULL DEFAULT 0,
                    $COL_WIS INTEGER NOT NULL DEFAULT 0,
                    $COL_CHA INTEGER NOT NULL DEFAULT 0,
                    $COL_NOTES TEXT NOT NULL DEFAULT '',
                    $COL_UPDATED_AT INTEGER NOT NULL
                )
                """.trimIndent()
            )
            db.execSQL("CREATE INDEX idx_characters_updated ON $TABLE($COL_UPDATED_AT DESC)")
        }

        override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
            var version = oldVersion
            if (version == 1) {
                listOf(COL_STR, COL_DEX, COL_CON, COL_INT, COL_WIS, COL_CHA).forEach { column ->
                    db.execSQL("ALTER TABLE $TABLE ADD COLUMN $column INTEGER NOT NULL DEFAULT 0")
                }
                version = 2
            }
            if (version == 2) {
                listOf(COL_ANCESTRY_ID, COL_BACKGROUND_ID, COL_CLASS_ID).forEach { column ->
                    db.execSQL("ALTER TABLE $TABLE ADD COLUMN $column TEXT NOT NULL DEFAULT ''")
                }
                version = 3
            }
            if (version != newVersion) {
                error("Missing RuneSheet character DB migration: $oldVersion -> $newVersion (stopped at $version)")
            }
        }
    }

    private companion object {
        const val DB_NAME = "pf2e-builder-ru.db"
        const val DB_VERSION = 3
        const val TABLE = "characters"
        const val COL_ID = "id"
        const val COL_NAME = "name"
        const val COL_LEVEL = "level"
        const val COL_ANCESTRY = "ancestry"
        const val COL_BACKGROUND = "background"
        const val COL_CLASS = "class_name"
        const val COL_ANCESTRY_ID = "ancestry_id"
        const val COL_BACKGROUND_ID = "background_id"
        const val COL_CLASS_ID = "class_id"
        const val COL_STR = "strength"
        const val COL_DEX = "dexterity"
        const val COL_CON = "constitution"
        const val COL_INT = "intelligence"
        const val COL_WIS = "wisdom"
        const val COL_CHA = "charisma"
        const val COL_NOTES = "notes"
        const val COL_UPDATED_AT = "updated_at"
        const val LEGACY_KEY = "characters"
        const val MIGRATED_FLAG = "migrated-to-sqlite-v1"
    }
}
