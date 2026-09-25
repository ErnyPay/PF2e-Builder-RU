plugins { id("com.android.application"); id("org.jetbrains.kotlin.plugin.compose") }
android { namespace = "com.pf2erus.app"; compileSdk = 36
    defaultConfig { applicationId = "com.pf2erus.app"; minSdk = 32; targetSdk = 36; versionCode = 1; versionName = "0.1.0-alpha.1" }
    buildFeatures { compose = true }
}
dependencies {
    implementation(platform("androidx.compose:compose-bom:2026.02.01"))
    implementation("androidx.activity:activity-compose:1.8.0")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
}
