package com.pf2ebuilder.ru.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.pf2ebuilder.ru.BuildConfig

data class CharacterSummary(
    val id: String,
    val name: String,
    val level: Int,
    val className: String,
)

private enum class Screen { Characters, Diagnostics }

@Composable
fun PF2eBuilderApp() {
    var screen by remember { mutableStateOf(Screen.Characters) }
    Surface(modifier = Modifier.fillMaxSize()) {
        when (screen) {
            Screen.Characters -> CharacterListScreen(onDiagnostics = { screen = Screen.Diagnostics })
            Screen.Diagnostics -> DiagnosticsScreen(onBack = { screen = Screen.Characters })
        }
    }
}

@Composable
private fun CharacterListScreen(onDiagnostics: () -> Unit) {
    val characters = remember {
        listOf(
            CharacterSummary("demo", "Новый герой", 1, "Класс не выбран"),
        )
    }

    Column(modifier = Modifier.fillMaxSize().padding(20.dp)) {
        Text("PF2e Builder RU", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Независимая нативная оболочка · offline first", color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(20.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = { /* Character editor is the next vertical slice. */ }) {
                Text("Новый персонаж")
            }
            OutlinedButton(onClick = onDiagnostics) {
                Text("Диагностика")
            }
        }

        Spacer(Modifier.height(20.dp))
        Text("Персонажи", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp))

        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(characters, key = { it.id }) { character ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text(character.name, style = MaterialTheme.typography.titleMedium)
                        Text("Уровень ${character.level} · ${character.className}")
                    }
                }
            }
        }
    }
}

@Composable
private fun DiagnosticsScreen(onBack: () -> Unit) {
    Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Диагностика", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Application ID: ${BuildConfig.APPLICATION_ID}")
        Text("Версия: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
        Text("Сеть: не запрошена в AndroidManifest")
        Text("Реклама: отсутствует")
        Text("Billing: отсутствует")
        Text("Firebase: отсутствует")
        Text("Хранилище: локальное (реализация следующего этапа)")
        Spacer(Modifier.height(8.dp))
        Button(onClick = onBack) { Text("Назад") }
    }
}
