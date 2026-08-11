package com.pf2ebuilder.ru.domain

import org.junit.Assert.assertEquals
import org.junit.Test

class CharacterValidationTest {
    @Test
    fun levelIsClampedToPf2eRange() {
        assertEquals(1, CharacterValidation.normalizeLevel(-3))
        assertEquals(1, CharacterValidation.normalizeLevel(1))
        assertEquals(12, CharacterValidation.normalizeLevel(12))
        assertEquals(20, CharacterValidation.normalizeLevel(99))
    }

    @Test
    fun blankNameGetsSafeFallback() {
        assertEquals("Без имени", CharacterValidation.normalizeName("   "))
        assertEquals("Лини", CharacterValidation.normalizeName("  Лини  "))
    }
}
