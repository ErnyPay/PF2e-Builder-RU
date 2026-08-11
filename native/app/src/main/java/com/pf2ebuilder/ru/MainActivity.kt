package com.pf2ebuilder.ru

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.pf2ebuilder.ru.ui.PF2eBuilderApp
import com.pf2ebuilder.ru.ui.PF2eBuilderTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PF2eBuilderTheme {
                PF2eBuilderApp()
            }
        }
    }
}
