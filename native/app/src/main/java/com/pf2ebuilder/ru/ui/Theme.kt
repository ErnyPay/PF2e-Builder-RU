package com.pf2ebuilder.ru.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val AppColors = darkColorScheme(
    primary = Color(0xFF59D6C1),
    secondary = Color(0xFF797EFF),
    background = Color(0xFF121826),
    surface = Color(0xFF202B40),
    onPrimary = Color(0xFF121826),
    onBackground = Color(0xFFF4F7FC),
    onSurface = Color(0xFFF4F7FC),
)

@Composable
fun PF2eBuilderTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = AppColors, content = content)
}
