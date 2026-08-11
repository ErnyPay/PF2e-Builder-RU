# PF2e Builder RU — native Android app

Это самостоятельный Android-модуль PF2e Builder RU. Он не содержит и не патчит код Pathbuilder.

## Уже работает

- собственный `applicationId`: `com.pf2ebuilder.ru.builderx`;
- Kotlin + Jetpack Compose;
- список локальных персонажей;
- создание и редактирование базовой карточки персонажа;
- удаление с подтверждением;
- постоянное локальное сохранение;
- JSON export/import через Android Storage Access Framework без разрешения на общий доступ к файлам;
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

Схема намеренно маленькая: дальше она будет расширяться версионированными блоками характеристик, навыков, черт, экипировки и заклинаний с миграциями.

## Build stack

- Android Gradle Plugin 9.3.1;
- Gradle 9.5.0+;
- compile/target SDK 36 (временно для стабильной доступности SDK в hosted CI);
- Kotlin 2.4.10;
- Compose BOM 2026.06.00;
- JDK 17+.

## Следующий вертикальный срез

1. Room/SQLite вместо временного SharedPreferences repository;
2. характеристики и модификаторы;
3. source-controlled rules-data API;
4. выбор наследия/происхождения/класса из локального каталога;
5. миграции формата персонажа и импорт из transition/legacy сборок.
