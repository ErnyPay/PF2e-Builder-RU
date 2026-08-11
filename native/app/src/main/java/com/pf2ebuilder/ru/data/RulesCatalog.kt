package com.pf2ebuilder.ru.data

import android.content.Context
import org.json.JSONObject
import java.util.Locale

data class RuleEntity(
    val id: String,
    val type: String,
    val nameRu: String,
    val nameEn: String = "",
    val descriptionRu: String = "",
    val descriptionEn: String = "",
) {
    fun displayName(showEnglish: Boolean = false): String =
        if (showEnglish && nameEn.isNotBlank()) "$nameRu · $nameEn" else nameRu
}

class RulesCatalog private constructor(
    val catalogId: String,
    val entities: List<RuleEntity>,
) {
    val ancestries: List<RuleEntity> get() = byType("ancestry")
    val backgrounds: List<RuleEntity> get() = byType("background")
    val classes: List<RuleEntity> get() = byType("class")

    fun byType(type: String): List<RuleEntity> =
        entities.filter { it.type == type }.sortedBy { it.nameRu.lowercase(Locale.ROOT) }

    fun find(id: String?): RuleEntity? =
        id?.takeIf(String::isNotBlank)?.let { wanted -> entities.firstOrNull { it.id == wanted } }

    fun matchLegacy(type: String, value: String): RuleEntity? {
        val normalized = value.trim()
        if (normalized.isBlank()) return null
        return byType(type).firstOrNull {
            it.nameRu.equals(normalized, ignoreCase = true) ||
                it.nameEn.equals(normalized, ignoreCase = true)
        }
    }

    fun displayName(id: String, legacy: String): String =
        find(id)?.nameRu ?: legacy.trim()

    companion object {
        fun load(context: Context): RulesCatalog =
            parse(context.assets.open("base.json").bufferedReader().use { it.readText() })

        fun parse(text: String): RulesCatalog {
            val root = JSONObject(text)
            val array = root.optJSONArray("entities")
            val entities = buildList {
                if (array != null) {
                    for (index in 0 until array.length()) {
                        val raw = array.getJSONObject(index)
                        val name = raw.getJSONObject("name")
                        val description = raw.optJSONObject("description")
                        add(
                            RuleEntity(
                                id = raw.getString("id"),
                                type = raw.getString("type"),
                                nameRu = name.getString("ru"),
                                nameEn = name.optString("en"),
                                descriptionRu = description?.optString("ru").orEmpty(),
                                descriptionEn = description?.optString("en").orEmpty(),
                            )
                        )
                    }
                }
            }
            return RulesCatalog(
                catalogId = root.optString("catalogId", "unknown"),
                entities = entities,
            )
        }

        fun empty(): RulesCatalog = RulesCatalog("empty", emptyList())
    }
}
