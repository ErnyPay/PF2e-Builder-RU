package com.pf2erus.app
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
class MainActivity : ComponentActivity() { override fun onCreate(state: Bundle?) { super.onCreate(state); setContent { App() } } }
@Composable fun App() {
    MaterialTheme(colorScheme = darkColorScheme()) {
        Surface(modifier = Modifier.fillMaxSize(), color = Color(0xFF121212)) {
            Column(modifier = Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center) {
                Text("2eRUS", style = MaterialTheme.typography.displayMedium, color = Color.White)
                Spacer(Modifier.height(16.dp))
                Text("Конструктор персонажей PF2e", color = Color.LightGray)
                Spacer(Modifier.height(24.dp))
                Button(onClick = {}) { Text("Начать") }
            }
        }
    }
}
