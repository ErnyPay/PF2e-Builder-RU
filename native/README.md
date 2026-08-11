# PF2e Builder RU — native Android shell

Это начало самостоятельного Android-приложения. В отличие от transition APK в корне проекта, этот модуль **не содержит и не патчит код Pathbuilder**.

## Текущее состояние

- собственный `applicationId`: `com.pf2ebuilder.ru.builderx` (совпадает с alpha-переходником для будущего бесшовного обновления);
- Kotlin + Jetpack Compose;
- локальный стартовый экран персонажей;
- diagnostics screen;
- **нет** разрешения INTERNET;
- **нет** Firebase, Ads и Play Billing зависимостей;
- версия `0.2.0-dev` / versionCode `300`.

## Build stack

- Android Gradle Plugin 9.3.1;
- Gradle 9.5.0+;
- compile/target SDK 36 (временно для доступности стабильного Android SDK пакета в hosted CI; переход на 37 — отдельный безболезненный bump);
- Kotlin 2.4.10;
- Compose BOM 2026.06.00;
- JDK 17+.

## Следующий вертикальный срез

1. локальная модель персонажа;
2. создание/редактирование имени и уровня;
3. JSON export/import;
4. Room/SQLite storage;
5. первый rules-data интерфейс без привязки к upstream DB.
