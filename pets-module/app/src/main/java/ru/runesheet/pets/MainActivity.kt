package ru.runesheet.pets

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

enum class PetType(val title: String) { ANIMAL("Верный зверь"), FAMILIAR("Фамильяр"), EIDOLON("Эйдолон"), CONSTRUCT("Конструкт") }
data class RunePet(val id: Long, val name: String, val type: PetType, val level: Int)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) { super.onCreate(savedInstanceState); setContent { MaterialTheme { PetsScreen() } } }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable fun PetsScreen() {
    var pets by remember { mutableStateOf(listOf<RunePet>()) }
    var showAdd by remember { mutableStateOf(false) }
    Scaffold(topBar = { TopAppBar(title = { Text("Питомцы RuneSheet") }) }, floatingActionButton = { FloatingActionButton(onClick = { showAdd = true }) { Text("+") } }) { pad ->
        if (pets.isEmpty()) Box(Modifier.padding(pad).padding(24.dp)) { Text("Питомцев пока нет. Нажмите +, чтобы добавить.") }
        else LazyColumn(Modifier.padding(pad).fillMaxSize(), contentPadding = PaddingValues(12.dp)) { items(pets) { pet -> Card(Modifier.fillMaxWidth().padding(vertical = 5.dp)) { Column(Modifier.padding(16.dp)) { Text(pet.name, style = MaterialTheme.typography.titleMedium); Text("${pet.type.title} • уровень ${pet.level}") } } } }
    }
    if (showAdd) AddPetDialog(onDismiss = { showAdd = false }) { name, type -> pets = pets + RunePet(System.currentTimeMillis(), name, type, 1); showAdd = false }
}

@Composable fun AddPetDialog(onDismiss: () -> Unit, onAdd: (String, PetType) -> Unit) {
    var name by remember { mutableStateOf("") }; var type by remember { mutableStateOf(PetType.ANIMAL) }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("Новый питомец") }, text = { Column { OutlinedTextField(name, { name = it }, label = { Text("Имя") }); Spacer(Modifier.height(12.dp)); PetType.entries.forEach { t -> Row { RadioButton(type == t, { type = t }); Text(t.title, Modifier.padding(top = 12.dp)) } } } }, confirmButton = { TextButton(onClick = { if (name.isNotBlank()) onAdd(name, type) }) { Text("Добавить") } }, dismissButton = { TextButton(onClick = onDismiss) { Text("Отмена") } })
}
