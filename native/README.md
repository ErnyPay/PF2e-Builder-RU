# PF2e Builder RU — native Android app

Это самостоятельный Android-модуль PF2e Builder RU. Он не содержит и не патчит код Pathbuilder.

## Уже работает

- собственный `applicationId`: `com.pf2ebuilder.ru.builderx`;
- Kotlin + Jetpack Compose;
- локальный список персонажей;
- создание и редактирование базовой карточки персонажа;
- удаление с подтверждением;
- постоянное хранение в собственной SQLite `pf2e-builder-ru.db`;
- автоматическая миграция раннего dev-хранилища SharedPreferences -> SQLite;
- JSON export/import через Android Storage Access Framework без общего file permission;
- diagnostics screen;
- unit-тесты базовой валидации;
- **нет** разрешения INTERNET;
- **нет** Firebase, Ads и Play Billing зависимостей;
- версия `0.2.0-dev` / versionCode `300`.

## Формат персонажа v1

Экспортируемый файл имеет схему `pf2e-builder-ru.character`, версию `1` и пока хранит базовые поля:

- id;
- имя;
- уровень;
- наследие;
- происхождение;
- класс;
- заметки.

JSON остаётся переносимым внешним форматом, а SQLite — внутренним persistent storage. Они версионируются отдельно.

## Build stack

- Android Gradle Plugin 9.3.1;
- Gradle 9.5.0+;
- compile/target SDK 36 (временно для стабильной доступности SDK в hosted CI);
- Kotlin 2.4.10;
- Compose BOM 2026.06.00;
- JDK 17+.

## Следующий вертикальный срез

1. typed character model: характеристики, защиты и навыки;
2. source-controlled rules-data API;
3. выбор наследия/происхождения/класса из локального каталога;
4. нормализованные дочерние таблицы для повторяющихся selections;
5. миграции формата персонажа и импорт из transition/legacy сборок.
