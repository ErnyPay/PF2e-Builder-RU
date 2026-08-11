# PF2e Builder RU

Независимый русскоязычный проект-конструктор персонажей для PF2e.

> **Статус:** active development. Проект уже состоит из двух параллельных частей: переходной совместимой alpha-сборки и полностью собственного нативного Android-приложения в `native/`.

## Native app — основное направление

`native/` — наш собственный Android-код, не содержащий и не патчащий Pathbuilder.

Сейчас в нём уже есть:

- отдельный application ID `com.pf2ebuilder.ru.builderx`;
- Kotlin + Jetpack Compose;
- собственная тема и иконка;
- локальный список персонажей;
- создание, редактирование и удаление базовой карточки;
- локальное сохранение без сервера;
- собственный JSON format `pf2e-builder-ru.character` v1;
- export/import через Android Storage Access Framework;
- экран диагностики;
- unit tests и GitHub Actions build;
- **нет INTERNET permission, Firebase, Ads и Play Billing**.

GitHub Actions публикует debug APK нативной оболочки как artifact каждого успешного native build.

## Transition build

Переходный pipeline в корне репозитория умеет получить совместимый APK **локально**, отделить application ID/branding/data directory, применить проверяемые бинарные патчи и подписать результат. Он нужен как временный мост, пока функциональность переносится в собственный `native/`.

Исходный APK Pathbuilder, расшифрованные upstream-базы и приватный ключ подписи **не хранятся в публичном репозитории**.

## Rules data

`rules/` — новый source-controlled слой игровых данных. Он начинается с пустого каталога и схемы с обязательным provenance/license. Upstream DB сюда не копируется. Новые коллекции принимаются только с явным источником и правовым основанием для распространения.

```bash
python scripts/validate_rules.py rules/catalog
```

## Transition build

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

MIT в этом репозитории относится только к оригинальному коду, тестам и документации PF2e Builder RU, если отдельный файл не говорит иначе. Она не перелицензирует Pathbuilder, Paizo IP или сторонние наборы данных. См. `NOTICE.md` и `docs/LEGAL.md`.
