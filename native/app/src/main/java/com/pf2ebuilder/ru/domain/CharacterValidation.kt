package com.pf2ebuilder.ru.domain

object CharacterValidation {
    fun normalizeName(value: String): String = value.trim().ifBlank { "Без имени" }
    fun normalizeLevel(value: Int): Int = value.coerceIn(1, 20)
}
