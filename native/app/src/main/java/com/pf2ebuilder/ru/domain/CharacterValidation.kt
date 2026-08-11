package com.pf2ebuilder.ru.domain

object CharacterValidation {
    fun normalizeName(value: String): String = value.trim().ifBlank { "Без имени" }
    fun normalizeLevel(value: Int): Int = value.coerceIn(1, 20)

    // Wide safety bounds keep corrupted/imported data sane without imposing a
    // character-creation rule that belongs in the rules engine.
    fun normalizeAttributeModifier(value: Int): Int = value.coerceIn(-20, 20)

    fun formatModifier(value: Int): String = if (value >= 0) "+$value" else value.toString()
}
