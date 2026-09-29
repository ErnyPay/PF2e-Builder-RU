package com.pf2erus.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties

@Composable internal fun SelectionScreen(title: String, current: String, cancel: () -> Unit, accept: (String) -> Unit) {
    val options = when (title) {
        "Родословная" -> listOf("Дварф", "Эльф", "Гном", "Гоблин", "Полурослик", "Человек", "Леший", "Орк")
        "Класс" -> listOf("Воин", "Страж", "Стрелок", "Изобретатель")
        "Предыстория" -> listOf("Бармен", "Адвокат", "Боевой механик", "Мародёр на поле боя", "Благословлённый", "Бухгалтер", "Охотник за головами", "Артиллерист", "Шарлатан")
        "Наследие" -> listOf("Айуварин", "Дромаар", "Умелый человек", "Разносторонний человек", "Зимнезатронутый человек")
        "Способность родословной" -> listOf("Арканные татуировки", "Астрология", "Кооперативная натура", "Учтивое возвращение", "Адвокат дьявола", "Драконий плевок", "Общая подготовка", "Зрящий во мраке", "Природные амбиции", "Природные навыки")
        else -> emptyList()
    }
    var query by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf(current.takeIf { it in options }) }
    var filter by remember { mutableStateOf("Все") }
    val filters = if (title == "Класс") listOf("Все", "Основные правила", "Expanded", "Классовые архетипы") else if (title == "Предыстория") listOf("Общий", "Региональные", "Кампания", "Пользовательский", "Все") else if (title.contains("Способность")) listOf("Все") else listOf("Всеобщий", "Необычный", "Редкий", "Все")
    Dialog(onDismissRequest = cancel, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        BackHandler(onBack = cancel)
        Surface(Modifier.fillMaxSize().safeDrawingPadding(), color = MaterialTheme.colorScheme.background) {
            Column(Modifier.fillMaxSize().padding(12.dp)) {
                Text(title, style = MaterialTheme.typography.titleLarge)
                OutlinedTextField(query, { query = it }, label = { Text("Поиск") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    filters.forEach { item -> FilterChip(selected = filter == item, onClick = { filter = item }, label = { Text(item) }) }
                }
                Text("Показаны только варианты, зафиксированные в оригинале. Полный каталог и описания ещё не подключены.", style = MaterialTheme.typography.bodySmall)
                LazyColumn(Modifier.weight(1f)) {
                    val visible = options.filter { it.contains(query, ignoreCase = true) && (filter == "Все" || filter == "Всеобщий" && title == "Родословная" || filter == "Основные правила" && it == "Воин") }
                    if (visible.isEmpty()) item { Text("В этой категории пока нет загруженных записей.", Modifier.padding(16.dp)) }
                    items(visible) { option ->
                        Surface(onClick = { selected = option }, color = if (selected == option) MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.surface, modifier = Modifier.fillMaxWidth().padding(vertical = 3.dp)) {
                            Column(Modifier.padding(14.dp)) {
                                Text(option, style = MaterialTheme.typography.titleMedium)
                                if (selected == option) Text("Описание и параметры будут доступны после подключения библиотеки.", style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    TextButton(onClick = cancel) { Text("Отмена") }
                    Button(enabled = selected != null, onClick = { selected?.let(accept) }) { Text("Принять") }
                }
            }
        }
    }
}

