# PF2e Builder RU

Репозиторий разработки русскоязычного конструктора персонажей и переходной совместимой сборки.

> **Публичная визуальная идентичность transition-сборки:** **RuneSheet RU**. Она намеренно не использует название Pathbuilder, логотипы Pathfinder/Paizo или их визуальный стиль.

> **Статус:** active development. Проект состоит из двух параллельных частей: переходной совместимой сборки RuneSheet RU и полностью собственного нативного Android-приложения в `native/`.

## Native app — долгосрочная кодовая база

`native/` — наш собственный Android-код, не содержащий и не патчащий Pathbuilder.

Сейчас в нём уже есть:

- отдельный application ID `com.pf2ebuilder.ru.builderx`;
- Kotlin + Jetpack Compose;
- собственная тема и иконка;
- локальный список персонажей;
- создание, редактирование и удаление базовой карточки;
- SQLite-хранилище с миграциями;
- собственный versioned JSON format `pf2e-builder-ru.character` v2 с импортом v1;
- export/import через Android Storage Access Framework;
- шесть характеристик персонажа;
- экран диагностики;
- unit tests и GitHub Actions build;
- **нет INTERNET permission, Firebase, Ads и Play Billing**.

GitHub Actions публикует debug APK нативной оболочки как artifact каждого успешного native build.

## RuneSheet RU — transition build

Переходный pipeline в корне репозитория получает совместимый APK **локально**, применяет проверяемые бинарные патчи и наши ресурсы и подписывает результат.

Текущий редизайн `0.3.0-alpha.2`:

- display name **RuneSheet RU**;
- оригинальный rune/compass sigil;
- графитовая, бирюзовая и янтарная палитра;
- собственные стартовые карточки без inherited fantasy artwork;
- нейтральный light background вместо parchment texture;
- собственные braces/scroll decoration;
- собственная action notation `1 / 2 / 3 / R / F`;
- русские baked-in labels стартового экрана;
- нет логотипов Paizo, Pathfinder или Pathbuilder.

Transition application ID пока сохраняется как `com.pf2ebuilder.ru.builderx`, потому что его безопасное изменение в унаследованном DEX ограничено сортировкой `string_ids`. Это внутреннее техническое имя, а не продуктовый бренд.

Исходный APK Pathbuilder, расшифрованные upstream-базы и приватный ключ подписи **не хранятся в публичном репозитории**.

> Важно: новый визуальный стиль снижает риск смешения брендов, но не превращает унаследованный бинарный код или данные в нашу собственность. Публичное распространение transition APK требует отдельной проверки прав и лицензий.

## Rules data

`rules/` — source-controlled слой игровых данных. Он начинается с проектной схемы с обязательным provenance/license. Upstream DB сюда не копируется. Новые коллекции принимаются только с явным источником и правовым основанием для распространения.

```bash
python scripts/validate_rules.py rules/catalog
```

## Сборка transition APK

Требования:

- Python 3.11+;
- Java/JDK с `jarsigner`;
- Python-зависимости из `requirements.txt`;
- локально предоставленный совместимый base APK;
- локальный PKCS#12 signing key.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

export PF2E_KEYSTORE_PASSWORD='...'
python build.py \
  --base /path/to/Pathbuilder2e_256_RU_DB76_round5_polished.apk \
  --keystore /path/to/pf2e-builder-ru-signing.p12
```

Build по умолчанию проверяет SHA-256 базовой сборки, чтобы бинарные патчи не применялись к несовместимой версии.

## Документация

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Character format](docs/CHARACTER_FORMAT.md)
- [Branding](docs/BRANDING.md)
- [Inherited services](docs/UPSTREAM_SERVICES.md)
- [Distribution / licensing notes](docs/LEGAL.md)
- [Rules data](rules/README.md)

## Репозиторий и секреты

`.gitignore` запрещает APK/AAB, signing keys, локальные work/dist и другие бинарные/секретные артефакты. Приватный Android signing key должен храниться отдельно и резервироваться безопасно; его нельзя коммитить.

## Лицензия

MIT в этом репозитории относится только к оригинальному коду, тестам и документации проекта, если отдельный файл не говорит иначе. Она не перелицензирует Pathbuilder, Paizo IP или сторонние наборы данных. См. `NOTICE.md` и `docs/LEGAL.md`.
