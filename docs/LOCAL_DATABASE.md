# Native local database

PF2e Builder RU owns a local SQLite database named `pf2e-builder-ru.db`.

## Schema v2

Table `characters`:

- `id TEXT PRIMARY KEY` — stable character UUID;
- `name TEXT`;
- `level INTEGER`;
- `ancestry TEXT`;
- `background TEXT`;
- `class_name TEXT`;
- `strength INTEGER`;
- `dexterity INTEGER`;
- `constitution INTEGER` — displayed in RU UI as «Выносливость»;
- `intelligence INTEGER`;
- `wisdom INTEGER`;
- `charisma INTEGER`;
- `notes TEXT`;
- `updated_at INTEGER`.

`updated_at` is indexed and currently drives the default most-recently-edited ordering.

## Migrations

### SharedPreferences -> SQLite v1

The first SQLite repository automatically imports the temporary `characters-v1` SharedPreferences collection from earlier native dev builds and then removes that legacy JSON payload.

### SQLite v1 -> v2

Six attribute-modifier columns are added with a safe default of `0`. Existing characters survive the upgrade unchanged in every pre-existing field.

## Policy

Future database versions must use explicit migrations. The helper intentionally fails loudly when a version bump has no migration rather than silently destroying user characters.

As the character model grows, normalized child tables will be introduced for selections, feats, equipment, spells and other repeating structures. The JSON export format remains the portable compatibility boundary and evolves independently through its own versioned migrations.
