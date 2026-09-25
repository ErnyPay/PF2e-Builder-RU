package com.pf2erus.app
import android.os.Bundle
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
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType
class MainActivity : ComponentActivity() { override fun onCreate(state: Bundle?) { super.onCreate(state); setContent { App() } } }
data class Character(val name: String, val level: String, val ancestry: String, val heroClass: String)
@Composable fun App() {
    val winter = darkColorScheme(
        primary = Color(0xFF8ED8FF),
        onPrimary = Color(0xFF003548),
        secondary = Color(0xFFB9E7FF),
        background = Color(0xFF071A2B),
        surface = Color(0xFF102B43),
        onSurface = Color(0xFFE8F6FF)
    )
    MaterialTheme(colorScheme = winter) {
        Surface(modifier = Modifier.fillMaxSize(), color = Color(0xFF071A2B)) {
            val screen = remember { mutableStateOf("home") }
            val characters = remember { mutableStateListOf<Character>() }
            when (screen.value) {
                "home" -> HomeScreen { screen.value = it }
                "characters" -> CharactersScreen(characters, { screen.value = "create" }, { screen.value = "home" })
                "create" -> CreateScreen({ character -> characters.add(character); screen.value = "characters" }, { screen.value = "home" })
                else -> SectionScreen("Настройки", "Язык, тема и параметры приложения") { screen.value = "home" }
            }
        }
    }
}

@Composable private fun CharactersScreen(items: List<Character>, create: () -> Unit, back: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text("Персонажи", style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(Modifier.height(16.dp))
        if (items.isEmpty()) Text("Персонажей пока нет", color = Color.LightGray)
        items.forEach { character -> Card(Modifier.fillMaxWidth().padding(vertical = 5.dp)) { Column(Modifier.padding(16.dp)) { Text(character.name); Text("${character.ancestry} · ${character.heroClass} · уровень ${character.level}") } } }
        Spacer(Modifier.height(16.dp))
        Button(onClick = create, modifier = Modifier.fillMaxWidth()) { Text("Создать персонажа") }
        OutlinedButton(onClick = back) { Text("Назад") }
    }
}

@Composable private fun CreateScreen(save: (Character) -> Unit, back: () -> Unit) {
    val name = remember { mutableStateOf("") }
    val level = remember { mutableStateOf("1") }
    val ancestry = remember { mutableStateOf("Человек") }
    val heroClass = remember { mutableStateOf("Воин") }
    val ancestryOpen = remember { mutableStateOf(false) }
    val classOpen = remember { mutableStateOf(false) }
    val ancestries = listOf("Человек", "Эльф", "Дворф", "Гном", "Полурослик")
    val classes = listOf("Воин", "Волшебник", "Плут", "Жрец", "Рейнджер")
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text("Новый персонаж", style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(name.value, { name.value = it }, label = { Text("Имя") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(level.value, { level.value = it.filter(Char::isDigit) }, label = { Text("Уровень") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.fillMaxWidth(), singleLine = true)
        Spacer(Modifier.height(10.dp))
        Box {
            OutlinedButton(onClick = { ancestryOpen.value = true }, modifier = Modifier.fillMaxWidth()) { Text("Происхождение: ${ancestry.value}") }
            DropdownMenu(expanded = ancestryOpen.value, onDismissRequest = { ancestryOpen.value = false }) { ancestries.forEach { item -> DropdownMenuItem(text = { Text(item) }, onClick = { ancestry.value = item; ancestryOpen.value = false }) } }
        }
        Spacer(Modifier.height(10.dp))
        Box {
            OutlinedButton(onClick = { classOpen.value = true }, modifier = Modifier.fillMaxWidth()) { Text("Класс: ${heroClass.value}") }
            DropdownMenu(expanded = classOpen.value, onDismissRequest = { classOpen.value = false }) { classes.forEach { item -> DropdownMenuItem(text = { Text(item) }, onClick = { heroClass.value = item; classOpen.value = false }) } }
        }
        Spacer(Modifier.height(18.dp))
        Button(onClick = { save(Character(name.value, level.value, ancestry.value, heroClass.value)) }, modifier = Modifier.fillMaxWidth(), enabled = name.value.isNotBlank()) { Text("Сохранить персонажа") }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = back) { Text("Отмена") }
    }
}

@Composable private fun HomeScreen(open: (String) -> Unit) {
    Scaffold(bottomBar = { NavigationBar { NavigationBarItem(true, { }, icon = { Text("♙") }, label = { Text("Персонажи") }); NavigationBarItem(false, { }, icon = { Text("✦") }, label = { Text("Библиотека") }); NavigationBarItem(false, { open("settings") }, icon = { Text("⚙") }, label = { Text("Настройки") }) } }) { padding ->
        Column(Modifier.fillMaxSize().padding(padding).padding(20.dp)) {
            Text("2eRUS", style = MaterialTheme.typography.headlineLarge, color = Color(0xFFE8F6FF))
            Text("PF2e Character Builder", color = Color(0xFFB9D9EA))
            Spacer(Modifier.height(24.dp))
            Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color(0xFF163A59))) { Column(Modifier.padding(18.dp)) { Text("Мои персонажи", style = MaterialTheme.typography.titleLarge); Text("Создайте первого героя", color = Color(0xFFB9D9EA)); Spacer(Modifier.height(14.dp)); Button(onClick = { open("create") }) { Text("Создать персонажа") } } }
            Spacer(Modifier.height(16.dp))
            Text("Быстрый доступ", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            OutlinedButton(onClick = { open("characters") }, modifier = Modifier.fillMaxWidth()) { Text("Открыть список персонажей") }
        }
    }
}

@Composable private fun SectionScreen(title: String, subtitle: String, back: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text(title, style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(Modifier.height(12.dp))
        Text(subtitle, color = Color.LightGray)
        Spacer(Modifier.height(24.dp))
        OutlinedButton(onClick = back) { Text("Назад") }
    }
}
