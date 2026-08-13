# PF2e Builder RU — native Android app

Это самостоятельный Android-модуль PF2e Builder RU. Он не содержит и не патчит код Pathbuilder.

## Уже работает

- собственный `applicationId`: `com.pf2ebuilder.ru.builderx`;
- Kotlin + Jetpack Compose;
- локальный список персонажей;
- создание и редактирование базовой карточки персонажа;
- шесть модификаторов характеристик: Сила, Ловкость, Выносливость, Интеллект, Мудрость, Харизма;
- удаление с подтверждением;
- собственная SQLite `pf2e-builder-ru.db`;
- SQLite migration v1 -> v2 и миграция раннего SharedPreferences storage;
- JSON character format v2 с импортом v1;
- JSON export/import через Android Storage Access Framework;
- diagnostics screen;
- unit-тесты базовой валидации/форматирования;
- **нет** разрешения INTERNET;
- **нет** Firebase, Ads и Play Billing зависимостей;
- версия `0.2.0-dev` / versionCode `300`.

## Два независимых versioned storage boundaries

- SQLite — внутреннее локальное хранилище и собственные DB migrations;
- JSON `pf2e-builder-ru.character` — переносимый формат для backup/share/import с отдельными format migrations.

Это позволяет менять внутреннюю схему приложения без привязки пользовательских экспортов к SQLite implementation details.

## Build stack

- Android Gradle Plugin 9.3.1;
- Gradle 9.5.0+;
- compile/target SDK 36 (временно для стабильной доступности SDK в hosted CI);
- Kotlin 2.4.10;
- Compose BOM 2026.06.00;
- JDK 17+.

## Следующий вертикальный срез

1. owned rules catalog runtime loader;
2. stable-ID выбор наследия/происхождения/класса;
3. профiciencies/skills и derived calculations;
4. нормализованные дочерние таблицы для repeating selections;
5. transition/legacy character migration adapter.
