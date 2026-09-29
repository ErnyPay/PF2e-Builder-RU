package com.pf2erus.app
import android.os.Bundle
import androidx.compose.ui.platform.LocalContext
import org.json.JSONArray
import org.json.JSONObject
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.foundation.clickable
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType
class MainActivity : ComponentActivity() { override fun onCreate(state: Bundle?) { super.onCreate(state); setContent { App() } } }
data class Character(val name: String, val level: String, val ancestry: String, val heroClass: String, val coreOnly: Boolean = false, val adventurePaths: Boolean = false)
@Composable fun App() {
    val preferences = LocalContext.current.getSharedPreferences("characters", 0)
    val dark = remember { mutableStateOf(preferences.getBoolean("dark", true)) }
    val winter = darkColorScheme(
        primary = Color(0xFF8ED8FF),
        onPrimary = Color(0xFF003548),
        secondary = Color(0xFFB9E7FF),
        background = Color(0xFF071A2B),
        surface = Color(0xFF102B43),
        onSurface = Color(0xFFE8F6FF)
    )
    MaterialTheme(colorScheme = if (dark.value) winter else lightColorScheme(primary = Color(0xFF17638B), background = Color(0xFFF0F8FF), surface = Color(0xFFE4F1FA), onSurface = Color(0xFF102B43))) {
        Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            val screen = remember { mutableStateOf("home") }
            val characters = remember {
                mutableStateListOf<Character>().apply {
                    val stored = runCatching { JSONArray(preferences.getString("items", "[]")) }.getOrElse { JSONArray() }
                    for (i in 0 until stored.length()) {
                        val item = stored.optJSONObject(i) ?: continue
                        add(Character(item.optString("name"), item.optString("level", "1"), item.optString("ancestry"), item.optString("heroClass"), item.optBoolean("coreOnly"), item.optBoolean("adventurePaths")))
                    }
                }
            }
            val active = remember { mutableStateOf<Character?>(null) }
            when (screen.value) {
                "home" -> HomeScreen(dark.value, { dark.value = it; preferences.edit().putBoolean("dark", it).apply() }) { screen.value = it }
                "characters" -> CharactersScreen(characters, { screen.value = "create" }, { screen.value = "home" })
                "create" -> CreateScreen({ character -> characters.add(character); preferences.edit().putString("items", JSONArray().apply { characters.forEach { put(JSONObject().put("name", it.name).put("level", it.level).put("ancestry", it.ancestry).put("heroClass", it.heroClass).put("coreOnly", it.coreOnly).put("adventurePaths", it.adventurePaths)) } }.toString()).apply(); active.value = character; screen.value = "editor" }, { screen.value = "home" })
                "editor" -> active.value?.let { CharacterSheet(it) { screen.value = "characters" } }
                "library" -> LibraryScreen { screen.value = "home" }
                else -> SettingsScreen(dark.value, { dark.value = it; preferences.edit().putBoolean("dark", it).apply() }) { screen.value = "home" }
            }
        }
    }
}

@Composable private fun SettingsScreen(dark: Boolean, changeTheme: (Boolean) -> Unit, back: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Text("Настройки", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.onSurface); Spacer(Modifier.height(18.dp))
        Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) { Column(Modifier.padding(16.dp)) { Text("Оформление", style = MaterialTheme.typography.titleLarge); Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) { Text("Тёмная тема"); Switch(dark, changeTheme) } } }
        Spacer(Modifier.height(12.dp)); Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) { Column(Modifier.padding(16.dp)) { Text("Данные", style = MaterialTheme.typography.titleLarge); Text("Импорт и экспорт персонажей", color = MaterialTheme.colorScheme.onSurfaceVariant); Spacer(Modifier.height(10.dp)); OutlinedButton(onClick = {}) { Text("Импортировать") }; OutlinedButton(onClick = {}) { Text("Экспортировать") } } }
        Spacer(Modifier.height(16.dp)); OutlinedButton(onClick = back) { Text("Назад") }
    }
}

@Composable private fun CharactersScreen(items: List<Character>, create: () -> Unit, back: () -> Unit) {
    val selected = remember { mutableStateOf<Character?>(null) }
    if (selected.value != null) { CharacterSheet(selected.value!!, { selected.value = null }); return }
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text("Персонажи", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.onSurface)
        Spacer(Modifier.height(16.dp))
        if (items.isEmpty()) Text("Персонажей пока нет", color = MaterialTheme.colorScheme.onSurfaceVariant)
        items.forEach { character -> Card(Modifier.fillMaxWidth().padding(vertical = 5.dp).clickable { selected.value = character }, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) { Column(Modifier.padding(16.dp)) { Text(character.name, style = MaterialTheme.typography.titleLarge); Text("${character.ancestry} · ${character.heroClass} · уровень ${character.level}", color = MaterialTheme.colorScheme.onSurfaceVariant) } } }
        Spacer(Modifier.height(16.dp))
        Button(onClick = create, modifier = Modifier.fillMaxWidth()) { Text("Создать персонажа") }
        OutlinedButton(onClick = back) { Text("Назад") }
    }
}

@Composable private fun CreateScreen(save: (Character) -> Unit, back: () -> Unit) {
    val adventure = remember { mutableStateOf(false) }
    androidx.activity.compose.BackHandler(onBack = back)
    AlertDialog(
        onDismissRequest = back,
        title = { Text("НОВЫЙ ПЕРСОНАЖ") },
        text = {
            Column {
                Text("Начните создание персонажа со всеми доступными вариантами или выберите только основные правила.")
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Checkbox(adventure.value, { adventure.value = it })
                    Text("Включить материалы приключений?")
                }
                Text("Выбор правил сохраняется с персонажем. Полные каталоги будут подключены на этапе библиотек.", style = MaterialTheme.typography.bodySmall)
            }
        },
        confirmButton = { TextButton(onClick = { save(Character("Неизвестный искатель приключений", "1", "Человек", "Воин", false, adventure.value)) }) { Text("Начать") } },
        dismissButton = { TextButton(onClick = { save(Character("Неизвестный искатель приключений", "1", "Человек", "Воин", true, adventure.value)) }) { Text("Только основные правила") } }
    )
}
@Composable private fun HomeScreen(dark: Boolean, changeTheme: (Boolean) -> Unit, open: (String) -> Unit) {
    Column(Modifier.fillMaxSize().padding(22.dp)) {
        Spacer(Modifier.height(18.dp))
        Button(onClick = {}, modifier = Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF28547A))) { Text("2eRUS", style = MaterialTheme.typography.titleLarge) }
        Spacer(Modifier.height(34.dp))
        HomeCard("НОВЫЙ ПЕРСОНАЖ", "Начать сборку героя", "СОЗДАТЬ") { open("create") }
        Spacer(Modifier.height(20.dp))
        HomeCard("МОИ ПЕРСОНАЖИ", "Продолжить или импортировать", "ОТКРЫТЬ") { open("characters") }
        Spacer(Modifier.height(20.dp))
        OutlinedButton(onClick = { open("settings") }, modifier = Modifier.fillMaxWidth()) { Text("Ещё") }
        Spacer(Modifier.height(28.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End, verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) { Switch(checked = dark, onCheckedChange = changeTheme); Spacer(Modifier.width(8.dp)); Text("Тёмная тема") }
    }
}

@Composable private fun HomeCard(title: String, subtitle: String, action: String, onClick: () -> Unit) {
    Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) { Column(Modifier.padding(22.dp)) { Text(title, style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.onSurface); Spacer(Modifier.height(10.dp)); Text(subtitle, color = MaterialTheme.colorScheme.onSurfaceVariant); Spacer(Modifier.height(14.dp)); Button(onClick = onClick) { Text(action) } } }
}

@Composable private fun SectionScreen(title: String, subtitle: String, back: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text(title, style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.onSurface)
        Spacer(Modifier.height(12.dp))
        Text(subtitle, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(24.dp))
        OutlinedButton(onClick = back) { Text("Назад") }
    }
}

@Composable private fun LibraryScreen(back: () -> Unit) {
    val tabs = listOf("Классы", "Происхождения", "Навыки", "Заклинания", "Предметы")
    val selected = remember { mutableStateOf(0) }
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Text("Библиотека", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.onSurface)
        Spacer(Modifier.height(14.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) { tabs.forEachIndexed { i, tab -> FilterChip(selected.value == i, { selected.value = i }, label = { Text(tab) }) } }
        Spacer(Modifier.height(18.dp))
        val entries = when (selected.value) { 0 -> listOf("Воин", "Волшебник", "Плут", "Жрец"); 1 -> listOf("Человек", "Эльф", "Дворф", "Гном"); 2 -> listOf("Акробатика", "Атлетика", "Медицина", "Скрытность"); 3 -> listOf("Искра", "Щит", "Лечебное заклинание", "Огненный шар"); else -> listOf("Длинный меч", "Кожаная броня", "Зелье лечения", "Рюкзак") }
        entries.forEach { entry -> Card(Modifier.fillMaxWidth().padding(vertical = 4.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) { Column(Modifier.padding(14.dp)) { Text(entry, style = MaterialTheme.typography.titleMedium); Text("Описание будет добавлено на этапе библиотек", color = MaterialTheme.colorScheme.onSurfaceVariant) } } }
        Spacer(Modifier.height(12.dp)); OutlinedButton(onClick = back) { Text("Назад") }
    }
}







