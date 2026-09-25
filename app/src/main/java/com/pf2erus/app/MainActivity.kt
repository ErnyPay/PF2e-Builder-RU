package com.pf2erus.app
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
class MainActivity : ComponentActivity() { override fun onCreate(state: Bundle?) { super.onCreate(state); setContent { App() } } }
@Composable fun App() {
    MaterialTheme(colorScheme = darkColorScheme()) {
        Surface(modifier = Modifier.fillMaxSize(), color = Color(0xFF121212)) {
            val screen = remember { mutableStateOf("home") }
            when (screen.value) {
                "home" -> HomeScreen { screen.value = it }
                "characters" -> SectionScreen("Персонажи", "Здесь будут сохранённые персонажи") { screen.value = "home" }
                "create" -> SectionScreen("Создать персонажа", "Выбор ancestry, класса и характеристик") { screen.value = "home" }
                else -> SectionScreen("Настройки", "Язык, тема и параметры приложения") { screen.value = "home" }
            }
        }
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
