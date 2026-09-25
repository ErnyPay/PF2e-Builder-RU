package com.pf2erus.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/** Layout reconstructed from the original application's observed editor screens. */
@Composable fun CharacterSheet(character: Character, back: () -> Unit) {
    val tabs = listOf("СБОРКА", "О ПЕРСОНАЖЕ", "ЗАЩИТА", "НАПАДЕНИЕ", "СНАРЯЖЕНИЕ", "НАВЫКИ", "ЗАКЛИНАНИЯ", "СПУТНИКИ", "СПОСОБНОСТИ")
    var selected by rememberSaveable { mutableIntStateOf(0) }
    var menu by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<String?>(null) }
    var draft by remember { mutableStateOf("") }
    val fields = remember { mutableStateMapOf("Имя персонажа" to character.name, "Родословная" to character.ancestry, "Класс" to character.heroClass) }
    fun edit(label: String) { draft = fields[label].orEmpty(); editing = label }
    BackHandler { if (editing != null) editing = null else if (menu) menu = false else back() }
    Column(Modifier.fillMaxSize().safeDrawingPadding()) {
        Surface(color = MaterialTheme.colorScheme.primaryContainer) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Box {
                    TextButton(onClick = { menu = true }) { Text("☰") }
                    DropdownMenu(menu, { menu = false }) {
                        DropdownMenuItem(text = { Text("К списку персонажей") }, onClick = { menu = false; back() })
                        DropdownMenuItem(text = { Text("Заметки") }, onClick = { menu = false; edit("Заметки") })
                    }
                }
                Text("${fields["Имя персонажа"]} · ${fields["Класс"]} ${character.level}", modifier = Modifier.weight(1f).padding(end = 8.dp), style = MaterialTheme.typography.titleMedium)
            }
        }
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())) {
            tabs.forEachIndexed { index, title ->
                TextButton(onClick = { selected = index }, colors = ButtonDefaults.textButtonColors(contentColor = if (selected == index) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)) { Text(title) }
            }
        }
        HorizontalDivider()
        key(selected) {
            Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(8.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                when (selected) {
                    0 -> {
                        listOf("Имя персонажа", "Родословная", "Предыстория", "Класс").forEach { label -> EditorField(label, fields[label] ?: "Не выбрано") { edit(label) } }
                        EditorHeading("УРОВЕНЬ ${character.level}")
                        Row(Modifier.fillMaxWidth()) {
                            listOf("Повышения характеристик", "Навык класса", "Обучение навыкам").forEach { label -> OutlinedButton(onClick = { edit(label) }, modifier = Modifier.weight(1f).padding(2.dp)) { Text(label, style = MaterialTheme.typography.labelSmall) } }
                        }
                        listOf("Наследие", "Способность родословной", "Классовая способность").forEach { label -> EditorField(label, fields[label] ?: "Не выбрано") { edit(label) } }
                        Text("Выборы последующих уровней появятся после подключения правил класса.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    1 -> {
                        EditorHeading("Уровень ${character.level}")
                        EditorField("Опыт", fields["Опыт"] ?: "0") { edit("Опыт") }
                        EditorField("Очки героя", fields["Очки героя"] ?: "1") { edit("Очки героя") }
                        Row(Modifier.fillMaxWidth()) { listOf("Размер", "Скорость").forEach { label -> Box(Modifier.weight(1f)) { EditorField(label, fields[label] ?: "—") { edit(label) } } }
                        listOf(listOf("Сила", "Ловкость"), listOf("Телосложение", "Интеллект"), listOf("Мудрость", "Харизма")).forEach { pair -> Row { pair.forEach { label -> Box(Modifier.weight(1f)) { EditorField(label, fields[label] ?: "—") { edit(label) } } } }
                        listOf("Пол", "Божество", "Возраст", "Языки", "Заметки").forEach { label -> EditorField(label, fields[label] ?: "Не задано") { edit(label) } }
                    }
                    2 -> {
                        Row { listOf("КБ", "ОЗ").forEach { label -> Box(Modifier.weight(1f)) { EditorField(label, fields[label] ?: "—") { edit(label) } } }
                        listOf("Стойкость", "Рефлекс", "Воля").forEach { BonusRow(it) }
                        EditorHeading("ВЛАДЕНИЕ ДОСПЕХАМИ")
                        Text("Лёгкие · Средние · Тяжёлые · Без доспехов")
                        listOf("Состояния", "Усиления", "Доспех", "Щит").forEach { label -> EditorField(label, fields[label] ?: "Не выбрано") { edit(label) } }
                    }
                    3 -> {
                        BonusRow("Восприятие")
                        EditorHeading("ВЛАДЕНИЕ ОРУЖИЕМ")
                        Text("Простое · Воинское · Продвинутое · Безоружное")
                        EditorField("Оружие", fields["Оружие"] ?: "Не добавлено") { edit("Оружие") }
                    }
                    4 -> {
                        Row { listOf("ПМ", "ЗМ", "СМ", "ММ").forEach { label -> Box(Modifier.weight(1f)) { EditorField(label, fields[label] ?: "0") { edit(label) } } }
                        listOf("Снаряжение", "Контейнеры", "Формулы").forEach { label -> EditorField(label, fields[label] ?: "Не добавлено") { edit(label) } }
                        EditorHeading("ОСНОВНОЙ ИНВЕНТАРЬ")
                        Text("Нагрузка и пределы будут рассчитаны после подключения правил.", style = MaterialTheme.typography.bodySmall)
                    }
                    5 -> listOf("Акробатика", "Аркана", "Атлетика", "Ремесло", "Обман", "Дипломатия", "Запугивание", "Знания", "Медицина", "Природа", "Оккультизм", "Восприятие", "Выступление", "Религия", "Общество", "Скрытность", "Выживание", "Воровство").forEach { BonusRow(it) }
                    6 -> { EditorHeading("ЗАКЛИНАНИЯ"); Text("Интерфейс заклинателя ещё сверяется с оригиналом."); EditorHeading("РИТУАЛЫ") }
                    7 -> Text("Спутники, эйдолоны, конструкты и фамильяры зависят от выбранных способностей и особенностей класса.")
                    8 -> { EditorHeading("СПОСОБНОСТИ"); Text("Список выбранных способностей будет подключён вместе с библиотеками.") }
                }
            }
        }
    }
    editing?.let { label ->
        AlertDialog(onDismissRequest = { editing = null }, title = { Text(label) }, text = {
            Column { Text("Ручной ввод для интерфейсного прототипа. Библиотеки выбора ещё не подключены.", style = MaterialTheme.typography.bodySmall); OutlinedTextField(draft, { draft = it }, modifier = Modifier.fillMaxWidth()) }
        }, confirmButton = { TextButton(onClick = { fields[label] = draft; editing = null }) { Text("Принять") } }, dismissButton = { TextButton(onClick = { editing = null }) { Text("Отмена") } })
    }
}

@Composable private fun EditorHeading(title: String) {
    Surface(color = MaterialTheme.colorScheme.secondaryContainer, modifier = Modifier.fillMaxWidth()) {
        Box(Modifier.padding(10.dp), contentAlignment = Alignment.Center) { Text(title, style = MaterialTheme.typography.titleMedium) }
    }
}

@Composable private fun EditorField(label: String, value: String, click: () -> Unit) {
    Surface(onClick = click, modifier = Modifier.fillMaxWidth(), color = MaterialTheme.colorScheme.surfaceVariant) {
        Column(Modifier.padding(horizontal = 12.dp, vertical = 10.dp)) { Text(label, style = MaterialTheme.typography.labelMedium); Text(value, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.primary) }
    }
}

@Composable private fun BonusRow(label: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
        Text("$label  —", modifier = Modifier.weight(1f))
        listOf("Хар.", "Обуч.", "Предм.").forEach { Text("$it\n—", modifier = Modifier.padding(horizontal = 6.dp), style = MaterialTheme.typography.labelSmall) }
    }
    HorizontalDivider()
}
