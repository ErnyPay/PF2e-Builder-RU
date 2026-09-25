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
    MaterialTheme(colorScheme = darkColorScheme()) {
        Surface(modifier = Modifier.fillMaxSize(), color = Color(0xFF121212)) {
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
    Column(Modifier.fillMaxSize().padding(24.dp)) {
        Text("Новый персонаж", style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(name.value, { name.value = it }, label = { Text("Имя") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(level.value, { level.value = it.filter(Char::isDigit) }, label = { Text("Уровень") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.fillMaxWidth(), singleLine = true)
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(ancestry.value, { ancestry.value = it }, label = { Text("Происхождение") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Spacer(Modifier.height(10.dp))
        OutlinedTextField(heroClass.value, { heroClass.value = it }, label = { Text("Класс") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Spacer(Modifier.height(18.dp))
        Button(onClick = { save(Character(name.value, level.value, ancestry.value, heroClass.value)) }, modifier = Modifier.fillMaxWidth(), enabled = name.value.isNotBlank()) { Text("Сохранить персонажа") }
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = back) { Text("Отмена") }
    }
}

@Composable private fun HomeScreen(open: (String) -> Unit) {
    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
        Text("2eRUS", style = MaterialTheme.typography.displayMedium, color = Color.White)
        Text("Конструктор персонажей PF2e", color = Color.LightGray)
        Spacer(Modifier.height(28.dp))
        Button(onClick = { open("characters") }, modifier = Modifier.fillMaxWidth()) { Text("Персонажи") }
        Spacer(Modifier.height(10.dp))
        Button(onClick = { open("create") }, modifier = Modifier.fillMaxWidth()) { Text("Создать персонажа") }
        Spacer(Modifier.height(10.dp))
        OutlinedButton(onClick = { open("settings") }, modifier = Modifier.fillMaxWidth()) { Text("Настройки") }
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
