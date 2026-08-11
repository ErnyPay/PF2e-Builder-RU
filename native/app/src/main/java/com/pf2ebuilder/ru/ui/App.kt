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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import com.pf2ebuilder.ru.data.RuleEntity
import com.pf2ebuilder.ru.data.RulesCatalog
import com.pf2ebuilder.ru.domain.CharacterValidation
import java.util.UUID

private enum class Screen { Characters, Diagnostics }

@Composable
fun PF2eBuilderApp() {
    val context = LocalContext.current
    val repository = remember { CharacterRepository(context) }
    val rules = remember {
        runCatching { RulesCatalog.load(context) }.getOrElse { RulesCatalog.empty() }
    }
    var screen by remember { mutableStateOf(Screen.Characters) }

    Surface(modifier = Modifier.fillMaxSize()) {
        when (screen) {
            Screen.Characters -> CharacterListScreen(repository, rules) { screen = Screen.Diagnostics }
            Screen.Diagnostics -> DiagnosticsScreen(repository.characters.size, rules) { screen = Screen.Characters }
        }
    }
}

@Composable
private fun CharacterListScreen(
    repository: CharacterRepository,
    rules: RulesCatalog,
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

    val importLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
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
        Text("RuneSheet RU", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Нативный конструктор · локальный каталог · без сети", color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(20.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Button(onClick = {
                editor = CharacterRecord(id = UUID.randomUUID().toString(), name = "", level = 1)
            }) { Text("Новый") }
            OutlinedButton(onClick = { importLauncher.launch(arrayOf("application/json", "text/plain")) }) {
                Text("Импорт")
            }
            OutlinedButton(onClick = onDiagnostics) { Text("Диагностика") }
        }

        message?.let {
            Spacer(Modifier.height(12.dp))
            Card(modifier = Modifier.fillMaxWidth()) { Text(it, modifier = Modifier.padding(12.dp)) }
        }

        Spacer(Modifier.height(20.dp))
        Text("Персонажи (${repository.characters.size})", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp))

        if (repository.characters.isEmpty()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Пока нет персонажей", style = MaterialTheme.typography.titleMedium)
                    Text("Создай первого героя и выбери народ, происхождение и класс из нашего каталога.")
                }
            }
        } else {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                repository.characters.forEach { character ->
                    CharacterCard(
                        character = character,
                        rules = rules,
                        onEdit = { editor = character },
                        onExport = {
                            exportCandidate = character
                            exportLauncher.launch(safeFileName(character.name) + ".runesheet.json")
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
            rules = rules,
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
    rules: RulesCatalog,
    onEdit: () -> Unit,
    onExport: () -> Unit,
    onDelete: () -> Unit,
) {
    val ancestryName = rules.displayName(character.ancestryId, character.ancestry)
    val backgroundName = rules.displayName(character.backgroundId, character.background)
    val className = rules.displayName(character.classId, character.className)

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text(character.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text("Уровень ${character.level}${className.takeIf { it.isNotBlank() }?.let { " · $it" } ?: ""}")
            if (ancestryName.isNotBlank()) Text("Народ: $ancestryName")
            if (backgroundName.isNotBlank()) Text("Происхождение: $backgroundName")
            Text(
                "СИЛ ${CharacterValidation.formatModifier(character.strength)} · " +
                    "ЛВК ${CharacterValidation.formatModifier(character.dexterity)} · " +
                    "ВЫН ${CharacterValidation.formatModifier(character.constitution)}"
            )
            Text(
                "ИНТ ${CharacterValidation.formatModifier(character.intelligence)} · " +
                    "МДР ${CharacterValidation.formatModifier(character.wisdom)} · " +
                    "ХАР ${CharacterValidation.formatModifier(character.charisma)}"
            )
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
    rules: RulesCatalog,
    onDismiss: () -> Unit,
    onSave: (CharacterRecord) -> Unit,
) {
    var name by remember(initial.id) { mutableStateOf(initial.name) }
    var levelText by remember(initial.id) { mutableStateOf(initial.level.toString()) }
    var ancestryId by remember(initial.id) {
        mutableStateOf(initial.ancestryId.ifBlank { rules.matchLegacy("ancestry", initial.ancestry)?.id.orEmpty() })
    }
    var backgroundId by remember(initial.id) {
        mutableStateOf(initial.backgroundId.ifBlank { rules.matchLegacy("background", initial.background)?.id.orEmpty() })
    }
    var classId by remember(initial.id) {
        mutableStateOf(initial.classId.ifBlank { rules.matchLegacy("class", initial.className)?.id.orEmpty() })
    }
    var strength by remember(initial.id) { mutableStateOf(initial.strength.toString()) }
    var dexterity by remember(initial.id) { mutableStateOf(initial.dexterity.toString()) }
    var constitution by remember(initial.id) { mutableStateOf(initial.constitution.toString()) }
    var intelligence by remember(initial.id) { mutableStateOf(initial.intelligence.toString()) }
    var wisdom by remember(initial.id) { mutableStateOf(initial.wisdom.toString()) }
    var charisma by remember(initial.id) { mutableStateOf(initial.charisma.toString()) }
    var notes by remember(initial.id) { mutableStateOf(initial.notes) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(if (isNew) "Новый персонаж" else "Изменить персонажа") },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Имя") }, singleLine = true)
                OutlinedTextField(
                    value = levelText,
                    onValueChange = { levelText = it.filter(Char::isDigit).take(2) },
                    label = { Text("Уровень 1–20") },
                    singleLine = true,
                )
                RulePickerField("Народ", ancestryId, initial.ancestry, rules.ancestries) { ancestryId = it }
                RulePickerField("Происхождение", backgroundId, initial.background, rules.backgrounds) { backgroundId = it }
                RulePickerField("Класс", classId, initial.className, rules.classes) { classId = it }

                Text("Модификаторы характеристик", style = MaterialTheme.typography.titleSmall)
                ModifierField("Сила", strength) { strength = it }
                ModifierField("Ловкость", dexterity) { dexterity = it }
                ModifierField("Выносливость", constitution) { constitution = it }
                ModifierField("Интеллект", intelligence) { intelligence = it }
                ModifierField("Мудрость", wisdom) { wisdom = it }
                ModifierField("Харизма", charisma) { charisma = it }
                OutlinedTextField(value = notes, onValueChange = { notes = it }, label = { Text("Заметки") }, minLines = 2)
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val ancestry = rules.find(ancestryId)
                val background = rules.find(backgroundId)
                val characterClass = rules.find(classId)
                onSave(
                    initial.copy(
                        name = name,
                        level = levelText.toIntOrNull() ?: 1,
                        ancestry = ancestry?.nameRu ?: initial.ancestry,
                        background = background?.nameRu ?: initial.background,
                        className = characterClass?.nameRu ?: initial.className,
                        ancestryId = ancestry?.id.orEmpty(),
                        backgroundId = background?.id.orEmpty(),
                        classId = characterClass?.id.orEmpty(),
                        strength = strength.toIntOrNull() ?: 0,
                        dexterity = dexterity.toIntOrNull() ?: 0,
                        constitution = constitution.toIntOrNull() ?: 0,
                        intelligence = intelligence.toIntOrNull() ?: 0,
                        wisdom = wisdom.toIntOrNull() ?: 0,
                        charisma = charisma.toIntOrNull() ?: 0,
                        notes = notes,
                    ).normalized()
                )
            }) { Text("Сохранить") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Отмена") } },
    )
}

@Composable
private fun RulePickerField(
    label: String,
    selectedId: String,
    legacyValue: String,
    options: List<RuleEntity>,
    onSelect: (String) -> Unit,
) {
    var open by remember { mutableStateOf(false) }
    val selected = options.firstOrNull { it.id == selectedId }

    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, style = MaterialTheme.typography.titleSmall)
        OutlinedButton(onClick = { open = true }, modifier = Modifier.fillMaxWidth()) {
            Text(selected?.displayName(showEnglish = true) ?: legacyValue.ifBlank { "Выбрать" })
        }
        selected?.descriptionRu?.takeIf(String::isNotBlank)?.let { description ->
            Text(description, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }

    if (open) {
        AlertDialog(
            onDismissRequest = { open = false },
            title = { Text(label) },
            text = {
                Column(
                    modifier = Modifier.verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    TextButton(
                        onClick = {
                            onSelect("")
                            open = false
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("Не выбрано") }
                    options.forEach { option ->
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                TextButton(
                                    onClick = {
                                        onSelect(option.id)
                                        open = false
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                ) { Text(option.displayName(showEnglish = true)) }
                                if (option.descriptionRu.isNotBlank()) {
                                    Text(option.descriptionRu, style = MaterialTheme.typography.bodySmall)
                                }
                            }
                        }
                    }
                }
            },
            confirmButton = {},
            dismissButton = { TextButton(onClick = { open = false }) { Text("Закрыть") } },
        )
    }
}

@Composable
private fun ModifierField(label: String, value: String, onValueChange: (String) -> Unit) {
    OutlinedTextField(
        value = value,
        onValueChange = { candidate -> if (candidate.matches(Regex("-?\\d{0,2}"))) onValueChange(candidate) },
        label = { Text(label) },
        singleLine = true,
        supportingText = { Text("Например: +4 вводится как 4, -1 как -1") },
    )
}

@Composable
private fun DiagnosticsScreen(characterCount: Int, rules: RulesCatalog, onBack: () -> Unit) {
    Column(modifier = Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("Диагностика", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Application ID: ${BuildConfig.APPLICATION_ID}")
        Text("Версия: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
        Text("Персонажей локально: $characterCount")
        Text("Каталог: ${rules.catalogId} · ${rules.entities.size} записей")
        Text("Народов: ${rules.ancestries.size} · происхождений: ${rules.backgrounds.size} · классов: ${rules.classes.size}")
        Text("Формат экспорта: ${CharacterJson.SCHEMA} v${CharacterJson.VERSION}")
        Text("Сеть: разрешение INTERNET отсутствует")
        Text("Реклама: отсутствует")
        Text("Billing: отсутствует")
        Text("Firebase: отсутствует")
        Text("Хранилище: SQLite pf2e-builder-ru.db v3")
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
