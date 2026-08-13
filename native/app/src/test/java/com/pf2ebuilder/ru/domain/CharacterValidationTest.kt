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

    @Test
    fun modifiersHaveStableDisplayAndImportBounds() {
        assertEquals("+0", CharacterValidation.formatModifier(0))
        assertEquals("+4", CharacterValidation.formatModifier(4))
        assertEquals("-2", CharacterValidation.formatModifier(-2))
        assertEquals(20, CharacterValidation.normalizeAttributeModifier(999))
        assertEquals(-20, CharacterValidation.normalizeAttributeModifier(-999))
    }
}
