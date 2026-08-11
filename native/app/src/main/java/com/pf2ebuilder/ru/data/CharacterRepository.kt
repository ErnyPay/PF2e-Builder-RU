package com.pf2ebuilder.ru.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

class CharacterRepository(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("characters-v1", Context.MODE_PRIVATE)

    var characters: List<CharacterRecord> by mutableStateOf(load())
        private set

    fun create(draft: CharacterRecord): CharacterRecord {
        val item = draft.normalized()
        characters = characters + item
        persist()
        return item
    }

    fun update(item: CharacterRecord) {
        val normalized = item.normalized()
        characters = characters.map { if (it.id == normalized.id) normalized else it }
        persist()
    }

    fun import(item: CharacterRecord) {
        val normalized = item.normalized()
        characters = if (characters.any { it.id == normalized.id }) {
            characters.map { if (it.id == normalized.id) normalized else it }
        } else {
            characters + normalized
        }
        persist()
    }

    fun delete(id: String) {
        characters = characters.filterNot { it.id == id }
        persist()
    }

    private fun load(): List<CharacterRecord> = CharacterJson.decodeCollection(prefs.getString(KEY, null))

    private fun persist() {
        prefs.edit().putString(KEY, CharacterJson.encodeCollection(characters)).apply()
    }

    private companion object {
        const val KEY = "characters"
    }
}
