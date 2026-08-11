package com.pf2ebuilder.ru.data

import com.pf2ebuilder.ru.domain.CharacterValidation
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

data class CharacterRecord(
    val id: String = UUID.randomUUID().toString(),
    val name: String,
    val level: Int = 1,
    val ancestry: String = "",
    val background: String = "",
    val className: String = "",
    val notes: String = "",
) {
    fun normalized(): CharacterRecord = copy(
        name = CharacterValidation.normalizeName(name),
        level = CharacterValidation.normalizeLevel(level),
        ancestry = ancestry.trim(),
        background = background.trim(),
        className = className.trim(),
        notes = notes.trim(),
    )
}

object CharacterJson {
    const val SCHEMA = "pf2e-builder-ru.character"
    const val VERSION = 1

    fun encodeCharacter(character: CharacterRecord): JSONObject {
        val c = character.normalized()
        return JSONObject()
            .put("id", c.id)
            .put("name", c.name)
            .put("level", c.level)
            .put("ancestry", c.ancestry)
            .put("background", c.background)
            .put("className", c.className)
            .put("notes", c.notes)
    }

    fun decodeCharacter(json: JSONObject): CharacterRecord = CharacterRecord(
        id = json.optString("id").ifBlank { UUID.randomUUID().toString() },
        name = json.optString("name", "Без имени"),
        level = json.optInt("level", 1),
        ancestry = json.optString("ancestry"),
        background = json.optString("background"),
        className = json.optString("className"),
        notes = json.optString("notes"),
    ).normalized()

    fun exportOne(character: CharacterRecord): String = JSONObject()
        .put("schema", SCHEMA)
        .put("version", VERSION)
        .put("character", encodeCharacter(character))
        .toString(2)

    fun importOne(text: String): CharacterRecord {
        val root = JSONObject(text)
        require(root.optString("schema") == SCHEMA) { "Неподдерживаемый формат файла" }
        require(root.optInt("version") == VERSION) { "Неподдерживаемая версия файла" }
        return decodeCharacter(root.getJSONObject("character"))
    }

    fun encodeCollection(characters: List<CharacterRecord>): String {
        val array = JSONArray()
        characters.forEach { array.put(encodeCharacter(it)) }
        return JSONObject()
            .put("version", VERSION)
            .put("characters", array)
            .toString()
    }

    fun decodeCollection(text: String?): List<CharacterRecord> {
        if (text.isNullOrBlank()) return emptyList()
        return runCatching {
            val root = JSONObject(text)
            val array = root.optJSONArray("characters") ?: JSONArray()
            buildList {
                for (index in 0 until array.length()) {
                    add(decodeCharacter(array.getJSONObject(index)))
                }
            }
        }.getOrDefault(emptyList())
    }
}
