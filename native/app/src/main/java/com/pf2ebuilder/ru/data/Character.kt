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
    val ancestryId: String = "",
    val backgroundId: String = "",
    val classId: String = "",
    val strength: Int = 0,
    val dexterity: Int = 0,
    val constitution: Int = 0,
    val intelligence: Int = 0,
    val wisdom: Int = 0,
    val charisma: Int = 0,
    val notes: String = "",
) {
    fun normalized(): CharacterRecord = copy(
        name = CharacterValidation.normalizeName(name),
        level = CharacterValidation.normalizeLevel(level),
        ancestry = ancestry.trim(),
        background = background.trim(),
        className = className.trim(),
        ancestryId = ancestryId.trim(),
        backgroundId = backgroundId.trim(),
        classId = classId.trim(),
        strength = CharacterValidation.normalizeAttributeModifier(strength),
        dexterity = CharacterValidation.normalizeAttributeModifier(dexterity),
        constitution = CharacterValidation.normalizeAttributeModifier(constitution),
        intelligence = CharacterValidation.normalizeAttributeModifier(intelligence),
        wisdom = CharacterValidation.normalizeAttributeModifier(wisdom),
        charisma = CharacterValidation.normalizeAttributeModifier(charisma),
        notes = notes.trim(),
    )
}

object CharacterJson {
    const val SCHEMA = "pf2e-builder-ru.character"
    const val VERSION = 3

    fun encodeCharacter(character: CharacterRecord): JSONObject {
        val c = character.normalized()
        return JSONObject()
            .put("id", c.id)
            .put("name", c.name)
            .put("level", c.level)
            .put("ancestry", c.ancestry)
            .put("background", c.background)
            .put("className", c.className)
            .put(
                "rules",
                JSONObject()
                    .put("ancestryId", c.ancestryId)
                    .put("backgroundId", c.backgroundId)
                    .put("classId", c.classId),
            )
            .put(
                "attributes",
                JSONObject()
                    .put("strength", c.strength)
                    .put("dexterity", c.dexterity)
                    .put("constitution", c.constitution)
                    .put("intelligence", c.intelligence)
                    .put("wisdom", c.wisdom)
                    .put("charisma", c.charisma),
            )
            .put("notes", c.notes)
    }

    fun decodeCharacter(json: JSONObject, version: Int = VERSION): CharacterRecord {
        val attributes = if (version >= 2) json.optJSONObject("attributes") else null
        val rules = if (version >= 3) json.optJSONObject("rules") else null
        return CharacterRecord(
            id = json.optString("id").ifBlank { UUID.randomUUID().toString() },
            name = json.optString("name", "Без имени"),
            level = json.optInt("level", 1),
            ancestry = json.optString("ancestry"),
            background = json.optString("background"),
            className = json.optString("className"),
            ancestryId = rules?.optString("ancestryId").orEmpty(),
            backgroundId = rules?.optString("backgroundId").orEmpty(),
            classId = rules?.optString("classId").orEmpty(),
            strength = attributes?.optInt("strength", 0) ?: 0,
            dexterity = attributes?.optInt("dexterity", 0) ?: 0,
            constitution = attributes?.optInt("constitution", 0) ?: 0,
            intelligence = attributes?.optInt("intelligence", 0) ?: 0,
            wisdom = attributes?.optInt("wisdom", 0) ?: 0,
            charisma = attributes?.optInt("charisma", 0) ?: 0,
            notes = json.optString("notes"),
        ).normalized()
    }

    fun exportOne(character: CharacterRecord): String = JSONObject()
        .put("schema", SCHEMA)
        .put("version", VERSION)
        .put("character", encodeCharacter(character))
        .toString(2)

    fun importOne(text: String): CharacterRecord {
        val root = JSONObject(text)
        require(root.optString("schema") == SCHEMA) { "Неподдерживаемый формат файла" }
        val version = root.optInt("version")
        require(version in 1..VERSION) { "Неподдерживаемая версия файла: $version" }
        return decodeCharacter(root.getJSONObject("character"), version)
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
            val version = root.optInt("version", 1).coerceIn(1, VERSION)
            val array = root.optJSONArray("characters") ?: JSONArray()
            buildList {
                for (index in 0 until array.length()) {
                    add(decodeCharacter(array.getJSONObject(index), version))
                }
            }
        }.getOrDefault(emptyList())
    }
}
