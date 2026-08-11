package com.pf2ebuilder.ru.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.pf2ebuilder.ru.BuildConfig
import com.pf2ebuilder.ru.data.CharacterJson
import com.pf2ebuilder.ru.data.CharacterRecord
import com.pf2ebuilder.ru.data.CharacterRepository
import java.util.UUID

private enum class Screen { Characters, Diagnostics }

@Composable
fun PF2eBuilderApp() {
    val context = LocalContext.current
    val repository = remember { CharacterRepository(context) }
    var screen by remember { mutableStateOf(Screen.Characters) }

    Surface(modifier = Modifier.fillMaxSize()) {
        when (screen) {
            Screen.Characters -> CharacterListScreen(
                repository = repository,
                onDiagnostics = { screen = Screen.Diagnostics },
            )
            Screen.Diagnostics -> DiagnosticsScreen(
                characterCount = repository.characters.size,
                onBack = { screen = Screen.Characters },
            )
        }
    }
}

@Composable
private fun CharacterListScreen(
    repository: CharacterRepository,
    onDiagnostics: () -> Unit,
) {
    val context = LocalContext.current
    var editor by remember { mutableStateOf<CharacterRecord?>(null) }
    var deleteCandidate by remember { mutableStateOf<CharacterRecord?>(null) }
    var exportCandidate by remember { mutableStateOf<CharacterRecord?>(null) }
    var message by remember { mutableStateOf<String?>(null) }

    val exportLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        val character = exportCandidate
        if (uri != null && character != null) {
            message = runCatching {
                context.contentResolver.openOutputStream(uri)?.bufferedWriter()?.use {
                    it.write(CharacterJson.exportOne(character))
                } ?: error("Не удалось открыть файл для записи")
                "Экспортировано: ${character.name}"
            }.getOrElse { "Ошибка экспорта: ${it.message ?: "неизвестная ошибка"}" }
        }
        exportCandidate = null
    }

    val importLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            message = runCatching {
                val text = context.contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
                    ?: error("Не удалось прочитать файл")
                val imported = CharacterJson.importOne(text)
                repository.import(imported)
                "Импортировано: ${imported.name}"
            }.getOrElse { "Ошибка импорта: ${it.message ?: "неизвестная ошибка"}" }
        }
    }

    Column(modifier = Modifier.fillMaxSize().padding(20.dp)) {
        Text("PF2e Builder RU", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Нативное приложение · локальная SQLite · без сети", color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(20.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(onClick = {
                editor = CharacterRecord(id = UUID.randomUUID().toString(), name = "", level = 1)
            }) {
                Text("Новый")
            }
            OutlinedButton(onClick = { importLauncher.launch(arrayOf("application/json", "text/plain")) }) {
                Text("Импорт")
            }
            OutlinedButton(onClick = onDiagnostics) {
                Text("Диагностика")
            }
        }

        message?.let {
            Spacer(Modifier.height(12.dp))
            Card(modifier = Modifier.fillMaxWidth()) {
                Text(it, modifier = Modifier.padding(12.dp))
            }
        }

        Spacer(Modifier.height(20.dp))
        Text("Персонажи (${repository.characters.size})", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp))

        if (repository.characters.isEmpty()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Пока нет персонажей", style = MaterialTheme.typography.titleMedium)
                    Text("Создай первого героя или импортируй файл PF2e Builder RU.")
                }
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(repository.characters, key = { it.id }) { character ->
                    CharacterCard(
                        character = character,
                        onEdit = { editor = character },
                        onExport = {
                            exportCandidate = character
                            exportLauncher.launch(safeFileName(character.name) + ".pf2eru.json")
                        },
                        onDelete = { deleteCandidate = character },
                    )
                }
            }
        }
    }

    editor?.let { current ->
        CharacterEditorDialog(
            initial = current,
            isNew = repository.characters.none { it.id == current.id },
            onDismiss = { editor = null },
            onSave = { value ->
                if (repository.characters.any { it.id == value.id }) repository.update(value) else repository.create(value)
                editor = null
                message = "Сохранено: ${value.name.trim().ifBlank { "Без имени" }}"
            },
        )
    }

    deleteCandidate?.let { character ->
        AlertDialog(
            onDismissRequest = { deleteCandidate = null },
            title = { Text("Удалить персонажа?") },
            text = { Text("${character.name} будет удалён только с этого устройства.") },
            confirmButton = {
                TextButton(onClick = {
                    repository.delete(character.id)
                    deleteCandidate = null
                    message = "Удалено: ${character.name}"
                }) { Text("Удалить") }
            },
            dismissButton = { TextButton(onClick = { deleteCandidate = null }) { Text("Отмена") } },
        )
    }
}

@Composable
private fun CharacterCard(
    character: CharacterRecord,
    onEdit: () -> Unit,
    onExport: () -> Unit,
    onDelete: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text(character.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text("Уровень ${character.level}${character.className.takeIf { it.isNotBlank() }?.let { " · $it" } ?: ""}")
            if (character.ancestry.isNotBlank()) Text("Наследие: ${character.ancestry}")
            if (character.background.isNotBlank()) Text("Происхождение: ${character.background}")
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                TextButton(onClick = onEdit) { Text("Изменить") }
                TextButton(onClick = onExport) { Text("Экспорт") }
                TextButton(onClick = onDelete) { Text("Удалить") }
            }
        }
    }
}

@Composable
private fun CharacterEditorDialog(
    initial: CharacterRecord,
    isNew: Boolean,
    onDismiss: () -> Unit,
    onSave: (CharacterRecord) -> Unit,
) {
    var name by remember(initial.id) { mutableStateOf(initial.name) }
    var levelText by remember(initial.id) { mutableStateOf(initial.level.toString()) }
    var ancestry by remember(initial.id) { mutableStateOf(initial.ancestry) }
    var background by remember(initial.id) { mutableStateOf(initial.background) }
    var className by remember(initial.id) { mutableStateOf(initial.className) }
    var notes by remember(initial.id) { mutableStateOf(initial.notes) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (isNew) "Новый персонаж" else "Изменить персонажа") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Имя") }, singleLine = true)
                OutlinedTextField(value = levelText, onValueChange = { levelText = it.filter(Char::isDigit).take(2) }, label = { Text("Уровень 1–20") }, singleLine = true)
                OutlinedTextField(value = ancestry, onValueChange = { ancestry = it }, label = { Text("Наследие") }, singleLine = true)
                OutlinedTextField(value = background, onValueChange = { background = it }, label = { Text("Происхождение") }, singleLine = true)
                OutlinedTextField(value = className, onValueChange = { className = it }, label = { Text("Класс") }, singleLine = true)
                OutlinedTextField(value = notes, onValueChange = { notes = it }, label = { Text("Заметки") }, minLines = 2)
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onSave(
                    initial.copy(
                        name = name,
                        level = levelText.toIntOrNull() ?: 1,
                        ancestry = ancestry,
                        background = background,
                        className = className,
                        notes = notes,
                    ).normalized()
                )
            }) { Text("Сохранить") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Отмена") } },
    )
}

@Composable
private fun DiagnosticsScreen(characterCount: Int, onBack: () -> Unit) {
    Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Диагностика", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Application ID: ${BuildConfig.APPLICATION_ID}")
        Text("Версия: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
        Text("Персонажей локально: $characterCount")
        Text("Формат экспорта: ${CharacterJson.SCHEMA} v${CharacterJson.VERSION}")
        Text("Сеть: разрешение INTERNET отсутствует")
        Text("Реклама: отсутствует")
        Text("Billing: отсутствует")
        Text("Firebase: отсутствует")
        Text("Хранилище: SQLite pf2e-builder-ru.db v1")
        Spacer(Modifier.height(8.dp))
        Button(onClick = onBack) { Text("Назад") }
    }
}

private fun safeFileName(value: String): String {
    val safe = value.trim().ifBlank { "character" }
        .replace(Regex("[^A-Za-zА-Яа-яЁё0-9._-]+"), "_")
        .trim('_')
    return safe.ifBlank { "character" }
}
